# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Public API for `ocx-mirror-sdk`.

Top-level imports are the only stable contract. Everything reachable via
underscored module paths is package-private and may change without notice.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from ocx_mirror_sdk.cache import FileCache, configure
from ocx_mirror_sdk.errors import (
    ApiResponseError,
    CacheError,
    ConfigurationError,
    HttpStatusError,
    HttpTimeoutError,
    OcxMirrorError,
    SchemaError,
    TransportError,
)
from ocx_mirror_sdk.github import Backend, list_releases
from ocx_mirror_sdk.index import IndexBuilder
from ocx_mirror_sdk.releases import Asset, Release
from ocx_mirror_sdk.text import extract_urls


def _resolve_version() -> str:
    """Return the installed package version, or a fallback when running from source."""
    try:
        return _pkg_version("ocx-mirror-sdk")
    except PackageNotFoundError:
        return "0.0.0+unknown"


__version__ = _resolve_version()

__all__ = [
    "ApiResponseError",
    "Asset",
    "Backend",
    "CacheError",
    "ConfigurationError",
    "FileCache",
    "HttpStatusError",
    "HttpTimeoutError",
    "IndexBuilder",
    "OcxMirrorError",
    "Release",
    "SchemaError",
    "TransportError",
    "__version__",
    "configure",
    "extract_urls",
    "list_releases",
]
