# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Tests for ``ocx_mirror_sdk.github_graphql.list_releases``.

Uses an injected ``httpx.Client`` with ``MockTransport`` (no plugin) per
``quality-tests.md`` §8, and ``FakeFileCache`` (``tests/_fakes.py``) per §7
in place of the disk-backed cache.
"""

import json
from collections.abc import Callable

import httpx
import pytest

from ocx_mirror_sdk import github_graphql
from ocx_mirror_sdk.github_graphql import list_releases
from tests._fakes import FakeFileCache

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _release_node(tag: str, *, assets: list[dict] | None = None, prerelease: bool = False, draft: bool = False) -> dict:
    """Construct a GraphQL ``Release`` node with a single-page asset list."""
    return {
        "tagName": tag,
        "isDraft": draft,
        "isPrerelease": prerelease,
        "releaseAssets": {
            "pageInfo": {"hasNextPage": False, "endCursor": None},
            "nodes": assets or [],
        },
    }


def _asset(name: str, url: str) -> dict:
    return {"name": name, "downloadUrl": url}


def _releases_page(nodes: list[dict], *, has_next: bool = False, end_cursor: str | None = None) -> dict:
    """Wrap release nodes in a GraphQL ``releases`` page envelope."""
    return {
        "data": {
            "repository": {
                "releases": {
                    "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
                    "nodes": nodes,
                }
            }
        }
    }


def _assets_page(nodes: list[dict], *, has_next: bool = False, end_cursor: str | None = None) -> dict:
    return {
        "data": {
            "repository": {
                "release": {
                    "releaseAssets": {
                        "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
                        "nodes": nodes,
                    }
                }
            }
        }
    }


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _set_token(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")


def _isolate_module_caches(monkeypatch) -> tuple[FakeFileCache, FakeFileCache]:
    """Swap the module-level release + asset caches with in-memory fakes."""
    releases_cache = FakeFileCache()
    assets_cache = FakeFileCache()
    monkeypatch.setattr(github_graphql, "_releases_cache", releases_cache)
    monkeypatch.setattr(github_graphql, "_assets_cache", assets_cache)
    return releases_cache, assets_cache


# ---------------------------------------------------------------------------
# No-token guard
# ---------------------------------------------------------------------------


def test_list_releases_raises_when_no_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    with pytest.raises(ValueError, match="GITHUB_TOKEN is required"):
        list_releases("owner", "repo")


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_list_releases_single_page_single_release(monkeypatch):
    _set_token(monkeypatch)
    _isolate_module_caches(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_releases_page(
                [_release_node("v1.0.0", assets=[_asset("tool.tgz", "https://x/tool.tgz")])],
            ),
        )

    result = list_releases("owner", "repo", client=_client(handler))

    assert len(result) == 1
    assert result[0].tag_name == "v1.0.0"
    assert [a.name for a in result[0].assets] == ["tool.tgz"]
    assert result[0].assets[0].browser_download_url == "https://x/tool.tgz"


def test_list_releases_paginates_releases(monkeypatch):
    _set_token(monkeypatch)
    _isolate_module_caches(monkeypatch)

    pages = iter(
        [
            _releases_page([_release_node("v1")], has_next=True, end_cursor="cursor-1"),
            _releases_page([_release_node("v2")], has_next=False),
        ]
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=next(pages))

    result = list_releases("o", "r", client=_client(handler))

    assert [r.tag_name for r in result] == ["v1", "v2"]


def test_list_releases_stops_when_page_returns_no_nodes(monkeypatch):
    _set_token(monkeypatch)
    _isolate_module_caches(monkeypatch)

    pages = iter(
        [
            _releases_page([_release_node("v1")], has_next=True, end_cursor="cursor-1"),
            _releases_page([], has_next=True, end_cursor="cursor-2"),
        ]
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=next(pages))

    result = list_releases("o", "r", client=_client(handler))

    assert [r.tag_name for r in result] == ["v1"]


def test_list_releases_paginates_assets_within_release(monkeypatch):
    _set_token(monkeypatch)
    _isolate_module_caches(monkeypatch)

    first_page_assets = [_asset(f"a{i}.tgz", f"https://x/a{i}") for i in range(3)]
    second_page_assets = [_asset(f"b{i}.tgz", f"https://x/b{i}") for i in range(2)]

    release_node = {
        "tagName": "v1",
        "isDraft": False,
        "isPrerelease": False,
        "releaseAssets": {
            "pageInfo": {"hasNextPage": True, "endCursor": "asset-cursor-1"},
            "nodes": first_page_assets,
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        query = body["query"]
        if "releases(" in query:
            return httpx.Response(200, json=_releases_page([release_node]))
        # asset-page query
        return httpx.Response(200, json=_assets_page(second_page_assets, has_next=False))

    result = list_releases("o", "r", client=_client(handler))

    asset_names = [a.name for a in result[0].assets]
    assert asset_names == [a["name"] for a in first_page_assets + second_page_assets]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_list_releases_raises_when_graphql_returns_errors(monkeypatch):
    _set_token(monkeypatch)
    _isolate_module_caches(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "rate limited"}], "data": None})

    with pytest.raises(RuntimeError, match="GraphQL errors"):
        list_releases("o", "r", client=_client(handler))


def test_list_releases_raises_on_http_error(monkeypatch):
    _set_token(monkeypatch)
    _isolate_module_caches(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"data": None})

    with pytest.raises(httpx.HTTPStatusError, match="500"):
        list_releases("o", "r", client=_client(handler))


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


def test_assets_cache_hit_skips_pagination(monkeypatch):
    _set_token(monkeypatch)
    _, assets_cache = _isolate_module_caches(monkeypatch)
    assets_cache.put_json("o/r/v1", [{"name": "cached.tgz", "downloadUrl": "https://x/cached.tgz"}])

    # Release node advertises a second asset page; the cache hit must short-circuit it.
    release_node = {
        "tagName": "v1",
        "isDraft": False,
        "isPrerelease": False,
        "releaseAssets": {
            "pageInfo": {"hasNextPage": True, "endCursor": "would-trigger-more"},
            "nodes": [_asset("stale.tgz", "https://x/stale.tgz")],
        },
    }

    request_log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        request_log.append(body["query"])
        return httpx.Response(200, json=_releases_page([release_node]))

    result = list_releases("o", "r", client=_client(handler))

    assert [a.name for a in result[0].assets] == ["cached.tgz"]
    # Only the releases query should hit; the asset-page query must NOT.
    assert all("releases(" in q for q in request_log)


def test_releases_cache_hit_skips_http(monkeypatch):
    _set_token(monkeypatch)
    releases_cache, _ = _isolate_module_caches(monkeypatch)
    releases_cache.put_json(
        "o/r/releases",
        [
            {
                "tag_name": "v1",
                "body": "",
                "prerelease": False,
                "draft": False,
                "assets": [{"name": "cached.tgz", "browser_download_url": "https://x/cached.tgz"}],
            }
        ],
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("HTTP must not be called on cache hit")

    result = list_releases("o", "r", client=_client(handler))

    assert [r.tag_name for r in result] == ["v1"]


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("include_prereleases", "include_drafts", "expected_tags"),
    [
        pytest.param(True, True, ["v1", "v2-rc", "v3-draft"], id="include-all"),
        pytest.param(False, True, ["v1", "v3-draft"], id="exclude-prereleases"),
        pytest.param(True, False, ["v1", "v2-rc"], id="exclude-drafts"),
        pytest.param(False, False, ["v1"], id="exclude-both"),
    ],
)
def test_list_releases_applies_filters(monkeypatch, include_prereleases, include_drafts, expected_tags):
    _set_token(monkeypatch)
    _isolate_module_caches(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_releases_page(
                [
                    _release_node("v1"),
                    _release_node("v2-rc", prerelease=True),
                    _release_node("v3-draft", draft=True),
                ]
            ),
        )

    result = list_releases(
        "o",
        "r",
        include_prereleases=include_prereleases,
        include_drafts=include_drafts,
        client=_client(handler),
    )

    assert [r.tag_name for r in result] == expected_tags
