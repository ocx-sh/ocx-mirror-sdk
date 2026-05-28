#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.3.0",
# ]
# ///
"""GraphQL-backed generator for a large repo.

python-build-standalone has ~735 assets per release. REST returns 504s,
so we route through GraphQL. We also redirect the cache root so CI runs
don't pollute ``~/.cache``.

Requires GITHUB_TOKEN (GraphQL has no anonymous access).

Usage:
    GITHUB_TOKEN=ghp_... uv run examples/02_python_build_standalone_graphql.py > pbs.json
"""

from pathlib import Path

from ocx_mirror_sdk import Backend, IndexBuilder, configure, list_releases


def main() -> None:
    configure(cache_root=Path(".cache/ocx-mirror-sdk"))

    releases = list_releases(
        "astral-sh",
        "python-build-standalone",
        backend=Backend.GRAPHQL,
        include_prereleases=False,
        include_drafts=False,
    )

    builder = IndexBuilder()
    for r in releases:
        builder.add_version(
            r.tag_name,
            assets={a.name: a.browser_download_url for a in r.assets},
        )

    builder.emit()


if __name__ == "__main__":
    main()
