# OKF Software Project Profile

This repository is an opinionated software-project profile built on OKF v0.3. The profile adds organization and maintenance rules without redefining the upstream format.

## Relationship To OKF v0.3

The upstream [OKF v0.3 specification](https://github.com/open-knowledge-format/open-knowledge-format/blob/main/SPEC.md) allows producers to organize concepts for their own domain. The directory categories in this repository are profile conventions, not OKF core requirements.

Profile rules may be stricter than upstream conformance. For example, upstream v0.3 treats non-reserved Markdown files without frontmatter as non-concepts, whereas this profile requires every non-reserved Markdown file in a maintained bundle to be a concept document with valid frontmatter. Validation output identifies whether a failure comes from `[OKF v0.3]` or `[software-project profile]`.

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

Treat `okf/index.md` as the first-hop router into the knowledge bundle. It should describe the available categories and link to useful indexes or concepts without duplicating their full content. Bundle-root `index.md` frontmatter declares `okf_version: "0.3"` and may include optional v0.3 §8.1 bundle metadata (`title`, `description`, `license`, and `x-` extensions).

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

- Require non-empty `type` for every non-reserved Markdown file in a maintained bundle.
- Add `sources` only for identifiable source material.
- Add or refresh `generated` when the current producer can be represented accurately.
- Never treat verification older than `generated.at` as verification of meaningfully changed content; remove stale `verified` events or record a fresh verification event (`verified[].at >= generated.at`).
- Use `status` only when `draft` or `deprecated` conveys useful lifecycle information; omission means `stable`.
- Use `superseded_by` only alongside `status: deprecated` to point to a replacement concept path.
- Use `stale_after` only when an absolute validity horizon is known (RFC 3339 offset-aware `date-time` or `YYYY-MM-DD` `full-date`).
- Reject legacy `timestamp` in v0.3 concept documents maintained by this repository.
- Accept `<producer>/<version>` and `<scheme>:<id>` (such as `human:<id>`, `team:<id>`, `process:<id>`, or custom lowercase schemes) for actor fields (`sources[].author`, `generated.by`, `verified[].by`), following OKF v0.3 §7.

Do not bulk-fill optional metadata with guesses. Missing optional signals are better than fabricated provenance or trust.

## Out Of Scope

- **Attested Computations (OKF v0.3 §10)**: This profile focuses on durable software-project documentation rather than attested computational artifacts (`computations/`, `# Computation`, `runtime`, `parameters`, `executor`, `attester`) or `references/` layouts. Unknown metadata fields and `x-` extensions are preserved and left unrejected per OKF v0.3 consumer rules.

## Repository Quality Rules

The repository additionally requires:

- Relative local links that resolve in the checked-in template.
- `okf_version: "0.3"` in each maintained bundle root.
- Deterministic validation of YAML and optional metadata shapes (skipping dot-files and dot-directories per OKF v0.3 §3.2).
- Updated indexes and dated log entries when bundle knowledge changes.
- No secrets, credentials, private URLs, personal data, or speculative claims presented as fact.
