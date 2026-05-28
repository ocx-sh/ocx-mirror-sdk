# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Hierarchy invariants for ``ocx_mirror_sdk.errors``."""

from pathlib import Path

import pytest

from ocx_mirror_sdk import (
    ApiResponseError,
    CacheError,
    ConfigurationError,
    HttpStatusError,
    HttpTimeoutError,
    OcxMirrorError,
    SchemaError,
    TransportError,
)


@pytest.mark.parametrize(
    "cls",
    [
        ConfigurationError,
        TransportError,
        ApiResponseError,
        SchemaError,
        CacheError,
    ],
    ids=[
        "ConfigurationError",
        "TransportError",
        "ApiResponseError",
        "SchemaError",
        "CacheError",
    ],
)
def test_subclasses_inherit_from_ocx_mirror_error(cls):
    assert issubclass(cls, OcxMirrorError)
    assert issubclass(cls, Exception)


@pytest.mark.parametrize(
    "cls",
    [HttpStatusError, HttpTimeoutError],
    ids=["HttpStatusError", "HttpTimeoutError"],
)
def test_http_errors_inherit_from_transport_error(cls):
    assert issubclass(cls, TransportError)
    assert issubclass(cls, OcxMirrorError)


def test_http_status_error_attributes():
    exc = HttpStatusError(status_code=503, url="https://x/y", response_text="upstream")
    assert exc.status_code == 503
    assert exc.url == "https://x/y"
    assert exc.response_text == "upstream"
    assert "HTTP 503" in str(exc)
    assert "https://x/y" in str(exc)


def test_http_timeout_error_attributes():
    exc = HttpTimeoutError(url="https://x/y")
    assert exc.url == "https://x/y"
    assert "https://x/y" in str(exc)


def test_api_response_error_carries_payload():
    payload = [{"message": "rate limited"}]
    exc = ApiResponseError("graphql errors", payload=payload)
    assert exc.payload == payload


def test_api_response_error_default_payload_is_none():
    exc = ApiResponseError()
    assert exc.payload is None


def test_schema_error_renders_field():
    exc = SchemaError("missing", field="tag_name")
    assert exc.field == "tag_name"
    assert "tag_name" in str(exc)


def test_schema_error_without_field():
    exc = SchemaError()
    assert exc.field is None
    assert "field=" not in str(exc)


def test_cache_error_renders_path(tmp_path):
    path = tmp_path / "broken"
    exc = CacheError("corrupt", path=path)
    assert exc.path == path
    assert str(path) in str(exc)


def test_cache_error_without_path():
    exc = CacheError()
    assert exc.path is None
    assert "path=" not in str(exc)


def test_chaining_preserves_cause():
    original = KeyError("tag_name")
    try:
        try:
            raise original
        except KeyError as e:
            raise SchemaError(field="tag_name") from e
    except SchemaError as exc:
        assert exc.__cause__ is original


def test_cache_error_path_type_is_path(tmp_path):
    """Type guard: ``path`` is a ``pathlib.Path``, not ``str``."""
    exc = CacheError(path=tmp_path / "x")
    assert isinstance(exc.path, Path)
