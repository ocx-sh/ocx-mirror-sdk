# Fetching releases

`list_releases(owner, repo, *, backend=Backend.REST, ...)` is the only
entry point. The `backend` kwarg picks between two implementations.

## REST vs GraphQL

| | `Backend.REST` (default) | `Backend.GRAPHQL` |
|---|---|---|
| Library | `github3.py` | `httpx` |
| Auth | Optional (`GITHUB_TOKEN`) | **Required** |
| Rate limit (unauthed) | 60 req/h | n/a (auth required) |
| Rate limit (authed) | 5 000 req/h | 5 000 points/h |
| Big repos (≥100 assets/release) | May 504 | OK |
| Fetches release notes (`body`) | Yes | No (empty string) |
| Release list TTL | 1 h | 1 h |
| Asset list TTL | n/a (single payload) | 7 d (immutable) |

### Pick REST when

- Repo is small (well under a thousand assets per release).
- You don't have / don't want to use a `GITHUB_TOKEN` locally.
- You need release-note `body` (e.g. to feed [`extract_urls`](filtering-urls.md)).

### Pick GraphQL when

- The REST endpoint returns 504s on a repo with many assets per release
  (e.g. `python-build-standalone`, `corretto`).
- You're running in CI where `GITHUB_TOKEN` is already available.

## Passing `Backend`

The enum and raw strings both work:

```python
list_releases("o", "r", backend=Backend.GRAPHQL)
list_releases("o", "r", backend="graphql")          # equivalent
list_releases("o", "r", backend="foo")              # ValueError
```

Unknown backend values are rejected by the `Backend` constructor —
your typo never reaches the network.

## Filtering

`include_prereleases=False` and `include_drafts=False` filter the
returned list. Filters are applied **after** the cache, so changing
them doesn't invalidate the cache or force a refetch:

```python
list_releases("o", "r", include_prereleases=False)
```

## Dependency injection

For tests, pass a transport-mocked client:

```python
import httpx

def handler(request):
    return httpx.Response(200, json={...})

list_releases(
    "o", "r",
    backend=Backend.GRAPHQL,
    client=httpx.Client(transport=httpx.MockTransport(handler)),
)
```

REST has an analogous `session=github3.GitHub | None` hook.
