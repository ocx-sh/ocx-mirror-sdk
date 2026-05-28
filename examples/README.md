# Examples

Each script is a fully self-contained PEP 723 generator that you can run
without cloning the repo:

```bash
uv run examples/01_shellcheck_rest.py
```

Or fetch and run in one shot:

```bash
uv run https://raw.githubusercontent.com/ocx-sh/ocx-mirror-sdk/main/examples/01_shellcheck_rest.py
```

| Script | Demonstrates |
|---|---|
| [`01_shellcheck_rest.py`](01_shellcheck_rest.py) | Smallest possible generator — REST backend, no filters, emit JSON |
| [`02_python_build_standalone_graphql.py`](02_python_build_standalone_graphql.py) | GraphQL backend on a big repo, with `FileCache.configure` |
| [`03_extract_urls_notes.py`](03_extract_urls_notes.py) | Pulling URLs out of release-note bodies with `extract_urls` |
| [`04_combined_index.py`](04_combined_index.py) | Full pipeline: fetch → filter → extract → build → emit |
| [`05_error_handling.py`](05_error_handling.py) | Handling the `OcxMirrorError` hierarchy in a generator |

All scripts pin `ocx-mirror-sdk` to a tag. Bump the tag when consuming
a newer release.
