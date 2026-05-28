# Install

Pre-1.0: no PyPI publishing yet. Two install paths, both reproducible:

- **Git tag** (primary) — concise URL, source build at install time.
- **Pre-built wheel** (alternative) — skip the build step by pinning the wheel
  attached to the GitHub Release.

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

## Pre-built wheel (alternative)

If you want to skip the source build (no `hatchling` at install time), pin
the wheel asset attached to the GitHub Release. Same reproducibility — `uv.lock`
hashes the wheel bytes.

PEP 723:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "ocx-mirror-sdk @ https://github.com/ocx-sh/ocx-mirror-sdk/releases/download/v0.3.0/ocx_mirror_sdk-0.3.0-py3-none-any.whl",
# ]
# ///
```

`pyproject.toml`:

```toml
[project]
dependencies = ["ocx-mirror-sdk"]

[tool.uv.sources]
ocx-mirror-sdk = { url = "https://github.com/ocx-sh/ocx-mirror-sdk/releases/download/v0.3.0/ocx_mirror_sdk-0.3.0-py3-none-any.whl" }
```

## Tag selection

| Source | Tag |
|---|---|
| Latest stable | [`v0.3.0`](https://github.com/ocx-sh/ocx-mirror-sdk/releases/tag/v0.3.0) |
| Bleeding edge (no stability guarantees) | `main` |

Bump only when you've read the release notes — pre-1.0 minor bumps **may**
break import names and exception types.
