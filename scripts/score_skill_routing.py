#!/usr/bin/env python3
"""Score Skill routing predictions against evals/skill-routing.yaml and summarize accuracy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from validate_skills import ROUTING_FIXTURE, canonical_skill_names, validate_routing_fixture
except ImportError:  # pragma: no cover - used when imported as scripts.score_skill_routing
    from .validate_skills import ROUTING_FIXTURE, canonical_skill_names, validate_routing_fixture

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_ORDER = ("positive", "overlap", "ambiguous", "negative")


def load_fixture(fixture_path: Path = ROUTING_FIXTURE, skill_names: set[str] | None = None) -> list[dict[str, Any]]:
    names = skill_names if skill_names is not None else canonical_skill_names(ROOT)
    errors = validate_routing_fixture(fixture_path, names)
    if errors:
        raise ValueError("Routing fixture validation failed:\n- " + "\n- ".join(errors))
    data = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    return list(data["cases"])


def load_predictions(predictions_path: Path) -> tuple[dict[str, str | None], dict[str, Any]]:
    raw_text = predictions_path.read_text(encoding="utf-8")
    try:
        raw = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"Cannot parse predictions file {predictions_path}: {exc}") from exc

    metadata: dict[str, Any] = {}
    entries: list[dict[str, Any]] = []

    if isinstance(raw, dict) and "results" in raw:
        if not isinstance(raw["results"], list):
            raise ValueError("Prediction file 'results' must be a list")
        entries = raw["results"]
        for key in ("schema_version", "host", "model", "run_id", "timestamp"):
            if key in raw:
                metadata[key] = raw[key]
    elif isinstance(raw, list):
        entries = raw
    elif isinstance(raw, dict):
        mapping: dict[str, str | None] = {}
        for case_id, selected in raw.items():
            if not isinstance(case_id, str) or not case_id.strip():
                raise ValueError(f"Invalid prediction case id: {case_id!r}")
            if selected is not None and not isinstance(selected, str):
                raise ValueError(f"Prediction for {case_id!r} must be a string or null")
            mapping[case_id] = selected
        return mapping, metadata
    else:
        raise ValueError("Predictions file must be a mapping with 'results', a list of result objects, or an id->skill mapping")

    mapping = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"results[{index}] must be a mapping")
        case_id = entry.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"results[{index}].id must be a non-empty string")
        if "selected" not in entry:
            raise ValueError(f"results[{index}] ({case_id}) is missing 'selected'")
        selected = entry["selected"]
        if selected is not None and not isinstance(selected, str):
            raise ValueError(f"results[{index}] ({case_id}).selected must be a string or null")
        if case_id in mapping:
            raise ValueError(f"Duplicate prediction for case id {case_id!r}")
        mapping[case_id] = selected

    return mapping, metadata


def summarize_fixture(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, int] = {}
    by_expected_skill: dict[str, int] = {}
    rejected_mentions: dict[str, int] = {}

    for case in cases:
        cat = case["category"]
        by_category[cat] = by_category.get(cat, 0) + 1
        skill_key = case["expect"] if case["expect"] is not None else "none"
        by_expected_skill[skill_key] = by_expected_skill.get(skill_key, 0) + 1
        for skill in case["reject"]:
            rejected_mentions[skill] = rejected_mentions.get(skill, 0) + 1

    ordered_categories = {
        cat: by_category[cat] for cat in CATEGORY_ORDER if cat in by_category
    }
    return {
        "total_cases": len(cases),
        "by_category": ordered_categories,
        "by_expected_skill": dict(sorted(by_expected_skill.items())),
        "rejected_mentions": dict(sorted(rejected_mentions.items())),
    }


def _rate(passed: int, total: int) -> float:
    return round(passed / total, 4) if total else 0.0


def evaluate_routing_results(
    cases: list[dict[str, Any]],
    predictions: dict[str, str | None],
    *,
    allow_partial: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    known_ids = {case["id"] for case in cases}
    unexpected_ids = sorted(set(predictions) - known_ids)
    if unexpected_ids:
        raise ValueError(f"Predictions contain unknown case IDs: {unexpected_ids}")

    missing_ids = [case["id"] for case in cases if case["id"] not in predictions]
    if missing_ids and not allow_partial:
        raise ValueError(f"Predictions are missing {len(missing_ids)} fixture case(s): {missing_ids}")

    evaluated_cases = [case for case in cases if case["id"] in predictions]
    total = len(evaluated_cases)
    passed = 0
    rejected_hits = 0
    negative_total = 0
    negative_false_positives = 0

    cat_counts: dict[str, list[int]] = {}
    skill_counts: dict[str, list[int]] = {}
    failures: list[dict[str, Any]] = []

    for case in evaluated_cases:
        case_id = case["id"]
        category = case["category"]
        expected = case["expect"]
        reject = case["reject"]
        selected = predictions[case_id]

        rejected_hit = selected is not None and selected in reject
        exact_match = selected == expected
        case_passed = exact_match and not rejected_hit

        cat_entry = cat_counts.setdefault(category, [0, 0])
        cat_entry[1] += 1
        if case_passed:
            passed += 1
            cat_entry[0] += 1

        skill_key = expected if expected is not None else "none"
        skill_entry = skill_counts.setdefault(skill_key, [0, 0])
        skill_entry[1] += 1
        if case_passed:
            skill_entry[0] += 1

        if rejected_hit:
            rejected_hits += 1

        if category == "negative":
            negative_total += 1
            if selected is not None:
                negative_false_positives += 1

        if not case_passed:
            if rejected_hit and expected is None:
                reason = "false_positive_rejected_skill"
            elif rejected_hit:
                reason = "selected_rejected_skill"
            elif selected is None:
                reason = "missed_expected_skill"
            elif expected is None:
                reason = "false_positive"
            else:
                reason = "wrong_skill"
            failures.append(
                {
                    "id": case_id,
                    "category": category,
                    "expect": expected,
                    "selected": selected,
                    "reject": reject,
                    "reason": reason,
                }
            )

    by_category = {
        cat: {
            "passed": cat_counts[cat][0],
            "total": cat_counts[cat][1],
            "accuracy": _rate(cat_counts[cat][0], cat_counts[cat][1]),
        }
        for cat in CATEGORY_ORDER
        if cat in cat_counts
    }
    by_expected_skill = {
        skill: {
            "passed": counts[0],
            "total": counts[1],
            "accuracy": _rate(counts[0], counts[1]),
        }
        for skill, counts in sorted(skill_counts.items())
    }

    report: dict[str, Any] = {
        "schema_version": 1,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "overall_accuracy": _rate(passed, total),
        "rejected_selection_count": rejected_hits,
        "negative_false_positive_rate": _rate(negative_false_positives, negative_total),
        "by_category": by_category,
        "by_expected_skill": by_expected_skill,
        "missing_case_ids": missing_ids,
        "failures": failures,
    }
    if metadata:
        report["metadata"] = metadata
    return report


def _pct(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def format_fixture_summary(summary: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(summary, indent=2)
    if fmt == "markdown":
        lines = [
            "# Skill Routing Fixture Summary",
            "",
            f"- Total cases: **{summary['total_cases']}**",
            "",
            "## By Category",
            "",
            "| Category | Cases |",
            "| --- | ---: |",
        ]
        for cat, count in summary["by_category"].items():
            lines.append(f"| `{cat}` | {count} |")
        lines += [
            "",
            "## By Expected Skill",
            "",
            "| Expected Skill | Cases |",
            "| --- | ---: |",
        ]
        for skill, count in summary["by_expected_skill"].items():
            lines.append(f"| `{skill}` | {count} |")
        return "\n".join(lines)

    lines = [f"Routing fixture summary: {summary['total_cases']} cases"]
    lines.append("By category:")
    for cat, count in summary["by_category"].items():
        lines.append(f"  - {cat}: {count}")
    lines.append("By expected Skill:")
    for skill, count in summary["by_expected_skill"].items():
        lines.append(f"  - {skill}: {count}")
    return "\n".join(lines)


def format_report(report: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(report, indent=2)
    if fmt == "markdown":
        lines = ["# Skill Routing Accuracy Report", ""]
        meta = report.get("metadata") or {}
        if meta:
            meta_parts = [f"{k}={v}" for k, v in meta.items() if k != "schema_version"]
            if meta_parts:
                lines.append(f"- Run metadata: {', '.join(meta_parts)}")
        lines += [
            f"- Overall accuracy: **{report['passed']}/{report['total']} ({_pct(report['overall_accuracy'])})**",
            f"- Rejected-Skill selections: **{report['rejected_selection_count']}**",
            f"- Negative false-positive rate: **{_pct(report['negative_false_positive_rate'])}**",
            "",
            "## By Category",
            "",
            "| Category | Passed | Total | Accuracy |",
            "| --- | ---: | ---: | ---: |",
        ]
        for cat, stats in report["by_category"].items():
            lines.append(f"| `{cat}` | {stats['passed']} | {stats['total']} | {_pct(stats['accuracy'])} |")
        lines += [
            "",
            "## By Expected Skill",
            "",
            "| Expected Skill | Passed | Total | Accuracy |",
            "| --- | ---: | ---: | ---: |",
        ]
        for skill, stats in report["by_expected_skill"].items():
            lines.append(f"| `{skill}` | {stats['passed']} | {stats['total']} | {_pct(stats['accuracy'])} |")
        if report["failures"]:
            lines += [
                "",
                "## Failures",
                "",
                "| Case ID | Category | Expected | Selected | Reason |",
                "| --- | --- | --- | --- | --- |",
            ]
            for fail in report["failures"]:
                exp = fail["expect"] if fail["expect"] is not None else "null"
                sel = fail["selected"] if fail["selected"] is not None else "null"
                lines.append(
                    f"| `{fail['id']}` | `{fail['category']}` | `{exp}` | `{sel}` | `{fail['reason']}` |"
                )
        return "\n".join(lines)

    lines = [
        f"Overall accuracy: {report['passed']}/{report['total']} ({_pct(report['overall_accuracy'])})",
        f"Rejected-Skill selections: {report['rejected_selection_count']}",
        f"Negative false-positive rate: {_pct(report['negative_false_positive_rate'])}",
        "By category:",
    ]
    for cat, stats in report["by_category"].items():
        lines.append(f"  - {cat}: {stats['passed']}/{stats['total']} ({_pct(stats['accuracy'])})")
    lines.append("By expected Skill:")
    for skill, stats in report["by_expected_skill"].items():
        lines.append(f"  - {skill}: {stats['passed']}/{stats['total']} ({_pct(stats['accuracy'])})")
    if report["failures"]:
        lines.append("Failures:")
        for fail in report["failures"]:
            lines.append(
                f"  - {fail['id']} ({fail['category']}): expected={fail['expect']!r}, selected={fail['selected']!r} [{fail['reason']}]"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score Skill routing predictions or summarize fixture coverage.")
    parser.add_argument("--fixture", type=Path, default=ROUTING_FIXTURE, help="Path to routing fixture YAML.")
    parser.add_argument("--predictions", type=Path, help="Path to JSON or YAML predictions file.")
    parser.add_argument(
        "--fixture-summary",
        action="store_true",
        help="Print deterministic fixture coverage counts without predictions.",
    )
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text", help="Output format.")
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=None,
        help="Fail with exit code 1 if overall accuracy is below this threshold (0.0 to 1.0).",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Allow prediction files that cover only a subset of fixture cases.",
    )
    args = parser.parse_args(argv)

    if args.min_accuracy is not None and not (0.0 <= args.min_accuracy <= 1.0):
        print("--min-accuracy must be between 0.0 and 1.0", file=sys.stderr)
        return 2

    try:
        cases = load_fixture(args.fixture)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.fixture_summary or args.predictions is None:
        if not args.fixture_summary and args.predictions is None:
            print("Provide --predictions <file> or --fixture-summary.", file=sys.stderr)
            return 2
        print(format_fixture_summary(summarize_fixture(cases), args.format))
        return 0

    try:
        predictions, metadata = load_predictions(args.predictions)
        report = evaluate_routing_results(
            cases,
            predictions,
            allow_partial=args.allow_partial,
            metadata=metadata,
        )
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(format_report(report, args.format))
    if args.min_accuracy is not None and report["overall_accuracy"] < args.min_accuracy:
        print(
            f"Accuracy {report['overall_accuracy']:.4f} is below --min-accuracy {args.min_accuracy:.4f}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
