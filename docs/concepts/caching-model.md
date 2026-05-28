# Caching model

`FileCache` is a thin TTL-based disk cache. It sits between `list_releases`
and the GitHub API so repeat runs of a generator (e.g. during local
development) don't burn the rate limit.

## What gets cached

| Cache | Default TTL | Key | Backend |
|---|---|---|---|
| REST release list | 1 h | `{owner}/{repo}/releases` | both |
| GraphQL release list | 1 h | `{owner}/{repo}/releases` | GraphQL only |
| GraphQL asset list | 7 d | `{owner}/{repo}/{tag}` | GraphQL only |

The asset cache has a long TTL because GitHub assets are immutable once
published — refetching gains nothing.

## Where it lives

By default: `~/.cache/ocx-mirror-sdk/<domain>/<key>`.

Each cache instance is a "domain" (a subdirectory). In CI, redirect the
root once at the top of your script so the cache lives next to the build
artifacts:

```python
from pathlib import Path
from ocx_mirror_sdk import configure

configure(cache_root=Path(".cache/ocx-mirror-sdk"))
```

## Cache miss is normal

`FileCache.get()` returns `None` on miss. Generators don't need to handle
the miss explicitly — `list_releases` does. The cache only raises
`CacheError` if the on-disk file exists but cannot be read or is corrupt
JSON (a genuinely abnormal event).

See the [Caching guide](../guide/caching.md) for invalidation strategies
and per-call overrides.
