from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_skills import PROFILE_SECTIONS, validate_routing_fixture, validate_skill


class ValidateSkillsTests(unittest.TestCase):
    def make_skill(self, directory: str, name: str, description: str = "Use for tests.") -> tuple[Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        skill_dir = root / directory
        skill_dir.mkdir()
        body = "# Test Skill\n\n" + "\n\n".join(PROFILE_SECTIONS) + "\n"
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n{body}", encoding="utf-8"
        )
        return skill_file, root

    def make_fixture(self, content: str) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        fixture = Path(temporary.name) / "routing.yaml"
        fixture.write_text(content, encoding="utf-8")
        return fixture

    def test_accepts_standard_and_profile(self) -> None:
        skill_file, root = self.make_skill("test-skill", "test-skill")
        self.assertEqual([], validate_skill(skill_file, root))

    def test_rejects_name_directory_mismatch(self) -> None:
        skill_file, root = self.make_skill("test-skill", "other-skill")
        errors = validate_skill(skill_file, root)
        self.assertTrue(any("must match parent directory" in error for error in errors))

    def test_rejects_profile_section_omission(self) -> None:
        skill_file, root = self.make_skill("test-skill", "test-skill")
        text = skill_file.read_text(encoding="utf-8").replace("## Guardrails", "## Safety")
        skill_file.write_text(text, encoding="utf-8")
        errors = validate_skill(skill_file, root)
        self.assertTrue(any("missing section ## Guardrails" in error for error in errors))

    def test_rejects_incomplete_routing_coverage(self) -> None:
        fixture = self.make_fixture(
            "cases:\n"
            "  - id: only-one\n"
            "    category: positive\n"
            "    prompt: Test one skill.\n"
            "    expect: one\n"
            "    reject: []\n"
        )
        errors = validate_routing_fixture(fixture, {"one", "two"})
        self.assertTrue(any("missing positive coverage" in error for error in errors))
        self.assertTrue(any("requires at least two overlap" in error for error in errors))
        self.assertTrue(any("requires at least one negative case" in error for error in errors))

    def test_accepts_complete_routing_fixture_with_ambiguous_category(self) -> None:
        fixture = self.make_fixture(
            "schema_version: 1\n"
            "cases:\n"
            "  - id: one-positive\n"
            "    category: positive\n"
            "    prompt: Run workflow one.\n"
            "    expect: one\n"
            "    reject: [two]\n"
            "    rationale: Clearly workflow one.\n"
            "  - id: two-positive\n"
            "    category: positive\n"
            "    prompt: Run workflow two.\n"
            "    expect: two\n"
            "    reject: [one]\n"
            "  - id: boundary-one-vs-two\n"
            "    category: ambiguous\n"
            "    prompt: Looks like two but is actually one.\n"
            "    expect: one\n"
            "    reject: [two]\n"
            "  - id: boundary-two-vs-one\n"
            "    category: overlap\n"
            "    prompt: Looks like one but is actually two.\n"
            "    expect: two\n"
            "    reject: [one]\n"
            "  - id: none-negative\n"
            "    category: negative\n"
            "    prompt: Just answer a read-only question.\n"
            "    expect: null\n"
            "    reject: [one, two]\n"
        )
        self.assertEqual([], validate_routing_fixture(fixture, {"one", "two"}))

    def test_rejects_malformed_routing_fixture_fields(self) -> None:
        fixture = self.make_fixture(
            "schema_version: 2\n"
            "extra_top: true\n"
            "cases:\n"
            "  - id: Bad_ID\n"
            "    category: positive\n"
            "    prompt: Duplicate prompt.\n"
            "    expect: null\n"
            "    reject: [one, one]\n"
            "    rationale: ''\n"
            "    unknown_field: 1\n"
            "  - id: neg-with-expect\n"
            "    category: negative\n"
            "    prompt: '  duplicate   prompt. '\n"
            "    expect: one\n"
            "    reject: []\n"
            "  - id: overlap-empty-reject\n"
            "    category: overlap\n"
            "    prompt: Boundary without reject.\n"
            "    expect: null\n"
            "    reject: []\n"
        )
        errors = validate_routing_fixture(fixture, {"one", "two"})
        self.assertTrue(any("unknown top-level keys" in e for e in errors))
        self.assertTrue(any("schema_version must equal 1" in e for e in errors))
        self.assertTrue(any("unknown keys" in e for e in errors))
        self.assertTrue(any("lowercase letters, numbers, and single hyphens" in e for e in errors))
        self.assertTrue(any("expect must name a Skill for positive cases" in e for e in errors))
        self.assertTrue(any("reject must not contain duplicates" in e for e in errors))
        self.assertTrue(any("rationale must be a non-empty string" in e for e in errors))
        self.assertTrue(any("duplicates another case prompt" in e for e in errors))
        self.assertTrue(any("expect must be null for negative cases" in e for e in errors))
        self.assertTrue(any("reject must be non-empty for negative cases" in e for e in errors))
        self.assertTrue(any("expect must name a Skill for overlap cases" in e for e in errors))
        self.assertTrue(any("reject must list at least one competing Skill" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
