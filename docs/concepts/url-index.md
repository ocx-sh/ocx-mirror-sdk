# The `url_index` format

`url_index` is a small JSON document that maps tool versions to download
URLs. The `ocx-mirror` binary reads it and republishes each URL as an OCI
artifact under a stable registry path.

## Schema ownership

The format is owned upstream by the `ocx_mirror` Rust crate in
[`ocx-sh/ocx`](https://github.com/ocx-sh/ocx). The crate generates the
JSON Schema; the SDK's `_schema.py` is regenerated from that schema via
`task codegen`.

The canonical schema lives at <https://ocx.sh/schemas/url-index/v1.json>.

## Shape

```json
{
  "versions": {
    "0.10.0": {
      "prerelease": false,
      "assets": {
        "shellcheck-v0.10.0.linux.x86_64.tar.xz": "https://github.com/koalaman/shellcheck/releases/download/v0.10.0/shellcheck-v0.10.0.linux.x86_64.tar.xz",
        "shellcheck-v0.10.0.darwin.aarch64.tar.xz": "https://github.com/koalaman/shellcheck/releases/download/v0.10.0/shellcheck-v0.10.0.darwin.aarch64.tar.xz"
      }
    }
  }
}
```

| Field | Meaning |
|---|---|
| `versions` | Map of version-string → version entry. |
| `versions[v].prerelease` | Hint for downstream consumers. The binary may skip prereleases. |
| `versions[v].assets` | Map of asset filename → download URL. The filename becomes the OCI artifact tag. |

Asset filenames are the primary key on the mirror side. Don't rename them
between runs — that changes the OCI artifact identity.

## Versioning

- `/v1.json` is the current schema. Forward-additive: new optional fields
  may appear; existing fields don't change shape or meaning.
- A move to `/v2.json` is a breaking schema change. When upstream cuts
  v2, this SDK ships a new major version.

See [Schema → url_index v1](../schema/url-index.md) for the field-by-field
reference.
