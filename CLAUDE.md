# Claude Code Instructions

This repository is a public template collection for Claude Code and Codex users who want reusable Skills and OKF project knowledge.

## Repository Purpose

Use this repository as a copyable starter kit for:

- Agent-readable project knowledge in `okf/`.
- Repeatable task workflows in `skills/`.
- Claude Code guidance in this file.
- Codex guidance in `AGENTS.md`.

## Before Making Changes

- Read [README.md](README.md).
- Read relevant docs under [docs/](docs/).
- For Skill changes, read the target `skills/*/SKILL.md` and update docs when usage changes.
- For OKF changes, read [okf/index.md](okf/index.md) and [okf/log.md](okf/log.md).

## Skill Usage Policy

- Use Skills for task process, not project facts.
- Choose the narrowest Skill that matches the work.
- If a task changes behavior, architecture, data shape, or an operating playbook, consider running `update-okf` after the implementation.
- Keep Skill descriptions precise enough for automatic or manual selection.

## OKF Usage Policy

- OKF is the project knowledge layer.
- Store architecture, domain concepts, data notes, feature behavior, and playbooks under `okf/`.
- Keep `okf/index.md` useful as the map of the knowledge bundle.
- Keep `okf/log.md` updated when meaningful knowledge changes are made.

## Documentation Update Rules

- Update README only for top-level usage or positioning changes.
- Update docs when setup, usage, customization, or OKF rules change.
- Update examples when a change would otherwise make the example misleading.
- Avoid duplicating long explanations across README and docs.

## Change Checklist

- [ ] README and relevant docs were checked.
- [ ] Related Skill files were updated when workflow changed.
- [ ] OKF index and log were checked when OKF changed.
- [ ] Links are relative and valid.
- [ ] No secrets, credentials, private URLs, or personal data were added.
- [ ] The final response explains validation performed.
