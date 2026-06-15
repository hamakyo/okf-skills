# Contributing

Thank you for improving OKF Skills. This repository is intended to stay small, portable, and easy to copy into other projects.

## What Fits

- Clearer Skill workflows.
- Better OKF examples.
- Documentation that helps first-time users.
- Fixes for broken links, ambiguous wording, or outdated guidance.
- Small examples that demonstrate real usage without requiring a full application.

## What Does Not Fit

- Project-specific private process.
- Secrets, tokens, private URLs, customer data, or personal data.
- Large frameworks or generated artifacts that make the template hard to copy.
- Skills that mix facts about one project with reusable workflow instructions.

## Change Guidelines

1. Keep OKF and Skills separate.
   - OKF stores project knowledge.
   - Skills store repeatable working procedures.
2. If you change a Skill, update related docs when behavior or usage changes.
3. If you change OKF structure, update `okf/index.md`, `docs/okf.md`, and examples if needed.
4. Keep Markdown readable in plain text.
5. Prefer relative links inside the repository.

## Pull Request Checklist

- [ ] README links still work.
- [ ] `AGENTS.md` and `CLAUDE.md` still point to relevant docs.
- [ ] Every Skill directory contains `SKILL.md`.
- [ ] New OKF concept documents include YAML frontmatter with `type`.
- [ ] No secrets, credentials, private URLs, or personal data were added.
- [ ] The change summary explains how the update was verified.
