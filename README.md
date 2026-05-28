# ocx-mirror-sdk

[![CI](https://github.com/ocx-sh/ocx-mirror-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/ocx-sh/ocx-mirror-sdk/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ocx-sh/ocx-mirror-sdk/branch/main/graph/badge.svg)](https://codecov.io/gh/ocx-sh/ocx-mirror-sdk)
[![Docs](https://github.com/ocx-sh/ocx-mirror-sdk/actions/workflows/docs.yml/badge.svg)](https://ocx-sh.github.io/ocx-mirror-sdk/)

Python SDK for authoring [`ocx-mirror`](https://github.com/ocx-sh/ocx) generator scripts.

`ocx-mirror` is OCX's tool for ingesting upstream tool releases (e.g. CPython, Bun, shellcheck) and republishing them as OCI artifacts. When upstream releases live somewhere `ocx-mirror` cannot crawl directly, a small Python *generator* emits a `url_index` JSON document. This SDK provides the typed building blocks for those generators.

📖 **Full documentation: <https://docs.ocx.sh/sdk/mirror/>**

## Install

In a [PEP 723](https://peps.python.org/pep-0723/) inline-metadata script (recommended for one-file generators):

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.3.0",
# ]
# ///

from ocx_mirror_sdk import IndexBuilder, list_releases, Backend
```

Or in a project `pyproject.toml`:

```toml
[project]
dependencies = ["ocx-mirror-sdk"]

[tool.uv.sources]
ocx-mirror-sdk = { git = "https://github.com/ocx-sh/ocx-mirror-sdk", tag = "v0.3.0" }
```

`uv.lock` pins to a commit SHA — `uv sync --frozen` is reproducible in CI.

Prefer a pre-built wheel (no source build at install time)? Pin the wheel
asset from the GitHub Release — see the
[install guide](https://docs.ocx.sh/sdk/mirror/getting-started/install/#pre-built-wheel-alternative).

## Quickstart

```python
from ocx_mirror_sdk import Backend, IndexBuilder, list_releases

# Fetch releases (REST default; switch to GraphQL on big repos)
releases = list_releases("shellcheck", "shellcheck")

# Or explicitly:
releases = list_releases("indygreg", "python-build-standalone", backend=Backend.GRAPHQL)

# Build a url_index document
builder = IndexBuilder()
for r in releases:
    if r.prerelease or r.draft:
        continue
    builder.add_version(
        r.tag_name.lstrip("v"),
        assets={a.name: a.browser_download_url for a in r.assets},
    )
builder.emit()  # writes JSON to stdout
```

More worked examples live under [`examples/`](examples/) and at <https://docs.ocx.sh/sdk/mirror/recipes/>.

## Public API

| Symbol | Purpose |
|---|---|
| `IndexBuilder` | Typed builder for the `url_index` JSON manifest |
| `list_releases` | Iterate GitHub releases — single router over REST and GraphQL |
| `Backend` | `StrEnum`: `REST` / `GRAPHQL` backend selector |
| `Asset`, `Release` | Typed views of release assets and releases |
| `extract_urls` | Pull download URLs from release notes |
| `FileCache`, `configure` | Disk-backed HTTP response cache; SDK-wide root override |

### Error hierarchy

Catch `OcxMirrorError` to recover from any SDK failure, or pick a subclass:

| Class | Raised when |
|---|---|
| `ConfigurationError` | `GITHUB_TOKEN` missing, client init failed |
| `TransportError` | Base for network errors |
| `HttpStatusError` | HTTP 4xx/5xx (carries `.status_code`, `.url`, `.response_text`) |
| `HttpTimeoutError` | Request timed out |
| `ApiResponseError` | Malformed JSON, GraphQL `errors` array, repo not found |
| `SchemaError` | Release payload missing or wrongly-typed field |
| `CacheError` | On-disk cache IO or corruption (NOT cache miss) |

Original lower-layer exceptions are preserved on `__cause__`.

## Schema

The `url_index` format is owned by the `ocx-mirror` Rust binary. Its JSON Schema is published at <https://ocx.sh/schemas/url-index/v1.json>. This SDK ships a generated `_schema.py` (under `src/ocx_mirror_sdk/`) regenerated via `task codegen`.

## Development

This repo dogfoods OCX. Install OCX once:

```bash
curl -sSL https://setup.ocx.sh | sh
```

Then everything runs through `ocx run`:

```bash
ocx run -- task verify     # format + lint + types + tests
ocx run -- task test
ocx run -- task codegen    # regenerate _schema.py from the published schema
ocx run -- task docs:serve # live-preview the docs site at localhost:8000
```

OCX bootstraps `task` and `uv`; `uv` pulls Python linters (`ruff`, `pyright`) from `[project.optional-dependencies] dev`, and docs tooling from `[project.optional-dependencies] docs`.

## Stability

Pre-1.0. Breaking changes ship without migration shims. When the upstream `url_index` schema bumps to `/v2.json`, this SDK ships a new major version.

## Coverage

`task verify` enforces ≥80% line + branch coverage on `src/ocx_mirror_sdk` (generated `_schema.py` excluded). Run `task cov:html` and open `htmlcov/index.html` to inspect uncovered lines locally. The threshold lives in `[tool.coverage.report] fail_under` in `pyproject.toml`.

## License

Apache-2.0 — see `LICENSE`.
