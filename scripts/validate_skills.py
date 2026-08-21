#!/usr/bin/env python3
"""Validate Agent Skills standard constraints and repository profile rules."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

try:
    from validation_utils import non_empty_string, parse_frontmatter
except ImportError:  # pragma: no cover - used when imported as scripts.validate_skills
    from .validation_utils import non_empty_string, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
ROUTING_FIXTURE = ROOT / "evals" / "skill-routing.yaml"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROFILE_SECTIONS = [
    "## When to use",
    "## Inputs",
    "## Required context",
    "## Workflow",
    "## Guardrails",
    "## Completion checklist",
    "## Expected final response",
]


def validate_skill(skill_file: Path, root: Path = ROOT) -> list[str]:
    try:
        rel = str(skill_file.relative_to(root))
    except ValueError:
        rel = str(skill_file)
    metadata, body, error = parse_frontmatter(skill_file)
    if error:
        return [f"{rel}: [Agent Skills standard] {error}"]
    if metadata is None:
        return [f"{rel}: [Agent Skills standard] missing YAML frontmatter"]

    errors: list[str] = []
    name = metadata.get("name")
    if not non_empty_string(name):
        errors.append(f"{rel}: [Agent Skills standard] name is required")
    elif len(name) > 64 or not NAME_RE.fullmatch(name):
        errors.append(f"{rel}: [Agent Skills standard] name must be 1-64 lowercase letters, numbers, or single hyphens")
    elif name != skill_file.parent.name:
        errors.append(f"{rel}: [Agent Skills standard] name must match parent directory {skill_file.parent.name!r}")

    description = metadata.get("description")
    if not non_empty_string(description):
        errors.append(f"{rel}: [Agent Skills standard] description is required")
    elif len(description) > 1024:
        errors.append(f"{rel}: [Agent Skills standard] description must be at most 1024 characters")

    compatibility = metadata.get("compatibility")
    if compatibility is not None and (not non_empty_string(compatibility) or len(compatibility) > 500):
        errors.append(f"{rel}: [Agent Skills standard] compatibility must be a non-empty string of at most 500 characters")
    skill_metadata = metadata.get("metadata")
    if skill_metadata is not None and (
        not isinstance(skill_metadata, dict)
        or any(not isinstance(key, str) or not isinstance(value, str) for key, value in skill_metadata.items())
    ):
        errors.append(f"{rel}: [Agent Skills standard] metadata must map strings to strings")
    allowed_tools = metadata.get("allowed-tools")
    if allowed_tools is not None and not non_empty_string(allowed_tools):
        errors.append(f"{rel}: [Agent Skills standard] allowed-tools must be a non-empty string")

    if not body.strip():
        errors.append(f"{rel}: [Agent Skills standard] Markdown instructions are required")
        return errors

    lines = body.splitlines()
    positions: list[int] = []
    for section in PROFILE_SECTIONS:
        if section not in lines:
            errors.append(f"{rel}: [Skill authoring profile] missing section {section}")
        else:
            positions.append(lines.index(section))
    if len(positions) == len(PROFILE_SECTIONS) and positions != sorted(positions):
        errors.append(f"{rel}: [Skill authoring profile] required sections are out of order")
    if not any(line.startswith("# ") for line in lines):
        errors.append(f"{rel}: [Skill authoring profile] missing Skill title heading")
    return errors


def skill_files(root: Path = ROOT) -> list[Path]:
    return sorted(path for path in root.rglob("SKILL.md") if ".git" not in path.parts)


def canonical_skill_names(root: Path = ROOT) -> set[str]:
    return {path.name for path in (root / "skills").iterdir() if (path / "SKILL.md").is_file()}


def validate_routing_fixture(path: Path, skill_names: set[str]) -> list[str]:
    rel = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"{rel}: [Skill routing fixture] cannot load fixture: {exc}"]
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        return [f"{rel}: [Skill routing fixture] requires a cases list"]

    errors: list[str] = []
    seen_ids: set[str] = set()
    positive: set[str] = set()
    rejected: set[str] = set()
    overlap_count = 0
    for index, case in enumerate(data["cases"]):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{rel}: [Skill routing fixture] {prefix} must be a mapping")
            continue
        case_id = case.get("id")
        if not non_empty_string(case_id):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.id is required")
        elif case_id in seen_ids:
            errors.append(f"{rel}: [Skill routing fixture] duplicate id {case_id!r}")
        else:
            seen_ids.add(case_id)
        category = case.get("category")
        if not isinstance(category, str) or category not in {"positive", "negative", "overlap"}:
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.category is invalid")
        if category == "overlap":
            overlap_count += 1
        if not non_empty_string(case.get("prompt")):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.prompt is required")
        expected = case.get("expect")
        if expected is not None and (not isinstance(expected, str) or expected not in skill_names):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.expect references unknown Skill {expected!r}")
        elif category == "positive" and expected is not None:
            positive.add(expected)
        reject = case.get("reject")
        if not isinstance(reject, list) or any(not isinstance(item, str) or item not in skill_names for item in reject):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.reject must list known Skills")
        else:
            rejected.update(reject)
            if expected in reject:
                errors.append(f"{rel}: [Skill routing fixture] {prefix} cannot expect and reject the same Skill")

    missing_positive = skill_names - positive
    if missing_positive:
        errors.append(f"{rel}: [Skill routing fixture] missing positive coverage for {sorted(missing_positive)}")
    missing_negative = skill_names - rejected
    if missing_negative:
        errors.append(f"{rel}: [Skill routing fixture] missing negative coverage for {sorted(missing_negative)}")
    if overlap_count < 2:
        errors.append(f"{rel}: [Skill routing fixture] requires at least two overlap cases")
    return errors


def main() -> int:
    files = skill_files()
    errors = [error for path in files for error in validate_skill(path)]
    errors.extend(validate_routing_fixture(ROUTING_FIXTURE, canonical_skill_names()))
    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated {len(files)} Skill files and the routing fixture against the standard and repository profile.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
