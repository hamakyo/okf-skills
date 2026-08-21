---
type: Playbook
title: Public Release Checklist
description: Steps to review before publishing this repository publicly.
tags: [release, oss]
generated: { by: openai-codex/gpt-5, at: 2026-08-21T18:26:11+09:00 }
---

# Checklist

1. Confirm README explains the project, usage, contribution, license, and disclaimer.
2. Confirm docs are linked from README and do not duplicate large sections unnecessarily.
3. Confirm every Skill directory has a `SKILL.md`.
4. Confirm `AGENTS.md` and `CLAUDE.md` are aligned but tool-specific.
5. Confirm OKF concept documents include frontmatter.
6. Search for secrets, credentials, private URLs, and personal data.
7. Review the license and copyright holder.
8. Run unit tests and the Markdown, OKF, Skill, and example-sync validators.
9. Run the Skill routing fixture as a semantic smoke test in supported hosts when descriptions changed.
10. Confirm README, docs, examples, and the changelog describe the same release behavior.
