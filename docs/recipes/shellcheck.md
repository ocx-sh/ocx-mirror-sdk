# shellcheck (REST)

Smallest end-to-end generator. Fetches every public release of
`koalaman/shellcheck`, drops prereleases and drafts, emits the
`url_index` JSON document.

No `GITHUB_TOKEN` required (REST works anonymously for public repos
within the unauthenticated rate limit).

```python title="examples/01_shellcheck_rest.py"
--8<-- "01_shellcheck_rest.py"
```

Run:

```bash
uv run examples/01_shellcheck_rest.py > shellcheck.json
```

## What to change for your tool

- `("koalaman", "shellcheck")` → your `(owner, repo)`.
- `r.tag_name.lstrip("v")` → whatever version-string mangling your tool
  needs.
- Add `pattern=` filtering, asset-name regexes, etc. as needed.
