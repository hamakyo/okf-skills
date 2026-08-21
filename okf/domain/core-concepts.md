---
type: Domain Concept
title: Core Concepts
description: Defines the main concepts used by the OKF Skills template.
tags: [okf, skills, agents, claude]
generated: { by: openai-codex/gpt-5, at: 2026-08-21T18:26:11+09:00 }
---

# OKF

OKF is the knowledge layer. It stores durable project facts in Markdown. This repository targets OKF v0.2.

# Software Project Profile

The software-project profile is this repository's optional organization and maintenance policy for using OKF in software repositories. Its directory categories and validation rules are not universal OKF requirements.

# Skill

A Skill is a reusable agent workflow. Portable Skills follow the upstream Agent Skills standard. Canonical Skills in this repository additionally follow the local Skill authoring profile.

# AGENTS.md

`AGENTS.md` is the Codex-facing instruction file for repository-level behavior.

# CLAUDE.md

`CLAUDE.md` is the Claude Code-facing instruction file for repository-level behavior.

# Rule Of Thumb

If information describes what is true about the project, put it in OKF. If it describes how an agent should work, put it in a Skill.
