---
type: Feature
title: Reusable Agent Workflows
description: Provides copyable Skills for common engineering tasks.
tags: [skills, workflow]
generated: { by: google-antigravity/agent, at: 2026-11-22T05:40:00+09:00 }
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

Canonical Skills follow both the upstream Agent Skills format and this repository's Skill authoring profile. Selected example copies are synchronized from the canonical source, routing fixtures cover positive, negative, and overlapping requests with measurable selection accuracy, and Codex evaluation scenarios verify observable workflow outcomes and guardrails for every canonical Skill.
