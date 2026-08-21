---
type: Data Contract
title: Skill Authoring Profile
description: Distinguishes the upstream Agent Skills format from this repository's stricter reusable Skill authoring profile.
tags: [skills, markdown]
generated: { by: openai-codex/gpt-5, at: 2026-08-21T18:26:11+09:00 }
---

# Upstream Agent Skills Standard

A portable Skill is a directory containing a `SKILL.md` file. The file starts with YAML frontmatter and continues with Markdown instructions.

The upstream standard requires:

```text
skills/<skill-name>/SKILL.md
```

```yaml
---
name: skill-name
description: Clear trigger condition for Codex or Claude Code. Explain when to use and when not to use this skill.
---
```

- `name` is 1-64 lowercase letters, numbers, or hyphens; has no leading, trailing, or consecutive hyphens; and matches the parent directory.
- `description` is non-empty, at most 1024 characters, and explains what the Skill does and when to use it.
- The Markdown body has no required upstream section names.
- `scripts/`, `references/`, and `assets/` are optional progressive-disclosure resources.

# OKF Skills Repository Profile

Canonical Skills under `skills/` follow a stricter authoring profile so contributors and agents can predict the workflow shape. This profile is not an upstream Agent Skills requirement.

Use these body sections in this order:

- `# Skill Title`
- `## When to use`
- `## Inputs`
- `## Required context`
- `## Workflow`
- `## Guardrails`
- `## Completion checklist`
- `## Expected final response`

Descriptions should front-load the main trigger and state important negative boundaries so automatic routing can distinguish neighboring Skills.

# Canonical Source And Copies

Top-level `skills/` is the canonical source. Example copies are selected through the example-copy manifest and must match the canonical file byte for byte.
