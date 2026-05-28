# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Exception hierarchy for `ocx_mirror_sdk`.

All exceptions raised from this SDK inherit from :class:`OcxMirrorError`.
Callers can catch the base class to recover from any SDK failure, or pick
a subclass for finer-grained handling.

See :doc:`.claude/rules/quality-errors.md` for the project rule that
codifies this hierarchy.
"""

from __future__ import annotations

from pathlib import Path


class OcxMirrorError(Exception):
    """Base class for every exception raised from `ocx_mirror_sdk`.

    Catch this to recover from any SDK-level failure::

        try:
            list_releases("owner", "repo")
        except OcxMirrorError as e:
            log.warning("SDK call failed: %s", e)
    """


class ConfigurationError(OcxMirrorError):
    """Required configuration is missing or invalid.

    Examples: ``GITHUB_TOKEN`` not set when required, `github3` client
    failed to initialize. Not retryable.
    """


class TransportError(OcxMirrorError):
    """Base class for network / transport failures (retry candidates)."""


class HttpStatusError(TransportError):
    """An HTTP response carried a non-2xx status code.

    Attributes:
        status_code: HTTP status code.
        url: Absolute request URL.
        response_text: First 1000 chars of the response body, or ``None``.
    """

    def __init__(
        self,
        *,
        status_code: int,
        url: str,
        response_text: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.url = url
        self.response_text = response_text
        super().__init__(f"HTTP {status_code} for {url}")


class HttpTimeoutError(TransportError):
    """The request did not complete within the configured timeout.

    Attributes:
        url: Absolute request URL.
    """

    def __init__(self, *, url: str) -> None:
        self.url = url
        super().__init__(f"HTTP timeout for {url}")


class ApiResponseError(OcxMirrorError):
    """The server responded but the payload is unusable.

    Examples: malformed JSON, GraphQL ``errors`` array, REST repository
    not found.

    Attributes:
        payload: Raw payload echoed for diagnostics. ``None`` when there
            was no parseable body (e.g. JSON decode failure).
    """

    def __init__(
        self,
        message: str = "unusable API response",
        *,
        payload: object = None,
    ) -> None:
        self.payload = payload
        super().__init__(message)


class SchemaError(OcxMirrorError):
    """Input data did not match the expected schema.

    Raised when :meth:`Release.from_dict` encounters missing or wrongly
    typed fields.

    Attributes:
        field: Name of the offending field, or ``None`` if unknown.
    """

    def __init__(
        self,
        message: str = "schema mismatch",
        *,
        field: str | None = None,
    ) -> None:
        self.field = field
        if field:
            message = f"{message}: field={field!r}"
        super().__init__(message)


class CacheError(OcxMirrorError):
    """An on-disk cache operation failed.

    Cache *misses* are not errors (see :meth:`FileCache.get` which
    returns ``None``). This class is reserved for genuinely abnormal
    events: corrupt JSON, IO failure, permission denied.

    Attributes:
        path: The on-disk path that triggered the failure, or ``None``.
    """

    def __init__(
        self,
        message: str = "cache operation failed",
        *,
        path: Path | None = None,
    ) -> None:
        self.path = path
        if path is not None:
            message = f"{message}: path={path}"
        super().__init__(message)


__all__ = [
    "ApiResponseError",
    "CacheError",
    "ConfigurationError",
    "HttpStatusError",
    "HttpTimeoutError",
    "OcxMirrorError",
    "SchemaError",
    "TransportError",
]
