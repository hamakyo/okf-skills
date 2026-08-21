# Skill Routing Evaluations

`skill-routing.yaml` is a portable prompt fixture for checking whether Skill descriptions route realistic requests to the intended workflow.

## Deterministic Validation

`python scripts/validate_skills.py` checks that:

- Every case has a unique identifier, category, prompt, expected Skill, and rejection list.
- Every referenced Skill exists in the canonical `skills/` directory.
- Every canonical Skill has positive and negative coverage.
- Overlap cases distinguish neighboring Skills.

This structural check runs in CI.

## Semantic Smoke Test

Before a release that changes Skill descriptions:

1. Present only the canonical Skill names and descriptions to each supported host.
2. Run every prompt from `skill-routing.yaml` in a clean task.
3. Confirm the selected Skill matches `expect`, or that no Skill is selected when `expect` is null.
4. Confirm none of the Skills in `reject` is selected.
5. Record host and version details in the pull request or release review notes.

Semantic routing depends on the host and model, so it is a release smoke test rather than a deterministic CI gate.
