---
type: Feature
title: Reusable Agent Workflows
description: Provides copyable Skills for common engineering tasks.
tags: [skills, workflow]
generated: { by: openai-codex/gpt-5, at: 2026-08-21T18:26:11+09:00 }
---

# Included Workflows

The repository ships these generic Skills:

- `implement-feature`
- `investigate-bug`
- `add-test`
- `refactor-safely`
- `update-okf`

# Expected Behavior

Each Skill should make the agent's process explicit enough that a new contributor can predict what context will be read, what changes may be made, and what validation should be reported.

Canonical Skills follow both the upstream Agent Skills format and this repository's Skill authoring profile. Selected example copies are synchronized from the canonical source and routing fixtures cover positive, negative, and overlapping requests.
