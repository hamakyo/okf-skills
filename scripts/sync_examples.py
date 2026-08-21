#!/usr/bin/env python3
"""Synchronize selected example Skills from the canonical skills directory."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "examples" / "skill-copies.yaml"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def load_manifest(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [], [f"{path}: invalid copy manifest: {exc}"]
    if not isinstance(data, dict) or not isinstance(data.get("targets"), list):
        return [], [f"{path}: copy manifest requires a targets list"]
    return data["targets"], []


def synchronize(root: Path, manifest: Path, check: bool) -> tuple[list[str], int]:
    targets, errors = load_manifest(manifest)
    if errors:
        return errors, 0

    copied = 0
    for target_index, target in enumerate(targets):
        if not isinstance(target, dict):
            errors.append(f"{manifest}: targets[{target_index}] must be a mapping")
            continue
        directory = target.get("directory")
        skills = target.get("skills")
        if not isinstance(directory, str) or not directory.strip():
            errors.append(f"{manifest}: targets[{target_index}].directory must be a non-empty string")
            continue
        if (
            not isinstance(skills, list)
            or not skills
            or any(not isinstance(name, str) or not SKILL_NAME_RE.fullmatch(name) for name in skills)
        ):
            errors.append(f"{manifest}: targets[{target_index}].skills must contain valid Skill names")
            continue

        target_root = root / directory
        if not within_root(target_root, root):
            errors.append(f"{manifest}: target directory escapes repository root: {directory}")
            continue

        declared = set(skills)
        if target_root.exists():
            actual = {path.parent.name for path in target_root.glob("*/SKILL.md")}
            for extra in sorted(actual - declared):
                errors.append(f"{target_root / extra / 'SKILL.md'}: undeclared example Skill copy")

        for name in skills:
            source = root / "skills" / name / "SKILL.md"
            destination = target_root / name / "SKILL.md"
            if not source.is_file():
                errors.append(f"{source}: canonical Skill is missing")
                continue
            if not within_root(destination, root):
                errors.append(f"{destination}: example Skill destination escapes repository root")
                continue
            if check:
                if not destination.is_file():
                    errors.append(f"{destination}: example Skill copy is missing")
                elif source.read_bytes() != destination.read_bytes():
                    errors.append(f"{destination}: example Skill copy differs from {source}")
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                copied += 1
    return errors, copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    errors, copied = synchronize(ROOT, args.manifest.resolve(), args.check)
    if errors:
        print("Example Skill synchronization failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.check:
        print("Example Skill copies match the canonical source.")
    else:
        print(f"Synchronized {copied} example Skill copies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
