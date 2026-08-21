#!/usr/bin/env python3
"""Validate local Markdown links for this template repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
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


def main() -> int:
    errors = validate_links()

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated local links in {len(markdown_files())} Markdown files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
