# Task Completion Checklist

Run before declaring any code task done.

## 1. Code regenerated (only if schema-affecting)

If you touched anything that changes `schemas/url-index.v1.json` (rare; upstream lives in `ocx-sh/ocx`) or pulled a newer schema:

```
task codegen
```

Then commit the regenerated `_schema.py` together with the schema bump.

## 2. Gate

```
task verify
```

Must exit 0. Breakdown if you want to iterate faster:

```
task format        # apply formatter
task lint          # ruff check
task types         # pyright
task test          # pytest
```

`verify` itself runs `format:check` (not `format`) — apply formatter locally before `verify` if needed.

## 3. Public API hygiene

If you added/removed a public symbol:

- Update `src/ocx_mirror_sdk/__init__.py` (`__all__` + re-export).
- Update `CLAUDE.md` "Public API" table if user-facing.
- Update `.claude/rules/architecture.md` "Public API contract" if the stability shape changed.

## 4. Commit

- Conventional Commits with scope (`feat(mirror-sdk): …`, `fix(cache): …`, `refactor(github): …`, `chore: …`).
- Body explains the why.
- Never push to `main`; open a PR.
- See `.claude/rules/workflow-git.md` for full commit rules.

## 5. Workflow-specific gates

Pick the workflow that applies and run its Phase checklist:

- Bug fix: `.claude/rules/workflow-bugfix.md` — failing regression test BEFORE fix.
- Feature: `.claude/rules/workflow-feature.md`.
- Refactor: `.claude/rules/workflow-refactor.md` — tests pass unchanged, one named transformation per commit.

Skipping `verify` is the most common failure mode.
