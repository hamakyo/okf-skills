# OKF In This Repository

OKF is the project knowledge layer. Skills are the work procedures. Keeping those responsibilities separate makes the repository easier for both humans and agents to maintain.

## Source Model

This repository follows the spirit of the Open Knowledge Format draft from GoogleCloudPlatform's knowledge-catalog project: a knowledge bundle is a directory tree of Markdown files, with reserved `index.md` and `log.md` files, and concept documents that can use YAML frontmatter.

Reference: [Open Knowledge Format SPEC](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)

## OKF Answers "What Is True?"

Use OKF for durable knowledge:

- Architecture decisions and boundaries.
- Domain concepts and vocabulary.
- Data structures, schemas, and contracts.
- Feature behavior and product rules.
- Playbooks for operations, release, incident response, or recurring work.

Do not use OKF for:

- One-off task plans.
- Temporary debugging notes.
- Agent behavior rules.
- Tool-specific prompt instructions.

## Skills Answer "How To Work"

Use Skills for repeatable workflows:

- How to implement a feature.
- How to investigate a bug.
- How to add tests.
- How to refactor safely.
- How to update OKF after code changes.

If a statement describes project truth, put it in OKF. If it describes agent process, put it in a Skill.

## Bundle Structure

The default bundle is:

```text
okf/
├── index.md
├── log.md
├── architecture/
├── domain/
├── data/
├── features/
└── playbooks/
```

Use the directories that matter for your project. Empty categories can be removed.

## Frontmatter

Reserved files:

- `index.md`: directory map for humans and agents.
- `log.md`: chronological update history.

Concept documents should include frontmatter:

```md
---
type: Feature
title: Account Deletion
description: Rules and flow for deleting an account.
tags: [accounts, privacy]
---
```

Recommended fields:

- `type`: required for concept documents.
- `title`: display name.
- `description`: one-sentence summary.
- `resource`: canonical URI when the concept describes an external asset.
- `tags`: short categorization list.
- `timestamp`: ISO 8601 timestamp for meaningful updates.

## Linking

Prefer relative links within your repository:

```md
See System Overview at `okf/architecture/overview.md`.
```

Agents should tolerate broken links during draft work, but public templates should avoid broken links.

## Updating OKF

Update OKF when a change affects durable knowledge:

- User-visible behavior.
- Architecture or ownership boundaries.
- Data models, schemas, or contracts.
- Domain terminology.
- Operational playbooks.

Use the [update-okf Skill](../skills/update-okf/SKILL.md) after implementation changes.
