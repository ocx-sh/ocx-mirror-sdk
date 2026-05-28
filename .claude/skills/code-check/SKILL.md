---
name: code-check
description: Use for code review, quality audits, SOLID/DRY consistency checks, pattern audits, or verifying anti-pattern compliance across the SDK.
user-invocable: true
argument-hint: "scope: all | module | path/to/dir"
triggers:
  - "code quality check"
  - "audit the code"
  - "quality audit"
  - "anti-pattern scan"
  - "solid check"
---

# Codebase Health Auditor

Role: audit `ocx-mirror-sdk` Python code for Clean Code, SOLID, DRY, pattern consistency.

## Workflow

1. **Scope** — confirm what to audit (whole repo, single module, single file).
2. **Audit** — walk the dimensions below.
3. **Report** — prioritised findings with `file:line` refs + remediation.

## Audit Dimensions

- **SOLID** — one responsibility per module/class, narrow interfaces, dependency inversion (e.g. injecting `FileCache` rather than constructing inline).
- **DRY** — knowledge duplication (MUST fix) vs incidental similarity (evaluate). Watch for repeated HTTP retry / token handling logic across `github.py` and `github_graphql.py`.
- **Smells** — long functions, god classes, primitive obsession (raw `dict`s where a `dataclass` would do), feature envy, message chains.
- **Consistency** — error handling, type annotations, naming, import strategy match existing patterns.
- **Architecture freshness** — verify `.claude/rules/architecture.md` module map still matches current code.

## Relevant Rules

- `.claude/rules/quality-core.md` — universal SOLID/DRY/YAGNI, severity tiers, review checklist
- `.claude/rules/quality-python.md` — Python 3.13+ block/warn-tier anti-patterns (bare `except`, mutable defaults, `assert` for validation, missing type annotations, `TaskGroup` over `gather`, modern generics)
- `.claude/rules/architecture.md` — module map, public API stability contract

## Tool Preferences

- **Grep/Glob first** — verify patterns before flagging.
- **`ocx run -- task lint`** — ruff (catches anti-patterns from `quality-python.md` automatically).
- **`ocx run -- task types`** — pyright surfaces type-system smells.

## Output Format

```markdown
## Codebase Health Report

### Executive Summary
**Health Score**: [A/B/C/D/F]
**Critical Issues**: [count]

### Pattern Violations
| Pattern | File:Line | Description | Remediation |

### SOLID Violations
| Principle | File:Line | Description | Remediation |

### Architecture Drift
| Rule File | Stale Reference | Current State |
```

## Constraints

- NO flagging incidental duplication as critical.
- NO recommending public API breakage in a release branch without bumping the major version.
- ALWAYS provide specific `file:line` refs + concrete remediation.

## Handoff

- To author — with specific fixes.
- Suggest opening a separate `refactor:` commit per finding cluster.

$ARGUMENTS
