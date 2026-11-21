from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import eval_codex_skills, validate_okf


class EvalCodexSkillsTests(unittest.TestCase):
    def test_repository_scenarios_validate_and_cover_all_core_skills(self) -> None:
        data = eval_codex_skills.load_scenarios()
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["host"], "codex")
        covered = {scenario["skill"] for scenario in data["scenarios"]}
        self.assertEqual(covered, eval_codex_skills.canonical_skills())

    def test_all_repository_scenario_baselines_are_valid(self) -> None:
        data = eval_codex_skills.load_scenarios()
        skill_dir = data["defaults"]["skill_dir"]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for scenario in data["scenarios"]:
                workspace = tmp_path / scenario["id"]
                snapshot = eval_codex_skills.stage_scenario_workspace(
                    scenario,
                    workspace,
                    skill_dir=skill_dir,
                )
                self.assertTrue(snapshot)

                for skill_name in scenario["workspace"]["copy_skills"]:
                    copied = workspace / skill_dir / skill_name / "SKILL.md"
                    self.assertTrue(copied.is_file(), f"missing copied skill {skill_name} in {scenario['id']}")

                okf_errors, okf_count = validate_okf.validate_bundle(workspace / "okf")
                self.assertEqual(okf_errors, [], f"baseline OKF invalid in {scenario['id']}: {okf_errors}")
                self.assertGreaterEqual(okf_count, 2)

                if (workspace / "tests").is_dir():
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

                if scenario["id"] == "update-okf-retry-policy-diff":
                    diff = subprocess.run(
                        ["git", "diff", "--name-only"],
                        cwd=workspace,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertEqual(diff.stdout.strip(), "src/http_client.py")

    def test_validate_rejects_malformed_and_secret_bearing_scenarios(self) -> None:
        base = eval_codex_skills.load_scenarios()
        broken = copy.deepcopy(base)
        broken["unknown_top"] = True
        broken["scenarios"] = [broken["scenarios"][0]]
        scenario = broken["scenarios"][0]
        scenario["prompt"] = "Use key sk-proj-abcdefghijklmnopqrstuvwxyz123456 to run tests."
        scenario["workspace"]["files"]["../escape.txt"] = "bad"
        scenario["assertions"]["files_must_not_change"].append("src/exporter.py")
        scenario["assertions"]["file_contains"].append({"path": "src/exporter.py", "pattern": "[unclosed"})

        errors = eval_codex_skills.validate_scenarios_data(broken)
        joined = "\n".join(errors)
        self.assertIn("unknown top-level keys", joined)
        self.assertIn("appears to contain a secret", joined)
        self.assertIn("unsafe path '../escape.txt'", joined)
        self.assertIn("overlapping paths in files_must_change and files_must_not_change", joined)
        self.assertIn("invalid regex", joined)
        self.assertIn("missing evaluation scenario for canonical Skill 'investigate-bug'", joined)

    def test_command_mode_passes_when_stub_satisfies_implement_feature(self) -> None:
        data = eval_codex_skills.load_scenarios()
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "stub_agent.py"
            stub.write_text(
                r"""
import os
from pathlib import Path

ws = Path(os.environ["OKF_EVAL_WORKSPACE"])
resp = Path(os.environ["OKF_EVAL_RESPONSE_FILE"])

(ws / "src" / "exporter.py").write_text(
    r'''from __future__ import annotations

from collections.abc import Iterable


def format_csv_row(values: Iterable[object], delimiter: str = ",") -> str:
    formatted: list[str] = []
    for value in values:
        text = "" if value is None else str(value)
        if any(ch in text for ch in (delimiter, '"', "\n", "\r")):
            text = '"' + text.replace('"', '""') + '"'
        formatted.append(text)
    return delimiter.join(formatted)
''',
    encoding="utf-8",
)

(ws / "tests" / "test_exporter.py").write_text(
    '''import unittest

from src.exporter import format_csv_row


class ExporterTests(unittest.TestCase):
    def test_default_comma_formatting(self) -> None:
        self.assertEqual(format_csv_row(["alpha", "beta,gamma"]), 'alpha,"beta,gamma"')

    def test_custom_delimiter(self) -> None:
        self.assertEqual(format_csv_row(["a", "b;c", "d,e"], delimiter=";"), 'a;"b;c";d,e')


if __name__ == "__main__":
    unittest.main()
''',
    encoding="utf-8",
)

(ws / "okf" / "features" / "exporter.md").write_text(
    '''---
type: Feature
title: CSV Row Exporter
description: Formats tabular rows into RFC 4180 style CSV lines with configurable delimiter.
tags: [exporter, csv]
---

# Behavior

`format_csv_row(values, delimiter=",")` serializes a sequence of values using the configured delimiter.
''',
    encoding="utf-8",
)

log_path = ws / "okf" / "log.md"
log_path.write_text(
    log_path.read_text(encoding="utf-8")
    + "\n## 2026-11-22\n\n- **Update**: Documented optional delimiter parameter.\n",
    encoding="utf-8",
)

resp.write_text("Implemented delimiter support and ran unittest successfully.\n", encoding="utf-8")
""",
                encoding="utf-8",
            )

            report = eval_codex_skills.run_suite(
                data,
                mode="command",
                scenario_ids=["implement-feature-csv-delimiter"],
                command_template=f"{{python}} {stub}",
            )
            self.assertEqual(report["summary"]["passed"], 1, eval_codex_skills.format_report(report))
            self.assertEqual(report["summary"]["failed"], 0)
            item = report["scenarios"][0]
            self.assertEqual(item["status"], "passed")
            self.assertEqual(
                item["changed_files"]["modified"],
                ["okf/features/exporter.md", "okf/log.md", "src/exporter.py", "tests/test_exporter.py"],
            )
            self.assertTrue(all(check["passed"] for check in item["checks"]))

    def test_command_mode_diagnoses_guardrail_violation_for_investigate_bug(self) -> None:
        data = eval_codex_skills.load_scenarios()
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "bad_investigator.py"
            stub.write_text(
                r"""
import os
from pathlib import Path

ws = Path(os.environ["OKF_EVAL_WORKSPACE"])
pricing = ws / "src" / "pricing.py"
pricing.write_text(pricing.read_text(encoding="utf-8").replace(">= 100", "> 100"), encoding="utf-8")
print("Fixed src/pricing.py so apply_discount allows 100 (> 100).")
""",
                encoding="utf-8",
            )

            report = eval_codex_skills.run_suite(
                data,
                mode="command",
                scenario_ids=["investigate-bug-hundred-percent-discount"],
                command_template=f"{{python}} {stub}",
            )
            self.assertEqual(report["summary"]["failed"], 1)
            item = report["scenarios"][0]
            self.assertEqual(item["status"], "failed")
            failed_checks = {c["kind"]: c for c in item["checks"] if not c["passed"]}
            self.assertIn("file_unchanged", failed_checks)
            self.assertIn("max_changed_files", failed_checks)

            md = eval_codex_skills.format_report(report, "markdown")
            self.assertIn("### Failure Diagnostics", md)
            self.assertIn("src/pricing.py", md)

    def test_command_mode_evaluates_update_okf_from_git_diff(self) -> None:
        data = eval_codex_skills.load_scenarios()
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "okf_updater.py"
            stub.write_text(
                r"""
import os
import subprocess
from pathlib import Path

ws = Path(os.environ["OKF_EVAL_WORKSPACE"])
resp = Path(os.environ["OKF_EVAL_RESPONSE_FILE"])
diff = subprocess.check_output(["git", "diff"], cwd=ws, text=True)
assert "MAX_RETRIES = 5" in diff

(ws / "okf" / "features" / "http-client.md").write_text(
    '''---
type: Feature
title: HTTP Retry Policy
description: Controls retry count and exponential backoff timing for outbound HTTP requests.
tags: [http, reliability]
---

# Behavior

Outbound HTTP requests retry up to `5` times using exponential backoff (`base_delay * (2 ** (attempt - 1))`).
''',
    encoding="utf-8",
)
log_path = ws / "okf" / "log.md"
log_path.write_text(
    log_path.read_text(encoding="utf-8")
    + "\n## 2026-11-22\n\n- **Update**: Recorded new 5-retry exponential backoff policy.\n",
    encoding="utf-8",
)
resp.write_text("Updated okf/features/http-client.md and okf/log.md from git diff.\n", encoding="utf-8")
""",
                encoding="utf-8",
            )

            report = eval_codex_skills.run_suite(
                data,
                mode="command",
                scenario_ids=["update-okf-retry-policy-diff"],
                command_template=f"{{python}} {stub}",
            )
            self.assertEqual(report["summary"]["passed"], 1, eval_codex_skills.format_report(report))
            item = report["scenarios"][0]
            self.assertEqual(item["status"], "passed")
            self.assertEqual(item["changed_files"]["modified"], ["okf/features/http-client.md", "okf/log.md"])

    def test_secret_redaction_and_json_report_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "leaky_stub.py"
            out_path = Path(tmp) / "report.json"
            stub.write_text(
                r"""
import os
from pathlib import Path

resp = Path(os.environ["OKF_EVAL_RESPONSE_FILE"])
resp.write_text(
    "Found bug in src/pricing.py apply_discount percent >= 100; propose > 100. "
    "token=sk-proj-1234567890abcdefghijklmnop "
    f"env={os.environ.get('OPENAI_API_KEY', '')}\n",
    encoding="utf-8",
)
""",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "custom-secret-value-99999"}):
                with contextlib.redirect_stdout(stdout):
                    exit_code = eval_codex_skills.main(
                        [
                            "--mode",
                            "command",
                            "--scenario",
                            "investigate-bug-hundred-percent-discount",
                            "--command",
                            f"{{python}} {stub}",
                            "--format",
                            "json",
                            "--output",
                            str(out_path),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            written = out_path.read_text(encoding="utf-8")
            self.assertNotIn("sk-proj-1234567890abcdefghijklmnop", written)
            self.assertNotIn("custom-secret-value-99999", written)
            self.assertIn("[REDACTED]", written)
            parsed = json.loads(written)
            self.assertEqual(parsed["summary"]["passed"], 1)

    def test_cli_validate_list_dry_run_and_missing_executable(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(eval_codex_skills.main(["--mode", "validate"]), 0)
        self.assertIn("Validated 5 Codex evaluation scenarios", buf.getvalue())

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(eval_codex_skills.main(["--list", "--format", "json"]), 0)
        listed = json.loads(buf.getvalue())
        self.assertEqual(len(listed["scenarios"]), 5)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(
                eval_codex_skills.main(
                    ["--mode", "dry-run", "--skill", "add-test", "--format", "markdown"]
                ),
                0,
            )
        self.assertIn("add-test-slugify-edge-cases", buf.getvalue())

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = eval_codex_skills.main(
                [
                    "--mode",
                    "command",
                    "--scenario",
                    "add-test-slugify-edge-cases",
                    "--command",
                    "nonexistent-codex-eval-binary-xyz",
                    "--format",
                    "json",
                ]
            )
        self.assertEqual(exit_code, 1)
        parsed = json.loads(buf.getvalue())
        self.assertEqual(parsed["summary"]["error"], 1)
        self.assertIn("executable not found", parsed["scenarios"][0]["runner"]["launch_error"])


if __name__ == "__main__":
    unittest.main()
