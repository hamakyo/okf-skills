from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from scripts.score_skill_routing import (
    evaluate_routing_results,
    format_report,
    load_fixture,
    load_predictions,
    main,
    summarize_fixture,
)
from scripts.validate_skills import ROUTING_FIXTURE, canonical_skill_names


class ScoreSkillRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = load_fixture(ROUTING_FIXTURE, canonical_skill_names())

    def test_repository_fixture_coverage(self) -> None:
        summary = summarize_fixture(self.cases)
        self.assertGreaterEqual(summary["total_cases"], 25)
        self.assertGreaterEqual(summary["by_category"]["positive"], 15)
        self.assertGreaterEqual(summary["by_category"]["overlap"], 10)
        self.assertGreaterEqual(summary["by_category"]["negative"], 5)
        for skill in canonical_skill_names():
            self.assertGreaterEqual(summary["by_expected_skill"][skill], 5)

    def test_perfect_predictions_score_100_percent(self) -> None:
        preds = {case["id"]: case["expect"] for case in self.cases}
        report = evaluate_routing_results(
            self.cases,
            preds,
            metadata={"host": "codex", "model": "test-model"},
        )
        self.assertEqual(report["total"], len(self.cases))
        self.assertEqual(report["passed"], len(self.cases))
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["overall_accuracy"], 1.0)
        self.assertEqual(report["rejected_selection_count"], 0)
        self.assertEqual(report["negative_false_positive_rate"], 0.0)
        self.assertEqual(report["failures"], [])

        markdown = format_report(report, "markdown")
        self.assertIn("# Skill Routing Accuracy Report", markdown)
        self.assertIn("host=codex", markdown)
        self.assertIn("100.0%", markdown)

    def test_mixed_failures_track_reasons_and_rates(self) -> None:
        preds = {case["id"]: case["expect"] for case in self.cases}
        preds["implement-feature-positive"] = None  # missed expected skill
        preds["bug-versus-feature"] = "implement-feature"  # selected rejected skill
        preds["general-documentation-negative"] = "update-okf"  # negative false positive

        report = evaluate_routing_results(self.cases, preds)
        self.assertEqual(report["failed"], 3)
        self.assertEqual(report["rejected_selection_count"], 2)
        self.assertGreater(report["negative_false_positive_rate"], 0.0)
        reasons = {f["id"]: f["reason"] for f in report["failures"]}
        self.assertEqual(reasons["implement-feature-positive"], "missed_expected_skill")
        self.assertEqual(reasons["bug-versus-feature"], "selected_rejected_skill")
        self.assertEqual(reasons["general-documentation-negative"], "false_positive_rejected_skill")

        markdown = format_report(report, "markdown")
        self.assertIn("## Failures", markdown)
        self.assertIn("selected_rejected_skill", markdown)

    def test_rejects_missing_or_unknown_predictions_by_default(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_routing_results(self.cases, {"implement-feature-positive": "implement-feature"})
        with self.assertRaises(ValueError):
            evaluate_routing_results(self.cases, {"nonexistent-case": "add-test"}, allow_partial=True)

        partial = evaluate_routing_results(
            self.cases,
            {"implement-feature-positive": "implement-feature"},
            allow_partial=True,
        )
        self.assertEqual(partial["total"], 1)
        self.assertEqual(partial["passed"], 1)
        self.assertEqual(len(partial["missing_case_ids"]), len(self.cases) - 1)

    def test_load_predictions_supports_structured_and_flat_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            structured = Path(tmp) / "preds.json"
            structured.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "host": "codex",
                        "results": [
                            {"id": "implement-feature-positive", "selected": "implement-feature"},
                            {"id": "general-documentation-negative", "selected": None},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            preds, meta = load_predictions(structured)
            self.assertEqual(preds["implement-feature-positive"], "implement-feature")
            self.assertIsNone(preds["general-documentation-negative"])
            self.assertEqual(meta["host"], "codex")

            flat = Path(tmp) / "flat.yaml"
            flat.write_text("implement-feature-positive: implement-feature\ngeneral-documentation-negative: null\n", encoding="utf-8")
            flat_preds, flat_meta = load_predictions(flat)
            self.assertEqual(flat_preds, preds)
            self.assertEqual(flat_meta, {})

            dup = Path(tmp) / "dup.json"
            dup.write_text(
                json.dumps(
                    [
                        {"id": "implement-feature-positive", "selected": "implement-feature"},
                        {"id": "implement-feature-positive", "selected": "add-test"},
                    ]
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_predictions(dup)

    def test_cli_fixture_summary_and_min_accuracy_gate(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--fixture-summary", "--format", "json"])
        self.assertEqual(code, 0)
        summary = json.loads(buf.getvalue())
        self.assertEqual(summary["total_cases"], len(self.cases))

        with tempfile.TemporaryDirectory() as tmp:
            preds_file = Path(tmp) / "preds.json"
            preds = {case["id"]: case["expect"] for case in self.cases}
            preds["implement-feature-positive"] = None
            preds_file.write_text(json.dumps(preds), encoding="utf-8")

            out = io.StringIO()
            err = io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                fail_code = main(["--predictions", str(preds_file), "--min-accuracy", "1.0"])
            self.assertEqual(fail_code, 1)
            self.assertIn("below --min-accuracy", err.getvalue())

            out2 = io.StringIO()
            with redirect_stdout(out2):
                pass_code = main(["--predictions", str(preds_file), "--min-accuracy", "0.90", "--format", "json"])
            self.assertEqual(pass_code, 0)
            parsed = json.loads(out2.getvalue())
            self.assertEqual(parsed["failed"], 1)


if __name__ == "__main__":
    unittest.main()
