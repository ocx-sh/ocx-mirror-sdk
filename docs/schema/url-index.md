# `url_index` v1

Canonical JSON Schema: <https://ocx.sh/schemas/url-index/v1.json>.

## Example

```json
{
  "versions": {
    "0.10.0": {
      "prerelease": false,
      "assets": {
        "shellcheck-v0.10.0.linux.x86_64.tar.xz": "https://github.com/koalaman/shellcheck/releases/download/v0.10.0/shellcheck-v0.10.0.linux.x86_64.tar.xz"
      }
    }
  }
}
```

## Fields

### Top level

| Field | Type | Required | Notes |
|---|---|---|---|
| `versions` | object | yes | Map of version-string → version entry. Keys are arbitrary strings; consumers compare them lexicographically or with semver, not as numbers. |

### Version entry

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `prerelease` | bool | no | `false` | Hint for downstream consumers. The `ocx-mirror` binary may skip prereleases by default. |
| `assets` | object | yes | — | Map of asset filename → download URL. The filename becomes the OCI artifact tag — don't rename between runs. |

## SDK round-trip

`IndexBuilder.emit()` produces JSON that validates against this schema.
The test suite verifies the round trip:

```bash
ocx run -- task test  # tests/test_schema.py validates IndexBuilder output
```

## Versioning

- **v1** (current): forward-additive. New optional fields may appear.
- **v2**: when the upstream Rust crate cuts v2, this SDK ships a new
  major version. Within v1, generators remain compatible.
