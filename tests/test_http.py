# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Tests for ``ocx_mirror_sdk.http`` — HTTP boundary via injected client.

Uses ``httpx.MockTransport`` per ``quality-tests.md`` §8; no ``respx``,
no patching of ``httpx.Client.send``.
"""

import httpx
import pytest

from ocx_mirror_sdk import ApiResponseError, HttpStatusError, HttpTimeoutError, http


def _make_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


# ---------------------------------------------------------------------------
# fetch_json
# ---------------------------------------------------------------------------


def test_fetch_json_returns_parsed_body():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hello": "world"})

    body = http.fetch_json("https://api.example.com/x", client=_make_client(handler))

    assert body == {"hello": "world"}


def test_fetch_json_raises_http_status_error_on_4xx():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "not found"})

    with pytest.raises(HttpStatusError, match="HTTP 404"):
        http.fetch_json("https://api.example.com/missing", client=_make_client(handler))


def test_fetch_json_raises_api_response_error_on_invalid_json():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<<not json>>")

    with pytest.raises(ApiResponseError, match="not valid JSON"):
        http.fetch_json("https://api.example.com/x", client=_make_client(handler))


def test_fetch_json_status_error_chains_to_httpx():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream gateway")

    with pytest.raises(HttpStatusError) as exc_info:
        http.fetch_json("https://api.example.com/x", client=_make_client(handler))

    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)
    assert exc_info.value.status_code == 503
    assert exc_info.value.response_text == "upstream gateway"


def test_fetch_json_raises_http_timeout_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout")

    with pytest.raises(HttpTimeoutError, match="timeout"):
        http.fetch_json("https://api.example.com/slow", client=_make_client(handler))


# ---------------------------------------------------------------------------
# fetch_text
# ---------------------------------------------------------------------------


def test_fetch_text_returns_response_body():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain body")

    body = http.fetch_text("https://api.example.com/x", client=_make_client(handler))

    assert body == "plain body"


def test_fetch_text_raises_http_status_error_on_5xx():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(HttpStatusError, match="HTTP 500"):
        http.fetch_text("https://api.example.com/boom", client=_make_client(handler))


def test_fetch_text_raises_http_timeout_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout")

    with pytest.raises(HttpTimeoutError):
        http.fetch_text("https://api.example.com/slow", client=_make_client(handler))


# ---------------------------------------------------------------------------
# post_json
# ---------------------------------------------------------------------------


def test_post_json_round_trips_body_and_returns_parsed_response():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"echo": "ok"})

    body = http.post_json(
        "https://api.example.com/x",
        body={"q": "hello"},
        headers={"Authorization": "Bearer abc"},
        client=_make_client(handler),
    )

    assert body == {"echo": "ok"}
    assert b'"q":"hello"' in captured["body"]  # httpx uses compact JSON
    assert captured["headers"]["authorization"] == "Bearer abc"


def test_post_json_raises_http_status_error_on_5xx():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="bad gateway")

    with pytest.raises(HttpStatusError, match="HTTP 502"):
        http.post_json(
            "https://api.example.com/x",
            body={},
            client=_make_client(handler),
        )


def test_post_json_raises_api_response_error_on_invalid_json():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<<bad>>")

    with pytest.raises(ApiResponseError, match="not valid JSON"):
        http.post_json(
            "https://api.example.com/x",
            body={},
            client=_make_client(handler),
        )


# ---------------------------------------------------------------------------
# Lazy singleton
# ---------------------------------------------------------------------------


def test_get_client_lazy_initializes_singleton(monkeypatch):
    monkeypatch.setattr(http, "_CLIENT", None)

    client = http._get_client()

    assert isinstance(client, httpx.Client)
    assert http._CLIENT is client


def test_get_client_returns_cached_singleton(monkeypatch):
    sentinel = httpx.Client()
    monkeypatch.setattr(http, "_CLIENT", sentinel)

    assert http._get_client() is sentinel


def test_fetch_json_uses_singleton_when_no_client_passed(monkeypatch):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"via": "singleton"})

    monkeypatch.setattr(http, "_CLIENT", _make_client(handler))

    body = http.fetch_json("https://api.example.com/x")

    assert body == {"via": "singleton"}
