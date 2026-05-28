# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Tests for the REST backend of ``ocx_mirror_sdk.list_releases``.

Exercises the router (``backend=Backend.REST``) end-to-end and the
``_login`` helper directly.
"""

from unittest.mock import MagicMock, patch

import pytest

from ocx_mirror_sdk import Asset, ConfigurationError, list_releases
from ocx_mirror_sdk.errors import ApiResponseError
from ocx_mirror_sdk.releases import Release


def _make_asset(name: str, url: str) -> MagicMock:
    asset = MagicMock()
    asset.name = name
    asset.browser_download_url = url
    return asset


def _make_release(
    tag: str,
    body: str = "",
    prerelease: bool = False,
    draft: bool = False,
    assets: list | None = None,
) -> MagicMock:
    release = MagicMock()
    release.tag_name = tag
    release.body = body
    release.prerelease = prerelease
    release.draft = draft
    release.assets.return_value = assets or []
    return release


@patch("ocx_mirror_sdk.github._rest._cache")
@patch("ocx_mirror_sdk.github._rest._login")
def test_list_releases_basic(mock_login, mock_cache):
    asset = _make_asset("tool.tar.gz", "https://example.com/tool.tar.gz")
    release = _make_release("v1.0.0", body="Release notes", assets=[asset])

    repo = MagicMock()
    repo.releases.return_value = [release]
    gh = MagicMock()
    gh.repository.return_value = repo
    mock_login.return_value = gh
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    results = list_releases("owner", "repo")

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


@patch("ocx_mirror_sdk.github._rest._cache")
@patch("ocx_mirror_sdk.github._rest._login")
def test_list_releases_empty(mock_login, mock_cache):
    repo = MagicMock()
    repo.releases.return_value = []
    gh = MagicMock()
    gh.repository.return_value = repo
    mock_login.return_value = gh
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    results = list_releases("owner", "repo")
    assert results == []


@patch("ocx_mirror_sdk.github._rest._cache")
@patch("ocx_mirror_sdk.github._rest._login")
def test_list_releases_repo_not_found_raises_api_response_error(mock_login, mock_cache):
    gh = MagicMock()
    gh.repository.return_value = None
    mock_login.return_value = gh
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    with pytest.raises(ApiResponseError, match="repository not found"):
        list_releases("owner", "nonexistent")


@patch("ocx_mirror_sdk.github._rest._cache")
@patch("ocx_mirror_sdk.github._rest._login")
def test_list_releases_prerelease_and_draft(mock_login, mock_cache):
    r1 = _make_release("v2.0.0-rc1", prerelease=True)
    r2 = _make_release("v1.0.0", draft=True)

    repo = MagicMock()
    repo.releases.return_value = [r1, r2]
    gh = MagicMock()
    gh.repository.return_value = repo
    mock_login.return_value = gh
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    results = list_releases("owner", "repo")
    assert results[0].prerelease is True
    assert results[1].draft is True


@patch("ocx_mirror_sdk.github._rest._cache")
@patch("ocx_mirror_sdk.github._rest._login")
def test_list_releases_null_body(mock_login, mock_cache):
    release = _make_release("v1.0.0")
    release.body = None

    repo = MagicMock()
    repo.releases.return_value = [release]
    gh = MagicMock()
    gh.repository.return_value = repo
    mock_login.return_value = gh
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    results = list_releases("owner", "repo")
    assert results[0].body == ""


@patch("ocx_mirror_sdk.github._rest._cache")
@patch("ocx_mirror_sdk.github._rest._login")
def test_list_releases_multiple_assets(mock_login, mock_cache):
    assets = [
        _make_asset("tool-linux.tar.gz", "https://example.com/linux.tar.gz"),
        _make_asset("tool-darwin.tar.gz", "https://example.com/darwin.tar.gz"),
    ]
    release = _make_release("v1.0.0", assets=assets)

    repo = MagicMock()
    repo.releases.return_value = [release]
    gh = MagicMock()
    gh.repository.return_value = repo
    mock_login.return_value = gh
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    results = list_releases("owner", "repo")
    assert len(results[0].assets) == 2
    names = {a.name for a in results[0].assets}
    assert names == {"tool-linux.tar.gz", "tool-darwin.tar.gz"}


@patch("ocx_mirror_sdk.github._rest._cache")
@patch("ocx_mirror_sdk.github._rest._login")
def test_exclude_prereleases(mock_login, mock_cache):
    stable = _make_release("v1.0.0")
    pre = _make_release("v2.0.0-rc1", prerelease=True)

    repo = MagicMock()
    repo.releases.return_value = [stable, pre]
    gh = MagicMock()
    gh.repository.return_value = repo
    mock_login.return_value = gh
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    results = list_releases("owner", "repo", include_prereleases=False)
    assert len(results) == 1
    assert results[0].tag_name == "v1.0.0"


@patch("ocx_mirror_sdk.github._rest._cache")
@patch("ocx_mirror_sdk.github._rest._login")
def test_exclude_drafts(mock_login, mock_cache):
    stable = _make_release("v1.0.0")
    draft = _make_release("v2.0.0", draft=True)

    repo = MagicMock()
    repo.releases.return_value = [stable, draft]
    gh = MagicMock()
    gh.repository.return_value = repo
    mock_login.return_value = gh
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    results = list_releases("owner", "repo", include_drafts=False)
    assert len(results) == 1
    assert results[0].tag_name == "v1.0.0"


@patch("ocx_mirror_sdk.github._rest._cache")
def test_cache_key_format(mock_cache):
    mock_cache.fetch_json.return_value = []

    list_releases("corretto", "corretto-21")

    mock_cache.fetch_json.assert_called_once()
    key = mock_cache.fetch_json.call_args[0][0]
    assert key == "corretto/corretto-21/releases"


@patch("ocx_mirror_sdk.github._rest._cache")
def test_cache_key_ignores_filters(mock_cache):
    mock_cache.fetch_json.return_value = []

    list_releases("o", "r", include_prereleases=False, include_drafts=False)

    key = mock_cache.fetch_json.call_args[0][0]
    assert key == "o/r/releases"


@patch("ocx_mirror_sdk.github._rest._cache")
def test_list_releases_accepts_string_backend(mock_cache):
    """Backend may be passed as raw string (StrEnum drop-in)."""
    mock_cache.fetch_json.return_value = []
    assert list_releases("o", "r", backend="rest") == []


@patch("ocx_mirror_sdk.github._rest._cache")
def test_list_releases_session_kwarg_replaces_login(mock_cache):
    """When ``session`` is injected, ``_login`` must NOT be called."""
    mock_cache.fetch_json.side_effect = lambda key, loader: loader()

    repo = MagicMock()
    repo.releases.return_value = []
    fake_session = MagicMock()
    fake_session.repository.return_value = repo

    with patch("ocx_mirror_sdk.github._rest._login") as mock_login:
        list_releases("o", "r", session=fake_session)

    mock_login.assert_not_called()
    fake_session.repository.assert_called_once_with("o", "r")


def test_list_releases_unknown_backend_raises_value_error():
    with pytest.raises(ValueError, match="'foo'"):
        list_releases("o", "r", backend="foo")


def test_release_round_trip():
    release = Release(
        tag_name="v1.0.0",
        body="notes",
        prerelease=False,
        draft=False,
        assets=[Asset(name="f.tar.gz", browser_download_url="https://x/f.tar.gz")],
    )
    assert Release.from_dict(release.to_dict()) == release


# ---------------------------------------------------------------------------
# _login() — patches the imported `github3` per "patch where used"
# (quality-tests.md §6).
# ---------------------------------------------------------------------------


def test_login_uses_token_when_env_set(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")

    with patch("ocx_mirror_sdk.github._rest.github3", autospec=True) as mock_gh3:
        gh = MagicMock()
        mock_gh3.login.return_value = gh

        from ocx_mirror_sdk.github._rest import _login

        result = _login()

    mock_gh3.login.assert_called_once_with(token="secret-token")
    mock_gh3.GitHub.assert_not_called()
    assert result is gh
    assert gh.session.default_read_timeout == 30


def test_login_uses_anonymous_when_no_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    with patch("ocx_mirror_sdk.github._rest.github3", autospec=True) as mock_gh3:
        gh = MagicMock()
        mock_gh3.GitHub.return_value = gh

        from ocx_mirror_sdk.github._rest import _login

        result = _login()

    mock_gh3.GitHub.assert_called_once_with()
    mock_gh3.login.assert_not_called()
    assert result is gh


def test_login_raises_configuration_error_when_github3_returns_none(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "bad-token")

    with patch("ocx_mirror_sdk.github._rest.github3", autospec=True) as mock_gh3:
        mock_gh3.login.return_value = None

        from ocx_mirror_sdk.github._rest import _login

        with pytest.raises(ConfigurationError, match="could not be initialized"):
            _login()
