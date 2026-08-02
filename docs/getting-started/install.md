# Install

Published on [PyPI](https://pypi.org/project/ocx-mirror-sdk/) as
`ocx-mirror-sdk`.

Pre-1.0 semver: minor bumps **may** break import names and exception types.
`~=X.Y.Z` pins the patch series; bump the minor deliberately after reading
the [changelog](../changelog.md).

## PEP 723 (recommended for one-file generators)

A generator script is a single file. [PEP 723](https://peps.python.org/pep-0723/)
inline-metadata lets you declare dependencies inside the script itself —
`uv` reads the block and provisions an ephemeral environment.

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["ocx-mirror-sdk~=0.5.2"]
# ///

from ocx_mirror_sdk import IndexBuilder, github
```

Run it directly:

```bash
uv run my_generator.py
```

## `pyproject.toml` (multi-file projects)

```bash
uv add ocx-mirror-sdk
```

`uv.lock` pins the exact version and hashes — `uv sync --frozen` is
reproducible in CI.

## Git tag / bleeding edge (alternative)

To track `main` (no stability guarantees), or pin a tag before it reaches
PyPI:

```toml
[project]
dependencies = ["ocx-mirror-sdk"]

[tool.uv.sources]
ocx-mirror-sdk = { git = "https://github.com/ocx-sh/ocx-mirror-sdk", branch = "main" }
```

Swap `branch = "main"` for `tag = "vX.Y.Z"` to pin a tag. Wheel + sdist are
also attached to every [GitHub Release](https://github.com/ocx-sh/ocx-mirror-sdk/releases)
for environments that install from release assets rather than an index.
