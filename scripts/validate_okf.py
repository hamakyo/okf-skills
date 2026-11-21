#!/usr/bin/env python3
"""Validate maintained OKF v0.3 bundles and repository profile rules."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    from validation_utils import non_empty_string, okf_timestamp, parse_frontmatter
except ImportError:  # pragma: no cover - used when imported as scripts.validate_okf
    from .validation_utils import non_empty_string, okf_timestamp, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLES = [ROOT / "okf", ROOT / "examples" / "minimal" / "okf"]
RESERVED = {"index.md", "log.md"}
DATE_HEADING_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})$")
ACTOR_RE = re.compile(r"^(?:[a-z][a-z0-9_-]*:[^\s:]+|[^\s/:]+/[^\s/:]+)$")
STATUS_VALUES = {"draft", "stable", "deprecated"}
ROOT_INDEX_STRING_KEYS = ("title", "description", "license")


def label(path: Path, bundle: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path.relative_to(bundle))


def validate_actor(value: Any, field: str, rel: str) -> list[str]:
    if not non_empty_string(value) or not ACTOR_RE.fullmatch(value):
        return [f"{rel}: [OKF v0.3] {field} must use <producer>/<version> or <scheme>:<id> (such as human:, team:, or process:)"]
    return []


def validate_timestamp(value: Any, field: str, rel: str) -> list[str]:
    if okf_timestamp(value) is None:
        return [f"{rel}: [OKF v0.3] {field} must be an RFC 3339 date-time with an explicit UTC offset or a YYYY-MM-DD full-date"]
    return []


def validate_usage_window(value: Any, field: str, rel: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{rel}: [OKF v0.3] {field} must be a mapping"]
    errors: list[str] = []
    for endpoint in ("from", "to"):
        if endpoint not in value:
            errors.append(f"{rel}: [OKF v0.3] {field}.{endpoint} is required")
        else:
            errors.extend(validate_timestamp(value[endpoint], f"{field}.{endpoint}", rel))
    start = okf_timestamp(value.get("from"))
    end = okf_timestamp(value.get("to"))
    if start is not None and end is not None and start > end:
        errors.append(f"{rel}: [OKF v0.3] {field}.from must not be after {field}.to")
    return errors


def validate_metadata(metadata: dict[str, Any], rel: str) -> list[str]:
    errors: list[str] = []
    if not non_empty_string(metadata.get("type")):
        errors.append(f"{rel}: [OKF v0.3] concept frontmatter requires a non-empty type")

    if "timestamp" in metadata:
        errors.append(f"{rel}: [software-project profile] legacy timestamp is superseded by generated.at")

    if "sources" in metadata:
        sources = metadata["sources"]
        if not isinstance(sources, list):
            errors.append(f"{rel}: [OKF v0.3] sources must be a list")
        else:
            for index, entry in enumerate(sources):
                prefix = f"sources[{index}]"
                if not isinstance(entry, dict):
                    errors.append(f"{rel}: [OKF v0.3] {prefix} must be a mapping")
                    continue
                if not non_empty_string(entry.get("resource")):
                    errors.append(f"{rel}: [OKF v0.3] {prefix}.resource is required")
                for key in ("id", "title"):
                    if key in entry and not non_empty_string(entry[key]):
                        errors.append(f"{rel}: [OKF v0.3] {prefix}.{key} must be a non-empty string")
                if "author" in entry:
                    errors.extend(validate_actor(entry["author"], f"{prefix}.author", rel))
                if "usage_count" in entry:
                    usage_count = entry["usage_count"]
                    if isinstance(usage_count, bool) or not isinstance(usage_count, int) or usage_count < 0:
                        errors.append(f"{rel}: [OKF v0.3] {prefix}.usage_count must be a non-negative integer")
                if "last_modified" in entry:
                    errors.extend(validate_timestamp(entry["last_modified"], f"{prefix}.last_modified", rel))
                if "usage_window" in entry:
                    errors.extend(validate_usage_window(entry["usage_window"], f"{prefix}.usage_window", rel))

    if "usage_window" in metadata:
        errors.extend(validate_usage_window(metadata["usage_window"], "usage_window", rel))

    generated = metadata.get("generated")
    if generated is not None:
        if not isinstance(generated, dict):
            errors.append(f"{rel}: [OKF v0.3] generated must be a mapping")
        else:
            errors.extend(validate_actor(generated.get("by"), "generated.by", rel))
            if "at" not in generated:
                errors.append(f"{rel}: [software-project profile] generated.at is required when generated is present")
            else:
                errors.extend(validate_timestamp(generated["at"], "generated.at", rel))

    verified = metadata.get("verified")
    if verified is not None:
        events = verified if isinstance(verified, list) else [verified]
        if not events:
            errors.append(f"{rel}: [OKF v0.3] verified must not be empty")
        for index, event in enumerate(events):
            prefix = f"verified[{index}]"
            if not isinstance(event, dict):
                errors.append(f"{rel}: [OKF v0.3] {prefix} must be a mapping")
                continue
            errors.extend(validate_actor(event.get("by"), f"{prefix}.by", rel))
            if "at" not in event:
                errors.append(f"{rel}: [OKF v0.3] {prefix}.at is required")
            else:
                errors.extend(validate_timestamp(event["at"], f"{prefix}.at", rel))

    if "status" in metadata:
        status = metadata["status"]
        if not non_empty_string(status):
            errors.append(f"{rel}: [OKF v0.3] status must be a non-empty string")
        elif status not in STATUS_VALUES:
            errors.append(f"{rel}: [software-project profile] status must be one of draft, stable, or deprecated")

    if "superseded_by" in metadata:
        superseded_by = metadata["superseded_by"]
        if not non_empty_string(superseded_by):
            errors.append(f"{rel}: [OKF v0.3] superseded_by must be a non-empty path string")
        elif metadata.get("status") != "deprecated":
            errors.append(f"{rel}: [software-project profile] superseded_by is only valid with status: deprecated")

    if "stale_after" in metadata:
        errors.extend(validate_timestamp(metadata["stale_after"], "stale_after", rel))
    return errors


def validate_reserved(path: Path, bundle: Path) -> list[str]:
    rel = label(path, bundle)
    metadata, body, error = parse_frontmatter(path)
    if error:
        return [f"{rel}: [OKF v0.3] {error}"]

    errors: list[str] = []
    if path.name == "index.md":
        if path == bundle / "index.md":
            if metadata is None:
                errors.append(f'{rel}: [software-project profile] bundle root must declare okf_version: "0.3"')
            else:
                if metadata.get("okf_version") != "0.3":
                    errors.append(f'{rel}: [software-project profile] okf_version must equal "0.3"')
                for key in ROOT_INDEX_STRING_KEYS:
                    if key in metadata and not non_empty_string(metadata[key]):
                        errors.append(f"{rel}: [OKF v0.3] root index {key} must be a non-empty string")
        elif metadata is not None:
            errors.append(f"{rel}: [OKF v0.3] non-root index.md must not contain frontmatter")
    elif metadata is not None:
        errors.append(f"{rel}: [OKF v0.3] log.md must not contain frontmatter")

    if not body.strip():
        errors.append(f"{rel}: [OKF v0.3] reserved file body must not be empty")
    if path.name == "log.md":
        date_headings = [line for line in body.splitlines() if line.startswith("## ")]
        if not date_headings:
            errors.append(f"{rel}: [OKF v0.3] log.md requires at least one YYYY-MM-DD section")
        for heading in date_headings:
            match = DATE_HEADING_RE.fullmatch(heading)
            if not match:
                errors.append(f"{rel}: [OKF v0.3] invalid log date heading {heading!r}")
            else:
                try:
                    date.fromisoformat(match.group(1))
                except ValueError:
                    errors.append(f"{rel}: [OKF v0.3] invalid log calendar date {heading!r}")
    return errors


def _has_dot_component(path: Path, bundle: Path) -> bool:
    return any(part.startswith(".") for part in path.relative_to(bundle).parts)


def validate_bundle(bundle: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    if not bundle.is_dir():
        return [f"{bundle}: [software-project profile] OKF bundle directory is missing"], 0

    root_index = bundle / "index.md"
    if not root_index.is_file():
        errors.append(f"{root_index}: [software-project profile] bundle root index.md is required")

    files = sorted(path for path in bundle.rglob("*.md") if not _has_dot_component(path, bundle))
    for path in files:
        if path.name in RESERVED:
            errors.extend(validate_reserved(path, bundle))
            continue
        rel = label(path, bundle)
        metadata, _body, error = parse_frontmatter(path)
        if error:
            errors.append(f"{rel}: [OKF v0.3] {error}")
        elif metadata is None:
            errors.append(f"{rel}: [software-project profile] concept document requires YAML frontmatter")
        else:
            errors.extend(validate_metadata(metadata, rel))
    return errors, len(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundles", nargs="*", type=Path)
    args = parser.parse_args()
    bundles = args.bundles or DEFAULT_BUNDLES

    errors: list[str] = []
    count = 0
    for bundle in bundles:
        bundle_errors, bundle_count = validate_bundle(bundle.resolve())
        errors.extend(bundle_errors)
        count += bundle_count

    if errors:
        print("OKF validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {count} OKF Markdown files across {len(bundles)} bundles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
