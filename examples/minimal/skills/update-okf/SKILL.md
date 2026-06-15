---
name: update-okf
description: Use after implementation changes to update OKF from git diff. Capture durable behavior, architecture, domain, data, or playbook changes. Do not use for temporary notes or formatting-only changes.
---

# Update OKF

## When to use

Use after changes that affect durable project knowledge.

## Inputs

- `git diff`
- Existing OKF files
- Current date

## Required context

- `okf/index.md`
- `okf/log.md`
- Changed files

## Workflow

1. Inspect `git diff`.
2. Identify durable knowledge changes.
3. Update existing OKF documents or add new concept documents.
4. Update `okf/index.md` if files were added or moved.
5. Add a dated entry to `okf/log.md`.
6. Check links.

## Guardrails

- Do not document every code edit.
- Do not add secrets, credentials, private URLs, or personal data.
- Do not write speculation as fact.

## Completion checklist

- [ ] Diff was inspected.
- [ ] OKF index was checked.
- [ ] OKF log was updated when OKF changed.
- [ ] Links were checked.

## Expected final response

Summarize OKF files changed, knowledge captured, and validation run.
