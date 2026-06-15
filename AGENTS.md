# Codex Instructions

This repository is a public template collection for Codex and Claude Code users who want reusable Skills and OKF project knowledge.

## Before You Work

- Read [README.md](README.md) first.
- Read the relevant document under [docs/](docs/) for the requested task.
- If the task uses a Skill, read the matching `skills/*/SKILL.md` before making changes.
- If the task touches OKF, read [okf/index.md](okf/index.md) and [okf/log.md](okf/log.md) before editing.

## Skill Rules

- Keep reusable workflow instructions in `skills/*/SKILL.md`.
- Keep project facts, architecture, domain concepts, data contracts, and playbooks in `okf/`.
- When changing a Skill, update related docs and examples if the usage or behavior changes.
- Use the Skill frontmatter description to make trigger conditions explicit.

## OKF Rules

- Treat OKF as project knowledge, not as a task checklist.
- Reserved files are `index.md` and `log.md`.
- Non-reserved OKF Markdown concept files should include YAML frontmatter with at least `type`.
- When changing OKF structure, confirm that `okf/index.md` and `okf/log.md` still describe the bundle accurately.

## Editing Rules

- Preserve the existing structure unless a small, clear improvement is needed.
- Prefer small, reviewable diffs.
- Use relative Markdown links inside this repository.
- Do not add secrets, API keys, tokens, private URLs, or personal data.
- Do not mix Codex-only guidance into `CLAUDE.md` unless it also applies to Claude Code.
- Do not mix Claude Code-only guidance into `AGENTS.md` unless it also applies to Codex.

## Final Response

In the final response, include:

- What changed.
- Which files were added or updated.
- What validation was run.
- Any remaining release or human-review tasks.
