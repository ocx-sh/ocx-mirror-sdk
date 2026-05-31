# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Tests for ``ocx_mirror_sdk.gitlab.list_releases`` (REST backend).

Uses an injected ``httpx.Client`` with ``MockTransport`` per
``quality-tests.md`` §8, and ``FakeFileCache`` (``tests/_fakes.py``) per §7 in
place of the disk-backed cache.
"""

import logging

import httpx
import pytest
from _fakes import FakeFileCache

from ocx_mirror_sdk import ApiResponseError, HttpStatusError, HttpTimeoutError, gitlab
from ocx_mirror_sdk.gitlab import _rest as rest_module

# ---------------------------------------------------------------------------
# Fixtures (hermetic: no real token, no real disk cache)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def cache(monkeypatch):
    """Swap the module-level disk cache with an in-memory fake."""
    fake = FakeFileCache()
    monkeypatch.setattr(rest_module, "_cache", fake)
    return fake


@pytest.fixture(autouse=True)
def _no_token(monkeypatch):
    monkeypatch.delenv("GITLAB_TOKEN", raising=False)
    monkeypatch.delenv("CI_JOB_TOKEN", raising=False)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _release(tag: str, *, description: str = "", upcoming: bool = False, links: list[dict] | None = None) -> dict:
    """Construct a GitLab release object."""
    return {
        "tag_name": tag,
        "description": description,
        "upcoming_release": upcoming,
        "assets": {"links": links or []},
    }


def _link(name: str, url: str, *, direct: str | None = None) -> dict:
    link = {"name": name, "url": url}
    if direct is not None:
        link["direct_asset_url"] = direct
    return link


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _single_page(releases: list[dict]):
    """A handler that serves one page of releases (empty thereafter)."""

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(200, json=releases if page == 1 else [])

    return handler


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------


def test_list_releases_maps_single_release_fields():
    handler = _single_page([_release("v1.0.0", description="notes", links=[_link("tool.tgz", "https://x/tool.tgz")])])

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert len(result) == 1
    rel = result[0]
    assert rel.tag_name == "v1.0.0"
    assert rel.body == "notes"
    assert rel.prerelease is False
    assert rel.draft is False
    assert [(a.name, a.browser_download_url) for a in rel.assets] == [("tool.tgz", "https://x/tool.tgz")]


def test_list_releases_prefers_direct_asset_url_over_url():
    handler = _single_page(
        [_release("v1", links=[_link("tool.tgz", "https://x/raw", direct="https://x/direct")])],
    )

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert result[0].assets[0].browser_download_url == "https://x/direct"


def test_list_releases_falls_back_to_url_when_no_direct_asset_url():
    handler = _single_page([_release("v1", links=[_link("tool.tgz", "https://x/raw")])])

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert result[0].assets[0].browser_download_url == "https://x/raw"


def test_list_releases_empty_links_yields_no_assets():
    handler = _single_page([_release("v1", links=[])])

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert result[0].assets == []


def test_list_releases_maps_upcoming_release_to_prerelease():
    handler = _single_page([_release("v2-rc", upcoming=True)])

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert result[0].prerelease is True


def test_list_releases_draft_is_always_false():
    handler = _single_page([_release("v1"), _release("v2-rc", upcoming=True)])

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert all(r.draft is False for r in result)


@pytest.mark.parametrize(
    "release",
    [
        pytest.param({"tag_name": "v1", "assets": {"links": []}}, id="description-key-missing"),
        pytest.param({"tag_name": "v1", "description": "", "assets": {"links": []}}, id="description-empty"),
        pytest.param({"tag_name": "v1", "description": None, "assets": {"links": []}}, id="description-null"),
    ],
)
def test_list_releases_normalizes_missing_description_to_empty_body(release):
    handler = _single_page([release])

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert result[0].body == ""


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_list_releases_excludes_prereleases_when_disabled():
    handler = _single_page([_release("v1"), _release("v2-rc", upcoming=True)])

    result = gitlab.list_releases("o", "p", include_prereleases=False, client=_client(handler))

    assert [r.tag_name for r in result] == ["v1"]


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


def test_list_releases_paginates_until_short_page(monkeypatch):
    monkeypatch.setattr(rest_module, "_PER_PAGE", 2)
    pages = {
        1: [_release("v1"), _release("v2")],
        2: [_release("v3")],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(200, json=pages.get(page, []))

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert [r.tag_name for r in result] == ["v1", "v2", "v3"]


def test_list_releases_stops_on_empty_trailing_page(monkeypatch):
    monkeypatch.setattr(rest_module, "_PER_PAGE", 2)
    pages = {
        1: [_release("v1"), _release("v2")],
        2: [],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(200, json=pages.get(page, []))

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert [r.tag_name for r in result] == ["v1", "v2"]


def test_list_releases_warns_and_truncates_at_max_pages(monkeypatch, caplog):
    monkeypatch.setattr(rest_module, "_PER_PAGE", 1)
    monkeypatch.setattr(rest_module, "_MAX_PAGES", 2)

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(200, json=[_release(f"v{page}")])

    with caplog.at_level(logging.WARNING, logger="ocx_mirror_sdk.gitlab._rest"):
        result = gitlab.list_releases("o", "p", client=_client(handler))

    assert [r.tag_name for r in result] == ["v1", "v2"]
    assert "reached page limit" in caplog.text


# ---------------------------------------------------------------------------
# URL building / host / encoding / auth
# ---------------------------------------------------------------------------


def test_list_releases_uses_default_gitlab_com_host():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json=[])

    gitlab.list_releases("o", "p", client=_client(handler))

    assert seen[0].startswith("https://gitlab.com/api/v4/projects/o%2Fp/releases")


def test_list_releases_self_hosted_host_builds_url_and_cache_key(cache):
    seen: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, json=[_release("v1")])

    gitlab.list_releases("grp", "proj", host="https://gitlab.example.com", client=_client(handler))

    assert seen[0].host == "gitlab.example.com"
    assert str(seen[0]).startswith("https://gitlab.example.com/api/v4/projects/grp%2Fproj/releases")
    assert "gitlab.example.com/grp/proj/releases" in cache.store


def test_list_releases_encodes_subgroup_path():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json=[])

    gitlab.list_releases("grp/sub", "proj", client=_client(handler))

    assert "projects/grp%2Fsub%2Fproj/releases" in seen[0]


def test_list_releases_sends_private_token_header_when_env_set(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "secret-token")
    seen: list[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers)
        return httpx.Response(200, json=[])

    gitlab.list_releases("o", "p", client=_client(handler))

    assert seen[0]["private-token"] == "secret-token"


def test_list_releases_uses_job_token_header_in_ci(monkeypatch):
    monkeypatch.setenv("CI_JOB_TOKEN", "ci-job-token")
    seen: list[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers)
        return httpx.Response(200, json=[])

    gitlab.list_releases("o", "p", client=_client(handler))

    assert seen[0]["job-token"] == "ci-job-token"
    assert "private-token" not in seen[0]


def test_list_releases_prefers_private_token_over_job_token(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "personal-token")
    monkeypatch.setenv("CI_JOB_TOKEN", "ci-job-token")
    seen: list[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers)
        return httpx.Response(200, json=[])

    gitlab.list_releases("o", "p", client=_client(handler))

    assert seen[0]["private-token"] == "personal-token"
    assert "job-token" not in seen[0]


def test_list_releases_omits_token_header_when_absent():
    seen: list[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers)
        return httpx.Response(200, json=[])

    gitlab.list_releases("o", "p", client=_client(handler))

    assert "private-token" not in seen[0]
    assert "job-token" not in seen[0]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_list_releases_raises_http_status_error_on_404():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "404 Project Not Found"})

    with pytest.raises(HttpStatusError, match="HTTP 404"):
        gitlab.list_releases("o", "missing", client=_client(handler))


def test_list_releases_http_status_error_chains_to_httpx():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream")

    with pytest.raises(HttpStatusError) as exc_info:
        gitlab.list_releases("o", "p", client=_client(handler))

    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)
    assert exc_info.value.status_code == 503


def test_list_releases_raises_http_timeout_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout")

    with pytest.raises(HttpTimeoutError):
        gitlab.list_releases("o", "p", client=_client(handler))


def test_list_releases_raises_api_response_error_on_non_list_payload():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": "unexpected object"})

    with pytest.raises(ApiResponseError, match="not a JSON array"):
        gitlab.list_releases("o", "p", client=_client(handler))


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


def test_list_releases_cache_hit_skips_http(cache):
    cache.put_json(
        "gitlab.com/o/p/releases",
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

    result = gitlab.list_releases("o", "p", client=_client(handler))

    assert [r.tag_name for r in result] == ["v1"]
    assert result[0].assets[0].name == "cached.tgz"
