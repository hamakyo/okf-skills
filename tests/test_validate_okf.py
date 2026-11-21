from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_okf import validate_bundle


class ValidateOkfTests(unittest.TestCase):
    def make_bundle(self, concept_frontmatter: str, root_index_frontmatter: str | None = None) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        bundle = Path(temporary.name) / "okf"
        bundle.mkdir()
        index_meta = root_index_frontmatter or 'okf_version: "0.3"'
        (bundle / "index.md").write_text(
            f"---\n{index_meta}\n---\n\n# Knowledge\n", encoding="utf-8"
        )
        (bundle / "log.md").write_text(
            "# Log\n\n## 2026-08-21\n\n- **Update**: Test.\n", encoding="utf-8"
        )
        (bundle / "concept.md").write_text(
            f"---\n{concept_frontmatter}\n---\n\n# Concept\n", encoding="utf-8"
        )
        return bundle

    def test_accepts_v03_metadata_and_root_bundle_metadata(self) -> None:
        bundle = self.make_bundle(
            "\n".join(
                [
                    "type: Feature",
                    "sources:",
                    "  - resource: ../requirements.md",
                    '    last_modified: "2026-05-30T00:00:00Z"',
                    'usage_window: { from: "2026-06-01T00:00:00Z", to: "2026-06-30T00:00:00Z" }',
                    'generated: { by: tool/1.0, at: "2026-08-21T09:00:00Z" }',
                    'verified: { by: "human:reviewer", at: "2026-08-21T10:00:00Z" }',
                    "status: deprecated",
                    "superseded_by: /features/v2.md",
                    'stale_after: "2026-12-31T00:00:00Z"',
                    "x-example-owner: team:platform",
                ]
            ),
            root_index_frontmatter="\n".join(
                [
                    'okf_version: "0.3"',
                    "title: Example Bundle",
                    "description: Bundle scope summary for agent discovery.",
                    "license: MIT",
                    "x-example-channel: stable",
                ]
            ),
        )
        errors, count = validate_bundle(bundle)
        self.assertEqual([], errors)
        self.assertEqual(3, count)

    def test_accepts_v03_date_only_timestamp_fields(self) -> None:
        bundle = self.make_bundle(
            "\n".join(
                [
                    "type: Feature",
                    "sources:",
                    "  - resource: ../requirements.md",
                    '    last_modified: "2026-05-30"',
                    'usage_window: { from: "2026-06-01", to: "2026-06-30" }',
                    'stale_after: "2026-12-31"',
                ]
            )
        )
        errors, _count = validate_bundle(bundle)
        self.assertEqual([], errors)

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
        self.assertTrue(any("[OKF v0.3] stale_after must be" in error for error in errors))

    def test_rejects_offsetless_trust_timestamps_as_upstream_errors(self) -> None:
        bundle = self.make_bundle(
            "type: Feature\n"
            "generated: { by: tool/1.0, at: '2026-08-21T09:00:00' }\n"
            "verified: { by: human:reviewer, at: '2026-08-21T10:00:00' }"
        )
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("[OKF v0.3] generated.at must be" in error for error in errors))
        self.assertTrue(any("[OKF v0.3] verified[0].at must be" in error for error in errors))

    def test_rejects_superseded_by_without_deprecated_status(self) -> None:
        bundle = self.make_bundle("type: Feature\nstatus: stable\nsuperseded_by: /features/v2.md")
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("superseded_by is only valid with status: deprecated" in error for error in errors))

    def test_rejects_invalid_log_heading(self) -> None:
        bundle = self.make_bundle("type: Feature")
        (bundle / "log.md").write_text("# Log\n\n## Unreleased\n", encoding="utf-8")
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("invalid log date heading" in error for error in errors))

    def test_rejects_invalid_status_type(self) -> None:
        bundle = self.make_bundle("type: Feature\nstatus: [stable]")
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("status must be a non-empty string" in error for error in errors))

    def test_requires_root_index(self) -> None:
        bundle = self.make_bundle("type: Feature")
        (bundle / "index.md").unlink()
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("root index.md is required" in error for error in errors))

    def test_accepts_team_and_custom_scheme_actors(self) -> None:
        bundle = self.make_bundle(
            "\n".join(
                [
                    "type: Feature",
                    "sources:",
                    "  - resource: ../requirements.md",
                    '    author: "team:ga4-docs"',
                    'generated: { by: "bot:doc-sync", at: "2026-08-21T09:00:00Z" }',
                    'verified: { by: "team:finance-fpa", at: "2026-08-21T10:00:00Z" }',
                ]
            )
        )
        errors, _count = validate_bundle(bundle)
        self.assertEqual([], errors)

    def test_rejects_invalid_actor(self) -> None:
        bundle = self.make_bundle(
            "type: Feature\n"
            "generated: { by: 'team:', at: '2026-08-21T09:00:00Z' }\n"
            "verified: { by: unknown-actor, at: '2026-08-21T10:00:00Z' }"
        )
        errors, _count = validate_bundle(bundle)
        self.assertTrue(any("generated.by must use" in error for error in errors))
        self.assertTrue(any("verified[0].by must use" in error for error in errors))

    def test_ignores_dot_paths_and_tolerates_attested_computation_fields(self) -> None:
        bundle = self.make_bundle(
            "\n".join(
                [
                    "type: Attested Computation",
                    "runtime: python/3.13",
                    "parameters:",
                    "  - { name: window_days, type: integer, required: true }",
                    "executor:",
                    "  resource: https://example.com/runner",
                    "attester:",
                    "  resource: https://example.com/attester",
                ]
            )
        )
        hidden_dir = bundle / ".internal"
        hidden_dir.mkdir()
        (hidden_dir / "notes.md").write_text("# Not part of bundle\n", encoding="utf-8")
        errors, count = validate_bundle(bundle)
        self.assertEqual([], errors)
        self.assertEqual(3, count)


if __name__ == "__main__":
    unittest.main()
