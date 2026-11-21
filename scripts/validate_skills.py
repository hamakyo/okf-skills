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
ROUTING_SCHEMA_VERSION = 1
ROUTING_TOP_KEYS = {"schema_version", "cases"}
ROUTING_CASE_KEYS = {"id", "category", "prompt", "expect", "reject", "rationale"}
ROUTING_CATEGORIES = {"positive", "negative", "overlap", "ambiguous"}
BOUNDARY_CATEGORIES = {"overlap", "ambiguous"}
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
    unknown_top = set(data) - ROUTING_TOP_KEYS
    if unknown_top:
        errors.append(f"{rel}: [Skill routing fixture] unknown top-level keys {sorted(unknown_top)}")
    if "schema_version" in data:
        version = data["schema_version"]
        if isinstance(version, bool) or version != ROUTING_SCHEMA_VERSION:
            errors.append(
                f"{rel}: [Skill routing fixture] schema_version must equal {ROUTING_SCHEMA_VERSION}"
            )

    seen_ids: set[str] = set()
    seen_prompts: set[str] = set()
    positive: set[str] = set()
    rejected: set[str] = set()
    boundary_covered: set[str] = set()
    negative_count = 0
    overlap_count = 0

    for index, case in enumerate(data["cases"]):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{rel}: [Skill routing fixture] {prefix} must be a mapping")
            continue

        unknown_keys = set(case) - ROUTING_CASE_KEYS
        if unknown_keys:
            errors.append(f"{rel}: [Skill routing fixture] {prefix} has unknown keys {sorted(unknown_keys)}")

        case_id = case.get("id")
        if not non_empty_string(case_id):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.id is required")
        elif not NAME_RE.fullmatch(case_id):
            errors.append(
                f"{rel}: [Skill routing fixture] {prefix}.id must use lowercase letters, numbers, and single hyphens"
            )
        elif case_id in seen_ids:
            errors.append(f"{rel}: [Skill routing fixture] duplicate id {case_id!r}")
        else:
            seen_ids.add(case_id)

        category = case.get("category")
        if not isinstance(category, str) or category not in ROUTING_CATEGORIES:
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.category is invalid")
        if category == "negative":
            negative_count += 1
        if category in BOUNDARY_CATEGORIES:
            overlap_count += 1

        prompt = case.get("prompt")
        if not non_empty_string(prompt):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.prompt is required")
        else:
            normalized_prompt = " ".join(prompt.split()).lower()
            if normalized_prompt in seen_prompts:
                errors.append(f"{rel}: [Skill routing fixture] {prefix}.prompt duplicates another case prompt")
            else:
                seen_prompts.add(normalized_prompt)

        if "rationale" in case and not non_empty_string(case["rationale"]):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.rationale must be a non-empty string")

        has_expect = "expect" in case
        expected = case.get("expect")
        if not has_expect:
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.expect is required")
        elif expected is not None and (not isinstance(expected, str) or expected not in skill_names):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.expect references unknown Skill {expected!r}")
        else:
            if category == "positive":
                if expected is None:
                    errors.append(f"{rel}: [Skill routing fixture] {prefix}.expect must name a Skill for positive cases")
                else:
                    positive.add(expected)
            elif category == "negative" and expected is not None:
                errors.append(f"{rel}: [Skill routing fixture] {prefix}.expect must be null for negative cases")
            elif category in BOUNDARY_CATEGORIES:
                if expected is None:
                    errors.append(
                        f"{rel}: [Skill routing fixture] {prefix}.expect must name a Skill for {category} cases"
                    )
                else:
                    boundary_covered.add(expected)

        reject = case.get("reject")
        if not isinstance(reject, list) or any(not isinstance(item, str) or item not in skill_names for item in reject):
            errors.append(f"{rel}: [Skill routing fixture] {prefix}.reject must list known Skills")
        else:
            if len(set(reject)) != len(reject):
                errors.append(f"{rel}: [Skill routing fixture] {prefix}.reject must not contain duplicates")
            rejected.update(reject)
            if expected is not None and expected in reject:
                errors.append(f"{rel}: [Skill routing fixture] {prefix} cannot expect and reject the same Skill")
            if category == "negative" and not reject:
                errors.append(f"{rel}: [Skill routing fixture] {prefix}.reject must be non-empty for negative cases")
            if category in BOUNDARY_CATEGORIES:
                if not reject:
                    errors.append(
                        f"{rel}: [Skill routing fixture] {prefix}.reject must list at least one competing Skill for {category} cases"
                    )
                boundary_covered.update(reject)

    missing_positive = skill_names - positive
    if missing_positive:
        errors.append(f"{rel}: [Skill routing fixture] missing positive coverage for {sorted(missing_positive)}")
    missing_negative = skill_names - rejected
    if missing_negative:
        errors.append(f"{rel}: [Skill routing fixture] missing negative coverage for {sorted(missing_negative)}")
    if negative_count < 1:
        errors.append(f"{rel}: [Skill routing fixture] requires at least one negative case with expect: null")
    if overlap_count < 2:
        errors.append(f"{rel}: [Skill routing fixture] requires at least two overlap/ambiguous cases")
    if len(skill_names) >= 2:
        missing_boundary = skill_names - boundary_covered
        if missing_boundary:
            errors.append(
                f"{rel}: [Skill routing fixture] missing overlap/ambiguous coverage for {sorted(missing_boundary)}"
            )
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
