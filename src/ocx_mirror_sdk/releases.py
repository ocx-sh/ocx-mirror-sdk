# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""Release model types — the return contract of :func:`list_releases`.

These types are source-agnostic. Today the only producer is GitHub
(:mod:`ocx_mirror_sdk.github`), but future sources (GitLab, Forgejo,
custom HTTP endpoints) return the same shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ocx_mirror_sdk.errors import SchemaError


@dataclass(frozen=True, slots=True)
class Asset:
    """A downloadable file attached to a release.

    Attributes:
        name: Filename of the asset (e.g. ``"node-v22.15.0-linux-x64.tar.gz"``).
        browser_download_url: Stable HTTPS URL the asset can be downloaded from.
    """

    name: str
    browser_download_url: str


@dataclass(frozen=True, slots=True)
class Release:
    """A release with its metadata and assets.

    Attributes:
        tag_name: The release tag (e.g. ``"v22.15.0"``).
        body: Release-notes body (may be empty).
        prerelease: Whether the release is flagged as pre-release upstream.
        draft: Whether the release is a draft.
        assets: List of downloadable :class:`Asset` objects.
    """

    tag_name: str
    body: str
    prerelease: bool
    draft: bool
    assets: list[Asset]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return {
            "tag_name": self.tag_name,
            "body": self.body,
            "prerelease": self.prerelease,
            "draft": self.draft,
            "assets": [{"name": a.name, "browser_download_url": a.browser_download_url} for a in self.assets],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Release:
        """Construct a :class:`Release` from a JSON-decoded dict.

        Raises:
            SchemaError: A required field is missing or wrongly typed.
        """
        try:
            return cls(
                tag_name=data["tag_name"],
                body=data.get("body", "") or "",
                prerelease=data["prerelease"],
                draft=data["draft"],
                assets=[Asset(name=a["name"], browser_download_url=a["browser_download_url"]) for a in data["assets"]],
            )
        except KeyError as e:
            field = e.args[0] if e.args else None
            raise SchemaError("missing required field", field=field) from e
        except TypeError as e:
            raise SchemaError("wrong field type") from e


__all__ = ["Asset", "Release"]
