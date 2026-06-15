---
type: Domain Concept
title: Core Concepts
description: Defines the main concepts used by the OKF Skills template.
tags: [okf, skills, agents, claude]
---

# OKF

OKF is the knowledge layer. It stores durable project facts in Markdown.

# Skill

A Skill is a reusable agent workflow. It describes when to use the workflow, what context to read, what steps to follow, and what guardrails apply.

# AGENTS.md

`AGENTS.md` is the Codex-facing instruction file for repository-level behavior.

# CLAUDE.md

`CLAUDE.md` is the Claude Code-facing instruction file for repository-level behavior.

# Rule Of Thumb

If information describes what is true about the project, put it in OKF. If it describes how an agent should work, put it in a Skill.
