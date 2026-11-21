from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import sync_adapters


class SyncAdaptersTests(unittest.TestCase):
    def test_repository_adapters_are_in_sync_and_valid(self) -> None:
        errors, _ = sync_adapters.synchronize(sync_adapters.ROOT, sync_adapters.DEFAULT_MANIFEST, check=True)
        self.assertEqual(errors, [])

        codex_manifest = json.loads(
            (sync_adapters.ROOT / "adapters" / "codex" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(codex_manifest["name"], "okf-skills")
        self.assertEqual(codex_manifest["skills"], "./skills")
        self.assertNotIn("..", codex_manifest["skills"])

        claude_manifest = json.loads(
            (sync_adapters.ROOT / "adapters" / "claude-code" / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(claude_manifest["name"], "okf-skills")
        self.assertFalse((sync_adapters.ROOT / "adapters" / "claude-code" / "CLAUDE.md").exists())

        canonical = sorted(p.parent.name for p in (sync_adapters.ROOT / "skills").glob("*/SKILL.md"))
        for skill_name in canonical:
            openai_yaml_path = (
                sync_adapters.ROOT / "adapters" / "codex" / "skills" / skill_name / "agents" / "openai.yaml"
            )
            self.assertTrue(openai_yaml_path.is_file())
            parsed = yaml.safe_load(openai_yaml_path.read_text(encoding="utf-8"))
            self.assertTrue(parsed["interface"]["display_name"])
            self.assertTrue(parsed["interface"]["short_description"])
            self.assertIsInstance(parsed["policy"]["allow_implicit_invocation"], bool)

    def test_detects_drift_in_skill_metadata_and_undeclared_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(sync_adapters.ROOT / "skills", root / "skills")
            (root / "adapters").mkdir(parents=True, exist_ok=True)
            manifest = root / "adapters" / "manifest.yaml"
            shutil.copyfile(sync_adapters.DEFAULT_MANIFEST, manifest)

            errors, written = sync_adapters.synchronize(root, manifest, check=False)
            self.assertEqual(errors, [])
            self.assertEqual(written, 17)

            check_errors, _ = sync_adapters.synchronize(root, manifest, check=True)
            self.assertEqual(check_errors, [])

            # Drift 1: modify generated SKILL.md
            drifted_skill = root / "adapters" / "codex" / "skills" / "add-test" / "SKILL.md"
            drifted_skill.write_text(drifted_skill.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")

            # Drift 2: modify generated agents/openai.yaml
            drifted_yaml = root / "adapters" / "codex" / "skills" / "add-test" / "agents" / "openai.yaml"
            drifted_yaml.write_text("interface: {}\n", encoding="utf-8")

            # Drift 3: modify generated Claude plugin.json
            drifted_json = root / "adapters" / "claude-code" / ".claude-plugin" / "plugin.json"
            drifted_json.write_text("{}\n", encoding="utf-8")

            # Drift 4: undeclared extra Skill directory
            extra_skill = root / "adapters" / "claude-code" / "skills" / "undeclared-skill" / "SKILL.md"
            extra_skill.parent.mkdir(parents=True, exist_ok=True)
            extra_skill.write_text("---\nname: undeclared-skill\ndescription: extra\n---\n", encoding="utf-8")

            drift_errors, _ = sync_adapters.synchronize(root, manifest, check=True)
            joined = "\n".join(drift_errors)
            self.assertIn("adapters/codex/skills/add-test/SKILL.md", joined)
            self.assertIn("adapters/codex/skills/add-test/agents/openai.yaml", joined)
            self.assertIn("adapters/claude-code/.claude-plugin/plugin.json", joined)
            self.assertIn("undeclared Claude Code adapter Skill copy", joined)

    def test_rejects_path_traversal_and_invalid_hex_color(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(sync_adapters.ROOT / "skills", root / "skills")
            manifest = root / "adapters" / "manifest.yaml"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            data = yaml.safe_load(sync_adapters.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
            data["adapters"]["claude_code"]["directory"] = "../outside"
            data["adapters"]["codex"]["skills"]["add-test"]["brand_color"] = "blue"
            manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

            errors, _ = sync_adapters.synchronize(root, manifest, check=True)
            joined = "\n".join(errors)
            self.assertIn("must be a safe relative POSIX path", joined)
            self.assertIn("brand_color must be a 6-digit hex color", joined)


if __name__ == "__main__":
    unittest.main()
