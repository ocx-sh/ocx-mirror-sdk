# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Format-agnostic file cache with TTL expiration.

Stores raw bytes on disk, keyed by a domain tag and an arbitrary cache key.
Freshness is determined by the file's modification time — no metadata envelope.
The caller decides how to serialize and deserialize the data.

A cache *miss* is normal control flow and returns ``None``. A genuinely
abnormal event (corrupt JSON on disk, IO failure, permission denied) raises
:class:`~ocx_mirror_sdk.errors.CacheError`.

Typical usage::

    cache = FileCache("github", max_age=3600)

    # fetch-through with JSON: calls the loader only on cache miss
    releases = cache.fetch_json("corretto/corretto-21", load_releases)

    # manual store / get (raw bytes)
    cache.put("key", b"raw bytes")
    cached = cache.get("key")  # -> bytes | None

    # manual store / get (JSON)
    cache.put_json("key", {"count": 42})
    obj = cache.get_json("key")  # -> Any | None
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ocx_mirror_sdk.errors import CacheError

_DEFAULT_ROOT = Path.home() / ".cache" / "ocx-mirror-sdk"

# Overridable via :func:`configure`. Module-private; cache instances read it
# lazily on each ``_path`` call so a call to ``configure`` before any IO is
# always picked up.
_cache_root_override: Path | None = None


def configure(*, cache_root: Path | None = None) -> None:
    """Override SDK-wide cache settings.

    Args:
        cache_root: New default cache root directory. Use ``None`` to
            reset to ``~/.cache/ocx-mirror-sdk/``. Cache instances pick up
            the change on their next IO call.

    Example:
        >>> from pathlib import Path
        >>> from ocx_mirror_sdk import configure
        >>> configure(cache_root=Path("/tmp/my-cache"))
    """
    global _cache_root_override
    _cache_root_override = cache_root


def _resolve_root() -> Path:
    return _cache_root_override if _cache_root_override is not None else _DEFAULT_ROOT


class FileCache:
    """TTL-based blob cache with domain separation.

    Args:
        domain: Namespace subdirectory (e.g. ``"github"``).
        max_age: Maximum age of cache entries in seconds.  ``0`` disables
            caching (every ``get`` returns ``None``, ``fetch`` always calls
            the loader).
        root: Root cache directory.  Defaults to the value set by
            :func:`configure`, or ``~/.cache/ocx-mirror-sdk/``.
    """

    def __init__(
        self,
        domain: str,
        *,
        max_age: int = 3600,
        root: Path | None = None,
    ) -> None:
        self._domain = domain
        self._explicit_root = root
        self._max_age = max_age

    @property
    def _dir(self) -> Path:
        return (self._explicit_root or _resolve_root()) / self._domain

    def _path(self, key: str) -> Path:
        """Turn a cache key into a file path (``/`` in key creates subdirs)."""
        return self._dir / key

    def get(self, key: str) -> bytes | None:
        """Return cached bytes for *key*, or ``None`` on miss / expiry.

        Raises:
            CacheError: The on-disk entry exists but cannot be read.
        """
        if self._max_age <= 0:
            return None
        path = self._path(key)
        if not path.exists():
            return None
        try:
            age = time.time() - path.stat().st_mtime
            if age >= self._max_age:
                return None
            return path.read_bytes()
        except OSError as e:
            raise CacheError("failed to read cache entry", path=path) from e

    def put(self, key: str, data: bytes) -> None:
        """Store *data* under *key*. No-op when caching is disabled.

        Raises:
            CacheError: Writing the entry failed (disk full, permission).
        """
        if self._max_age <= 0:
            return
        path = self._path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        except OSError as e:
            raise CacheError("failed to write cache entry", path=path) from e

    def fetch(self, key: str, loader: Callable[[], bytes]) -> bytes:
        """Return cached bytes or call *loader*, cache the result, and return it."""
        cached = self.get(key)
        if cached is not None:
            return cached
        data = loader()
        self.put(key, data)
        return data

    # -- JSON convenience layer ------------------------------------------------

    def get_json(self, key: str) -> Any | None:
        """Return the deserialized JSON object for *key*, or ``None`` on miss.

        Raises:
            CacheError: The on-disk entry exists but is not valid JSON.
        """
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise CacheError("cache entry is not valid JSON", path=self._path(key)) from e

    def put_json(self, key: str, obj: Any) -> None:
        """Serialize *obj* as JSON and store it under *key*."""
        self.put(key, json.dumps(obj).encode())

    def fetch_json(self, key: str, loader: Callable[[], Any]) -> Any:
        """Return cached JSON or call *loader*, cache the result, and return it.

        Unlike :meth:`fetch`, the *loader* returns a JSON-serializable object
        (not raw bytes) and the return value is the deserialized object.
        """
        cached = self.get_json(key)
        if cached is not None:
            return cached
        obj = loader()
        self.put_json(key, obj)
        return obj
