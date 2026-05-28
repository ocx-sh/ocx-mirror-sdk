# Conventions

## Modules

- Flat layout under `src/ocx_mirror_sdk/`; one concern per file (`cache.py`, `github.py`, `github_graphql.py`, `github_types.py`, `http.py`, `index.py`, `text.py`).
- Generated code lives in files prefixed `_` (currently only `_schema.py`); generated files are excluded from lint + types via `pyproject.toml`.
- Public API is the set re-exported from `__init__.py` `__all__`. Anything not in `__all__` is internal; rename freely.

## Headers + license

Every source file starts with:

```
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors
```

## Type style (Python 3.13)

- Modern generics only: `list[T]`, `dict[K, V]`, `X | None`. No `typing.List`, `typing.Optional`.
- Annotate all public functions; ruff `ANN` rule set enforces.
- Prefer `Protocol` over `ABC` at module boundaries; `dataclass(slots=True)` where feasible (see `.claude/rules/quality-python.md`).
- `_schema.py` uses `dataclasses.dataclass` output from `datamodel-codegen` — do not hand-edit.

## Error handling

- No bare `except`. Always name exception types; chain with `from e` (`from None` only when intentionally hiding).
- Validate external input (HTTP responses, env, file contents) at the boundary; trust internals.

## Tests

- One `test_<module>.py` per public-API module. Self-contained — no `conftest.py` fixtures yet (introduce only after 2+ real consumers).
- Use `unittest.mock` for network mocks; do not hit real GitHub from tests.
- `test_schema.py` round-trips `IndexBuilder.build()` against the vendored `schemas/url-index.v1.json` via `jsonschema`.
- Treat regression tests (Phase 3 of bug-fix workflow) as the standing rule: failing test first, then fix.

## Commits

- Conventional Commits: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`. Scope optional but used (`feat(mirror-sdk): …`).
- Body explains the why, not the what.
- `!` after type for breaking changes (see `4eaa4cf feat!: rename package ocx_gen → ocx_mirror_sdk`).
- Never push to `main`; never amend a pushed commit; never skip hooks.

## Tooling discipline

- `task verify` must pass before commit.
- Use semantic edit tools (Serena `replace_symbol_body`, `insert_*`) over raw Edit for code symbols. Use `replace_content` for sub-symbol regex edits.
- Refactor + behavior change never mixed (Two Hats Rule — `.claude/rules/quality-core.md`).
