---
type: Data Contract
title: Skill Markdown Format
description: The required shape for reusable Skill files in this repository.
tags: [skills, markdown]
---

# Required File

Every Skill lives at:

```text
skills/<skill-name>/SKILL.md
```

# Frontmatter

Each `SKILL.md` starts with YAML frontmatter:

```yaml
---
name: skill-name
description: Clear trigger condition for Codex or Claude Code. Explain when to use and when not to use this skill.
---
```

# Body Sections

Use these sections:

- `# Skill Title`
- `## When to use`
- `## Inputs`
- `## Required context`
- `## Workflow`
- `## Guardrails`
- `## Completion checklist`
- `## Expected final response`
