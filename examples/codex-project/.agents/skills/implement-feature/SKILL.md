---
name: implement-feature
description: Use when adding a new feature or changing existing behavior in a codebase. Read OKF before implementation and prefer the smallest coherent change. Do not use for pure bug triage, test-only work, or behavior-preserving refactors.
---

# Implement Feature

## When to use

Use this Skill when the task requires:

- Adding a new user-facing or developer-facing capability.
- Changing existing behavior.
- Extending an integration, workflow, UI, API, or data flow.
- Implementing a documented requirement from OKF, an issue, or a user request.

Do not use this Skill for:

- Investigating an unclear bug before root cause is known.
- Adding tests without implementation changes.
- Refactoring that should preserve behavior.
- Updating OKF after code has already changed.

## Inputs

- User request or issue description.
- Target repository and branch context.
- Relevant OKF documents, if present.
- Expected validation command or test scope, if known.

## Required context

Before editing, read:

- `README.md`
- `AGENTS.md` or `CLAUDE.md`, depending on the tool in use
- `okf/index.md`
- `okf/log.md`
- Relevant OKF documents under `okf/architecture/`, `okf/domain/`, `okf/data/`, `okf/features/`, or `okf/playbooks/`
- Existing code and tests around the target behavior

## Workflow

1. Restate the requested behavior in concrete terms.
2. Identify relevant OKF knowledge and note any gaps or conflicts.
3. Inspect the existing implementation path before proposing changes.
4. Choose the smallest coherent implementation approach that matches local patterns.
5. Make focused code changes.
6. Add or update tests when behavior changes.
7. Run the narrowest useful verification first, then broader checks when risk warrants it.
8. If durable behavior, architecture, data, domain, or playbook knowledge changed, run or recommend the `update-okf` Skill.

## Guardrails

- Do not skip OKF review when an `okf/` directory exists.
- Do not invent architecture that conflicts with OKF or existing code.
- Do not broaden the scope into unrelated cleanup.
- Do not silently change public APIs, schemas, migrations, or user-visible behavior beyond the request.
- Do not add secrets, credentials, private URLs, or personal data.
- If requirements are ambiguous and local context cannot resolve them, state the assumption before implementing.

## Completion checklist

- [ ] Relevant README, instructions, OKF, code, and tests were read.
- [ ] Implementation follows existing patterns.
- [ ] Tests were added or the reason for not adding tests is clear.
- [ ] Verification was run or the blocker is documented.
- [ ] OKF update need was checked.
- [ ] Final diff is focused on the requested behavior.

## Expected final response

Report:

- What behavior was implemented.
- Key files changed.
- Tests or checks run.
- Whether OKF was updated or why it was not needed.
- Any remaining risks or follow-up work.
