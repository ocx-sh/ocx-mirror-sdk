# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Shared fetch/deserialize/filter pipeline for release sources (package-private).

Source-agnostic: every backend (GitHub REST/GraphQL, GitLab REST, …) produces a
list of raw release dicts in the canonical :class:`Release` shape, and this
pipeline handles caching, deserialization, and filtering uniformly.
"""

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


def fetch_and_filter(
    cache: FileCache,
    cache_key: str,
    loader: Callable[[], list[dict[str, Any]]],
    *,
    label: str,
    include_prereleases: bool = True,
    include_drafts: bool = True,
) -> list[Release]:
    """Fetch raw release dicts (cached), deserialize, filter, and return.

    Args:
        cache: Cache to read/write through.
        cache_key: Base cache key; ``"/releases"`` is appended internally.
        loader: Callable returning raw release dicts in the canonical shape
            (``tag_name``, ``body``, ``prerelease``, ``draft``, ``assets``).
        label: Human-readable identifier used in log lines (e.g. ``"owner/repo"``).
        include_prereleases: If ``False``, pre-releases are excluded.
        include_drafts: If ``False``, draft releases are excluded.
    """
    log.info("fetching releases for %s", label)
    raw = cache.fetch_json(f"{cache_key}/releases", loader)
    log.info("got %d releases for %s", len(raw), label)
    releases = [Release.from_dict(r) for r in raw]

    releases = _filter_releases(
        releases,
        include_prereleases=include_prereleases,
        include_drafts=include_drafts,
    )
    if not include_prereleases or not include_drafts:
        log.info("after filtering: %d releases", len(releases))

    return releases
