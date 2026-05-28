# ocx-mirror-sdk

Python SDK for authoring [`ocx-mirror`](https://github.com/ocx-sh/ocx) generator scripts.

`ocx-mirror` is OCX's tool for ingesting upstream tool releases (e.g. CPython, Bun, shellcheck) and republishing them as OCI artifacts. When upstream releases live somewhere `ocx-mirror` cannot crawl directly, a small Python *generator* emits a `url_index` JSON document. This SDK provides the typed building blocks for those generators.

## Install

In a [PEP 723](https://peps.python.org/pep-0723/) inline-metadata script (recommended for one-file generators):

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.2.0",
# ]
# ///

from ocx_mirror_sdk import IndexBuilder, list_releases_graphql
```

Or in a project `pyproject.toml`:

```toml
[project]
dependencies = ["ocx-mirror-sdk"]

[tool.uv.sources]
ocx-mirror-sdk = { git = "https://github.com/ocx-sh/ocx-mirror-sdk", tag = "v0.2.0" }
```

`uv.lock` pins to a commit SHA — `uv sync --frozen` is reproducible in CI.

## Public API

| Symbol | Purpose |
|---|---|
| `IndexBuilder` | Typed builder for the `url_index` JSON manifest |
| `list_releases` | Iterate GitHub releases via REST (github3.py) |
| `list_releases_graphql` | Iterate GitHub releases via GraphQL (faster for large repos) |
| `Asset`, `Release` | Typed views of GitHub release assets |
| `extract_urls` | Pull download URLs from release notes |
| `FileCache` | Disk-backed HTTP response cache, 1h default TTL |

## Schema

The `url_index` format is owned by the `ocx-mirror` Rust binary. Its JSON Schema is published at <https://ocx.sh/schemas/url-index/v1.json>. This SDK ships a generated `_schema.py` (under `src/ocx_mirror_sdk/`) regenerated via `task codegen`.

## Development

This repo dogfoods OCX. Install OCX once:

```bash
curl -sSL https://setup.ocx.sh | sh
```

Then everything runs through `ocx run`:

```bash
ocx run -- task verify   # format + lint + types + tests
ocx run -- task test
ocx run -- task codegen  # regenerate _schema.py from the published schema
```

OCX bootstraps `task` and `uv`; `uv` pulls Python linters (`ruff`, `pyright`) from `[project.optional-dependencies] dev`.

## Stability

Pre-1.0. Breaking changes ship without migration shims. When the upstream `url_index` schema bumps to `/v2.json`, this SDK ships a new major version.

## License

Apache-2.0 — see `LICENSE`.
