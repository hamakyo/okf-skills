---
name: update-okf
description: Use after implementation changes to update OKF from git diff or changed files. Extract durable behavior, architecture, domain, data, and playbook changes into relevant OKF documents and log entries. Do not use for temporary task notes or changes with no durable project knowledge impact.
---

# Update OKF

## When to use

Use this Skill after code or documentation changes that affect:

- User-visible behavior.
- Architecture, ownership, or module boundaries.
- Domain terminology or business rules.
- Data structures, schemas, contracts, or migrations.
- Operational playbooks or recurring procedures.

Do not use this Skill for:

- Temporary investigation notes.
- Formatting-only changes.
- Internal refactors that do not alter durable knowledge.
- Duplicating implementation details that are already obvious from code and not useful as project knowledge.

## Inputs

- Current `git diff` or a list of changed files.
- Relevant issue, PR, or user request.
- Existing OKF bundle.
- Date for `okf/log.md` entry.
- Current producer actor in OKF form when known, such as `tool/version`, `human:<id>`, or `process:<id>`.

## Required context

Before editing OKF, read:

- `okf/index.md`
- `okf/log.md`
- Existing OKF documents related to changed behavior
- The implementation diff
- README or docs when the public usage story changed

## Workflow

1. Inspect `git diff` or changed files.
2. Extract only durable knowledge changes:
   - New or changed behavior.
   - New or changed architecture.
   - New or changed domain terms.
   - New or changed data contracts.
   - New or changed playbooks.
3. Map each knowledge change to an existing OKF document or create a new concept document.
4. Add or update YAML frontmatter for non-reserved concept documents:
   - Keep `type` non-empty.
   - Add or update `sources` when identifiable source material changed.
   - When `generated` exists and content meaningfully changes, update `generated.by` and `generated.at` for the current producer.
   - Add `generated` when the producer is known and can be represented without guessing.
   - Remove or replace `verified` events after meaningful content changes unless the new content was verified again.
   - Set `status` only when `draft` or `deprecated` conveys useful lifecycle information; omission means `stable`.
   - Set `stale_after` only when an absolute validity horizon is known.
   - Do not add the legacy `timestamp` field.
5. Keep `okf/index.md` accurate when adding, moving, or removing OKF documents.
6. Add a dated entry to `okf/log.md` using `YYYY-MM-DD`.
7. Avoid copying large code blocks unless they are the best durable reference.
8. Verify Markdown links and YAML metadata.

## Guardrails

- Do not turn OKF into a changelog of every code edit.
- Do not store secrets, credentials, private URLs, or personal data.
- Do not write speculative claims as facts.
- Do not fabricate producer identities, sources, verification events, or freshness deadlines.
- Do not treat verification of older content as verification of meaningfully changed content.
- Do not duplicate long README or docs sections.
- Do not change Skill behavior while updating OKF unless the task explicitly asks for it.
- Do not create empty directories or placeholder documents with no useful knowledge.

## Completion checklist

- [ ] Diff or changed files were inspected.
- [ ] Durable knowledge changes were separated from temporary implementation detail.
- [ ] Relevant OKF documents were updated or intentionally left unchanged.
- [ ] Provenance, trust, and lifecycle metadata were evaluated for meaningful content changes.
- [ ] `okf/index.md` was checked.
- [ ] `okf/log.md` has a dated entry when OKF changed.
- [ ] Links were checked.

## Expected final response

Report:

- Which knowledge changes were captured.
- OKF files added or updated.
- Whether `okf/index.md` and `okf/log.md` were updated.
- How provenance, verification, and freshness metadata were handled.
- Link or validation checks run.
- Any implementation changes that did not require OKF updates.
