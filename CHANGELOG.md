# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.2] - 2026-06-11

### Fixed

- Wrap httpx network/protocol errors as HttpTransportError *(http)*

## [0.5.1] - 2026-06-11

### Fixed

- Retry intermittent per-page 504s in REST crawl *(github)*

## [0.5.0] - 2026-06-11

### Added

- REST backend over httpx with inline assets + adaptive paging *(github)* **BREAKING**

## [0.4.2] - 2026-06-11

### Fixed

- Retry GraphQL errors unless type is permanent *(github)*

## [0.4.1] - 2026-06-11

### Fixed

- Retry transient GraphQL timeout errors *(github)*

## [0.4.0] - 2026-06-01

### Added

- Add GitLab release source *(gitlab)*
- Auto-select auth header from environment *(gitlab)*
- Scope list_releases to github/gitlab subpackages *(api)* **BREAKING**

### Changed

- Promote release pipeline to shared module

### Documentation

- Point Docs badge link at GitHub Pages URL
- Update for subpackage-scoped list_releases API

## [0.3.0] - 2026-05-28

### Added

- Add generator-based url_index sources *(mirror)*
- Add cache, github, and text utility modules *(mirror-sdk)*
- Rename package ocx_gen → ocx_mirror_sdk **BREAKING**
- Add coverage.py + Codecov + task wiring (fail_under=80) *(coverage)*
- Expose __version__ via importlib.metadata *(sdk)*

### Changed

- Accept optional injected httpx.Client *(http,graphql)*
- Collapse to single list_releases router, add typed error hierarchy *(api,errors)*

### Documentation

- Add quality-tests rule for pytest + fixtures + mocking *(rules)*
- Publish MkDocs Material site under docs.ocx.sh/sdk/mirror/
- Document wheel install path + changelog release ritual
- Point README badge at docs.yml workflow status
[0.5.2]: https://github.com/ocx-sh/ocx-mirror-sdk/compare/v0.5.1..v0.5.2
[0.5.1]: https://github.com/ocx-sh/ocx-mirror-sdk/compare/v0.5.0..v0.5.1
[0.5.0]: https://github.com/ocx-sh/ocx-mirror-sdk/compare/v0.4.2..v0.5.0
[0.4.2]: https://github.com/ocx-sh/ocx-mirror-sdk/compare/v0.4.1..v0.4.2
[0.4.1]: https://github.com/ocx-sh/ocx-mirror-sdk/compare/v0.4.0..v0.4.1
[0.4.0]: https://github.com/ocx-sh/ocx-mirror-sdk/compare/v0.3.0..v0.4.0
[0.3.0]: https://github.com/ocx-sh/ocx-mirror-sdk/tree/v0.3.0

