# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 The OCX Authors

"""GitLab authentication helpers (package-private).

The GitLab REST API accepts different tokens under different headers. We
auto-select based on the environment so the same generator script works both
locally and inside a GitLab CI/CD pipeline without code changes:

* ``GITLAB_TOKEN`` — a personal / project / group access token you set
  yourself; sent as ``PRIVATE-TOKEN``.
* ``CI_JOB_TOKEN`` — injected automatically into every GitLab CI/CD job;
  short-lived and limited-scope; sent as ``JOB-TOKEN``.

See <https://docs.gitlab.com/api/rest/authentication/>.
"""

from __future__ import annotations

import os

_PRIVATE_TOKEN_ENV = "GITLAB_TOKEN"
_JOB_TOKEN_ENV = "CI_JOB_TOKEN"


def _resolve_auth_header() -> dict[str, str] | None:
    """Return the auth header for the GitLab REST API, or ``None`` for anonymous.

    Precedence (first match wins):

    1. ``GITLAB_TOKEN`` → ``PRIVATE-TOKEN`` header. An explicitly-set access
       token has the broadest scope and reflects operator intent, so it wins
       over the ambient job token even inside a pipeline.
    2. ``CI_JOB_TOKEN`` → ``JOB-TOKEN`` header. Present automatically in
       GitLab CI/CD jobs.

    Returns ``None`` when neither is set — anonymous access works on public
    projects.
    """
    token = os.environ.get(_PRIVATE_TOKEN_ENV)
    if token:
        return {"PRIVATE-TOKEN": token}
    job_token = os.environ.get(_JOB_TOKEN_ENV)
    if job_token:
        return {"JOB-TOKEN": job_token}
    return None
