# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Tests for the REST backend of ``ocx_mirror_sdk.list_releases``.

Exercises the router (``backend=Backend.REST``) end-to-end with an injected
``httpx.Client`` + ``MockTransport`` per ``quality-tests.md`` §8, and
``FakeFileCache`` (``tests/_fakes.py``) per §7 in place of the disk cache.
"""

from collections.abc import Callable

import httpx
import pytest
from _fakes import FakeFileCache

from ocx_mirror_sdk import Asset
from ocx_mirror_sdk.errors import ApiResponseError, HttpStatusError
from ocx_mirror_sdk.github import _rest as rest_module
from ocx_mirror_sdk.github import list_releases
from ocx_mirror_sdk.releases import Release

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rel(
    tag: str, *, body: str = "", prerelease: bool = False, draft: bool = False, assets: list[dict] | None = None
) -> dict:
    """A REST release object as returned by the list endpoint (assets inline)."""
    return {
        "tag_name": tag,
        "body": body,
        "prerelease": prerelease,
        "draft": draft,
        "assets": assets if assets is not None else [],
    }


def _asset(name: str, url: str) -> dict:
    # Real payloads carry more keys; the backend must read only these two.
    return {"name": name, "browser_download_url": url, "id": 1, "size": 10}


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _isolate_cache(monkeypatch) -> FakeFileCache:
    cache = FakeFileCache()
    monkeypatch.setattr(rest_module, "_cache", cache)
    return cache


def _rest(path="o/r", **kw):
    return list_releases(path, backend="rest", **kw)


def _single_page_handler(releases: list[dict]) -> Callable[[httpx.Request], httpx.Response]:
    """Serve ``releases`` on page 1, then an empty page (end of pagination)."""

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(200, json=releases if page == 1 else [])

    return handler


def _silence_sleep(monkeypatch) -> list[float]:
    """Swap the per-page retry sleep seam for a no-op that records delays."""
    delays: list[float] = []
    monkeypatch.setattr(rest_module, "_sleep", lambda seconds: delays.append(seconds))
    return delays


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_list_releases_basic(monkeypatch):
    _isolate_cache(monkeypatch)
    handler = _single_page_handler(
        [_rel("v1.0.0", body="Release notes", assets=[_asset("tool.tar.gz", "https://x/tool.tar.gz")])]
    )

    results = _rest("owner/repo", client=_client(handler))

    assert len(results) == 1
    r = results[0]
    assert isinstance(r, Release)
    assert r.tag_name == "v1.0.0"
    assert r.body == "Release notes"
    assert r.prerelease is False
    assert r.draft is False
    assert len(r.assets) == 1
    assert isinstance(r.assets[0], Asset)
    assert r.assets[0].name == "tool.tar.gz"
    assert r.assets[0].browser_download_url == "https://x/tool.tar.gz"


def test_list_releases_empty(monkeypatch):
    _isolate_cache(monkeypatch)
    results = _rest("owner/repo", client=_client(_single_page_handler([])))
    assert results == []


def test_list_releases_null_body_normalised_to_empty(monkeypatch):
    _isolate_cache(monkeypatch)
    rel = _rel("v1.0.0")
    rel["body"] = None
    results = _rest("owner/repo", client=_client(_single_page_handler([rel])))
    assert results[0].body == ""


def test_list_releases_multiple_assets(monkeypatch):
    _isolate_cache(monkeypatch)
    rel = _rel(
        "v1.0.0",
        assets=[_asset("tool-linux.tar.gz", "https://x/linux"), _asset("tool-darwin.tar.gz", "https://x/darwin")],
    )
    results = _rest("owner/repo", client=_client(_single_page_handler([rel])))
    assert {a.name for a in results[0].assets} == {"tool-linux.tar.gz", "tool-darwin.tar.gz"}


def test_list_releases_paginates(monkeypatch):
    """Full pages are followed; a short page ends pagination."""
    _isolate_cache(monkeypatch)
    # per_page defaults to 100; emit a full page then a short page.
    page1 = [_rel(f"v{i}") for i in range(100)]
    page2 = [_rel("v100")]
    pages = {1: page1, 2: page2}

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        return httpx.Response(200, json=pages.get(page, []))

    results = _rest(client=_client(handler))
    assert [r.tag_name for r in results] == [f"v{i}" for i in range(101)]


# ---------------------------------------------------------------------------
# Adaptive page-size fallback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("overload_status", [502, 503, 504])
def test_falls_back_to_small_page_on_overload(monkeypatch, overload_status):
    """A 5xx overload at the default page size retries at the fallback size."""
    _isolate_cache(monkeypatch)
    seen_per_page: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        per_page = int(request.url.params.get("per_page"))
        page = int(request.url.params.get("page", "1"))
        seen_per_page.append(per_page)
        if per_page == rest_module._DEFAULT_PER_PAGE:
            return httpx.Response(overload_status, text="overloaded")
        # Fallback page size succeeds.
        return httpx.Response(200, json=[_rel("v1.0.0")] if page == 1 else [])

    results = _rest(client=_client(handler))

    assert [r.tag_name for r in results] == ["v1.0.0"]
    assert rest_module._DEFAULT_PER_PAGE in seen_per_page
    assert rest_module._FALLBACK_PER_PAGE in seen_per_page


def test_timeout_at_default_page_falls_back(monkeypatch):
    _isolate_cache(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        per_page = int(request.url.params.get("per_page"))
        page = int(request.url.params.get("page", "1"))
        if per_page == rest_module._DEFAULT_PER_PAGE:
            raise httpx.ReadTimeout("slow", request=request)
        return httpx.Response(200, json=[_rel("v1.0.0")] if page == 1 else [])

    results = _rest(client=_client(handler))
    assert [r.tag_name for r in results] == ["v1.0.0"]


def test_non_overload_status_does_not_fall_back(monkeypatch):
    """A 500 (not in the overload set) propagates without a fallback attempt."""
    _isolate_cache(monkeypatch)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, text="boom")

    with pytest.raises(HttpStatusError, match="HTTP 500"):
        _rest(client=_client(handler))
    assert calls == 1  # no fallback retry


def test_intermittent_page_504_at_fallback_size_retries_then_succeeds(monkeypatch):
    """A single page 504 at the fallback size is retried with backoff, not fatal."""
    _isolate_cache(monkeypatch)
    delays = _silence_sleep(monkeypatch)
    attempts: dict[int, int] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        per_page = int(request.url.params.get("per_page"))
        page = int(request.url.params.get("page", "1"))
        if per_page == rest_module._DEFAULT_PER_PAGE:
            return httpx.Response(504, text="too big")  # force fallback to small pages
        attempts[page] = attempts.get(page, 0) + 1
        # Page 1 504s twice, then succeeds; page 2 is the empty terminator.
        if page == 1 and attempts[page] <= 2:
            return httpx.Response(504, text="transient")
        return httpx.Response(200, json=[_rel("v1.0.0")] if page == 1 else [])

    results = _rest(client=_client(handler))

    assert [r.tag_name for r in results] == ["v1.0.0"]
    assert delays == [1.0, 2.0]  # two transient 504s → two backoff sleeps


def test_page_504_exhausts_retries_then_raises(monkeypatch):
    _isolate_cache(monkeypatch)
    delays = _silence_sleep(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        per_page = int(request.url.params.get("per_page"))
        if per_page == rest_module._DEFAULT_PER_PAGE:
            return httpx.Response(504, text="too big")
        return httpx.Response(504, text="always down")

    with pytest.raises(HttpStatusError, match="HTTP 504"):
        _rest(client=_client(handler))

    # _PAGE_RETRIES retries → that many backoff sleeps before the terminal raise.
    assert len(delays) == rest_module._PAGE_RETRIES


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_repo_not_found_raises_api_response_error(monkeypatch):
    _isolate_cache(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    with pytest.raises(ApiResponseError, match="repository not found"):
        _rest("owner/nonexistent", client=_client(handler))


def test_non_array_payload_raises_api_response_error(monkeypatch):
    _isolate_cache(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": "unexpected"})

    with pytest.raises(ApiResponseError, match="not a JSON array"):
        _rest(client=_client(handler))


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_exclude_prereleases(monkeypatch):
    _isolate_cache(monkeypatch)
    handler = _single_page_handler([_rel("v1.0.0"), _rel("v2.0.0-rc1", prerelease=True)])
    results = _rest("owner/repo", include_prereleases=False, client=_client(handler))
    assert [r.tag_name for r in results] == ["v1.0.0"]


def test_exclude_drafts(monkeypatch):
    _isolate_cache(monkeypatch)
    handler = _single_page_handler([_rel("v1.0.0"), _rel("v2.0.0", draft=True)])
    results = _rest("owner/repo", include_drafts=False, client=_client(handler))
    assert [r.tag_name for r in results] == ["v1.0.0"]


# ---------------------------------------------------------------------------
# Auth header
# ---------------------------------------------------------------------------


def test_token_sets_authorization_header(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    _isolate_cache(monkeypatch)
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("Authorization"))
        return httpx.Response(200, json=[])

    _rest(client=_client(handler))
    assert seen == ["Bearer secret-token"]


def test_no_token_omits_authorization_header(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    _isolate_cache(monkeypatch)
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("Authorization"))
        return httpx.Response(200, json=[])

    _rest(client=_client(handler))
    assert seen == [None]


# ---------------------------------------------------------------------------
# Cache key + router behaviour
# ---------------------------------------------------------------------------


def test_cache_key_format(monkeypatch):
    cache = _isolate_cache(monkeypatch)
    list_releases("corretto/corretto-21", client=_client(_single_page_handler([])))
    assert "corretto/corretto-21/releases" in cache.store


def test_cache_key_ignores_filters(monkeypatch):
    cache = _isolate_cache(monkeypatch)
    list_releases("o/r", include_prereleases=False, include_drafts=False, client=_client(_single_page_handler([])))
    assert "o/r/releases" in cache.store


def test_list_releases_accepts_string_backend(monkeypatch):
    _isolate_cache(monkeypatch)
    assert list_releases("o/r", backend="rest", client=_client(_single_page_handler([]))) == []


def test_list_releases_unknown_backend_raises_value_error():
    with pytest.raises(ValueError, match="'foo'"):
        list_releases("o/r", backend="foo")


def test_list_releases_invalid_path_raises():
    with pytest.raises(ValueError, match="github path must be 'owner/repo'"):
        list_releases("just-owner")


def test_release_round_trip():
    release = Release(
        tag_name="v1.0.0",
        body="notes",
        prerelease=False,
        draft=False,
        assets=[Asset(name="f.tar.gz", browser_download_url="https://x/f.tar.gz")],
    )
    assert Release.from_dict(release.to_dict()) == release
