---
name: qa-engineer
description: Use when designing test suites, writing tests for the SDK, validating an implementation against the schema/contract, or planning test coverage before implementation. Trigger: /qa-engineer.
user-invocable: true
argument-hint: "module-or-feature-to-test"
triggers:
  - "write tests for"
  - "design test suite"
  - "test coverage plan"
  - "validate against the schema"
---

# QA Engineer

Role: test strategy, writing, and validation for `ocx-mirror-sdk`.

## Workflow

### Contract-First (new feature)

Tests written **before** implementation from the public-API contract:

1. **Read contract** — `.claude/rules/architecture.md` public API table + schema at `schemas/url-index.v1.json`.
2. **Write specification tests** — encode each requirement as a test describing WHAT, not HOW.
3. **Verify failing** — tests must compile + fail with `NotImplementedError` / clear missing-symbol error against stubs.
4. **Validate green** — post-implementation, verify all specification tests pass.

### Post-Implementation (coverage)

Analyse → plan → write → run → cover happy, error, edge cases.

## Test Quality Standards

- **Deterministic** — same result every run, no timing or network assumptions. Mock `github3` and `httpx`.
- **Isolated** — each test uses its own temp dir for `FileCache`; no shared state.
- **Clear** — test name describes behaviour (`test_list_releases_filters_drafts`, not `test_github_2`).
- **Complete** — happy + error + edge cases.
- **Regression test for every bug fix** — bug fix without a regression test gets rejected.

## Relevant Rules

- `.claude/rules/quality-core.md` — universal test quality, DAMP > DRY in tests
- `.claude/rules/quality-python.md` — pytest 3.13+ patterns, `pytest.raises`, type annotations
- `.claude/rules/architecture.md` — public API surface that tests must protect

## Tool Preferences

- **`ocx run -- task test`** — full pytest run.
- **`ocx run -- uv run pytest tests/test_<module>.py -v`** — single-file feedback loop.
- **Mocks**: `unittest.mock.patch` against the module-local cache and login helpers (see existing patterns in `tests/test_github.py`).

## Constraints

- NO flaky tests — fix or remove. No `time.sleep` waits.
- NO network calls from tests — always mock the HTTP client.
- NO shared mutable state between tests — use fresh `tmp_path` per test.
- ALWAYS add a regression test per bug fix.

## Handoff

- To author — for bugs found during testing.
- To `/code-check` — after suite passes, before merge.

$ARGUMENTS
