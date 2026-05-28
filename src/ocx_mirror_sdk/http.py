# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Retry-aware HTTP client for generator scripts.

Public helpers wrap transport-layer exceptions into the SDK's typed
:mod:`ocx_mirror_sdk.errors` hierarchy. Callers should expect
:class:`HttpStatusError`, :class:`HttpTimeoutError`, or
:class:`ApiResponseError` instead of raw ``httpx`` exceptions.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from ocx_mirror_sdk.errors import ApiResponseError, HttpStatusError, HttpTimeoutError

_CLIENT: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            transport=httpx.HTTPTransport(retries=3),
        )
    return _CLIENT


def _wrap_status(exc: httpx.HTTPStatusError) -> HttpStatusError:
    response_text: str | None = None
    try:
        response_text = exc.response.text[:1000]
    except Exception:
        response_text = None
    return HttpStatusError(
        status_code=exc.response.status_code,
        url=str(exc.request.url),
        response_text=response_text,
    )


def fetch_json(url: str, *, client: httpx.Client | None = None) -> Any:
    """Fetch a URL and parse the response as JSON.

    Args:
        url: Target URL.
        client: Optional injected client. Defaults to the module-level
            singleton (lazy-initialized with sane retry / timeout). Tests
            should pass ``httpx.Client(transport=httpx.MockTransport(...))``.

    Raises:
        HttpStatusError: Response status was 4xx/5xx.
        HttpTimeoutError: Request timed out.
        ApiResponseError: Body was not valid JSON.
    """
    try:
        response = (client or _get_client()).get(url)
        response.raise_for_status()
    except httpx.TimeoutException as e:
        raise HttpTimeoutError(url=url) from e
    except httpx.HTTPStatusError as e:
        raise _wrap_status(e) from e
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise ApiResponseError("response body is not valid JSON", payload=None) from e


def fetch_text(url: str, *, client: httpx.Client | None = None) -> str:
    """Fetch a URL and return the response body as text.

    Args:
        url: Target URL.
        client: Optional injected client. See :func:`fetch_json` for details.

    Raises:
        HttpStatusError: Response status was 4xx/5xx.
        HttpTimeoutError: Request timed out.
    """
    try:
        response = (client or _get_client()).get(url)
        response.raise_for_status()
    except httpx.TimeoutException as e:
        raise HttpTimeoutError(url=url) from e
    except httpx.HTTPStatusError as e:
        raise _wrap_status(e) from e
    return response.text


def post_json(
    url: str,
    *,
    body: Any,
    headers: dict[str, str] | None = None,
    client: httpx.Client | None = None,
) -> Any:
    """POST a JSON payload and parse the response as JSON.

    Args:
        url: Target URL.
        body: JSON-serializable request body.
        headers: Optional request headers (e.g. ``Authorization``).
        client: Optional injected client. See :func:`fetch_json` for details.

    Raises:
        HttpStatusError: Response status was 4xx/5xx.
        HttpTimeoutError: Request timed out.
        ApiResponseError: Body was not valid JSON.
    """
    try:
        response = (client or _get_client()).post(url, headers=headers, json=body)
        response.raise_for_status()
    except httpx.TimeoutException as e:
        raise HttpTimeoutError(url=url) from e
    except httpx.HTTPStatusError as e:
        raise _wrap_status(e) from e
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise ApiResponseError("response body is not valid JSON", payload=None) from e
