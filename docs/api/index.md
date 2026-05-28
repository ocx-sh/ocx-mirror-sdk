# API reference

Auto-generated from docstrings via
[mkdocstrings](https://mkdocstrings.github.io/python/).

## Public symbols

| Symbol | Module | Page |
|---|---|---|
| `IndexBuilder` | `ocx_mirror_sdk.index` | [IndexBuilder](index-builder.md) |
| `Asset`, `Release` | `ocx_mirror_sdk.releases` | [Releases](releases.md) |
| `list_releases`, `Backend` | `ocx_mirror_sdk.github` | [Releases](releases.md) |
| `FileCache`, `configure` | `ocx_mirror_sdk.cache` | [Cache](cache.md) |
| `fetch_json`, `fetch_text`, `post_json` | `ocx_mirror_sdk.http` | [HTTP](http.md) |
| `extract_urls` | `ocx_mirror_sdk.text` | [Text](text.md) |
| `OcxMirrorError` + subclasses | `ocx_mirror_sdk.errors` | [Errors](errors.md) |

## Conventions

- All names exported from `ocx_mirror_sdk` are public; anything under
  `ocx_mirror_sdk.<module>._foo` is package-private.
- Docstrings follow [Google style](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods).
- `Raises:` sections list every exception the function may raise from
  the SDK's hierarchy; lower-layer exceptions are wrapped (preserved on
  `__cause__`).
