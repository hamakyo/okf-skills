# Skill Routing Evaluations

`skill-routing.yaml` is a machine-readable fixture for checking whether Skill descriptions route realistic maintenance requests to the intended workflow, avoid irrelevant Skills, and disambiguate neighboring Skills consistently.

Deterministic fixture validation and accuracy scoring are kept separate from model-backed execution so repository CI stays fast, offline, and reproducible.

## Fixture Format

`evals/skill-routing.yaml` uses `schema_version: 1` with a top-level `cases` list. Each case defines:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | yes | Unique kebab-case case identifier. |
| `category` | enum | yes | `positive`, `negative`, `overlap` (or `ambiguous` for boundary disambiguation). |
| `prompt` | string | yes | Realistic user prompt presented to the agent host. |
| `expect` | string \| `null` | yes | Expected canonical Skill name, or `null` when no Skill should be selected. |
| `reject` | list[string] | yes | Canonical Skills that must not be selected for this prompt. |
| `rationale` | string | no | Short note explaining why `expect` is preferred over `reject`. |

Category invariants enforced deterministically:

- `positive`: `expect` must be a canonical Skill name.
- `negative`: `expect` must be `null` and `reject` must be non-empty.
- `overlap` / `ambiguous`: `expect` must be a canonical Skill name and `reject` must list at least one competing Skill.

## Deterministic Validation (CI)

`python scripts/validate_skills.py` validates both canonical Skills and `evals/skill-routing.yaml`:

- Top-level `schema_version` (when set) equals `1` and no unknown keys appear.
- Every case has a unique kebab-case `id`, valid `category`, non-empty unique `prompt`, valid `expect`, valid duplicate-free `reject`, and non-empty `rationale` (when present).
- `expect` never appears inside `reject`, and every referenced Skill exists under `skills/`.
- Every canonical Skill has positive coverage, negative (`reject`) coverage, and overlap/ambiguous boundary coverage, and at least one `negative` (`expect: null`) case exists.

You can also inspect deterministic fixture coverage counts without model outputs:

```bash
python scripts/score_skill_routing.py --fixture-summary
```

## Measuring And Reporting Selection Accuracy

Model-backed execution (for Codex, Claude Code, or future automated harnesses) should produce a machine-readable JSON or YAML prediction file and score it with `scripts/score_skill_routing.py`.

### Prediction File Format

Preferred object format (JSON or YAML):

```json
{
  "schema_version": 1,
  "host": "codex",
  "model": "example-model",
  "results": [
    { "id": "implement-feature-positive", "selected": "implement-feature" },
    { "id": "general-documentation-negative", "selected": null }
  ]
}
```

A flat `{ "<case-id>": "<skill-or-null>" }` mapping or a bare list of `{ "id", "selected" }` objects is also accepted.

### Accuracy Calculation Rules

For each case in `evals/skill-routing.yaml`:

- **Exact match (`passed`)**: `selected == expect` (and `selected` is not in `reject`).
- **Rejected hit (`rejected_hit`)**: `selected` is non-null and appears in `reject`.
- **Negative false positive**: on `negative` cases (`expect: null`), any non-null `selected` Skill counts as a false positive.
- **Missing case**: treated as a failure by default (use `--allow-partial` only for exploratory subsets).

Reported metrics:

- **Overall accuracy**: `passed / total`
- **By category**: `passed / total` separately for `positive`, `overlap` (and `ambiguous` if present), and `negative`
- **By expected Skill**: `passed / total` for each canonical Skill plus `none` (`expect: null`)
- **Negative false-positive rate**: `negative_false_positives / negative_total`
- **Rejected-Skill selections**: count of cases where a Skill listed in `reject` was chosen
- **Failure breakdown**: every failing case with `id`, `category`, `expect`, `selected`, `reject`, and `reason`

### Running The Accuracy Scorer

```bash
# Text summary
python scripts/score_skill_routing.py --predictions path/to/predictions.json

# Markdown table for PRs or release review notes
python scripts/score_skill_routing.py --predictions path/to/predictions.json --format markdown

# Machine-readable JSON with a minimum accuracy gate
python scripts/score_skill_routing.py --predictions path/to/predictions.json --format json --min-accuracy 0.90
```

## Model-Backed Semantic Smoke Test

Before a release that changes Skill descriptions:

1. Present only the canonical Skill names and descriptions to each supported host.
2. Run every prompt from `evals/skill-routing.yaml` in a clean task and record each selected Skill (`null` if none) in a prediction file (do not commit credentials or raw session logs).
3. Run `python scripts/score_skill_routing.py --predictions <file> --format markdown`.
4. Confirm overall accuracy, category breakdown, and zero rejected-Skill hits match expectations, and paste the Markdown summary along with host/model/version details into the pull request or release review notes.
