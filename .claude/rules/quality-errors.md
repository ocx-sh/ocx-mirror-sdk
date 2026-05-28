# Error Handling

Project-specific rule for `ocx-mirror-sdk`. Companion to `quality-python.md` (universal Python anti-patterns) and `quality-core.md` (design principles). Applies to all code under `src/ocx_mirror_sdk/**` and `tests/`.

The SDK exposes ~15 public symbols and is consumed from small PEP 723 generator scripts. Callers should be able to write **one** `try / except` clause around the whole SDK and recover meaningfully.

---

## Paradigm

**Raise typed exceptions from a single hierarchy.** Do not return `Result` / `Either` wrappers. Do not return `None` to signal failure. The only exception to "raise on failure" is when *absence* is normal on a healthy system (cache miss, `dict.get` style) — see rule 7.

The hierarchy rooted at `OcxMirrorError` lives in `src/ocx_mirror_sdk/errors.py` and is re-exported from `ocx_mirror_sdk`. All public exception classes are part of the public API.

---

## Rules

1. **One base class.** Every exception raised from `src/ocx_mirror_sdk/**` inherits `OcxMirrorError`. Callers must be able to write `except OcxMirrorError:` and catch everything we throw.
2. **No bare stdlib raises from SDK code.** No `raise RuntimeError`, `raise ValueError`, `raise KeyError`, `raise TypeError` inside `src/`. Use the typed subclass that matches the failure kind. Stdlib exceptions are fine at module-import time (`ImportError`) or for genuine programmer-error guards.
3. **Always chain with `from e`** when wrapping a lower-layer exception. Ruff `B904` is enforced. The original traceback is part of the contract — debuggers and structured loggers rely on `__cause__`.
4. **`from None` only to hide an implementation detail** the caller can never act on. Add an inline comment explaining the choice.
5. **No bare `except:` / no unqualified `except Exception:`** in library code. Catch the narrowest type that crosses our trust boundary. Test fixtures and CLI entry points may catch broader to format output, but only at the outermost layer.
6. **Validate at the boundary, trust inward.** Wrap external IO (`httpx`, `json`, `github3`, on-disk reads) at the *first* SDK function that touches it. Internal helpers assume validated input — no defensive `if x is None: raise` at every layer.
7. **No `None` sentinel for exceptional cases.** Return `None` *iff* the absence is expected on a healthy system (cache miss, `re.search` no match, `dict.get`). Network failure, malformed payload, missing config — these raise.
8. **Carry typed attributes.** `HttpStatusError(status_code=503, url="...")` not stringly-typed `str(exc)` parsing at call sites. Subclass `__init__` builds the message from the attributes, never the reverse.
9. **Preserve `__cause__`.** Don't rewrap an already-SDK exception inside another SDK exception. Let it propagate. Tests assert `exc.__cause__ is original_httpx_error`.
10. **Log once, at the public boundary.** Public entry points (`list_releases`, `IndexBuilder.build`, `FileCache.fetch_json`) log at `WARNING` before raising. Internal helpers never log+raise (avoids double-logs in the consumer's output).
11. **Name everything `*Error`**, not `*Exception`. No stutter (`OcxMirrorError`, not `OcxMirrorSdkError` — the package name is already `ocx_mirror_sdk`).
12. **No `ExceptionGroup` / `except*`** until a real concurrent code path lands. Introducing PEP 654 is itself an API break — defer.

---

## Hierarchy

```
OcxMirrorError                          # single base; user does `except OcxMirrorError:`
├── ConfigurationError                  # missing GITHUB_TOKEN, github3 init failure
├── TransportError                      # base for anything from httpx / urllib3 / github3 transport
│   ├── HttpStatusError                 # attributes: status_code, url, response_text
│   └── HttpTimeoutError                # wraps httpx.TimeoutException
├── ApiResponseError                    # GraphQL "errors" array, malformed JSON, repo-not-found
│                                       # attribute: payload (dict | list | None)
├── SchemaError                         # Release.from_dict missing/typed-wrong fields
│                                       # attribute: field (str | None)
└── CacheError                          # FileCache file IO failure, corrupt on-disk JSON
                                        # attribute: path (Path | None)
```

Catch granularity:

- `except OcxMirrorError:` — catch-all for SDK failures
- `except TransportError:` — retry / backoff candidate
- `except ConfigurationError:` — surface to user, not retryable
- `except ApiResponseError, SchemaError:` — bug or upstream contract change

## Examples

```python
# Wrap a lower-layer exception at the boundary.
try:
    resp = client.get(url)
    resp.raise_for_status()
    return resp.json()
except httpx.HTTPStatusError as e:
    raise HttpStatusError(
        status_code=e.response.status_code,
        url=str(e.request.url),
        response_text=e.response.text[:1000],
    ) from e
except httpx.TimeoutException as e:
    raise HttpTimeoutError(url=url) from e
except json.JSONDecodeError as e:
    raise ApiResponseError(payload=None) from e
```

```python
# Cache miss is NORMAL — return None.
data = self.get(key)
if data is None:
    data = loader()
    self.put(key, data)
return data

# Cache CORRUPTION is exceptional — raise.
try:
    return json.loads(self._path(key).read_bytes())
except json.JSONDecodeError as e:
    raise CacheError(path=self._path(key)) from e
```

```python
# Public boundary: log once, then raise.
log = logging.getLogger(__name__)

def list_releases(owner: str, repo: str, ...) -> list[Release]:
    try:
        return _do_list_releases(owner, repo, ...)
    except OcxMirrorError as e:
        log.warning("list_releases failed for %s/%s: %s", owner, repo, e)
        raise
```

---

## Sources

- [PEP 3134 — Exception Chaining and Embedded Tracebacks](https://peps.python.org/pep-3134/)
- [PEP 409 — Suppressing exception context](https://peps.python.org/pep-0409/)
- [PEP 654 — Exception Groups and `except*`](https://peps.python.org/pep-0654/)
- [Google Python Style Guide §2.4 Exceptions](https://google.github.io/styleguide/pyguide.html#24-exceptions)
- [HTTPX exception hierarchy](https://www.python-httpx.org/exceptions/)
- [anthropic-sdk-python — error model](https://github.com/anthropics/anthropic-sdk-python#handling-errors)
