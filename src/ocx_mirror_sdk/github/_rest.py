# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""GitHub REST backend.

Thin wrapper around ``github3.py``. Caches per ``(owner, repo)`` for 1h
under ``~/.cache/ocx-mirror-sdk/github/``.
"""

from __future__ import annotations

import logging

import github3

from ocx_mirror_sdk.cache import FileCache
from ocx_mirror_sdk.errors import ApiResponseError, ConfigurationError
from ocx_mirror_sdk.github._auth import _get_token
from ocx_mirror_sdk.github._pipeline import _fetch_and_filter
from ocx_mirror_sdk.releases import Release

log = logging.getLogger(__name__)

_cache = FileCache("github")


def _login() -> github3.GitHub:
    """Create a GitHub client, authenticated if ``GITHUB_TOKEN`` is set.

    Raises:
        ConfigurationError: ``github3.login`` returned ``None`` (empty or
            invalid token).
    """
    token = _get_token()
    gh = github3.login(token=token) if token else github3.GitHub()
    if gh is None:
        raise ConfigurationError("github3 client could not be initialized (empty or invalid token)")
    gh.session.default_read_timeout = 30
    return gh


def list_releases_rest(
    owner: str,
    repo: str,
    *,
    include_prereleases: bool = True,
    include_drafts: bool = True,
    cache: FileCache | None = None,
    session: github3.GitHub | None = None,
) -> list[Release]:
    """Fetch releases via GitHub REST."""
    effective_cache = cache or _cache

    def fetch() -> list[dict]:
        gh = session if session is not None else _login()
        repository = gh.repository(owner, repo)
        if repository is None:
            raise ApiResponseError(
                f"repository not found: {owner}/{repo}",
                payload=None,
            )

        results: list[dict] = []
        for release in repository.releases():
            assets = [
                {"name": asset.name, "browser_download_url": asset.browser_download_url} for asset in release.assets()
            ]
            results.append(
                {
                    "tag_name": release.tag_name,
                    "body": release.body or "",
                    "prerelease": release.prerelease,
                    "draft": release.draft,
                    "assets": assets,
                }
            )
        return results

    return _fetch_and_filter(
        owner,
        repo,
        effective_cache,
        fetch,
        include_prereleases=include_prereleases,
        include_drafts=include_drafts,
    )
