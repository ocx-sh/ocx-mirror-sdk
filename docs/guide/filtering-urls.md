# Filtering URLs

Some upstreams don't attach downloads as GitHub release assets — they
link to artifacts in the release-notes body. `extract_urls` pulls
those out.

## Basic use

```python
from ocx_mirror_sdk import extract_urls

text = "Download [linux](https://example.com/tool.tar.gz) or windows."
extract_urls(text)
# ['https://example.com/tool.tar.gz']
```

Behavior:

- HTTP and HTTPS only.
- Deduplicates while preserving first-occurrence order.
- Strips trailing punctuation (`.`, `,`, `;`, `:`).
- Strips Markdown / HTML delimiters (parentheses, angle brackets, quotes,
  closing brackets).

## With a pattern filter

The optional `pattern=` kwarg is passed to `re.search` against each URL:

```python
extract_urls(text, pattern=r"\.tar\.gz$")
# only URLs ending in .tar.gz
```

## Combining with `Release.body`

Typical recipe:

```python
import re

ASSET_RE = re.compile(r"^bun-(linux|darwin|windows)-(x64|aarch64)\.zip$")

for r in releases:
    structured = {a.name: a.browser_download_url for a in r.assets if ASSET_RE.match(a.name)}
    if structured:
        builder.add_version(r.tag_name, assets=structured)
        continue

    # Fallback: pull URLs out of the release-notes prose
    fallback = {
        url.rsplit("/", 1)[-1]: url
        for url in extract_urls(r.body, pattern=ASSET_RE.pattern)
    }
    if fallback:
        builder.add_version(r.tag_name, assets=fallback)
```

See [`examples/04_combined_index.py`](https://github.com/ocx-sh/ocx-mirror-sdk/blob/main/examples/04_combined_index.py)
for a runnable version.
