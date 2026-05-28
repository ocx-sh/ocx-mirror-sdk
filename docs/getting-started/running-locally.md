# Running locally

A generator emits JSON to stdout. The `ocx-mirror` Rust binary consumes it
and republishes the referenced assets as OCI artifacts.

## Dry run

Install the binary once:

```bash
curl -sSL https://setup.ocx.sh | sh
ocx install ocx-mirror   # or whichever bootstrap your env uses
```

Then pipe the generator output:

```bash
uv run my_generator.py | ocx-mirror --dry-run --stdin
```

`--dry-run` checks the URLs are reachable and the schema validates,
without publishing anything.

## In CI

A typical GitHub Actions cron job looks like:

```yaml title=".github/workflows/mirror.yml"
on:
  schedule:
    - cron: "17 4 * * *"
  workflow_dispatch:

jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v6
      - name: Generate url_index
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: uv run my_generator.py > url_index.json
      - name: Publish via ocx-mirror
        run: ocx-mirror publish < url_index.json
```

See [recipes › CI cron](../recipes/combined-index.md) for a fully worked
end-to-end pipeline.
