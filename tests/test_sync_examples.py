from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.sync_examples import synchronize


class SyncExamplesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        canonical = self.root / "skills" / "example" / "SKILL.md"
        canonical.parent.mkdir(parents=True)
        canonical.write_text("canonical\n", encoding="utf-8")
        self.manifest = self.root / "examples" / "skill-copies.yaml"
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text(
            "targets:\n  - directory: examples/minimal/skills\n    skills: [example]\n",
            encoding="utf-8",
        )

    def test_sync_then_check(self) -> None:
        errors, copied = synchronize(self.root, self.manifest, check=False)
        self.assertEqual([], errors)
        self.assertEqual(1, copied)
        errors, _copied = synchronize(self.root, self.manifest, check=True)
        self.assertEqual([], errors)

    def test_detects_drift(self) -> None:
        synchronize(self.root, self.manifest, check=False)
        destination = self.root / "examples" / "minimal" / "skills" / "example" / "SKILL.md"
        destination.write_text("drift\n", encoding="utf-8")
        errors, _copied = synchronize(self.root, self.manifest, check=True)
        self.assertTrue(any("differs" in error for error in errors))

    def test_rejects_skill_path_traversal(self) -> None:
        self.manifest.write_text(
            "targets:\n  - directory: examples/minimal/skills\n    skills: [../../outside]\n",
            encoding="utf-8",
        )
        errors, _copied = synchronize(self.root, self.manifest, check=False)
        self.assertTrue(any("valid Skill names" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
