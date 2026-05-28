# Schema

The `url_index` JSON format is owned upstream by the `ocx_mirror` Rust
crate in [`ocx-sh/ocx`](https://github.com/ocx-sh/ocx). This SDK
consumes the JSON Schema and regenerates a Python dataclass module
(`_schema.py`) via `task codegen`.

- **[`url_index` v1](url-index.md)** — field-by-field reference.
- Canonical schema URL: <https://ocx.sh/schemas/url-index/v1.json>.
