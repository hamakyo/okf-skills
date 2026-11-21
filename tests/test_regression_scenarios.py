from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import eval_codex_skills, validate_okf

REGRESSION_SCENARIOS = eval_codex_skills.ROOT / "evals" / "regression-scenarios.yaml"


class RegressionScenariosTests(unittest.TestCase):
    def test_regression_scenarios_validate_and_cover_all_core_skills(self) -> None:
        data = eval_codex_skills.load_scenarios(REGRESSION_SCENARIOS)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["host"], "codex")

        canonical = eval_codex_skills.canonical_skills()
        covered = {scenario["skill"] for scenario in data["scenarios"]}
        self.assertEqual(covered, canonical)

        for scenario in data["scenarios"]:
            self.assertEqual(scenario["workspace"].get("fixture"), "evals/fixtures/maintenance-app")
            self.assertEqual(set(scenario["workspace"]["copy_skills"]), canonical)
            self.assertIn("allowed_changed_paths", scenario["assertions"])

    def test_all_regression_baselines_stage_and_pass_baseline_checks(self) -> None:
        data = eval_codex_skills.load_scenarios(REGRESSION_SCENARIOS)
        skill_dir = data["defaults"]["skill_dir"]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for scenario in data["scenarios"]:
                workspace = tmp_path / scenario["id"]
                eval_codex_skills.stage_scenario_workspace(
                    scenario,
                    workspace,
                    skill_dir=skill_dir,
                )

                okf_errors, okf_count = validate_okf.validate_bundle(workspace / "okf")
                self.assertEqual(okf_errors, [], f"OKF invalid in {scenario['id']}: {okf_errors}")
                self.assertEqual(okf_count, 5)

                completed = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(
                    completed.returncode,
                    0,
                    f"baseline tests failed in {scenario['id']}: {completed.stderr or completed.stdout}",
                )

                if scenario["id"] == "e2e-investigate-bug-tax-discount-order":
                    repro = subprocess.run(
                        [
                            sys.executable,
                            "-c",
                            "from src.invoices import Invoice, calculate_invoice_total; "
                            "print(calculate_invoice_total(Invoice('BUG', 2000, discount_percent=20, tax_percent=10)))",
                        ],
                        cwd=workspace,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertEqual(repro.stdout.strip(), "1800")

                if scenario["id"] == "e2e-update-okf-storage-and-void-status":
                    diff = subprocess.run(
                        ["git", "diff", "--name-only"],
                        cwd=workspace,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertEqual(sorted(diff.stdout.splitlines()), ["src/invoices.py", "src/storage.py"])

    def test_allowed_changed_paths_and_diagnostic_categories_catch_drift(self) -> None:
        data = eval_codex_skills.load_scenarios(REGRESSION_SCENARIOS)
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "drifting_stub.py"
            stub.write_text(
                r"""
import os
from pathlib import Path

ws = Path(os.environ["OKF_EVAL_WORKSPACE"])
resp = Path(os.environ["OKF_EVAL_RESPONSE_FILE"])

# Unintended edit to unrelated storage module, plus missing OKF update and missing Skill reference
storage = ws / "src" / "storage.py"
storage.write_text(storage.read_text(encoding="utf-8") + "\n# unintended edit\n", encoding="utf-8")
resp.write_text("Done editing without citing skill or OKF.\n", encoding="utf-8")
""",
                encoding="utf-8",
            )

            report = eval_codex_skills.run_suite(
                data,
                mode="command",
                scenario_ids=["e2e-implement-feature-invoice-currency"],
                command_template=f"{{python}} {stub}",
            )
            self.assertEqual(report["summary"]["failed"], 1)
            item = report["scenarios"][0]
            self.assertEqual(
                item["failed_categories"],
                ["context", "documentation", "execution", "routing"],
            )
            self.assertEqual(
                report["summary"]["failures_by_category"],
                {"context": 1, "documentation": 1, "execution": 1, "routing": 1},
            )
            failed_kinds = {c["kind"]: c for c in item["checks"] if not c["passed"]}
            self.assertIn("allowed_changed_paths", failed_kinds)
            self.assertIn("src/storage.py", failed_kinds["allowed_changed_paths"]["detail"])

            markdown = eval_codex_skills.format_report(report, "markdown")
            self.assertIn("Failures by diagnostic category:", markdown)
            self.assertIn("`routing`=1", markdown)
            self.assertIn("`context`=1", markdown)
            self.assertIn("`documentation`=1", markdown)

    def test_refactor_safely_regression_passes_with_reference_stub(self) -> None:
        data = eval_codex_skills.load_scenarios(REGRESSION_SCENARIOS)
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "refactor_stub.py"
            stub.write_text(
                r"""
import os
from pathlib import Path

ws = Path(os.environ["OKF_EVAL_WORKSPACE"])
resp = Path(os.environ["OKF_EVAL_RESPONSE_FILE"])

(ws / "src" / "reporting.py").write_text(
    r'''from __future__ import annotations

from collections.abc import Iterable

from src.invoices import VALID_STATUSES, Invoice, calculate_invoice_total, format_cents


def _aggregate_totals(invoices: Iterable[Invoice]) -> tuple[int, int, int]:
    count = 0
    open_cents = 0
    paid_cents = 0
    for invoice in invoices:
        if invoice.status not in VALID_STATUSES:
            raise ValueError(f"unsupported invoice status: {invoice.status!r}")
        total = calculate_invoice_total(invoice)
        count += 1
        if invoice.status == "open":
            open_cents += total
        else:
            paid_cents += total
    return count, open_cents, paid_cents


def summarize_invoices(invoices: Iterable[Invoice]) -> dict[str, int]:
    count, open_cents, paid_cents = _aggregate_totals(invoices)
    return {
        "count": count,
        "open_cents": open_cents,
        "paid_cents": paid_cents,
        "total_cents": open_cents + paid_cents,
    }


def format_monthly_report(invoices: Iterable[Invoice]) -> str:
    summary = summarize_invoices(invoices)
    return "\n".join(
        [
            f"Invoices: {summary['count']}",
            f"Open: {format_cents(summary['open_cents'])}",
            f"Paid: {format_cents(summary['paid_cents'])}",
            f"Total: {format_cents(summary['total_cents'])}",
        ]
    )
''',
    encoding="utf-8",
)
resp.write_text("Used refactor-safely to extract _aggregate_totals and ran unittest.\n", encoding="utf-8")
""",
                encoding="utf-8",
            )

            report = eval_codex_skills.run_suite(
                data,
                mode="command",
                scenario_ids=["e2e-refactor-safely-report-aggregation"],
                command_template=f"{{python}} {stub}",
            )
            self.assertEqual(report["summary"]["passed"], 1, eval_codex_skills.format_report(report))
            self.assertEqual(report["scenarios"][0]["changed_files"]["modified"], ["src/reporting.py"])

    def test_validate_detects_secret_inside_fixture_directory(self) -> None:
        base = eval_codex_skills.load_scenarios(REGRESSION_SCENARIOS)
        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp)
            for skill in eval_codex_skills.canonical_skills():
                skill_file = fake_root / "skills" / skill / "SKILL.md"
                skill_file.parent.mkdir(parents=True, exist_ok=True)
                skill_file.write_text("---\nname: x\ndescription: y\n---\n", encoding="utf-8")
            fixture_dir = fake_root / "evals" / "fixtures" / "leaky"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            (fixture_dir / "config.py").write_text(
                'TOKEN = "ghp_1234567890abcdefghijklmnopqrstuv"\n',
                encoding="utf-8",
            )

            mutated = copy.deepcopy(base)
            for scenario in mutated["scenarios"]:
                scenario["workspace"]["fixture"] = "evals/fixtures/leaky"

            errors = eval_codex_skills.validate_scenarios_data(mutated, root=fake_root)
            self.assertTrue(
                any("appears to contain a secret (github-token)" in err for err in errors),
                errors,
            )


if __name__ == "__main__":
    unittest.main()
