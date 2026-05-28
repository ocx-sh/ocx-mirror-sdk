---
title: ocx-mirror-sdk
hide:
  - navigation
---

# ocx-mirror-sdk

!!! warning "Pre-1.0 — API may change between minor versions"
    Breaking changes ship without migration shims. Pin to a tag, watch the
    [release notes](https://github.com/ocx-sh/ocx-mirror-sdk/releases).

**Python SDK for authoring [`ocx-mirror`](https://github.com/ocx-sh/ocx) generator scripts.**

`ocx-mirror` is OCX's tool for ingesting upstream tool releases and republishing
them as OCI artifacts. When upstream releases live somewhere `ocx-mirror`
cannot crawl directly, a small Python *generator* emits a `url_index` JSON
document. This SDK provides the typed building blocks for those generators.

## At a glance

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **[Getting started](getting-started/index.md)**

    ---

    Install via PEP 723 or `[tool.uv.sources]`, write a 25-line generator,
    run it locally.

-   :material-book-open-page-variant:{ .lg .middle } **[Guide](guide/index.md)**

    ---

    REST vs GraphQL, caching, error handling, troubleshooting `GITHUB_TOKEN`
    and rate limits.

-   :material-file-document-multiple:{ .lg .middle } **[Recipes](recipes/index.md)**

    ---

    Fully runnable examples — shellcheck (REST), python-build-standalone
    (GraphQL), URL extraction.

-   :material-api:{ .lg .middle } **[API reference](api/index.md)**

    ---

    Auto-generated from docstrings. Every public symbol, its signature,
    parameters, exceptions, and examples.

</div>

## Public API at a glance

```python
from ocx_mirror_sdk import (
    Backend, IndexBuilder, list_releases, extract_urls,
    Asset, Release, FileCache, configure,
    OcxMirrorError, HttpStatusError, ApiResponseError,
)

releases = list_releases("shellcheck", "shellcheck")
# Or, on a big repo:
releases = list_releases("astral-sh", "python-build-standalone", backend=Backend.GRAPHQL)

builder = IndexBuilder()
for r in releases:
    if r.prerelease or r.draft:
        continue
    builder.add_version(
        r.tag_name.lstrip("v"),
        assets={a.name: a.browser_download_url for a in r.assets},
    )
builder.emit()
```

## See also

- :material-github: [Source on GitHub](https://github.com/ocx-sh/ocx-mirror-sdk)
- :material-puzzle: [`ocx-mirror` Rust binary](https://github.com/ocx-sh/ocx)
- :material-file-code: [`url_index` JSON Schema](https://ocx.sh/schemas/url-index/v1.json)
- :material-web: [OCX project portal](https://ocx.sh)
