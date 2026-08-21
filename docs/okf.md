# OKF v0.2 In This Repository

OKF is the project knowledge layer. Skills are the work procedures. Keeping those responsibilities separate makes the repository easier for both humans and agents to maintain.

## Upstream Standard

This repository targets [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). An OKF bundle is a directory tree of Markdown files. `index.md` and `log.md` are reserved filenames; every other Markdown file is a concept document with YAML frontmatter.

The upstream standard is intentionally minimal:

- Every concept document has parseable YAML frontmatter.
- `type` is the only universally required concept field.
- A bundle-root `index.md` may declare `okf_version: "0.2"`.
- Producers may add unknown metadata, and consumers should preserve it.
- Broken links or missing optional metadata do not make an upstream bundle invalid.

This repository applies additional software-project conventions. Those choices are documented separately in the [Software Project Profile](okf-software-project-profile.md).

## OKF Answers "What Is True?"

Use OKF for durable knowledge:

- Architecture decisions and boundaries.
- Domain concepts and vocabulary.
- Data structures, schemas, and contracts.
- Feature behavior and product rules.
- Playbooks for operations, release, incident response, or recurring work.

Do not use OKF for:

- One-off task plans.
- Temporary debugging notes.
- Agent behavior rules.
- Tool-specific prompt instructions.

## Skills Answer "How To Work"

Use Skills for repeatable workflows:

- How to implement a feature.
- How to investigate a bug.
- How to add tests.
- How to refactor safely.
- How to update OKF after code changes.

If a statement describes project truth, put it in OKF. If it describes agent process, put it in a Skill.

## Concept Frontmatter

Concept documents use YAML frontmatter:

```md
---
type: Feature
title: Account Deletion
description: Rules and flow for deleting an account.
tags: [accounts, privacy]
---
```

Core fields:

- `type`: required, non-empty concept kind.
- `title`: optional display name.
- `description`: optional one-sentence summary.
- `resource`: optional URI for an underlying asset.
- `tags`: optional categorization list.

## Provenance, Trust, And Lifecycle

OKF v0.2 defines optional metadata families. Their absence is valid and meaningful; do not add placeholder values.

### `sources`

Use `sources` when claims derive from identifiable internal or external material. Each entry requires a non-empty `resource`. Add an `id` when the body attributes individual claims through matching Markdown footnotes.

```yaml
sources:
  - id: account-policy
    resource: ../references/account-policy.md
    title: Account policy
    last_modified: 2026-05-30T00:00:00Z
usage_window: { from: 2026-06-01T00:00:00Z, to: 2026-06-30T00:00:00Z }
```

OKF v0.2 defines timestamp-valued fields, including `last_modified` and `usage_window` endpoints, as ISO 8601 datetimes with an explicit UTC offset.

### `generated`

Use `generated` to identify who or what produced the current content. `generated.by` follows the OKF actor convention, and `generated.at` records the last meaningful content change with an explicit UTC offset.

```yaml
generated:
  by: documentation-agent/1.0
  at: 2026-08-21T09:00:00Z
```

The legacy `timestamp` field is superseded by `generated.at`. Do not add `timestamp` to v0.2 concept documents.

### `verified`

Use `verified` only when an actor has checked the current content against its sources or resource. A verification performed before a meaningful content change must not be presented as verification of the new content.

```yaml
verified:
  - by: human:reviewer-id
    at: 2026-08-21T10:00:00Z
```

### `status`

Use `status: draft` for incomplete or unreviewed knowledge and `status: deprecated` for retained historical knowledge that is no longer current. Omitted `status` means `stable`.

### `stale_after`

Use `stale_after` only when a concept has a known absolute expiry instant. It is an offset-aware datetime, not a date or relative time-to-live.

```yaml
stale_after: 2026-12-31T00:00:00Z
```

## Linking

Use normal Markdown links. This repository profile prefers relative links because the templates are copied into other repositories:

```md
See [Repository Structure](../okf/architecture/repository-structure.md).
```

Upstream OKF consumers must tolerate broken links, but this public template validates its own local links as a repository quality rule.

## Updating OKF

Update OKF when a change affects durable knowledge:

- User-visible behavior.
- Architecture or ownership boundaries.
- Data models, schemas, or contracts.
- Domain terminology.
- Operational playbooks.

Use the [update-okf Skill](../skills/update-okf/SKILL.md) after implementation changes.
