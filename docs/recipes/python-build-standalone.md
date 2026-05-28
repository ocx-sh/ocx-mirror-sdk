# python-build-standalone (GraphQL)

`astral-sh/python-build-standalone` publishes ~735 assets per release.
The REST API returns 504 — switch to GraphQL. Also redirect the cache
root so CI keeps its caches local.

Requires `GITHUB_TOKEN`.

```python title="examples/02_python_build_standalone_graphql.py"
--8<-- "02_python_build_standalone_graphql.py"
```

Run:

```bash
GITHUB_TOKEN=ghp_... uv run examples/02_python_build_standalone_graphql.py > pbs.json
```

## Why GraphQL helps here

GraphQL lets the SDK paginate assets within each release independently,
so no single response is large enough to time out. Asset lists are
cached for 7 days because assets are immutable once published.

See [Guide → Fetching releases](../guide/fetching-releases.md) for the
full REST-vs-GraphQL decision table.
