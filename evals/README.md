# Skill Evaluations

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

## Codex Skill Evaluation Harness

`codex-scenarios.yaml` and `scripts/eval_codex_skills.py` provide a reproducible harness for evaluating whether Codex follows the core Skills in realistic, isolated git workspaces. Rather than grading prose subjectively, every scenario checks observable outcomes: file creation/modification boundaries, guardrail files left untouched, unit tests and OKF validation commands, and required summary facts.

### Scenario Format

`evals/codex-scenarios.yaml` uses `schema_version: 1` with `host: codex`, optional `defaults` (`skill_dir`, `timeout_seconds`), and a `scenarios` list. Each scenario defines:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | yes | Unique kebab-case scenario identifier. |
| `skill` | string | yes | Canonical Skill under `skills/` exercised by the scenario. |
| `title` | string | yes | Short human-readable summary of the task. |
| `description` | string | yes | Concise note describing the observable workflow and guardrails under test. |
| `prompt` | string | yes | Exact task prompt sent to Codex on stdin. |
| `timeout_seconds` | int | no | Optional per-scenario timeout override in seconds. |
| `workspace` | object | yes | Workspace setup: `copy_skills`, inline `files`, optional `working_tree_files` (unstaged diff applied after the baseline commit), and optional `fixture` directory path. |
| `assertions` | object | yes | Observable pass/fail checks (`files_must_exist`, `files_must_not_exist`, `files_must_change`, `files_must_not_change`, `max_changed_files`, `forbidden_paths`, `file_contains`, `file_not_contains`, `commands`, `response_contains`, `response_not_contains`). |

Included scenarios cover all five canonical Skills:

- `implement-feature-csv-delimiter` (`implement-feature`)
- `investigate-bug-hundred-percent-discount` (`investigate-bug`)
- `add-test-slugify-edge-cases` (`add-test`)
- `refactor-safely-email-normalization` (`refactor-safely`)
- `update-okf-retry-policy-diff` (`update-okf`)

### Deterministic Repository Checks vs Codex/API-Backed Evaluations

| Dimension | Deterministic Repository Checks (CI) | Codex / API-Backed Evaluations |
| --- | --- | --- |
| Commands | `validate_markdown.py`, `validate_okf.py`, `validate_skills.py`, `sync_examples.py --check`, `eval_codex_skills.py --mode validate`, `unittest` | `eval_codex_skills.py --mode codex` (or `--mode command`), plus `score_skill_routing.py` on model predictions |
| Network & API keys | None (fully offline, zero API cost) | Requires local Codex CLI / model credentials |
| Reproducibility | Deterministic pass/fail on every commit and PR | Subject to model/runtime variance; evaluated via observable file, command, and guardrail assertions |
| Primary failure signal | Broken links, invalid OKF/Skill metadata, example drift, malformed fixtures, leaked secrets | Behavioral regressions: missed tests, guardrail violations (e.g., editing code during investigation), invalid OKF updates |
| Where to run | Every PR in GitHub Actions and locally before commit | Locally before Skill/prompt changes or releases, or in opt-in credentialed workflows |

### Running The Codex Evaluation Harness

```bash
# 1. Deterministic schema, coverage, and secret-hygiene validation (runs in CI)
python scripts/eval_codex_skills.py --mode validate

# 2. List scenarios
python scripts/eval_codex_skills.py --list --format markdown

# 3. Safe dry-run: stage isolated git workspaces and preview commands without calling Codex
python scripts/eval_codex_skills.py --mode dry-run

# 4. Run against local Codex CLI (requires authenticated `codex` CLI; writes local report outside git)
python scripts/eval_codex_skills.py --mode codex --format markdown --output .eval-results/codex-eval.md

# 5. Run a single scenario or pass extra Codex CLI flags
python scripts/eval_codex_skills.py --mode codex --scenario implement-feature-csv-delimiter --codex-arg --model --codex-arg gpt-5-codex

# 6. Run through a custom wrapper or deterministic local stub
python scripts/eval_codex_skills.py --mode command --command "{python} path/to/wrapper.py" --format json
```

When a scenario fails, the report captures runner exit status, exact added/modified/deleted workspace files, and per-assertion pass/fail diagnostics so failures can be separated into runner setup errors, guardrail violations, failing tests, or broken OKF metadata.

### Secret And Credential Hygiene

- `eval_codex_skills.py --mode validate` scans prompts and inline workspace files for credential patterns and rejects matches deterministically.
- Never place API keys, tokens, private URLs, or personal data in `evals/codex-scenarios.yaml`, fixture files, or committed outputs.
- Runtime reports redact detected secret patterns and sensitive environment variable values before printing or writing `--output` files.
- Store local model-backed evaluation outputs under `.eval-results/` (listed in `.gitignore`) and share only sanitized summaries in pull requests or release notes.
