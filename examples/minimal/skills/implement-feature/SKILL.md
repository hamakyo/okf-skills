---
name: implement-feature
description: Use when adding or changing project behavior. Read OKF first and keep the diff focused. Do not use for pure investigation, test-only work, or behavior-preserving refactors.
---

# Implement Feature

## When to use

Use for feature additions or behavior changes.

## Inputs

- User request or issue.
- Relevant OKF documents.
- Existing code and tests.

## Required context

- `okf/index.md`
- `okf/log.md`
- Relevant files under `okf/`
- Code and tests around the target behavior

## Workflow

1. Read OKF before editing.
2. Identify the smallest implementation path.
3. Follow existing code patterns.
4. Add or update tests when behavior changes.
5. Run relevant validation.
6. Use `update-okf` if durable knowledge changed.

## Guardrails

- Do not invent behavior that conflicts with OKF.
- Do not broaden the scope into unrelated cleanup.
- Do not change public APIs or schemas without explicit approval.

## Completion checklist

- [ ] OKF was read.
- [ ] Change is focused.
- [ ] Tests or validation were run.
- [ ] OKF update need was checked.

## Expected final response

Summarize behavior implemented, files changed, validation run, and whether OKF was updated.
