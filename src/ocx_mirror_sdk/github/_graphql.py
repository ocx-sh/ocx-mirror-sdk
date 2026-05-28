# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""GitHub GraphQL backend.

Use on repos where the REST API 504s due to large per-release asset
counts (e.g. python-build-standalone). Release list cached for 1h,
asset lists cached per release for 7d (assets are immutable).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ocx_mirror_sdk.cache import FileCache
from ocx_mirror_sdk.errors import ApiResponseError, ConfigurationError
from ocx_mirror_sdk.github._auth import _get_token
from ocx_mirror_sdk.github._pipeline import _fetch_and_filter
from ocx_mirror_sdk.http import post_json
from ocx_mirror_sdk.releases import Release

log = logging.getLogger(__name__)

_releases_cache = FileCache("github-graphql")
_assets_cache = FileCache("github-graphql-assets", max_age=7 * 86400)

_GRAPHQL_URL = "https://api.github.com/graphql"

_RELEASES_QUERY = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    releases(first: 20, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        tagName
        isDraft
        isPrerelease
        releaseAssets(first: 100) {
          pageInfo { hasNextPage endCursor }
          nodes { name downloadUrl }
        }
      }
    }
  }
}
"""

_ASSETS_PAGE_QUERY = """
query($owner: String!, $repo: String!, $tag: String!, $cursor: String!) {
  repository(owner: $owner, name: $repo) {
    release(tagName: $tag) {
      releaseAssets(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { name downloadUrl }
      }
    }
  }
}
"""


def _graphql(
    client: httpx.Client,
    headers: dict[str, str],
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """POST a GraphQL query and return the ``data`` envelope.

    Raises:
        HttpStatusError / HttpTimeoutError: Transport failure (via :func:`post_json`).
        ApiResponseError: GraphQL ``errors`` array present, or unexpected
            response shape.
    """
    payload = post_json(
        _GRAPHQL_URL,
        body={"query": query, "variables": variables},
        headers=headers,
        client=client,
    )
    if not isinstance(payload, dict):
        raise ApiResponseError("graphql response is not a JSON object", payload=payload)
    if "errors" in payload:
        raise ApiResponseError("graphql errors", payload=payload["errors"])
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ApiResponseError("graphql response missing data", payload=payload)
    return data


def _fetch_all_assets(
    client: httpx.Client,
    headers: dict[str, str],
    owner: str,
    repo: str,
    tag: str,
    first_page: dict[str, Any],
) -> list[dict[str, Any]]:
    """Fetch all assets for a release, with per-release caching."""
    cache_key = f"{owner}/{repo}/{tag}"
    cached = _assets_cache.get_json(cache_key)
    if cached is not None:
        log.debug("  %s: %d assets (cached)", tag, len(cached))
        return cached

    assets = list(first_page["nodes"])
    page_info = first_page["pageInfo"]

    while page_info["hasNextPage"]:
        log.debug("  %s: fetching more assets (%d so far)", tag, len(assets))
        data = _graphql(
            client,
            headers,
            _ASSETS_PAGE_QUERY,
            {
                "owner": owner,
                "repo": repo,
                "tag": tag,
                "cursor": page_info["endCursor"],
            },
        )
        page = data["repository"]["release"]["releaseAssets"]
        assets.extend(page["nodes"])
        page_info = page["pageInfo"]

    log.debug("  %s: %d total assets", tag, len(assets))
    _assets_cache.put_json(cache_key, assets)
    return assets


def list_releases_graphql(
    owner: str,
    repo: str,
    *,
    include_prereleases: bool = True,
    include_drafts: bool = True,
    cache: FileCache | None = None,
    client: httpx.Client | None = None,
) -> list[Release]:
    """Fetch releases via GitHub GraphQL.

    Raises:
        ConfigurationError: ``GITHUB_TOKEN`` is not set.
    """
    token = _get_token()
    if not token:
        raise ConfigurationError("GITHUB_TOKEN is required for the GraphQL API (anonymous access is not supported)")

    effective_cache = cache or _releases_cache
    headers = {"Authorization": f"Bearer {token}"}

    def fetch() -> list[dict]:
        all_releases: list[dict] = []
        cursor: str | None = None
        max_pages = 20

        ctx = client if client is not None else httpx.Client(timeout=30.0)
        owns_client = client is None
        try:
            for page_num in range(max_pages):
                log.info(
                    "fetching releases page %d for %s/%s (%d so far)",
                    page_num + 1,
                    owner,
                    repo,
                    len(all_releases),
                )
                data = _graphql(
                    ctx,
                    headers,
                    _RELEASES_QUERY,
                    {"owner": owner, "repo": repo, "cursor": cursor},
                )
                releases_data = data["repository"]["releases"]
                nodes = releases_data["nodes"]

                if not nodes:
                    break

                for node in nodes:
                    tag = node["tagName"]
                    assets_raw = _fetch_all_assets(ctx, headers, owner, repo, tag, node["releaseAssets"])
                    all_releases.append(
                        {
                            "tag_name": tag,
                            "body": "",
                            "prerelease": node["isPrerelease"],
                            "draft": node["isDraft"],
                            "assets": [
                                {"name": a["name"], "browser_download_url": a["downloadUrl"]} for a in assets_raw
                            ],
                        }
                    )

                page_info = releases_data["pageInfo"]
                if not page_info["hasNextPage"]:
                    break
                cursor = page_info["endCursor"]
            else:
                log.warning(
                    "reached page limit (%d pages, %d releases) for %s/%s — results may be truncated",
                    max_pages,
                    len(all_releases),
                    owner,
                    repo,
                )
        finally:
            if owns_client:
                ctx.close()

        return all_releases

    return _fetch_and_filter(
        owner,
        repo,
        effective_cache,
        fetch,
        include_prereleases=include_prereleases,
        include_drafts=include_drafts,
    )
