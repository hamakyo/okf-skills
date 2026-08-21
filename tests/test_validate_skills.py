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
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        fixture = Path(temporary.name) / "routing.yaml"
        fixture.write_text(
            "cases:\n"
            "  - id: only-one\n"
            "    category: positive\n"
            "    prompt: Test one skill.\n"
            "    expect: one\n"
            "    reject: []\n",
            encoding="utf-8",
        )
        errors = validate_routing_fixture(fixture, {"one", "two"})
        self.assertTrue(any("missing positive coverage" in error for error in errors))
        self.assertTrue(any("requires at least two overlap" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
