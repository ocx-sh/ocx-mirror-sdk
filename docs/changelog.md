# Changelog

For the authoritative changelog, see the
[GitHub Releases](https://github.com/ocx-sh/ocx-mirror-sdk/releases) page.

Notable releases:

## Unreleased

_Add user-facing changes here as they land. Before tagging, rename this
heading to `## vX.Y.Z — <name>` and add the release date._

## v0.3.0 — Maturity pass

- **Breaking**: `list_releases_graphql` removed. Use
  `list_releases(..., backend=Backend.GRAPHQL)`.
- **Breaking**: typed exception hierarchy. Callers catching
  `ValueError`, `RuntimeError`, `httpx.HTTPStatusError`, or `KeyError`
  from this SDK must update — see [Error handling](guide/error-handling.md).
- **New**: `Backend` `StrEnum`, `configure(cache_root=...)`,
  `OcxMirrorError` + subclasses, `http.post_json`.
- **Internal**: `github/` package, REST `session=` DI hook,
  `IndexBuilder.build()` returns a snapshot.
- Docs site published at <https://docs.ocx.sh/sdk/mirror/>.

## v0.2.0

- Initial public extraction from the OCX monorepo.

## Pre-history

See git history for the `ocx-sh/ocx` repo before extraction.

---

### Release ritual

Before tagging `vX.Y.Z`:

1. Run `ocx run -- task release:prep VERSION=X.Y.Z` to bump `pyproject.toml`,
   `README.md`, and `docs/getting-started/install.md` in one shot.
2. Edit this file by hand: rename the `## Unreleased` heading to
   `## vX.Y.Z — <name>`, add the release date, and start a fresh empty
   `## Unreleased` section above it.
3. Commit, then push the `vX.Y.Z` tag.

The release workflow re-checks tag ↔ `pyproject.toml` coherence before it
builds, so any drift fails fast at CI rather than producing a wrong-version
wheel.
