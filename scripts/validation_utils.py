"""Shared helpers for deterministic Markdown frontmatter validation."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

FULL_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    """Return metadata, Markdown body, and an error message when parsing fails."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None, text, None

    try:
        closing = lines.index("---", 1)
    except ValueError:
        return None, text, "unterminated YAML frontmatter"

    raw_metadata = "\n".join(lines[1:closing])
    try:
        loaded = yaml.safe_load(raw_metadata)
    except yaml.YAMLError as exc:
        detail = str(exc).splitlines()[0]
        return None, text, f"invalid YAML frontmatter: {detail}"

    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        return None, text, "YAML frontmatter must be a mapping"

    body = "\n".join(lines[closing + 1 :]).lstrip("\n")
    return loaded, body, None


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def aware_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        if FULL_DATE_RE.fullmatch(value):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00").replace("z", "+00:00"))
        except ValueError:
            return None
    else:
        return None

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def okf_timestamp(value: Any) -> datetime | None:
    """Parse an OKF v0.3 RFC 3339 timestamp (offset-aware date-time or full-date)."""
    if isinstance(value, datetime):
        return aware_datetime(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if isinstance(value, str):
        if FULL_DATE_RE.fullmatch(value):
            try:
                parsed_date = date.fromisoformat(value)
            except ValueError:
                return None
            return datetime(parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=timezone.utc)
        return aware_datetime(value)
    return None
