# Quickstart

```python
from ocx_mirror_sdk import Backend, IndexBuilder, list_releases

releases = list_releases("shellcheck", "shellcheck")

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

That's a complete, valid generator. It:

1. Fetches all releases from `koalaman/shellcheck` via REST.
2. Skips prereleases and drafts.
3. Adds each remaining release to an `IndexBuilder` keyed by the
   tag with `v` stripped.
4. Emits the JSON document to stdout.

The first run hits GitHub's API; the second is served from
`~/.cache/ocx-mirror-sdk/github/`. Local iteration is free.

## On big repos

`shellcheck` is small. If the REST API 504s on yours, opt into the
GraphQL backend:

```python
releases = list_releases(
    "astral-sh", "python-build-standalone",
    backend=Backend.GRAPHQL,
)
```

GraphQL requires `GITHUB_TOKEN`; REST works anonymously (5 000 req/h).
See [Fetching releases](fetching-releases.md) for the decision table.
