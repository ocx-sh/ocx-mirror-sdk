# Your first generator

A complete generator is ~25 lines. Save this as `shellcheck.py`:

```python title="examples/01_shellcheck_rest.py"
--8<-- "01_shellcheck_rest.py"
```

Run it:

```bash
uv run shellcheck.py > shellcheck.json
```

Output is a `url_index` JSON document — a map of versions to asset URLs,
validated against the [v1 JSON Schema](https://ocx.sh/schemas/url-index/v1.json).

Next: hand it to the `ocx-mirror` binary for a [dry run](running-locally.md).
