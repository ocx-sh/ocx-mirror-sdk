# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""GitHub REST backend.

Paginates the releases list endpoint directly over ``httpx`` and reads the
**inline** ``assets`` array carried by each release object — no per-release
asset refetch. Release list cached per ``(owner, repo)`` for 1h under
``~/.cache/ocx-mirror-sdk/github/``.

The list endpoint 504s on repos whose releases carry hundreds of assets
(python-build-standalone) when ``per_page`` is large, because GitHub
serialises every asset of every release on the page. We therefore page at
``per_page=100`` by default and transparently fall back to a small page size
on a 502/503/504 / timeout, which keeps the request count tiny on normal repos
while still completing on asset-heavy ones.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

import httpx

from ocx_mirror_sdk._pipeline import fetch_and_filter
from ocx_mirror_sdk.cache import FileCache
from ocx_mirror_sdk.errors import ApiResponseError, HttpStatusError, HttpTimeoutError
from ocx_mirror_sdk.github._auth import _get_token
from ocx_mirror_sdk.http import fetch_json
from ocx_mirror_sdk.releases import Release

log = logging.getLogger(__name__)

_cache = FileCache("github")

_API_ROOT = "https://api.github.com"
_DEFAULT_PER_PAGE = 100
# Small enough that the list endpoint serialises even ~850-asset releases
# (python-build-standalone) within the timeout — see module docstring.
_FALLBACK_PER_PAGE = 10
_MAX_PAGES = 100  # backstop: _MAX_PAGES * per_page releases
_OVERLOAD_STATUS = frozenset({502, 503, 504})

# Even at a small page size GitHub intermittently 504s an individual page under
# load, so retry a single overloaded page a few times before giving up.
_PAGE_RETRIES = 3
_PAGE_RETRY_BACKOFF_BASE = 1.0  # seconds; sleep = base * 2**attempt

# Sleep seam — module attribute so tests can swap it for a no-op
# (`monkeypatch.setattr(_rest, "_sleep", lambda _s: None)`) per
# quality-tests.md §9 instead of patching stdlib ``time.sleep``.
_sleep: Callable[[float], None] = time.sleep


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _is_overload(exc: Exception) -> bool:
    """True when *exc* is a transient overload worth retrying at a smaller page."""
    return isinstance(exc, HttpTimeoutError) or (
        isinstance(exc, HttpStatusError) and exc.status_code in _OVERLOAD_STATUS
    )


def _fetch_page(
    owner: str,
    repo: str,
    per_page: int,
    page: int,
    *,
    headers: dict[str, str],
    client: httpx.Client | None,
    retries: int,
) -> list:
    """Fetch one releases page, retrying transient overloads with backoff.

    Raises:
        ApiResponseError: Repository not found (404) or non-array payload.
        HttpStatusError / HttpTimeoutError: A non-overload failure, or an
            overload that survived every retry.
    """
    url = f"{_API_ROOT}/repos/{owner}/{repo}/releases"
    for attempt in range(retries + 1):
        try:
            batch = fetch_json(url, headers=headers, params={"per_page": per_page, "page": page}, client=client)
        except HttpStatusError as e:
            if e.status_code == 404:
                raise ApiResponseError(f"repository not found: {owner}/{repo}", payload=None) from e
            if not _is_overload(e) or attempt == retries:
                raise
        except HttpTimeoutError:
            if attempt == retries:
                raise
            log.debug("timeout fetching %s page %d (attempt %d); retrying", url, page, attempt + 1)
        else:
            if not isinstance(batch, list):
                raise ApiResponseError("github releases response is not a JSON array", payload=batch)
            return batch
        delay = _PAGE_RETRY_BACKOFF_BASE * (2**attempt)
        log.warning(
            "releases page %d for %s/%s at per_page=%d overloaded; retry %d/%d in %.1fs",
            page,
            owner,
            repo,
            per_page,
            attempt + 1,
            retries,
            delay,
        )
        _sleep(delay)
    raise AssertionError("unreachable: loop returns or raises")


def _crawl(
    owner: str,
    repo: str,
    per_page: int,
    *,
    headers: dict[str, str],
    client: httpx.Client | None,
    retries: int,
) -> list[dict]:
    """Page the releases list endpoint, returning raw release dicts.

    Reads the inline ``assets`` array on each release (complete even for
    releases with hundreds of assets), so no per-release asset call is made.
    Each page is fetched with ``retries`` transient-overload retries.

    Raises:
        ApiResponseError: Repository not found (404) or non-array payload.
        HttpStatusError / HttpTimeoutError: A page that overloaded past its
            retries — the caller decides whether to retry at a smaller size.
    """
    releases: list[dict] = []
    for page in range(1, _MAX_PAGES + 1):
        batch = _fetch_page(owner, repo, per_page, page, headers=headers, client=client, retries=retries)
        for rel in batch:
            releases.append(
                {
                    "tag_name": rel["tag_name"],
                    "body": rel.get("body") or "",
                    "prerelease": rel.get("prerelease", False),
                    "draft": rel.get("draft", False),
                    "assets": [
                        {"name": a["name"], "browser_download_url": a["browser_download_url"]}
                        for a in rel.get("assets", [])
                    ],
                }
            )
        if len(batch) < per_page:
            break
    else:
        log.warning(
            "reached page limit (%d pages at per_page=%d) for %s/%s — results may be truncated",
            _MAX_PAGES,
            per_page,
            owner,
            repo,
        )
    return releases


def list_releases_rest(
    owner: str,
    repo: str,
    *,
    include_prereleases: bool = True,
    include_drafts: bool = True,
    cache: FileCache | None = None,
    client: httpx.Client | None = None,
    per_page: int = _DEFAULT_PER_PAGE,
) -> list[Release]:
    """Fetch releases via GitHub REST, paging with adaptive page-size fallback."""
    effective_cache = cache or _cache
    headers = _headers()

    def fetch() -> list[dict]:
        # At the fallback (small) size, tolerate intermittent per-page 504s with
        # retries. At the default (large) size, fail fast on overload — a 504
        # there is systematic (page too big to serialise), so drop straight to
        # the smaller size rather than burning backoff on a page that won't fit.
        if per_page <= _FALLBACK_PER_PAGE:
            return _crawl(owner, repo, per_page, headers=headers, client=client, retries=_PAGE_RETRIES)
        try:
            return _crawl(owner, repo, per_page, headers=headers, client=client, retries=0)
        except (HttpStatusError, HttpTimeoutError) as e:
            if not _is_overload(e):
                raise
            log.warning(
                "releases list for %s/%s at per_page=%d overloaded (%s); retrying at per_page=%d",
                owner,
                repo,
                per_page,
                e,
                _FALLBACK_PER_PAGE,
            )
        # Fallback at the smaller page size, with per-page retries.
        return _crawl(owner, repo, _FALLBACK_PER_PAGE, headers=headers, client=client, retries=_PAGE_RETRIES)

    return fetch_and_filter(
        effective_cache,
        f"{owner}/{repo}",
        fetch,
        label=f"{owner}/{repo}",
        include_prereleases=include_prereleases,
        include_drafts=include_drafts,
    )
