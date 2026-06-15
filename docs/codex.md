# Using OKF Skills With Codex

Codex can use this repository as a set of local instructions, reusable Skills, and project knowledge templates.

## Files Codex Should Read

- [../AGENTS.md](../AGENTS.md): repository-level Codex instructions.
- [../README.md](../README.md): public overview and common usage.
- `skills/*/SKILL.md`: reusable source library in this template repository.
- `.agents/skills/*/SKILL.md`: Codex project Skills for auto-discovery after copying into your own repository.
- `okf/index.md` and related OKF documents: project knowledge.

## Relationship Between AGENTS.md and Skills

`AGENTS.md` sets repository-wide behavior for Codex:

- Read README and relevant docs before work.
- Keep Skills and docs synchronized.
- Check OKF index and log before OKF edits.
- Keep diffs small and validation explicit.

Skills provide narrower workflows. For example, `implement-feature` tells Codex how to approach feature work, while `update-okf` tells Codex how to reflect implementation changes back into OKF. Use top-level `skills/` as the source library and `.agents/skills/` inside a Codex project.

## Typical Codex Prompts

Feature work:

```text
Use the implement-feature skill.
Read AGENTS.md, README.md, docs/okf.md, and relevant OKF files first.
Implement account deletion with the smallest reasonable diff.
Run available tests and update OKF if behavior changes.
```

Bug investigation:

```text
Use the investigate-bug skill.
Do not fix immediately.
First reproduce the issue, identify likely causes, describe impact, and propose the smallest fix.
```

OKF update:

```text
Use the update-okf skill.
Inspect git diff and update OKF only for durable behavior, architecture, domain, data, or playbook changes.
```

## Recommended Repository Setup

In your project repository:

```text
.
├── AGENTS.md
├── CLAUDE.md
├── okf/
└── .agents/
    └── skills/
```

Keep Codex-specific instructions in `AGENTS.md`. Put Codex-discovered project Skills under `.agents/skills/`. Keep durable facts in OKF.

See [../examples/codex-project/](../examples/codex-project/) for a minimal auto-discovery layout.

## Validation Expectations

Ask Codex to include validation in the final response:

- Tests or checks run.
- Files inspected when no automated tests exist.
- Any checks that could not be run.
- Remaining human review items.
