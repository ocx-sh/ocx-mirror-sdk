# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""GitLab release source — REST backend.

Sibling to :mod:`ocx_mirror_sdk.github`. Use ``gitlab.list_releases(namespace,
project, *, host=...)`` to fetch releases from gitlab.com or a self-hosted
GitLab instance. Returns the same source-agnostic :class:`~ocx_mirror_sdk.Release`
objects as the GitHub source.
"""

from ocx_mirror_sdk.gitlab._rest import list_releases

__all__ = ["list_releases"]
