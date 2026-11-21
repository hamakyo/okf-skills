# Changelog

All notable changes to this project will be documented in this file.

This project follows a lightweight changelog format suitable for template repositories.

## Unreleased

## [0.3.0] - 2026-11-22

- Migrated upstream OKF references, validators, bundles, fixtures, docs, and `update-okf` Skill from deprecated `GoogleCloudPlatform/open-knowledge-format` (OKF v0.2) to official `open-knowledge-format/open-knowledge-format` (OKF v0.3), supporting §8.1 root bundle metadata, RFC 3339 `date-time` and `full-date` timestamps, generalized `<scheme>:<id>` actors, §5.3 current `verified` semantics, §5.4 `superseded_by`, `x-` extensions, and §3.2 dot-path exclusion (#8, #13).
- Expanded Skill routing fixtures (`evals/skill-routing.yaml`) with positive, negative, and ambiguous categories and added deterministic accuracy scoring (`scripts/score_skill_routing.py`) (#9).
- Added automated Codex Skill evaluation harness (`scripts/eval_codex_skills.py` and `evals/codex-scenarios.yaml`) covering all five canonical Skills with deterministic validation and observable assertions (#10).
- Added self-contained `evals/fixtures/maintenance-app/` fixture repository, end-to-end regression scenarios (`evals/regression-scenarios.yaml`), unintended-change scope checks (`allowed_changed_paths`), and diagnostic failure categories (`routing`, `context`, `execution`, `documentation`) (#11).
- Documented adapter and plugin packaging tradeoffs (`docs/packaging.md`) and added deterministically synchronized optional host adapters (`adapters/codex/` and `adapters/claude-code/`) via `scripts/sync_adapters.py` while keeping copy-based installation primary (#12).
- Added Japanese README (`README.ja.md`) and refreshed the project roadmap toward v1.0.

## [0.2.0] - 2026-08-21

- Upgraded the repository and minimal bundle to the OKF v0.2 software-project profile (#2).
- Distinguished upstream Agent Skills requirements from the repository Skill authoring profile.
- Added deterministic OKF and Skill validation, example Skill synchronization, and initial routing fixtures.

## [0.1.1] - 2026-06-16

- Added Markdown link validation (`scripts/validate_markdown.py`), CI workflow, and tool usage matrix (`docs/usage-matrix.md`).

## [0.1.0] - 2026-06-16

- Initial public template structure for OKF, Codex Skills, and Claude Code guidance.
- Added reusable Skills for feature implementation, bug investigation, test additions, safe refactoring, and OKF updates.
- Added documentation for getting started, Codex, Claude Code, OKF, and customization, plus minimal and host-specific examples.
