# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Tests for ``ocx_mirror_sdk.http`` — HTTP boundary via injected client.

Uses ``httpx.MockTransport`` per ``quality-tests.md`` §8; no ``respx``,
no patching of ``httpx.Client.send``.
"""

import httpx
import pytest

from ocx_mirror_sdk import http


def _make_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_json_returns_parsed_body():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hello": "world"})

    body = http.fetch_json("https://api.example.com/x", client=_make_client(handler))

    assert body == {"hello": "world"}


def test_fetch_text_returns_response_body():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain body")

    body = http.fetch_text("https://api.example.com/x", client=_make_client(handler))

    assert body == "plain body"


def test_fetch_json_raises_on_http_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "not found"})

    with pytest.raises(httpx.HTTPStatusError, match="404"):
        http.fetch_json("https://api.example.com/missing", client=_make_client(handler))


def test_fetch_text_raises_on_http_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(httpx.HTTPStatusError, match="500"):
        http.fetch_text("https://api.example.com/boom", client=_make_client(handler))


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
