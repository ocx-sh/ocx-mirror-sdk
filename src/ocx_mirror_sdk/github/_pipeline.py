# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Shared fetch/deserialize/filter pipeline for GitHub backends (package-private)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from ocx_mirror_sdk.cache import FileCache
from ocx_mirror_sdk.releases import Release

log = logging.getLogger(__name__)


def _filter_releases(
    releases: list[Release],
    *,
    include_prereleases: bool = True,
    include_drafts: bool = True,
) -> list[Release]:
    """Filter releases by prerelease/draft status."""
    if not include_prereleases:
        releases = [r for r in releases if not r.prerelease]
    if not include_drafts:
        releases = [r for r in releases if not r.draft]
    return releases


def _fetch_and_filter(
    owner: str,
    repo: str,
    cache: FileCache,
    loader: Callable[[], list[dict[str, Any]]],
    *,
    include_prereleases: bool = True,
    include_drafts: bool = True,
) -> list[Release]:
    """Fetch raw release dicts (cached), deserialize, filter, and return."""
    log.info("fetching releases for %s/%s", owner, repo)
    raw = cache.fetch_json(f"{owner}/{repo}/releases", loader)
    log.info("got %d releases for %s/%s", len(raw), owner, repo)
    releases = [Release.from_dict(r) for r in raw]

    releases = _filter_releases(
        releases,
        include_prereleases=include_prereleases,
        include_drafts=include_drafts,
    )
    if not include_prereleases or not include_drafts:
        log.info("after filtering: %d releases", len(releases))

    return releases
