#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.3.0",
# ]
# ///
"""End-to-end generator: fetch → filter → extract → build → emit.

Fetches Bun releases, filters non-stable + draft, prefers structured
release assets, falls back to URLs scraped from release notes.

Usage:
    uv run examples/04_combined_index.py > bun.json
"""

import re

from ocx_mirror_sdk import IndexBuilder, extract_urls, list_releases

# Match the structured Bun release-asset filenames we want to publish.
ASSET_RE = re.compile(r"^bun-(linux|darwin|windows)-(x64|aarch64)\.zip$")


def main() -> None:
    releases = list_releases(
        "oven-sh",
        "bun",
        include_prereleases=False,
        include_drafts=False,
    )

    builder = IndexBuilder()
    for r in releases:
        version = r.tag_name.lstrip("bun-v")
        assets: dict[str, str] = {}

        # Prefer structured assets
        for asset in r.assets:
            if ASSET_RE.match(asset.name):
                assets[asset.name] = asset.browser_download_url

        # Fall back to URLs in release notes if none matched
        if not assets and r.body:
            for url in extract_urls(r.body, pattern=ASSET_RE.pattern):
                name = url.rsplit("/", 1)[-1]
                assets[name] = url

        builder.add_version(version, assets=assets)

    builder.emit()


if __name__ == "__main__":
    main()
