---
paths:
  - src/**
  - tests/**
---

# Architecture

`ocx-mirror-sdk` is a small, self-contained Python library. Public API is seven symbols, organised across seven hand-written modules plus one generated schema. The whole repo is the SDK — there are no internal subsystems.

## Module map

| Module | Role |
|---|---|
| `__init__.py` | Re-exports the public API. Single place to look up what consumers see. |
| `index.py` | `IndexBuilder` — typed builder that emits the `url_index` JSON document. Backed by generated `_schema` dataclasses. |
| `github.py` | `list_releases` via REST (`github3.py`). Caches per `(owner, repo)` for 1h. |
| `github_graphql.py` | `list_releases` via GraphQL. Use on repos where REST 504s (e.g. many assets per release). Caches per release for 7d (assets are immutable). |
| `github_types.py` | `Asset`, `Release` dataclasses + the shared `fetch_and_filter` post-processor + `get_token` helper. |
| `cache.py` | `FileCache` — disk-backed JSON cache, configurable TTL, atomic writes. |
| `http.py` | Small shared HTTP helper. |
| `text.py` | `extract_urls` — pull download URLs from release-note bodies. |
| `_schema.py` | **Generated.** Dataclasses for the `url_index` format. Regenerated via `task codegen`. |

## Public API contract

| Symbol | Stability |
|---|---|
| `IndexBuilder` | Stable shape: `add_version(version, *, assets, prerelease=False)` + `build()` + `emit(file=stdout)` |
| `list_releases`, `list_releases_graphql` | Same signature; choose by repo size |
| `Asset`, `Release` | Dataclasses; assume forward-additive fields |
| `extract_urls(text)` | Returns `list[str]` |
| `FileCache(namespace, *, max_age=…)` | Threadsafe-ish on a single host; not safe across machines |

Pre-1.0: breaking changes ship without migration shims. Bump version, document in the GitHub release notes, expect consumers to pin.

## Schema dependency

The `url_index` format is defined by the `ocx_mirror` Rust crate in `ocx-sh/ocx`:

```
crates/ocx_mirror/src/source/url_index.rs  →  cargo run -p ocx_mirror -- schema url-index  →  https://ocx.sh/schemas/url-index/v1.json
```

This SDK is a downstream consumer. The flow:

1. `task schema:fetch` (or `task codegen`) pulls `https://ocx.sh/schemas/url-index/v1.json` into `schemas/url-index.v1.json`.
2. `task codegen` runs `datamodel-codegen` on that file → writes `src/ocx_mirror_sdk/_schema.py`.
3. The vendored `schemas/url-index.v1.json` is checked in as a release snapshot and also used by `tests/test_schema.py` to validate `IndexBuilder` output round-trip.

When the upstream schema bumps to `/v2.json`, ship a new major version of this SDK. Within `v1` of the schema, additive changes are non-breaking for consumers as long as the builder still produces valid documents.

## Release cadence

- Tag `vX.Y.Z` → GitHub Actions builds wheel + creates GitHub Release.
- No PyPI publishing yet — consumers pin via `git+https://github.com/ocx-sh/ocx-mirror-sdk@vX.Y.Z` (PEP 723 inline metadata or `[tool.uv.sources]`).
- `uv.lock` on the consumer side resolves the tag to a commit SHA → reproducible installs.

## Testing

`tests/` covers every public-API module + one schema round-trip test. Use `pytest`; mocks via `unittest.mock`. No fixtures live under `tests/conftest.py` yet — keep tests self-contained until two real consumers of a fixture appear.

Run via `task test`; full gate via `task verify`.
