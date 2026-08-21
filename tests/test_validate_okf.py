from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_okf import validate_bundle


class ValidateOkfTests(unittest.TestCase):
    def make_bundle(self, concept_frontmatter: str) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        bundle = Path(temporary.name) / "okf"
        bundle.mkdir()
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.2"\n---\n\n# Knowledge\n', encoding="utf-8"
        )
        (bundle / "log.md").write_text(
            "# Log\n\n## 2026-08-21\n\n- **Update**: Test.\n", encoding="utf-8"
        )
        (bundle / "concept.md").write_text(
            f"---\n{concept_frontmatter}\n---\n\n# Concept\n", encoding="utf-8"
        )
        return bundle

    def test_accepts_v02_metadata(self) -> None:
        bundle = self.make_bundle(
            "\n".join(
                [
                    "type: Feature",
                    "sources:",
                    "  - resource: ../requirements.md",
                    "generated: { by: tool/1.0, at: 2026-08-21T09:00:00Z }",
                    "verified: { by: human:reviewer, at: 2026-08-21T10:00:00Z }",
                    "status: stable",
                    "stale_after: 2026-12-31T00:00:00Z",
                ]
            )
        )
        errors, count = validate_bundle(bundle)
        self.assertEqual([], errors)
        self.assertEqual(3, count)

    def test_rejects_legacy_timestamp(self) -> None:
        bundle = self.make_bundle("type: Feature\ntimestamp: 2026-08-21T09:00:00Z")
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("legacy timestamp" in error for error in errors))

    def test_rejects_missing_generated_at_and_naive_staleness(self) -> None:
        bundle = self.make_bundle(
            "type: Feature\ngenerated: { by: tool/1.0 }\nstale_after: 2026-12-31T00:00:00"
        )
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("generated.at is required" in error for error in errors))
        self.assertTrue(any("stale_after must be" in error for error in errors))

    def test_rejects_invalid_log_heading(self) -> None:
        bundle = self.make_bundle("type: Feature")
        (bundle / "log.md").write_text("# Log\n\n## Unreleased\n", encoding="utf-8")
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("invalid log date heading" in error for error in errors))

    def test_rejects_invalid_status_type(self) -> None:
        bundle = self.make_bundle("type: Feature\nstatus: [stable]")
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("status must be one of" in error for error in errors))

    def test_requires_root_index(self) -> None:
        bundle = self.make_bundle("type: Feature")
        (bundle / "index.md").unlink()
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("root index.md is required" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
