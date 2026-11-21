---
type: Architecture
title: Repository Structure
description: Defines the responsibility boundaries between README, docs, OKF, Skills, and examples.
tags: [architecture, repository]
generated: { by: google-antigravity/agent, at: 2026-11-22T05:47:00+09:00 }
---

# Purpose

The repository is a copyable template collection for agent-assisted software work.

# Boundaries

| Area | Responsibility |
| --- | --- |
| `README.md` | Public entry point and quick start. |
| `docs/` | Focused usage guides with limited duplication. |
| `skills/` | Reusable task workflows for agents. |
| `okf/` | Durable project knowledge organized by the software-project profile. |
| `examples/` | Copyable starter configurations. |
| `evals/` | Machine-readable Skill routing fixtures, Codex evaluation scenarios, and end-to-end fixture repositories (`evals/fixtures/`). |
| `scripts/` | Deterministic validators, example synchronization, routing scorer, and Codex evaluation runner. |
| `AGENTS.md` | Codex-specific repository guidance. |
| `CLAUDE.md` | Claude Code-specific repository guidance. |

# Design Rule

Project facts belong in OKF. Agent workflows belong in Skills. Tool-specific repository behavior belongs in `AGENTS.md` or `CLAUDE.md`.

The top-level `skills/` directory is the canonical Skill source. Example Skill directories contain selected synchronized copies rather than independent variants.
