# Suggested Commands

All commands assume `direnv allow` has been run (or session has `eval "$(ocx env --shell=sh)"`). Otherwise prefix with `ocx run -- `.

## Dev loop

| Command | Purpose |
|---|---|
| `task` | Default → runs `task verify` |
| `task verify` | Full gate: `format:check` → `lint` → `types` → `test` (run before every commit) |
| `task test` | pytest only |
| `task lint` | `ruff check src tests` |
| `task types` | `pyright` |
| `task format` | Apply `ruff format` |
| `task format:check` | Format check (no write); used by `verify` |
| `task schema:fetch` | Re-pull `https://ocx.sh/schemas/url-index/v1.json` into `schemas/` |
| `task codegen` | Regenerate `src/ocx_mirror_sdk/_schema.py` from fetched schema |

Override the schema source for local dev / PR preview: `SCHEMA_URL=… task codegen`.

## Targeted test runs

```
uv run --extra dev pytest tests/test_index.py -k "version"
uv run --extra dev pytest -x        # stop on first failure
```

## OCX meta

| Command | Purpose |
|---|---|
| `ocx run -- task verify` | Run the gate without an activated env |
| `ocx env --shell=sh` | Print eval-able env activation |
| `ocx direnv export` | Used by `.envrc`; rarely run by hand |

## Git / GitHub

Standard `git` + `gh`. Never push to `main`; PR workflow only.

## Linux notes

Host is Linux — standard GNU coreutils. No BSD/macOS-specific flags needed. Use `rg`/`grep` as normal (this repo is small; either fine).
