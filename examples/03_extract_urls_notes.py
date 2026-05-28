#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.3.0",
# ]
# ///
"""Some upstreams attach assets via prose in release notes, not as
GitHub release assets. ``extract_urls`` recovers them.

Usage:
    uv run examples/03_extract_urls_notes.py
"""

from ocx_mirror_sdk import extract_urls

NOTES = """
## Release v1.4.2

Downloads:

- Linux x86_64: https://example.com/tool-1.4.2-linux-x86_64.tar.gz
- macOS arm64: <https://example.com/tool-1.4.2-darwin-arm64.tar.gz>.
- Windows: (https://example.com/tool-1.4.2-windows.zip)

See the [docs](https://example.com/docs) for upgrade notes.
"""


def main() -> None:
    # Pull every URL
    for url in extract_urls(NOTES):
        print(url)

    print("---")

    # Filter to download archives only
    for url in extract_urls(NOTES, pattern=r"\.(tar\.gz|zip)$"):
        print(url)


if __name__ == "__main__":
    main()
