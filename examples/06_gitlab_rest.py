#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.3.0",
# ]
# ///
"""Minimal generator: GitLab releases via REST → url_index JSON.

Mirrors ``01_shellcheck_rest.py`` for a GitLab-hosted project. The same
``IndexBuilder`` consumes the source-agnostic ``Release`` objects.

For a self-hosted instance, pass ``host="https://gitlab.example.com"`` and set
``GITLAB_TOKEN`` for private projects.

Usage:
    uv run examples/06_gitlab_rest.py > gitlab-runner.json
"""

from ocx_mirror_sdk import IndexBuilder, gitlab


def main() -> None:
    releases = gitlab.list_releases("gitlab-org", "gitlab-runner")

    builder = IndexBuilder()
    for r in releases:
        if r.prerelease:
            continue
        builder.add_version(
            r.tag_name.lstrip("v"),
            assets={a.name: a.browser_download_url for a in r.assets},
        )

    builder.emit()


if __name__ == "__main__":
    main()
