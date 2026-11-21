# OKF v0.3 In This Repository

OKF is the project knowledge layer. Skills are the work procedures. Keeping those responsibilities separate makes the repository easier for both humans and agents to maintain.

## Upstream Standard

This repository targets [Open Knowledge Format v0.3](https://github.com/open-knowledge-format/open-knowledge-format/blob/main/SPEC.md). An OKF bundle is a directory tree of Markdown files. `index.md` and `log.md` are reserved filenames, dot-files and dot-directories are excluded from traversal, and non-reserved Markdown files with YAML frontmatter declaring a non-empty `type` are concept documents.

The upstream standard is intentionally minimal:

- Every concept document has parseable YAML frontmatter with a non-empty `type` (Markdown files without frontmatter or `type` are treated as non-concepts by upstream consumers).
- A bundle-root `index.md` may declare bundle metadata in YAML frontmatter: `okf_version: "0.3"`, `title`, `description`, `license`, and extension keys (§8.1).
- Producers may add unknown metadata—and `x-` prefixed keys are reserved for producer extensions at all levels (§4.1)—which consumers must preserve.
- Broken links or missing optional metadata do not make an upstream bundle invalid.

The upstream repository also ships general-purpose `okf-generate` and `okf-consume` Skills. This repository complements them with reusable software-maintenance workflow Skills and additional software-project conventions documented in the [Software Project Profile](okf-software-project-profile.md).

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

OKF v0.3 defines optional metadata families. Their absence is valid and meaningful; do not add placeholder values.

### Timestamps And Actors

- **Timestamps (§5):** Timestamp-valued fields (`sources[].last_modified`, `usage_window.from`/`to`, `generated.at`, `verified[].at`, `stale_after`) accept either an RFC 3339 `date-time` with an explicit UTC offset (for example, `2026-08-21T09:00:00Z`) or an RFC 3339 `full-date` (`YYYY-MM-DD`, interpreted as `00:00:00Z`). Offsetless datetimes such as `2026-08-21T09:00:00` are invalid.
- **Actors (§7):** Actor fields (`sources[].author`, `generated.by`, `verified[].by`) use either `<producer>/<version>` or `<scheme>:<id>` (such as `human:<id>`, `team:<id>`, `process:<id>`, or a custom lowercase scheme). For trust tiers, only `human:` yields `human-reviewed`; `team:` and other non-human actors yield `machine-confirmed`.

### `sources`

Use `sources` when claims derive from identifiable internal or external material. Each entry requires a non-empty `resource`. Add an `id` when the body attributes individual claims through matching Markdown footnotes.

```yaml
sources:
  - id: account-policy
    resource: ../references/account-policy.md
    title: Account policy
    last_modified: 2026-05-30
usage_window: { from: 2026-06-01T00:00:00Z, to: 2026-06-30T00:00:00Z }
```

### `generated`

Use `generated` to identify who or what produced the current content. `generated.by` identifies the producing actor, and `generated.at` records the last meaningful content change.

```yaml
generated:
  by: documentation-agent/1.0
  at: 2026-08-21T09:00:00Z
```

The legacy `timestamp` field is superseded by `generated.at`. Do not add `timestamp` to v0.3 concept documents.

### `verified`

Use `verified` only when an actor has checked the current content against its sources or resource. Under OKF v0.3 (§5.3), only **current** verification events—those with `verified[].at >= generated.at`, or any event when `generated` is absent—count toward trust tier. Older events may remain as historical records, or be removed when superseded, but a verification performed before a meaningful content change must never be presented as verification of the new content.

```yaml
verified:
  - by: human:reviewer-id
    at: 2026-08-21T10:00:00Z
```

### `status` And `superseded_by`

Use `status: draft` for incomplete or unreviewed knowledge and `status: deprecated` for retained historical knowledge that is no longer current. Omitted `status` means `stable`.

When deprecating a concept that has a replacement, OKF v0.3 (§5.4) allows `superseded_by` with the relative path to the replacement concept:

```yaml
status: deprecated
superseded_by: features/account-deletion-v2.md
```

### `stale_after`

Use `stale_after` only when a concept has a known absolute validity horizon (RFC 3339 offset-aware `date-time` or `YYYY-MM-DD` `full-date`, not a relative time-to-live).

```yaml
stale_after: 2026-12-31T00:00:00Z
```

### Attested Computations (Out Of Scope For This Profile)

OKF v0.3 (§10) also defines Attested Computation concepts (`# Computation`, `computations/`, `references/`, and metadata fields such as `runtime`, `parameters`, `executor`, and `attester`). This software-project template does not scaffold or enforce Attested Computation contracts; following OKF v0.3 forward-compatibility rules, `scripts/validate_okf.py` tolerates unknown metadata keys and `x-` producer extensions so bundles that include computation metadata remain valid.

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
