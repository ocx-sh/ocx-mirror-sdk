---
paths:
  - src/**
  - tests/**
---

# Architecture

`ocx-mirror-sdk` is a small, self-contained Python library. The public API is a single import path; everything else is package-private.

## Module map

| Module | Role |
|---|---|
| `__init__.py` | Re-exports the public API. Single source of truth for what consumers see. |
| `index.py` | `IndexBuilder` — typed builder that emits the `url_index` JSON document. `build()` returns a snapshot copy decoupled from the builder. |
| `releases.py` | `Asset`, `Release` dataclasses. Source-agnostic release model (the return contract of `list_releases`). |
| `errors.py` | `OcxMirrorError` hierarchy. Every exception raised from the SDK inherits from this base. See `quality-errors.md`. |
| `cache.py` | `FileCache` — disk-backed cache with TTL + atomic writes. `configure(cache_root=...)` for SDK-wide root override. Miss returns `None`; IO failure / corrupt JSON raise `CacheError`. |
| `http.py` | Retry-aware HTTP helpers (`fetch_json`, `fetch_text`, `post_json`). Wraps `httpx` exceptions into typed `Transport*` errors at the boundary. |
| `text.py` | `extract_urls` — pull download URLs from release-note bodies. |
| `github/` | GitHub release source package. Only `Backend` + `list_releases` are re-exported. |
| `github/_router.py` | `Backend` `StrEnum` + the `list_releases` router. Dispatches to REST or GraphQL backend; logs once at the public boundary before re-raising. |
| `github/_rest.py` | REST backend (`github3.py`). Caches per `(owner, repo)` for 1h. Accepts an optional `session=` DI hook. |
| `github/_graphql.py` | GraphQL backend (`httpx` via `http.post_json`). Caches releases for 1h; per-release asset lists for 7d (assets are immutable). |
| `github/_pipeline.py` | Shared `_fetch_and_filter` post-processor used by both backends. |
| `github/_auth.py` | `_get_token` — reads `GITHUB_TOKEN`. |
| `_schema.py` | **Generated.** Dataclasses for the `url_index` format. Regenerated via `task codegen`. |

## Public API contract

| Symbol | Stability |
|---|---|
| `IndexBuilder` | `add_version(version, *, assets, prerelease=False)` + `build()` + `emit(file=stdout)`. `build()` returns a snapshot. |
| `list_releases(owner, repo, *, backend=Backend.REST, ...)` | Single router over REST + GraphQL. Accepts `Backend` enum or raw string. Unknown backend → `ValueError`. |
| `Backend` | `StrEnum` with `REST` / `GRAPHQL`. |
| `Asset`, `Release` | Frozen dataclasses; assume forward-additive fields. |
| `extract_urls(text)` | Returns deduplicated `list[str]`. |
| `FileCache(domain, *, max_age=…)` | Threadsafe-ish on a single host; not safe across machines. |
| `configure(*, cache_root=None)` | SDK-wide override for the cache root. |
| `OcxMirrorError` + subclasses | Stable hierarchy; new leaf classes may be added under existing categories. |

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

- Tag `vX.Y.Z` → `.github/workflows/release.yml` runs `task verify`, `uv build`, and attaches the resulting `*.whl` + `*.tar.gz` to a GitHub Release. `generate_release_notes: true` populates the release body from commits since the previous tag.
- A coherence guard in the workflow re-checks `${GITHUB_REF_NAME#v}` against the `version =` in `pyproject.toml` and fails fast on drift — a wrong-version tag never produces an artifact.
- The same workflow accepts `workflow_dispatch` for branch dry runs: build runs, but the GitHub Release upload is skipped and artifacts land in a 1-day `dist-dry-run` retention slot instead.
- Docs deploy on every push to `main` via `.github/workflows/docs.yml`.
- No PyPI publishing yet. Consumers pin either:
  - the git tag: `git+https://github.com/ocx-sh/ocx-mirror-sdk@vX.Y.Z` (PEP 723 inline metadata or `[tool.uv.sources]` `git` form), or
  - the wheel asset: `https://github.com/ocx-sh/ocx-mirror-sdk/releases/download/vX.Y.Z/ocx_mirror_sdk-X.Y.Z-py3-none-any.whl` (`[tool.uv.sources]` `url` form).
- `uv.lock` makes both paths reproducible — git tag → commit SHA, wheel URL → byte hash.
- The release helper `ocx run -- task release:prep VERSION=X.Y.Z` bumps `pyproject.toml`, `README.md`, and `docs/getting-started/install.md` in one shot. `docs/changelog.md` stays human-curated — rename `## Unreleased` to `## vX.Y.Z — <name>` before tagging.

## Testing

`tests/` covers every public-API module + one schema round-trip test. Use `pytest`; mocks via `unittest.mock`; hand-written fakes (e.g. `FakeFileCache`) in `tests/_fakes.py` per `quality-tests.md` §7. HTTP boundary uses injected `httpx.Client` with `MockTransport`. Patch where used (e.g. `ocx_mirror_sdk.github._rest._cache`), not where defined.

Run via `task test`; full gate via `task verify`.
