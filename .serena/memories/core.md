# ocx-mirror-sdk — Core

Python SDK for authoring `ocx-mirror` generator scripts. Generators emit `url_index` JSON; `ocx-mirror` (Rust, in `ocx-sh/ocx`) republishes upstream releases as OCI artifacts. This repo is a downstream **consumer** of the `url_index` JSON Schema published at <https://ocx.sh/schemas/url-index/v1.json>.

Whole repo = one SDK. No internal subsystems. Pre-1.0; breaking changes ship without shims.

## Source map

- `src/ocx_mirror_sdk/` — public package. Module roles in `.claude/rules/architecture.md`. Generated `_schema.py` (regen via `task codegen`) is excluded from lint/types.
- `tests/` — pytest, one file per public module + `test_schema.py` for JSON Schema round-trip.
- `schemas/url-index.v1.json` — vendored snapshot of the upstream schema; checked in for offline installs + test round-trip.
- `taskfile.yml` — single root taskfile; `verify` is the gate.
- `ocx.toml` / `ocx.lock` — OCX dogfood toolchain (host `task` + `uv`).
- `.envrc` — `direnv` hook that sources `ocx direnv export` on cd.
- `.claude/rules/` — universal + python + workflow rules; read on demand.

## Public API (7 symbols)

`IndexBuilder`, `list_releases`, `list_releases_graphql`, `Asset`, `Release`, `extract_urls`, `FileCache`. Re-exported from `ocx_mirror_sdk/__init__.py`.

## Invariants

- `verify` green before commit.
- Never push to `main` without review; work on branches.
- Generated `_schema.py` not hand-edited; regenerate with `task codegen` (needs network unless `SCHEMA_URL` points local).
- Schema major bump (`/v2.json` upstream) ⇒ new SDK major version.
- Public API additions: also add to `__all__` + `__init__.py`.

## References

- Tech + toolchain pins: `mem:tech_stack`
- Day-to-day commands: `mem:suggested_commands`
- Code style + design conventions: `mem:conventions`
- Done-checklist (commands to run when finishing a change): `mem:task_completion`
- Module map + schema sync protocol: `.claude/rules/architecture.md`
- Work-type router (bug / feature / refactor): `.claude/rules/workflow-intent.md`
