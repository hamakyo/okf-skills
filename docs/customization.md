# Customization

This repository is designed to be copied and trimmed. Keep only the parts that help your project.

## Customizing OKF

Start with `okf/index.md` and describe your project in concrete terms:

- What the system does.
- Who uses it.
- Where architecture, domain, data, feature, and playbook knowledge lives.
- Which documents are authoritative.

Then add project-specific documents. Examples:

```text
okf/architecture/runtime.md
okf/domain/billing.md
okf/data/customer-profile.md
okf/features/onboarding.md
okf/playbooks/release.md
```

Remove categories you do not use.

The category layout is the repository's [Software Project Profile](okf-software-project-profile.md), not a core OKF requirement. Keep `okf_version: "0.2"` in the bundle-root index and keep non-reserved concept documents conformant with [OKF v0.2](okf.md).

## Customizing Skills

Skills should remain workflow-focused. Good additions:

- Required context to inspect before work.
- Project-specific guardrails.
- Expected validation commands.
- Final response requirements.

Avoid putting changing project facts directly in Skills. Link to OKF instead.

## Adding a New Skill

Create:

```text
skills/<skill-name>/SKILL.md
```

The top-level `skills/` directory is the reusable source library. In an actual project, copy selected Skills under `.agents/skills/` for Codex or `.claude/skills/` for Claude Code.

The upstream Agent Skills standard requires a `SKILL.md` file with valid `name` and `description` metadata. Canonical Skills in this repository additionally use this authoring profile:

```md
---
name: skill-name
description: Clear trigger condition. Include when to use and when not to use it.
---

# Skill Title

## When to use

## Inputs

## Required context

## Workflow

## Guardrails

## Completion checklist

## Expected final response
```

Then update:

- [../README.md](../README.md) Skill catalog.
- Relevant docs under `docs/`.
- Examples if the new Skill changes recommended setup.

Add the Skill to `examples/skill-copies.yaml` only when it should appear in an example layout, then run `python scripts/sync_examples.py`.

## Customizing AGENTS.md

Add Codex-specific instructions such as:

- Test commands.
- Build commands.
- Branch or commit rules.
- Project-specific verification steps.
- Paths Codex should inspect before editing.

Keep reusable task workflow in Skills, not `AGENTS.md`.

## Customizing CLAUDE.md

Add Claude Code-specific instructions such as:

- How Claude Code should select Skills.
- Project validation expectations.
- Claude-specific workflow preferences.

Keep Claude Code setup separate from Codex-specific setup so users can adopt either tool independently.

## Common Customization Patterns

Add a release playbook:

```text
okf/playbooks/release.md
```

Add a project-specific testing Skill:

```text
.agents/skills/test-database-migration/SKILL.md
.claude/skills/test-database-migration/SKILL.md
```

Add architecture knowledge:

```text
okf/architecture/service-boundaries.md
```

## Review Before Publishing

- README links work.
- `AGENTS.md` and `CLAUDE.md` link to README or docs.
- Every Skill has `SKILL.md`.
- OKF concept documents have frontmatter.
- No secrets, credentials, private URLs, or personal data are present.
