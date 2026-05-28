---
paths:
  - taskfile.yml
  - taskfiles/**/*.yml
---

# Taskfile Conventions

[Taskfile](https://taskfile.dev) v3 is the project task runner. Single root `taskfile.yml` — this repo is small enough that splitting into subsystem taskfiles is unnecessary.

## OCX Conventions

1. **`verify` is the contract.** `task verify` is the gate that must pass before commit (format check → lint → types → tests).
2. **Composite tasks aggregate subtasks.** Each tool (lint, format, types, test) gets its own task so it's independently runnable. `verify` references composite tasks only — one entry per concern.
3. **`default` runs `verify`.** Bare `task` does the right thing.

## Taskfile features in use

| Feature | Purpose |
|---|---|
| `deps:` | Sequential dependency (`codegen` depends on `schema:fetch`) |
| `desc:` | One-line description shown by `task --list` |
| Variable overrides | `SCHEMA_URL=…` lets contributors point codegen at a local file |
| `sources:` + `status:` | Cache codegen output by source file hash (add when introducing) |

## Caching contract

When adding tasks with expensive outputs, follow the standard pattern:

```yaml
codegen:
  cmds: [uv run datamodel-codegen --input {{.SCHEMA_FILE}} --output src/ocx_mirror_sdk/_schema.py ...]
  sources: ['{{.SCHEMA_FILE}}']
  status: ['test src/ocx_mirror_sdk/_schema.py -nt {{.SCHEMA_FILE}}']
```

- `sources:` — fingerprinted; change triggers re-run.
- `status:` — load-bearing skip; exit 0 means already done.
- `generates:` — documentation only (not load-bearing per [go-task #2181](https://github.com/go-task/task/issues/2181)).
- `.task/` cache directory must be in `.gitignore`.

## Includes and `dir:` scoping

Only one taskfile in this repo, so include semantics don't apply. If the repo ever grows a `taskfiles/` directory:

| Variable | Resolves to |
|---|---|
| `{{.ROOT_DIR}}` | Directory of the root (entry-point) taskfile |
| `{{.TASKFILE_DIR}}` | Directory of the currently executing taskfile |
| `{{.USER_WORKING_DIR}}` | Directory from which `task` was invoked |

## Preconditions vs status

| Field | Use | Semantics |
|---|---|---|
| `preconditions:` + `msg:` | Guard — abort if not ready | Failure aborts; downstream tasks don't run |
| `status:` | Cache — skip if done | Exit 0 = up-to-date, skip silently |

## Project-specific contract

- **`schema:fetch` reads the website.** Default URL is `https://ocx.sh/schemas/url-index/v1.json`. Override via `SCHEMA_URL=…` for local dev or PR previews.
- **`codegen` writes `_schema.py`.** Generated file is checked in so consumers (including `uv pip install git+…`) don't need network access at install time.

## Sources

- [Taskfile schema reference](https://taskfile.dev/docs/reference/schema)
- [Taskfile usage](https://taskfile.dev/usage/) — sources/status/method, run modes, env, preconditions
- [go-task #2181](https://github.com/go-task/task/issues/2181) — `generates:` globs not fingerprinted
