# Install

Pre-1.0: no PyPI publishing yet. Pin to a git tag.

## PEP 723 (recommended for one-file generators)

A generator script is a single file. [PEP 723](https://peps.python.org/pep-0723/)
inline-metadata lets you declare dependencies inside the script itself —
`uv` reads the block and provisions an ephemeral environment.

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ git+https://github.com/ocx-sh/ocx-mirror-sdk@v0.3.0",
# ]
# ///

from ocx_mirror_sdk import IndexBuilder, list_releases, Backend
```

Run it directly:

```bash
uv run my_generator.py
```

## `pyproject.toml` (multi-file projects)

```toml
[project]
dependencies = ["ocx-mirror-sdk"]

[tool.uv.sources]
ocx-mirror-sdk = { git = "https://github.com/ocx-sh/ocx-mirror-sdk", tag = "v0.3.0" }
```

`uv.lock` pins the tag to a commit SHA — `uv sync --frozen` is reproducible.

## Tag selection

| Source | Tag |
|---|---|
| Latest stable | [`v0.3.0`](https://github.com/ocx-sh/ocx-mirror-sdk/releases/tag/v0.3.0) |
| Bleeding edge (no stability guarantees) | `main` |

Bump only when you've read the release notes — pre-1.0 minor bumps **may**
break import names and exception types.
