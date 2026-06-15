---
name: refactor-safely
description: Use when improving internal structure, readability, duplication, or maintainability without changing behavior. Keep diffs small and preserve public APIs, schemas, and user-visible behavior. Do not use when behavior, contracts, or migrations must change.
---

# Refactor Safely

## When to use

Use this Skill when:

- Reducing duplication.
- Improving naming or structure.
- Extracting helpers or simplifying control flow.
- Preparing code for a later change while preserving behavior.

Do not use this Skill when:

- User-visible behavior must change.
- Public APIs, schemas, migrations, or data contracts must change.
- The code is not covered enough to safely refactor and no validation plan exists.

## Inputs

- Target files, modules, or code smell.
- Reason for the refactor.
- Available tests or validation commands.
- Relevant OKF docs when architecture or contracts are documented.

## Required context

Before editing, read:

- Existing code around the target area.
- Tests that cover the behavior.
- Relevant OKF architecture, data, or feature documents.
- Public API, schema, or integration boundaries.

## Workflow

1. Define the behavior that must remain unchanged.
2. Identify public APIs, schemas, data contracts, and external behavior that must not move.
3. Run or identify baseline tests when available.
4. Make the smallest meaningful structural change.
5. Avoid mixing formatting-only changes with logic movement unless the repository already does so.
6. Run targeted tests.
7. Compare the diff to confirm behavior was preserved.
8. If a behavior change becomes necessary, stop and switch to `implement-feature` or ask for confirmation.

## Guardrails

- Do not change behavior intentionally or accidentally.
- Do not change public APIs, schemas, migrations, serialized formats, or user-visible text without explicit approval.
- Do not perform broad cleanup outside the requested area.
- Do not introduce new dependencies unless explicitly justified.
- Do not remove tests to simplify the refactor.
- Do not update OKF unless architecture, boundaries, or maintainership knowledge changed.

## Completion checklist

- [ ] Behavior to preserve was identified.
- [ ] Public APIs and schemas were checked.
- [ ] Diff is small and scoped.
- [ ] Tests or validation were run.
- [ ] Any residual risk is stated.

## Expected final response

Report:

- What was refactored.
- Why behavior should be unchanged.
- Files changed.
- Tests or checks run.
- Any risks or follow-up opportunities.
