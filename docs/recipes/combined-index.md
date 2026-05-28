# Combined index

End-to-end pipeline: fetch → filter → extract → build → emit. Uses
structured assets when present, falls back to URLs scraped from
release-notes prose.

```python title="examples/04_combined_index.py"
--8<-- "04_combined_index.py"
```

Run:

```bash
uv run examples/04_combined_index.py > bun.json
```

## Shape of the pattern

This is the canonical "real" generator. The pieces:

1. **Fetch** — `list_releases(...)`, filtered to stable.
2. **Discriminate** — asset-name regex picks the structured assets we
   want to publish.
3. **Fallback** — if structured assets are absent, `extract_urls` on
   `r.body` recovers any URLs in the release notes.
4. **Build** — `IndexBuilder.add_version(...)` accumulates each
   version's assets.
5. **Emit** — `builder.emit()` writes the `url_index` JSON to stdout.

For error handling around this pattern, see
[`examples/05_error_handling.py`](https://github.com/ocx-sh/ocx-mirror-sdk/blob/main/examples/05_error_handling.py).
