# Fetching releases

Each release source has its own entry point in a provider namespace:

| Source | Call | Transports |
|---|---|---|
| GitHub | `github.list_releases` | REST + GraphQL (`backend=`) |
| GitLab | `gitlab.list_releases` | REST |

All of them return the same source-agnostic
[`Release`](../api/releases.md#release) objects, so the rest of your generator
(filtering, `IndexBuilder`) is identical regardless of source.

## GitHub

`github.list_releases("owner/repo", *, backend=github.Backend.REST, ...)` is the
GitHub entry point. The `backend` kwarg picks between two implementations.

## REST vs GraphQL

| | `Backend.REST` (default) | `Backend.GRAPHQL` |
|---|---|---|
| Library | `httpx` | `httpx` |
| Auth | Optional (`GITHUB_TOKEN`) | **Required** |
| Rate limit (unauthed) | 60 req/h | n/a (auth required) |
| Rate limit (authed) | 5 000 **req**/h | 5 000 **points**/h |
| Cost per full crawl | A handful of requests (assets inline) | Hundreds of points (asset pagination) |
| Big repos (≥100 assets/release) | OK (auto-pages smaller on 504) | OK, but burns points fast |
| Fetches release notes (`body`) | Yes | No (empty string) |
| Release list TTL | 1 h | 1 h |
| Asset list TTL | n/a (single payload) | 7 d (immutable) |

### Pick REST when

- **Almost always** — it is the default and far cheaper on the rate budget
  (request-count limited, with all assets returned inline). It now pages at
  `per_page=100` and transparently falls back to a small page size on a
  502/503/504/timeout, so asset-heavy repos (`python-build-standalone`,
  `corretto`) no longer need GraphQL.
- You need release-note `body` (e.g. to feed [`extract_urls`](filtering-urls.md)).

### Pick GraphQL when

- You have a specific reason REST cannot serve a repo. Note its limit is a
  **points** budget (≈5 000/h, shared across concurrent CI jobs) that a heavy
  crawl exhausts quickly — prefer REST unless you have measured otherwise.

## Passing `Backend`

The enum and raw strings both work:

```python
github.list_releases("o/r", backend=github.Backend.GRAPHQL)
github.list_releases("o/r", backend="graphql")          # equivalent
github.list_releases("o/r", backend="foo")              # ValueError
```

Unknown backend values are rejected by the `Backend` constructor —
your typo never reaches the network.

## Filtering

`include_prereleases=False` and `include_drafts=False` filter the
returned list. Filters are applied **after** the cache, so changing
them doesn't invalidate the cache or force a refetch:

```python
github.list_releases("o/r", include_prereleases=False)
```

## Dependency injection

For tests, pass a transport-mocked client:

```python
import httpx

def handler(request):
    return httpx.Response(200, json={...})

github.list_releases(
    "o/r",
    backend=github.Backend.GRAPHQL,
    client=httpx.Client(transport=httpx.MockTransport(handler)),
)
```

The same `client=httpx.Client | None` hook works for `Backend.REST` — both
backends share the injected client.

## GitLab

`gitlab.list_releases("namespace/project", *, host="https://gitlab.com", ...)`
fetches releases from the GitLab REST API (`httpx`, no extra dependency).

```python
from ocx_mirror_sdk import gitlab

# gitlab.com
releases = gitlab.list_releases("gitlab-org/gitlab-runner")

# self-hosted instance
releases = gitlab.list_releases("group/project", host="https://gitlab.example.com")

# nested subgroups go in the namespace; the final segment is the project
releases = gitlab.list_releases("group/subgroup/project")
```

| | GitLab REST |
|---|---|
| Library | `httpx` |
| Auth | Auto-selected from the environment; anonymous works on public projects |
| Self-hosted | `host=` (default `https://gitlab.com`) |
| Release notes (`body`) | Yes (`description`) |
| Release list TTL | 1 h |

### Authentication

The token and header are picked from the environment automatically, so the
same script runs locally and inside a GitLab CI/CD pipeline unchanged
(precedence — first match wins):

| Env var | Header sent | Typical source |
|---|---|---|
| `GITLAB_TOKEN` | `PRIVATE-TOKEN` | Personal / project / group access token you set |
| `CI_JOB_TOKEN` | `JOB-TOKEN` | Injected automatically into every GitLab CI/CD job |

`GITLAB_TOKEN` wins when both are present — an access token you set
explicitly has broader scope than the short-lived job token. With neither
set, requests are anonymous (fine for public projects). See the
[GitLab REST API authentication docs](https://docs.gitlab.com/api/rest/authentication/).

Field mapping into [`Release`](../api/releases.md#release):

- `prerelease` ← GitLab's `upcoming_release` flag.
- `draft` is always `False` — GitLab has no draft releases, so
  `include_drafts` is not a parameter here.
- `assets` ← author-curated `assets.links` (preferring `direct_asset_url`).
  Auto-generated source archives (`assets.sources`) are not included.

`include_prereleases=False` and dependency injection (`cache=`, `client=`)
work exactly as on the GitHub side.
