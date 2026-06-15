---
type: Architecture
title: Repository Structure
description: Defines the responsibility boundaries between README, docs, OKF, Skills, and examples.
tags: [architecture, repository]
---

# Purpose

The repository is a copyable template collection for agent-assisted software work.

# Boundaries

| Area | Responsibility |
| --- | --- |
| `README.md` | Public entry point and quick start. |
| `docs/` | Focused usage guides with limited duplication. |
| `skills/` | Reusable task workflows for agents. |
| `okf/` | Durable project knowledge. |
| `examples/` | Copyable starter configurations. |
| `AGENTS.md` | Codex-specific repository guidance. |
| `CLAUDE.md` | Claude Code-specific repository guidance. |

# Design Rule

Project facts belong in OKF. Agent workflows belong in Skills. Tool-specific repository behavior belongs in `AGENTS.md` or `CLAUDE.md`.
