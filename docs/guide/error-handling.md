# Error handling

Every exception raised from `ocx_mirror_sdk` inherits from
`OcxMirrorError`. One `except` clause catches everything; subclass
matching gives finer control.

## The hierarchy

```text
OcxMirrorError
├── ConfigurationError       missing GITHUB_TOKEN, client init failed
├── TransportError           base for network errors
│   ├── HttpStatusError      .status_code, .url, .response_text
│   └── HttpTimeoutError     .url
├── ApiResponseError         malformed JSON, GraphQL errors, repo not found
├── SchemaError              Release.from_dict field mismatch
└── CacheError               disk IO / corrupt JSON (NOT cache miss)
```

## The catch-all

```python
from ocx_mirror_sdk import OcxMirrorError, list_releases

try:
    releases = list_releases("o", "r")
except OcxMirrorError as e:
    log.warning("SDK call failed: %s", e)
    raise
```

## Selective catch

```python
from ocx_mirror_sdk import (
    ConfigurationError, ApiResponseError, TransportError, HttpStatusError,
)

try:
    releases = list_releases("o", "r")
except ConfigurationError as e:
    # Bad config — surface to user, do not retry
    sys.exit(64)  # EX_USAGE
except HttpStatusError as e:
    if e.status_code == 404:
        # Repo really doesn't exist
        ...
    elif e.status_code >= 500:
        # Transient — retry candidate
        ...
except TransportError:
    # Timeouts / connect errors — backoff + retry
    ...
except ApiResponseError as e:
    # Upstream contract violation
    log.error("bad payload: %r", e.payload)
    raise
```

## `__cause__` preserves the original

The SDK wraps `httpx.HTTPStatusError`, `httpx.TimeoutException`,
`json.JSONDecodeError`, `KeyError`, and `OSError` — but never loses
the original. Inspect via `exc.__cause__`:

```python
try:
    list_releases("o", "r")
except HttpStatusError as e:
    print(e.__cause__)  # httpx.HTTPStatusError(...)
```

## Cache miss is **not** an error

`FileCache.get()` returns `None` on miss — that's normal control flow.
Only `CacheError` indicates an abnormal cache state (corrupt file,
permission denied).

## What the SDK never raises

- Stdlib exceptions like bare `ValueError`, `RuntimeError`, `KeyError`
  from inside SDK code (`Backend("foo")` is the one deliberate
  exception — `ValueError` from the stdlib `StrEnum` constructor).
- `httpx.HTTPStatusError`, `httpx.TimeoutException`, `httpx.RequestError`.
- `json.JSONDecodeError`.

If you catch one of these from an `ocx_mirror_sdk` call, that's a bug —
file an issue.

## See also

- [`api/errors.md`](../api/errors.md) — full reference for each class.
- [`examples/05_error_handling.py`](https://github.com/ocx-sh/ocx-mirror-sdk/blob/main/examples/05_error_handling.py) —
  retry-with-backoff pattern.
- Project rule: `.claude/rules/quality-errors.md` in the repo.
