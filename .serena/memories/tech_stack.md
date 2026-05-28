# Tech Stack

## Language + runtime

- Python `>=3.13` (hard floor; see `pyproject.toml [project]`).
- Type checker target: `pythonVersion = "3.13"` (pyright, standard mode).
- Ruff target: `py313`, line length 120.

## Runtime deps

- `github3.py>=4` — REST GitHub client (used by `github.py`).
- `httpx>=0.28` — HTTP for GraphQL + raw fetches.

## Dev deps (`[project.optional-dependencies] dev`)

- `datamodel-code-generator>=0.26` — generates `_schema.py` from JSON Schema, dataclass output.
- `jsonschema>=4` — round-trip validation in `test_schema.py`.
- `pyright>=1.1` — type checker.
- `pytest>=8` — test runner; `addopts = ["-ra", "--strict-markers"]`.
- `ruff>=0.9` — lint + format (no Black).

## Toolchain (host)

Managed via OCX (`ocx.toml`):

- `task` — `ocx.sh/go-task:3` (runner; v3 syntax).
- `uv` — `ocx.sh/uv:0` (env + package manager; resolves `[project.optional-dependencies] dev`).

`direnv` hook (`.envrc`) sources `ocx direnv export` so `task` + `uv` are on `PATH` inside the repo. Without `direnv`, prefix every command with `ocx run -- …`.

## Build backend

`hatchling`; wheel package at `src/ocx_mirror_sdk`. `py.typed` marker shipped.

## Lint rule set (ruff)

`E`, `W`, `F`, `I`, `B`, `UP`, `ANN`, `RUF`. `ANN401` ignored project-wide. `tests/*` exempt from `ANN`. `_schema.py` exempt from `ALL` (generated).

## Pyright scope

`include = ["src", "tests"]`; excludes generated `_schema.py`.
