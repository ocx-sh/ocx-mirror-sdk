# Troubleshooting

## `ConfigurationError: GITHUB_TOKEN is required`

You're using `Backend.GRAPHQL`. The GraphQL API has no anonymous access.

Fix:

```bash
export GITHUB_TOKEN=ghp_...
```

In CI:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## `HttpStatusError: HTTP 504 for https://api.github.com/...`

REST gateway-timeouted on a repo with many assets per release. Switch
to GraphQL:

```python
list_releases("o", "r", backend=Backend.GRAPHQL)
```

## `HttpStatusError: HTTP 403 for https://api.github.com/...` (rate limit)

Unauthenticated REST is capped at 60 req/h. Authenticate:

```bash
export GITHUB_TOKEN=ghp_...
```

Authenticated REST is capped at 5 000 req/h. If you hit that, lengthen
the cache TTL or switch to GraphQL (more efficient per-call cost).

## `ApiResponseError: repository not found: o/r`

The `(owner, repo)` pair doesn't exist or your token can't see it.
Check the spelling and (for private repos) that the token has `repo`
scope.

## Cache "stale" — I want a fresh fetch

```bash
rm -rf ~/.cache/ocx-mirror-sdk/github/owner/repo
```

Or per-call:

```python
from ocx_mirror_sdk import FileCache, list_releases

list_releases("o", "r", cache=FileCache("github", max_age=0))
```

## `mkdocstrings` complains about `_schema.py` during docs build

`mkdocstrings` is configured to skip private modules (`filters: ["!^_"]`).
If you see warnings, make sure your `mkdocs.yml` matches the one in this
repo — the filter must include `!^_`.

## Imports fail with `ImportError: cannot import name ...`

You're on a tag older than the breaking change you're trying to use.
Bump the tag — see the [release notes](https://github.com/ocx-sh/ocx-mirror-sdk/releases).

| Symptom | Tag you need |
|---|---|
| Can't import `Backend` | ≥ v0.3.0 |
| Can't import `OcxMirrorError` | ≥ v0.3.0 |
| `list_releases_graphql` removed | upgraded to v0.3.0 — use `list_releases(..., backend=Backend.GRAPHQL)` |
