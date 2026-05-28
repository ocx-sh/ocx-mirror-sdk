#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.3.0",
# ]
# ///
"""How to handle the OcxMirrorError hierarchy in a generator.

Showcases:
- single-base catch + log
- branching on subclass for retry vs surface
- inspecting __cause__ for the original lower-layer exception

Usage:
    uv run examples/05_error_handling.py
"""

import logging
import sys
import time

from ocx_mirror_sdk import (
    ApiResponseError,
    ConfigurationError,
    HttpStatusError,
    HttpTimeoutError,
    OcxMirrorError,
    TransportError,
    list_releases,
)

log = logging.getLogger("generator")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def fetch_with_retry(owner: str, repo: str, *, attempts: int = 3) -> list:
    for attempt in range(1, attempts + 1):
        try:
            return list_releases(owner, repo)
        except (HttpTimeoutError, HttpStatusError) as e:
            # 5xx + timeouts are retry candidates
            if isinstance(e, HttpStatusError) and e.status_code < 500:
                raise  # 4xx is a contract error — surface immediately
            backoff = 2**attempt
            log.warning("transport failure (attempt %d/%d): %s — retry in %ds",
                        attempt, attempts, e, backoff)
            time.sleep(backoff)
    raise RuntimeError(f"exhausted retries for {owner}/{repo}")


def main() -> int:
    try:
        releases = fetch_with_retry("koalaman", "shellcheck")
    except ConfigurationError as e:
        log.error("config: %s", e)
        return 64  # EX_USAGE
    except ApiResponseError as e:
        log.error("upstream contract violation: %s (payload=%r)", e, e.payload)
        return 65  # EX_DATAERR
    except TransportError as e:
        log.error("network: %s (cause=%r)", e, e.__cause__)
        return 69  # EX_UNAVAILABLE
    except OcxMirrorError as e:
        log.error("sdk: %s", e)
        return 1

    print(f"fetched {len(releases)} releases", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
