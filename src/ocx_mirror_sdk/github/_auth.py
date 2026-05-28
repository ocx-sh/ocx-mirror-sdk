# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""GitHub authentication helpers (package-private)."""

from __future__ import annotations

import os


def _get_token() -> str | None:
    """Return the GitHub token from the environment, or ``None``."""
    return os.environ.get("GITHUB_TOKEN")
