#!/usr/bin/env python3
"""Validate Markdown links and Skill frontmatter for this template repo."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
REQUIRED_SKILL_SECTIONS = [
    "## When to use",
    "## Inputs",
    "## Required context",
    "## Workflow",
    "## Guardrails",
    "## Completion checklist",
    "## Expected final response",
]


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts
    )


def validate_links() -> list[str]:
    errors: list[str] = []

    for md_file in markdown_files():
        text = md_file.read_text(encoding="utf-8")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.split("#", 1)[0].strip()
            if not target or URL_RE.match(target):
                continue

            if target.startswith("/"):
                resolved = ROOT / target.lstrip("/")
            else:
                resolved = md_file.parent / target

            if not resolved.resolve().exists():
                errors.append(f"{md_file.relative_to(ROOT)}: missing link target {raw_target}")

    return errors


def skill_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("SKILL.md")
        if ".git" not in path.parts
    )


def frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def validate_skills() -> list[str]:
    errors: list[str] = []

    for skill_file in skill_files():
        text = skill_file.read_text(encoding="utf-8")
        rel = skill_file.relative_to(ROOT)
        metadata = frontmatter(text)

        if metadata is None:
            errors.append(f"{rel}: missing YAML frontmatter")
        else:
            if not re.search(r"^name:\s*\S+", metadata, re.MULTILINE):
                errors.append(f"{rel}: missing frontmatter name")
            if not re.search(r"^description:\s*\S+", metadata, re.MULTILINE):
                errors.append(f"{rel}: missing frontmatter description")

        for section in REQUIRED_SKILL_SECTIONS:
            if section not in text:
                errors.append(f"{rel}: missing section {section}")

    return errors


def main() -> int:
    errors = validate_links() + validate_skills()

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(markdown_files())} Markdown files and {len(skill_files())} Skill files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
