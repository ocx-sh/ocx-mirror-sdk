# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""GitHub release source — REST + GraphQL backends behind a single router."""

from ocx_mirror_sdk.github._router import Backend, list_releases

__all__ = ["Backend", "list_releases"]
