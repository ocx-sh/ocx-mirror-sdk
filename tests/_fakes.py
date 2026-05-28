# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""In-memory test doubles for SDK collaborators.

Per ``quality-tests.md`` §7: when we own the interface, prefer a hand-written
fake over deep ``MagicMock`` chains. Fakes survive interface drift; mocks
silently rot.
"""

import json
from collections.abc import Callable
from typing import Any


class FakeFileCache:
    """Dict-backed fake of :class:`ocx_mirror_sdk.cache.FileCache`.

    Same public surface, zero disk I/O. Keys live in :attr:`store` so tests
    can inspect cached payloads directly.

    Behavioral parity:

    * ``max_age=0`` disables caching: ``get*`` returns ``None`` and
      ``put*`` is a no-op (matching the real :class:`FileCache`).
    * Otherwise, values never expire — tests that need expiry assertions
      should use the real ``FileCache`` with ``tmp_path``.
    """

    def __init__(self, *, max_age: int = 3600) -> None:
        self._max_age = max_age
        self.store: dict[str, bytes] = {}

    # -- bytes API -------------------------------------------------------------

    def get(self, key: str) -> bytes | None:
        if self._max_age <= 0:
            return None
        return self.store.get(key)

    def put(self, key: str, data: bytes) -> None:
        if self._max_age <= 0:
            return
        self.store[key] = data

    def fetch(self, key: str, loader: Callable[[], bytes]) -> bytes:
        cached = self.get(key)
        if cached is not None:
            return cached
        data = loader()
        self.put(key, data)
        return data

    # -- JSON convenience layer ------------------------------------------------

    def get_json(self, key: str) -> Any | None:
        raw = self.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def put_json(self, key: str, obj: Any) -> None:
        self.put(key, json.dumps(obj).encode())

    def fetch_json(self, key: str, loader: Callable[[], Any]) -> Any:
        cached = self.get_json(key)
        if cached is not None:
            return cached
        obj = loader()
        self.put_json(key, obj)
        return obj
