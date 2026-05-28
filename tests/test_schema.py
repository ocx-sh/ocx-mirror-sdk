# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Round-trip test: builder output must validate against the JSON Schema.

The schema lives at ``schemas/url-index.v1.json``, mirrored from
https://ocx.sh/schemas/url-index/v1.json. Run ``task codegen`` to refresh
both ``_schema.py`` and the snapshot used here.
"""

import io
import json
from pathlib import Path

import jsonschema

from ocx_mirror_sdk import IndexBuilder

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "url-index.v1.json"


def _load_schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as fp:
        return json.load(fp)


def test_empty_index_validates() -> None:
    builder = IndexBuilder()
    out = io.StringIO()
    builder.emit(file=out)

    data = json.loads(out.getvalue())
    jsonschema.validate(instance=data, schema=_load_schema())
    assert data == {"versions": {}}


def test_single_version_validates() -> None:
    builder = IndexBuilder()
    builder.add_version(
        "1.2.3",
        assets={"linux-amd64.tar.gz": "https://example.com/v1.2.3/linux-amd64.tar.gz"},
    )
    out = io.StringIO()
    builder.emit(file=out)

    data = json.loads(out.getvalue())
    jsonschema.validate(instance=data, schema=_load_schema())
    assert data["versions"]["1.2.3"]["prerelease"] is False
    assert data["versions"]["1.2.3"]["assets"]["linux-amd64.tar.gz"].startswith("https://")


def test_prerelease_flag_validates() -> None:
    builder = IndexBuilder()
    builder.add_version("2.0.0-rc1", assets={"any.zip": "https://example.com/rc.zip"}, prerelease=True)
    out = io.StringIO()
    builder.emit(file=out)

    data = json.loads(out.getvalue())
    jsonschema.validate(instance=data, schema=_load_schema())
    assert data["versions"]["2.0.0-rc1"]["prerelease"] is True


def test_invalid_payload_rejected() -> None:
    """Sanity check that the schema actually rejects malformed data."""
    bad = {"versions": {"1.0.0": {"prerelease": "not-a-bool", "assets": {}}}}
    try:
        jsonschema.validate(instance=bad, schema=_load_schema())
    except jsonschema.ValidationError:
        return
    raise AssertionError("schema accepted invalid prerelease type")
