# Caching

The SDK caches API responses on disk so repeat runs of a generator are
cheap. You usually don't need to touch the cache directly — `list_releases`
handles it transparently. This page covers the cases where you do.

## Default behavior

| What | TTL | Where |
|---|---|---|
| REST + GraphQL release lists | 1 h | `~/.cache/ocx-mirror-sdk/github/`, `~/.cache/ocx-mirror-sdk/github-graphql/` |
| GraphQL per-release asset lists | 7 d | `~/.cache/ocx-mirror-sdk/github-graphql-assets/` |

## Redirecting the cache root

In CI you usually want the cache next to the build artifacts:

```python
from pathlib import Path
from ocx_mirror_sdk import configure

configure(cache_root=Path(".cache/ocx-mirror-sdk"))
```

`configure` is idempotent and applies to every `FileCache` that
materializes after the call. Call it once at script start.

## Per-call override

Pass `cache=` to disable caching for a specific call:

```python
from ocx_mirror_sdk import FileCache, list_releases

# Force a fresh fetch — TTL=0 means "always miss, never store"
list_releases("o", "r", cache=FileCache("github", max_age=0))
```

## Invalidation

There is no `invalidate()` method by design. To re-fetch:

- Delete the relevant subdirectory:
  ```bash
  rm -rf ~/.cache/ocx-mirror-sdk/github/owner/
  ```
- Or pass `cache=FileCache("github", max_age=0)` to bypass.

## When `CacheError` fires

The cache distinguishes "expected absence" from "abnormal failure":

| Situation | Behavior |
|---|---|
| Key not present | `get()` returns `None` (no exception) |
| Key expired | `get()` returns `None` (no exception) |
| File present but unreadable | `CacheError` |
| File present but corrupt JSON (`get_json`) | `CacheError` |
| Disk full / permission denied on `put` | `CacheError` |

This follows the project rule that `None` sentinels are reserved for
*expected* absences. See [Error handling](error-handling.md).
