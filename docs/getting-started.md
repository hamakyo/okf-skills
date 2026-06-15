# Getting Started

This guide shows how to copy the template into another repository and make the first useful edits.

## 1. Copy the Minimal Template

From this repository:

```sh
cp -R examples/minimal/* /path/to/your-repo/
```

For a fuller setup, copy these directories and files instead:

```sh
cp -R AGENTS.md CLAUDE.md okf skills /path/to/your-repo/
```

## 2. Describe Your Project

Open `okf/index.md` in your target repository and replace the placeholder text with:

- The purpose of the project.
- The main users or systems.
- The most important architecture, domain, data, feature, and playbook documents.
- Links to existing docs if they are public or safe to share with agents.

## 3. Add One Useful OKF Document

Start with one document that prevents common mistakes. Good first choices:

- `okf/architecture/overview.md`
- `okf/domain/core-concepts.md`
- `okf/features/main-workflow.md`
- `okf/playbooks/release.md`

Non-reserved OKF concept documents should include frontmatter:

```md
---
type: Architecture
title: System Overview
description: Describes the main runtime components and ownership boundaries.
tags: [architecture]
---
```

## 4. Choose a Skill

Use the Skill that matches the task:

- Feature or behavior change: `implement-feature`
- Unknown defect: `investigate-bug`
- Test coverage: `add-test`
- Behavior-preserving cleanup: `refactor-safely`
- Documentation of implementation changes: `update-okf`

## 5. Ask the Agent Clearly

Example prompt:

```text
Use the implement-feature skill.
Read AGENTS.md, README.md, and relevant OKF files first.
Add CSV export to the reports page.
After implementation, use update-okf if behavior or architecture changed.
```

## 6. Review the Result

Before merging generated changes:

- Check the diff for unintended behavior changes.
- Run tests or the closest available verification.
- Confirm OKF changes describe durable knowledge, not temporary task notes.
- Confirm no secrets, credentials, private URLs, or personal data were added.

## Next Steps

- Read [Codex usage](codex.md) if you use Codex.
- Read [Claude Code usage](claude-code.md) if you use Claude Code.
- Read [OKF](okf.md) to understand the knowledge model.
- Read [Customization](customization.md) before adding project-specific Skills.
