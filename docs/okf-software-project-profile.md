# OKF Software Project Profile

This repository is an opinionated software-project profile built on OKF v0.2. The profile adds organization and maintenance rules without redefining the upstream format.

## Relationship To OKF v0.2

The upstream [OKF v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) allows producers to organize concepts for their own domain. The directory categories in this repository are profile conventions, not OKF core requirements.

Profile rules may be stricter than upstream conformance. Validation output should identify whether a failure comes from the upstream format or this repository profile.

## Directory Layout

The default software-project bundle is:

```text
okf/
├── index.md
├── log.md
├── architecture/
├── domain/
├── data/
├── features/
└── playbooks/
```

The categories mean:

| Directory | Durable knowledge |
| --- | --- |
| `architecture/` | Components, boundaries, ownership, and important design decisions. |
| `domain/` | Business concepts, vocabulary, invariants, and rules. |
| `data/` | Schemas, contracts, formats, and lifecycle constraints. |
| `features/` | User-visible and developer-visible behavior. |
| `playbooks/` | Repeatable operational and maintenance procedures. |

Projects may remove unused categories or add domain-specific ones. A conformant OKF bundle does not need this exact layout.

## Bundle Router

Treat `okf/index.md` as the first-hop router into the knowledge bundle. It should describe the available categories and link to useful indexes or concepts without duplicating their full content.

Use progressive disclosure:

```text
AGENTS.md / CLAUDE.md
        ↓
okf/index.md
        ↓
relevant concepts only
        ↓
code / tests / task-specific context
```

Read `okf/log.md` when change history is relevant or when editing OKF. Do not require every task or Skill to load the entire log.

## Metadata Policy

- Require only non-empty `type` for every concept document.
- Add `sources` only for identifiable source material.
- Add or refresh `generated` when the current producer can be represented accurately.
- Remove or replace stale `verified` events after meaningful content changes unless the new content was re-verified.
- Use `status` only when `draft` or `deprecated` conveys useful lifecycle information; omission means `stable`.
- Use `stale_after` only when an absolute expiry is known.
- Reject legacy `timestamp` in v0.2 concept documents maintained by this repository.

Do not bulk-fill optional metadata with guesses. Missing optional signals are better than fabricated provenance or trust.

## Repository Quality Rules

The repository additionally requires:

- Relative local links that resolve in the checked-in template.
- `okf_version: "0.2"` in each maintained bundle root.
- Deterministic validation of YAML and optional metadata shapes.
- Updated indexes and dated log entries when bundle knowledge changes.
- No secrets, credentials, private URLs, personal data, or speculative claims presented as fact.
