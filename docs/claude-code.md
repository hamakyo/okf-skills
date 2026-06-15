# Using OKF Skills With Claude Code

Claude Code can use this repository as a lightweight operating manual for project-aware development.

## Files Claude Code Should Read

- [../CLAUDE.md](../CLAUDE.md): repository-level Claude Code instructions.
- [../README.md](../README.md): public overview and common usage.
- `skills/*/SKILL.md`: reusable source library in this template repository.
- `.claude/skills/*/SKILL.md`: Claude Code project Skills for auto-discovery after copying into your own repository.
- `okf/index.md` and related OKF documents: project knowledge.

## Relationship Between CLAUDE.md and Skills

`CLAUDE.md` describes how Claude Code should operate in the repository:

- Use Skills for task workflow.
- Use OKF for project knowledge.
- Update docs when usage changes.
- Check OKF index and log before editing OKF.

Skills are intentionally tool-neutral enough to be useful in both Codex and Claude Code. Use top-level `skills/` as the source library and `.claude/skills/` inside a Claude Code project.

## Typical Claude Code Prompts

Feature work:

```text
Use the implement-feature skill.
Read CLAUDE.md, README.md, and relevant OKF files first.
Implement the requested behavior, then run the update-okf skill if durable knowledge changed.
```

Bug investigation:

```text
Use the investigate-bug skill.
Reproduce the failure and summarize root cause candidates before editing code.
```

Test work:

```text
Use the add-test skill.
Follow existing test style and cover normal, error, and boundary cases where relevant.
```

## Recommended Repository Setup

For Claude Code auto-discovery, use:

```text
.
├── CLAUDE.md
├── okf/
└── .claude/
    └── skills/
```

See [../examples/claude-code-project/](../examples/claude-code-project/) for a minimal auto-discovery layout.

## Validation Expectations

Ask Claude Code to report:

- What was changed.
- What was tested or inspected.
- Whether OKF was updated or intentionally left unchanged.
- Any remaining manual review items.
