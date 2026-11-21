# Evaluation Fixture Repositories

This directory holds small, self-contained fixture repositories used by end-to-end regression scenarios in [../regression-scenarios.yaml](../regression-scenarios.yaml).

## Layout Conventions

Each fixture repository under `evals/fixtures/<name>/` should stay small enough to copy and execute repeatedly during development and follow a realistic project structure:

```text
evals/fixtures/<name>/
├── AGENTS.md           # Codex repository instructions
├── CLAUDE.md           # Claude Code repository instructions
├── README.md           # Project overview and test command
├── okf/                # Valid OKF v0.3 project knowledge bundle
│   ├── index.md
│   ├── log.md
│   ├── architecture/
│   └── features/
├── src/                # Minimal zero-dependency source modules
└── tests/              # Deterministic stdlib unittest baseline
```

Design rules:

- Do not commit `.agents/skills/` or `.claude/skills/` copies inside fixture directories; `scripts/eval_codex_skills.py` stages canonical Skills from top-level `skills/` into each temporary workspace automatically.
- Keep baseline `okf/` bundles valid under `scripts/validate_okf.py` and baseline unit tests green under `python -m unittest discover -s tests`.
- Include at least one unrelated module (`src/storage.py` in `maintenance-app`) so regression scenarios can detect unintended file or behavior changes outside the requested task scope.
- Never place secrets, credentials, private URLs, or personal data in fixture files.

## Included Fixtures

- [maintenance-app/](maintenance-app/README.md): Minimal multi-module invoice and reporting project used across all five core Skill regression scenarios.
