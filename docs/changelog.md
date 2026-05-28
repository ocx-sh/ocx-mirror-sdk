# Changelog

For the authoritative changelog, see the
[GitHub Releases](https://github.com/ocx-sh/ocx-mirror-sdk/releases) page.

Notable releases:

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
