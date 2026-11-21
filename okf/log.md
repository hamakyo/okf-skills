# OKF Update Log

## 2026-11-22

- **Update**: Added `evals/fixtures/maintenance-app/` fixture repository, `evals/regression-scenarios.yaml`, unintended-change scope checks (`allowed_changed_paths`), and diagnostic failure categories (`routing`, `context`, `execution`, `documentation`).
- **Update**: Added Codex Skill evaluation harness (`evals/codex-scenarios.yaml` and `scripts/eval_codex_skills.py`) with observable assertions for all five canonical Skills and documented `evals/` and `scripts/` boundaries in OKF.
- **Update**: Pointed upstream OKF v0.2 specification links to `GoogleCloudPlatform/open-knowledge-format`.
- **Update**: Documented OKF v0.2 §10 Attested Computations as out of scope for the software-project profile while preserving unknown metadata keys.
- **Update**: Accepted `team:<id>` actor identifiers in `scripts/validate_okf.py` to match upstream v0.2 examples, and updated README source-attribution wording to `sources`.

## 2026-08-21

- **Update**: Declared the bundle as OKF v0.2 and documented the distinction between upstream OKF and the software-project profile.
- **Update**: Separated the upstream Agent Skills format from the repository Skill authoring profile.
- **Update**: Added provenance, trust, lifecycle, validation, example synchronization, and routing-evaluation knowledge.

## 2026-06-16

- **Initialization**: Created the initial OKF bundle for the public template repository.
- **Reference**: Aligned the bundle shape with the Open Knowledge Format draft structure of Markdown concept files, index files, and log files.
