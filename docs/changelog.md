# Changelog

For the authoritative changelog, see the
[GitHub Releases](https://github.com/ocx-sh/ocx-mirror-sdk/releases) page.

Notable releases:

## v0.4.2 — Robust GraphQL retry (2026-06-11)

- **Fix**: the GraphQL retry added in v0.4.1 only matched a fixed list of error
  *message* substrings. GitHub's concurrent-load timeout / secondary-rate-limit
  errors carry no stable `type` and inconsistent wording, so they slipped past
  the markers. `github.list_releases(..., backend=Backend.GRAPHQL)` now retries
  any HTTP 200 `errors` batch by default (5 attempts, exponential backoff),
  opting **out** only when an error carries a permanent `type` (`NOT_FOUND`,
  `FORBIDDEN`, `UNAUTHORIZED`, `INSUFFICIENT_SCOPES`, `UNPROCESSABLE`), which
  still raise immediately. Supersedes v0.4.1.

## v0.4.1 — Transient GraphQL retry (2026-06-11)

- **Fix**: `github.list_releases(..., backend=Backend.GRAPHQL)` now retries
  transient GitHub GraphQL failures — the HTTP 200 `errors` array carrying a
  timeout / "something went wrong while executing your query" message that
  GitHub returns on asset-heavy repos (python-build-standalone) — up to 4
  attempts with exponential backoff before raising. Hard errors (`NOT_FOUND`,
  validation, auth, rate-limit) still raise immediately and non-retryably, so
  the `ApiResponseError` contract is unchanged.

## v0.4.0 — GitLab + scoped sources (2026-06-01)

- **Breaking**: top-level `list_releases` and `Backend` removed. Use
  `github.list_releases("owner/repo")` / `github.Backend`. Both GitHub and
  GitLab `list_releases` now take a single `"namespace/project"` path slug
  instead of separate args.
- **New**: GitLab release source. `gitlab.list_releases("namespace/project", *,
  host="https://gitlab.com", include_prereleases=True, ...)` fetches releases
  from gitlab.com or a self-hosted instance via the REST API (no new
  dependency). Returns the same `Release`/`Asset` objects as the GitHub source.
  Authentication is auto-selected from the environment: `GITLAB_TOKEN`
  (`PRIVATE-TOKEN` header) takes precedence, falling back to `CI_JOB_TOKEN`
  (`JOB-TOKEN` header) inside GitLab CI/CD jobs; anonymous on public projects.
- **New**: `http.fetch_json` accepts an optional `headers=` argument.
- **Internal**: the shared fetch/deserialize/filter pipeline moved from
  `github/_pipeline.py` to `ocx_mirror_sdk/_pipeline.py` (now used by both
  providers). No public-API change.

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
