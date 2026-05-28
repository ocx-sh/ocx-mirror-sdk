# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

import os
import stat
import time

import pytest

from ocx_mirror_sdk import CacheError, FileCache, configure
from ocx_mirror_sdk import cache as cache_module


def test_put_and_get(tmp_path):
    cache = FileCache("test", root=tmp_path)
    cache.put("key", b"hello")
    assert cache.get("key") == b"hello"


def test_miss_on_empty(tmp_path):
    cache = FileCache("test", root=tmp_path)
    assert cache.get("nonexistent") is None


def test_miss_on_expired(tmp_path):
    cache = FileCache("test", max_age=1, root=tmp_path)
    path = tmp_path / "test" / "key"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"old")
    # Backdate mtime
    old_time = time.time() - 10
    os.utime(path, (old_time, old_time))
    assert cache.get("key") is None


def test_hit_within_ttl(tmp_path):
    cache = FileCache("test", max_age=3600, root=tmp_path)
    cache.put("key", b"fresh")
    assert cache.get("key") == b"fresh"


def test_disabled_when_max_age_zero(tmp_path):
    cache = FileCache("test", max_age=0, root=tmp_path)
    cache.put("key", b"value")
    assert cache.get("key") is None


def test_nested_key(tmp_path):
    cache = FileCache("test", root=tmp_path)
    cache.put("owner/repo.json", b"data")
    assert cache.get("owner/repo.json") == b"data"


def test_fetch_calls_loader_on_miss(tmp_path):
    cache = FileCache("test", root=tmp_path)
    calls = []

    def loader():
        calls.append(1)
        return b"loaded"

    result = cache.fetch("key", loader)
    assert result == b"loaded"
    assert len(calls) == 1


def test_fetch_uses_cache_on_hit(tmp_path):
    cache = FileCache("test", root=tmp_path)
    calls = []

    def loader():
        calls.append(1)
        return b"loaded"

    cache.fetch("key", loader)
    result = cache.fetch("key", loader)
    assert result == b"loaded"
    assert len(calls) == 1


def test_fetch_bypassed_when_disabled(tmp_path):
    cache = FileCache("test", max_age=0, root=tmp_path)
    calls = []

    def loader():
        calls.append(1)
        return b"value"

    cache.fetch("key", loader)
    cache.fetch("key", loader)
    assert len(calls) == 2


def test_domain_separation(tmp_path):
    cache_a = FileCache("domain-a", root=tmp_path)
    cache_b = FileCache("domain-b", root=tmp_path)
    cache_a.put("key", b"a-value")
    cache_b.put("key", b"b-value")
    assert cache_a.get("key") == b"a-value"
    assert cache_b.get("key") == b"b-value"


def test_binary_data(tmp_path):
    cache = FileCache("test", root=tmp_path)
    data = bytes(range(256))
    cache.put("binary", data)
    assert cache.get("binary") == data


# -- JSON convenience methods -------------------------------------------------


def test_put_json_and_get_json(tmp_path):
    cache = FileCache("test", root=tmp_path)
    cache.put_json("key", {"count": 42, "items": [1, 2]})
    assert cache.get_json("key") == {"count": 42, "items": [1, 2]}


def test_get_json_miss(tmp_path):
    cache = FileCache("test", root=tmp_path)
    assert cache.get_json("missing") is None


def test_get_json_expired(tmp_path):
    cache = FileCache("test", max_age=1, root=tmp_path)
    cache.put_json("key", {"val": 1})
    path = tmp_path / "test" / "key"
    old_time = time.time() - 10
    os.utime(path, (old_time, old_time))
    assert cache.get_json("key") is None


def test_fetch_json_calls_loader_on_miss(tmp_path):
    cache = FileCache("test", root=tmp_path)
    calls = []

    def loader():
        calls.append(1)
        return {"loaded": True}

    result = cache.fetch_json("key", loader)
    assert result == {"loaded": True}
    assert len(calls) == 1


def test_fetch_json_uses_cache_on_hit(tmp_path):
    cache = FileCache("test", root=tmp_path)
    calls = []

    def loader():
        calls.append(1)
        return [1, 2, 3]

    cache.fetch_json("key", loader)
    result = cache.fetch_json("key", loader)
    assert result == [1, 2, 3]
    assert len(calls) == 1


def test_fetch_json_bypassed_when_disabled(tmp_path):
    cache = FileCache("test", max_age=0, root=tmp_path)
    calls = []

    def loader():
        calls.append(1)
        return "value"

    cache.fetch_json("key", loader)
    cache.fetch_json("key", loader)
    assert len(calls) == 2


# -- Error paths --------------------------------------------------------------


def test_get_json_raises_cache_error_on_corrupt_payload(tmp_path):
    cache = FileCache("test", root=tmp_path)
    path = tmp_path / "test" / "corrupt"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"<<not json>>")

    with pytest.raises(CacheError, match="not valid JSON"):
        cache.get_json("corrupt")


def test_get_raises_cache_error_on_unreadable_file(tmp_path):
    """Permission-denied on read surfaces as CacheError."""
    if os.geteuid() == 0:
        pytest.skip("root bypasses POSIX permission bits")
    cache = FileCache("test", root=tmp_path)
    cache.put("locked", b"data")
    path = tmp_path / "test" / "locked"
    os.chmod(path, 0)
    try:
        with pytest.raises(CacheError, match="failed to read"):
            cache.get("locked")
    finally:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def test_put_raises_cache_error_on_unwritable_dir(tmp_path):
    """Permission-denied on write surfaces as CacheError."""
    if os.geteuid() == 0:
        pytest.skip("root bypasses POSIX permission bits")
    cache = FileCache("locked-domain", root=tmp_path)
    # Create the domain dir first so write resolves the failure to mkdir->write
    cache.put("seed", b"x")
    os.chmod(tmp_path / "locked-domain", stat.S_IRUSR | stat.S_IXUSR)
    try:
        with pytest.raises(CacheError, match="failed to write"):
            cache.put("new", b"data")
    finally:
        os.chmod(tmp_path / "locked-domain", stat.S_IRWXU)


# -- configure() override -----------------------------------------------------


def test_configure_overrides_default_cache_root(tmp_path, monkeypatch):
    """configure(cache_root=...) redirects the default root."""
    monkeypatch.setattr(cache_module, "_cache_root_override", None)
    try:
        configure(cache_root=tmp_path)
        # New instance with NO explicit root reads the override lazily.
        cache = FileCache("dom")
        cache.put("k", b"v")
        assert (tmp_path / "dom" / "k").read_bytes() == b"v"
    finally:
        configure(cache_root=None)


def test_explicit_root_overrides_configure(tmp_path, monkeypatch):
    """When ``root=`` is passed to FileCache, configure() is ignored."""
    monkeypatch.setattr(cache_module, "_cache_root_override", tmp_path / "ignored")
    cache = FileCache("dom", root=tmp_path / "explicit")
    cache.put("k", b"v")
    assert (tmp_path / "explicit" / "dom" / "k").read_bytes() == b"v"
    assert not (tmp_path / "ignored").exists()
