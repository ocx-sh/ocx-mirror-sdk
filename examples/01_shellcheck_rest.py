#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.3.0",
# ]
# ///
"""Minimal generator: shellcheck releases via REST → url_index JSON.

Usage:
    uv run examples/01_shellcheck_rest.py > shellcheck.json
"""

from ocx_mirror_sdk import IndexBuilder, list_releases


def main() -> None:
    releases = list_releases("koalaman", "shellcheck")

    builder = IndexBuilder()
    for r in releases:
        if r.prerelease or r.draft:
            continue
        builder.add_version(
            r.tag_name.lstrip("v"),
            assets={a.name: a.browser_download_url for a in r.assets},
        )

    builder.emit()


if __name__ == "__main__":
    main()
