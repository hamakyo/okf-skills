---
name: investigate-bug
description: Use when a defect, regression, failing test, incident, or unclear failure needs investigation. Reproduce and analyze before fixing. Do not use when the exact root cause and approved fix are already known.
---

# Investigate Bug

## When to use

Use this Skill when:

- A failure needs reproduction.
- The root cause is unknown.
- A regression or incident may affect multiple areas.
- The user asks for diagnosis, triage, or investigation.

Do not use this Skill when:

- The task is a straightforward implementation request.
- The exact fix is already known and only needs to be applied.
- The work is only adding test coverage for known behavior.

## Inputs

- Bug report, failing command, stack trace, screenshot, or reproduction notes.
- Expected behavior and actual behavior.
- Environment details if available.
- Relevant OKF documents if the behavior is domain-specific.

## Required context

Before editing code, read:

- `README.md`
- `AGENTS.md` or `CLAUDE.md`, depending on the tool in use
- `okf/index.md` and relevant OKF documents when the bug relates to documented behavior
- Existing tests for the affected area
- Recent changes or `git diff` when the bug may be introduced locally

## Workflow

1. Capture the reported symptom.
2. Identify or create the smallest reproduction path.
3. Run the failing test, command, or scenario when possible.
4. Compare actual behavior with documented or expected behavior.
5. List plausible root causes with evidence.
6. Inspect the narrowest relevant code paths.
7. Determine impact scope and whether related behavior may also be affected.
8. Propose the smallest fix and the test that should prevent recurrence.
9. Only implement the fix if the user requested implementation or the task clearly expects it.

## Guardrails

- Do not jump directly to a fix before reproduction or evidence.
- Do not rewrite broad areas while investigating.
- Do not ignore OKF if it defines the expected behavior.
- Do not treat speculation as confirmed root cause.
- Do not remove failing tests to make the suite pass.
- Do not add secrets, credentials, private URLs, or personal data to logs or docs.

## Completion checklist

- [ ] Symptom is described.
- [ ] Reproduction was attempted and result is documented.
- [ ] Expected behavior source is identified or uncertainty is stated.
- [ ] Root cause candidates are ranked by evidence.
- [ ] Impact scope is summarized.
- [ ] Minimal fix and test plan are proposed or implemented.

## Expected final response

Report:

- Reproduction steps and result.
- Most likely root cause.
- Impact scope.
- Minimal fix plan or implemented fix.
- Tests or checks run.
- Remaining unknowns.
