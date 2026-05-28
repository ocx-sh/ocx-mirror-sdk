# Enums

Project-specific rule for `ocx-mirror-sdk`. Companion to `quality-python.md` (universal Python anti-patterns). Applies to closed-set named choices that appear on the SDK's public API or cross any module boundary.

Bare strings (`backend="rest"`) are convenient at the call site but lose type safety, IDE autocomplete, and runtime validation. Pick the right construct on the first attempt — promoting later means a breaking change.

---

## Decision matrix

| Construct | When to use |
|---|---|
| **`StrEnum`** (3.11+ stdlib) | Closed set of named choices crossing the public API, especially if the value is serialized to JSON / CLI / env var. Default for SDK kwargs. |
| **`IntEnum`** | Closed set of integer wire values (HTTP status codes, exit codes). |
| **`Enum`** (plain) | Opaque internal tokens never serialized — state-machine states, debug flags. |
| **`Literal[...]`** | Pure static-type narrowing for a one-off kwarg in a single function, never serialized, no runtime validation needed. Promote to `StrEnum` once a second public callsite uses the same set. |

`backend=` on `list_releases` is the canonical SDK kwarg pattern → **`StrEnum`** (`Backend.REST`, `Backend.GRAPHQL`).

---

## Rules

1. **Closed set crossing the public API → `StrEnum`.** Strings on the wire, enum in code. Type checkers narrow correctly; callers get autocomplete; raw string input still works because `StrEnum` *is* `str`.
2. **Integer wire values → `IntEnum`.**
3. **Opaque internal tokens never serialized → plain `Enum`.**
4. **Pure type narrowing for a single private use → `Literal[...]` allowed.** Promote to `StrEnum` once a second public callsite appears.
5. **Coerce input via the constructor**: `Backend(value)`, never `Backend[value]`. The constructor takes the *value* ("rest"); `[ ]` takes the *member name* ("REST"). Wrong lookup mode silently picks the wrong member.
6. **Members `UPPER_SNAKE_CASE`; values lowercase matching the wire convention.** `Backend.REST = "rest"`, never `Backend.Rest = "Rest"`.
7. **`from enum import StrEnum, auto`** — explicit import, no `import *`.
8. **No methods on enum classes** beyond `__str__` if you need to override it. Helpers (lookup tables, validators) go beside the enum as module-level functions. Keep enums tiny (KISS).
9. **Enum classes are frozen by stdlib** — don't subclass an enum that already has members. Mixin via `class MyEnum(str, Enum):` only if `StrEnum` is unavailable.
10. **Use `auto()` only when the value is implementation-detail.** If the value is a wire string, spell it out (`REST = "rest"`); future-proof against `_generate_next_value_` surprises.

---

## Examples

```python
# Public API kwarg — StrEnum.
from enum import StrEnum

class Backend(StrEnum):
    """GitHub release-fetch backend selection."""
    REST = "rest"
    GRAPHQL = "graphql"

def list_releases(owner: str, repo: str, *, backend: Backend | str = Backend.REST) -> ...:
    backend = Backend(backend)   # accepts "graphql" or Backend.GRAPHQL; rejects "foo"
    ...
```

```python
# Pure type narrowing inside a private helper — Literal is fine.
from typing import Literal

def _normalize_status(s: Literal["ok", "fail"]) -> bool:
    return s == "ok"
```

```python
# Opaque internal flag — plain Enum.
from enum import Enum, auto

class _RequestState(Enum):
    PENDING = auto()
    RUNNING = auto()
    DONE = auto()
```

---

## Sources

- [Python 3.13 — `enum` HOWTO](https://docs.python.org/3/howto/enum.html)
- [Python 3.13 — `enum` module reference](https://docs.python.org/3/library/enum.html)
- [PEP 663 — Standardizing Enum str(), repr(), and format() behaviors](https://peps.python.org/pep-0663/)
- [Google Python Style Guide — Enum usage](https://google.github.io/styleguide/pyguide.html)
- [The case for StrEnum in Python 3.11 — tsak.dev](https://tsak.dev/posts/python-enum/)
