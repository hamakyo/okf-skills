---
name: add-test
description: Use when adding or improving tests for existing behavior, regressions, edge cases, or coverage gaps. Follow existing test style and cover normal, error, and boundary cases where relevant. Do not use when behavior is undefined or implementation must change first.
---

# Add Test

## When to use

Use this Skill when:

- Existing behavior needs test coverage.
- A regression needs a failing test.
- Edge cases or error paths need explicit coverage.
- A refactor needs safety tests before code changes.

Do not use this Skill when:

- The expected behavior is unclear.
- The requested work requires implementation before tests can be meaningful.
- The task is primarily documentation or OKF maintenance.

## Inputs

- Target behavior, file, bug, or coverage gap.
- Expected behavior.
- Existing test command or framework, if known.
- Related OKF documents when behavior is domain-specific.

## Required context

Before editing tests, read:

- Existing tests near the target area.
- Test helpers, fixtures, factories, and naming conventions.
- Relevant implementation only enough to understand test boundaries.
- Relevant OKF documents when they define expected behavior.

## Workflow

1. Identify the expected behavior and source of truth.
2. Inspect nearby tests to match style, structure, naming, and helpers.
3. Choose the right test level: unit, integration, end-to-end, or snapshot.
4. Add focused tests for useful cases:
   - Normal path.
   - Error or invalid input path.
   - Boundary values or edge cases.
5. Prefer stable assertions over brittle implementation details.
6. Run the new test directly.
7. Run related test files or suites when risk warrants it.
8. If tests expose a defect, stop and report it unless the user asked to fix it.

## Guardrails

- Do not change production behavior unless explicitly asked.
- Do not rewrite the test framework or large fixtures for a narrow test request.
- Do not add tests that only assert mocks were called unless that is the meaningful contract.
- Do not hide flaky tests by weakening assertions without explanation.
- Do not add secrets, credentials, private URLs, or personal data to fixtures.

## Completion checklist

- [ ] Existing test style was followed.
- [ ] Test scope matches the behavior.
- [ ] Normal, error, and boundary cases were considered.
- [ ] New tests were run directly where possible.
- [ ] Any failing behavior is clearly reported.

## Expected final response

Report:

- What behavior is now covered.
- Test files changed.
- Test commands run and results.
- Any uncovered cases or blockers.
