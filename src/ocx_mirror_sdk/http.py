# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Retry-aware HTTP client for generator scripts."""

import httpx

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


def fetch_json(url: str, *, client: httpx.Client | None = None) -> object:
    """Fetch a URL and parse the response as JSON.

    Args:
        url: Target URL.
        client: Optional injected client. Defaults to the module-level
            singleton (lazy-initialized with sane retry / timeout). Tests
            should pass ``httpx.Client(transport=httpx.MockTransport(...))``.
    """
    response = (client or _get_client()).get(url)
    response.raise_for_status()
    return response.json()


def fetch_text(url: str, *, client: httpx.Client | None = None) -> str:
    """Fetch a URL and return the response body as text.

    Args:
        url: Target URL.
        client: Optional injected client. See :func:`fetch_json` for details.
    """
    response = (client or _get_client()).get(url)
    response.raise_for_status()
    return response.text
