# URLs from release notes

Some projects link downloads in their release-notes prose instead of
attaching them as GitHub release assets. `extract_urls` recovers them.

```python title="examples/03_extract_urls_notes.py"
--8<-- "03_extract_urls_notes.py"
```

Run:

```bash
uv run examples/03_extract_urls_notes.py
```

## Tips

- The `pattern=` kwarg is a `re.search` pattern — anchor with `^` / `$`
  as you would in any Python regex.
- URLs are deduplicated in first-occurrence order, so the script's
  filename-derivation logic stays deterministic.
