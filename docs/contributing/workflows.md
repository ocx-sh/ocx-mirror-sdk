# Workflows

| Task | What it does |
|---|---|
| `task verify` | Full gate: format check + lint + types + tests + coverage. **Must pass before commit.** |
| `task format` | Apply `ruff format` |
| `task lint` | `ruff check` |
| `task types` | `pyright` |
| `task test` | `pytest` under `coverage` |
| `task cov:html` | Open `htmlcov/index.html` for uncovered branches |
| `task codegen` | Re-fetch JSON Schema + regenerate `_schema.py` |
| `task docs:serve` | Live-preview the docs site at `localhost:8000` |
| `task docs:build` | Strict build into `site/` |

## Conventional commits

Follow the [Conventional Commits](https://www.conventionalcommits.org/)
shape:

```
feat: add Backend.GRAPHQL routing
fix: handle 429 retries with backoff
refactor: collapse github_types into the github/ package
docs: explain the OcxMirrorError hierarchy
test: cover post_json against MockTransport
ci: pin actions to commit SHAs
```

Pre-1.0: breaking changes can ship as `feat:` or `refactor:` — note the
break in the body. No deprecation shims required (see the project's
`stability` policy).

## Branching

| Branch | Purpose |
|---|---|
| `main` | Stable / released code. Docs deploy from here. |
| `feat/<topic>` | Feature branches. PR target is `main`. |
| Tags `vX.Y.Z` | Release tags; trigger the release workflow. |

## Releasing

1. Bump `version = "X.Y.Z"` in `pyproject.toml`.
2. Commit + tag: `git tag -s vX.Y.Z -m "X.Y.Z"`.
3. Push: `git push --follow-tags`.
4. The release workflow builds the wheel and creates a GitHub Release.
5. Docs auto-deploy on push to `main`.
