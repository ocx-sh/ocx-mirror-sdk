# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Router for :func:`list_releases` — dispatches to REST or GraphQL backend."""

from __future__ import annotations

import logging
from enum import StrEnum

import github3
import httpx

from ocx_mirror_sdk.cache import FileCache
from ocx_mirror_sdk.errors import OcxMirrorError
from ocx_mirror_sdk.github._graphql import list_releases_graphql
from ocx_mirror_sdk.github._rest import list_releases_rest
from ocx_mirror_sdk.releases import Release

log = logging.getLogger(__name__)


class Backend(StrEnum):
    """GitHub release-fetch backend selection.

    Values:
        REST: ``github3.py`` REST API. Default. Fast for small repos.
        GRAPHQL: ``httpx``-backed GraphQL API. Use on repos where REST
            504s due to large per-release asset counts.
    """

    REST = "rest"
    GRAPHQL = "graphql"


def list_releases(
    owner: str,
    repo: str,
    *,
    backend: Backend | str = Backend.REST,
    include_prereleases: bool = True,
    include_drafts: bool = True,
    cache: FileCache | None = None,
    session: github3.GitHub | None = None,
    client: httpx.Client | None = None,
) -> list[Release]:
    """Return releases for *owner/repo* as :class:`Release` objects.

    Args:
        owner: Repository owner.
        repo: Repository name.
        backend: :class:`Backend` selection. Accepts a :class:`Backend`
            member or its string value (``"rest"`` / ``"graphql"``).
            Default: :attr:`Backend.REST`.
        include_prereleases: If ``False``, pre-releases are excluded.
        include_drafts: If ``False``, draft releases are excluded.
        cache: Optional :class:`FileCache` override.
        session: Optional injected ``github3.GitHub`` client.
            Used only when ``backend=Backend.REST``.
        client: Optional injected ``httpx.Client``.
            Used only when ``backend=Backend.GRAPHQL``.

    Raises:
        ValueError: ``backend`` is not a valid :class:`Backend` value.
        ConfigurationError: ``GITHUB_TOKEN`` is missing (GraphQL only).
        TransportError: HTTP failure.
        ApiResponseError: Server returned an unusable payload.

    Example:
        >>> from ocx_mirror_sdk import list_releases, Backend
        >>> releases = list_releases("shellcheck", "shellcheck", backend=Backend.REST)
        >>> sorted({r.tag_name for r in releases})  # doctest: +SKIP
        ['v0.10.0', 'v0.9.0', ...]
    """
    backend = Backend(backend)
    try:
        if backend is Backend.REST:
            return list_releases_rest(
                owner,
                repo,
                include_prereleases=include_prereleases,
                include_drafts=include_drafts,
                cache=cache,
                session=session,
            )
        # Backend.GRAPHQL
        return list_releases_graphql(
            owner,
            repo,
            include_prereleases=include_prereleases,
            include_drafts=include_drafts,
            cache=cache,
            client=client,
        )
    except OcxMirrorError as e:
        log.warning("list_releases(%s, %s, backend=%s) failed: %s", owner, repo, backend, e)
        raise


__all__ = ["Backend", "list_releases"]
