# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""GitLab REST backend.

Fetches releases via the GitLab REST API (``GET /api/v4/projects/:id/releases``)
using :func:`ocx_mirror_sdk.http.fetch_json`. Caches per ``(host, namespace,
project)`` for 1h under ``~/.cache/ocx-mirror-sdk/gitlab/``.

GitLab has no draft releases and no separate pre-release flag beyond
``upcoming_release`` (true while the ``released_at`` date is in the future), so
``draft`` is always ``False`` and ``prerelease`` maps to ``upcoming_release``.
Only author-curated ``assets.links`` are surfaced; auto-generated source
archives (``assets.sources``) are skipped.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote, urlsplit

import httpx

from ocx_mirror_sdk._pipeline import fetch_and_filter
from ocx_mirror_sdk.cache import FileCache
from ocx_mirror_sdk.errors import ApiResponseError, OcxMirrorError
from ocx_mirror_sdk.gitlab._auth import _resolve_auth_header
from ocx_mirror_sdk.http import fetch_json
from ocx_mirror_sdk.releases import Release

log = logging.getLogger(__name__)

_cache = FileCache("gitlab")
_PER_PAGE = 100
_MAX_PAGES = 50

DEFAULT_HOST = "https://gitlab.com"


def _normalize_release(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a GitLab release object to the canonical :class:`Release` shape."""
    links = raw.get("assets", {}).get("links", []) or []
    assets = [
        {
            "name": link["name"],
            "browser_download_url": link.get("direct_asset_url") or link["url"],
        }
        for link in links
    ]
    return {
        "tag_name": raw["tag_name"],
        "body": raw.get("description") or "",
        "prerelease": bool(raw.get("upcoming_release", False)),
        "draft": False,
        "assets": assets,
    }


def list_releases(
    namespace: str,
    project: str,
    *,
    host: str = DEFAULT_HOST,
    include_prereleases: bool = True,
    cache: FileCache | None = None,
    client: httpx.Client | None = None,
) -> list[Release]:
    """Return releases for a GitLab project as :class:`Release` objects.

    Args:
        namespace: Project namespace. May contain nested subgroups
            (e.g. ``"gitlab-org/security"``).
        project: Project (repository) name.
        host: GitLab instance base URL. Default: ``"https://gitlab.com"``.
            Set this for self-hosted instances (e.g. ``"https://gitlab.example.com"``).
        include_prereleases: If ``False``, upcoming (pre-)releases are excluded.
        cache: Optional :class:`FileCache` override.
        client: Optional injected ``httpx.Client`` (tests pass a
            ``MockTransport`` client).

    Raises:
        TransportError: HTTP failure (e.g. ``HttpStatusError`` 404 when the
            project does not exist or is private).
        ApiResponseError: Server returned an unusable payload.

    Example:
        >>> from ocx_mirror_sdk import gitlab
        >>> releases = gitlab.list_releases("gitlab-org", "gitlab-runner")  # doctest: +SKIP
        >>> sorted({r.tag_name for r in releases})  # doctest: +SKIP
        ['v16.0.0', 'v16.1.0', ...]
    """
    try:
        return _do_list_releases(
            namespace,
            project,
            host=host,
            include_prereleases=include_prereleases,
            cache=cache,
            client=client,
        )
    except OcxMirrorError as e:
        log.warning("gitlab.list_releases(%s/%s @ %s) failed: %s", namespace, project, host, e)
        raise


def _do_list_releases(
    namespace: str,
    project: str,
    *,
    host: str,
    include_prereleases: bool,
    cache: FileCache | None,
    client: httpx.Client | None,
) -> list[Release]:
    effective_cache = cache or _cache
    project_id = quote(f"{namespace}/{project}", safe="")
    base = f"{host.rstrip('/')}/api/v4/projects/{project_id}"
    headers = _resolve_auth_header()
    netloc = urlsplit(host).netloc or host
    cache_key = f"{netloc}/{namespace}/{project}"

    def fetch() -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for page in range(1, _MAX_PAGES + 1):
            url = f"{base}/releases?per_page={_PER_PAGE}&page={page}"
            batch = fetch_json(url, headers=headers, client=client)
            if not isinstance(batch, list):
                raise ApiResponseError("gitlab releases response is not a JSON array", payload=batch)
            results.extend(_normalize_release(r) for r in batch)
            if len(batch) < _PER_PAGE:
                break
        else:
            log.warning(
                "reached page limit (%d pages, %d releases) for %s/%s — results may be truncated",
                _MAX_PAGES,
                len(results),
                namespace,
                project,
            )
        return results

    return fetch_and_filter(
        effective_cache,
        cache_key,
        fetch,
        label=f"{namespace}/{project} @ {netloc}",
        include_prereleases=include_prereleases,
        include_drafts=True,
    )
