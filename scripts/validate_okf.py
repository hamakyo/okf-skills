#!/usr/bin/env python3
"""Validate maintained OKF v0.2 bundles and repository profile rules."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    from validation_utils import aware_datetime, non_empty_string, parse_frontmatter
except ImportError:  # pragma: no cover - used when imported as scripts.validate_okf
    from .validation_utils import aware_datetime, non_empty_string, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLES = [ROOT / "okf", ROOT / "examples" / "minimal" / "okf"]
RESERVED = {"index.md", "log.md"}
DATE_HEADING_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})$")
ACTOR_RE = re.compile(r"^(?:human:[^\s:]+|process:[^\s:]+|[^\s/]+/[^\s/]+)$")
STATUS_VALUES = {"draft", "stable", "deprecated"}


def label(path: Path, bundle: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path.relative_to(bundle))


def validate_actor(value: Any, field: str, rel: str) -> list[str]:
    if not non_empty_string(value) or not ACTOR_RE.fullmatch(value):
        return [f"{rel}: [OKF v0.2] {field} must use tool/version, human:<id>, or process:<id>"]
    return []


def validate_datetime(value: Any, field: str, rel: str) -> list[str]:
    if aware_datetime(value) is None:
        return [f"{rel}: [OKF v0.2] {field} must be an ISO 8601 datetime with an explicit UTC offset"]
    return []


def validate_usage_window(value: Any, field: str, rel: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{rel}: [OKF v0.2] {field} must be a mapping"]
    errors: list[str] = []
    for endpoint in ("from", "to"):
        if endpoint not in value:
            errors.append(f"{rel}: [OKF v0.2] {field}.{endpoint} is required")
        else:
            errors.extend(validate_datetime(value[endpoint], f"{field}.{endpoint}", rel))
    start = aware_datetime(value.get("from"))
    end = aware_datetime(value.get("to"))
    if start is not None and end is not None and start > end:
        errors.append(f"{rel}: [OKF v0.2] {field}.from must not be after {field}.to")
    return errors


def validate_metadata(metadata: dict[str, Any], rel: str) -> list[str]:
    errors: list[str] = []
    if not non_empty_string(metadata.get("type")):
        errors.append(f"{rel}: [OKF v0.2] concept frontmatter requires a non-empty type")

    if "timestamp" in metadata:
        errors.append(f"{rel}: [software-project profile] legacy timestamp is superseded by generated.at")

    sources = metadata.get("sources")
    if sources is not None:
        if not isinstance(sources, list):
            errors.append(f"{rel}: [OKF v0.2] sources must be a list")
        else:
            for index, source in enumerate(sources):
                prefix = f"sources[{index}]"
                if not isinstance(source, dict):
                    errors.append(f"{rel}: [OKF v0.2] {prefix} must be a mapping")
                    continue
                if not non_empty_string(source.get("resource")):
                    errors.append(f"{rel}: [OKF v0.2] {prefix}.resource is required")
                for key in ("id", "title"):
                    if key in source and not non_empty_string(source[key]):
                        errors.append(f"{rel}: [OKF v0.2] {prefix}.{key} must be a non-empty string")
                if "author" in source:
                    errors.extend(validate_actor(source["author"], f"{prefix}.author", rel))
                if "usage_count" in source and (
                    isinstance(source["usage_count"], bool)
                    or not isinstance(source["usage_count"], int)
                    or source["usage_count"] < 0
                ):
                    errors.append(f"{rel}: [OKF v0.2] {prefix}.usage_count must be a non-negative integer")
                if "last_modified" in source:
                    errors.extend(validate_datetime(source["last_modified"], f"{prefix}.last_modified", rel))
                if "usage_window" in source:
                    errors.extend(validate_usage_window(source["usage_window"], f"{prefix}.usage_window", rel))

    if "usage_window" in metadata:
        errors.extend(validate_usage_window(metadata["usage_window"], "usage_window", rel))

    generated = metadata.get("generated")
    if generated is not None:
        if not isinstance(generated, dict):
            errors.append(f"{rel}: [OKF v0.2] generated must be a mapping")
        else:
            errors.extend(validate_actor(generated.get("by"), "generated.by", rel))
            if "at" not in generated:
                errors.append(f"{rel}: [software-project profile] generated.at is required when generated is present")
            else:
                errors.extend(validate_datetime(generated["at"], "generated.at", rel))

    verified = metadata.get("verified")
    if verified is not None:
        events = verified if isinstance(verified, list) else [verified]
        if not events:
            errors.append(f"{rel}: [OKF v0.2] verified must not be empty")
        for index, event in enumerate(events):
            prefix = f"verified[{index}]"
            if not isinstance(event, dict):
                errors.append(f"{rel}: [OKF v0.2] {prefix} must be a mapping")
                continue
            errors.extend(validate_actor(event.get("by"), f"{prefix}.by", rel))
            if "at" not in event:
                errors.append(f"{rel}: [OKF v0.2] {prefix}.at is required")
            else:
                errors.extend(validate_datetime(event["at"], f"{prefix}.at", rel))

    if "status" in metadata:
        status = metadata["status"]
        if not isinstance(status, str) or status not in STATUS_VALUES:
            errors.append(f"{rel}: [OKF v0.2] status must be one of draft, stable, or deprecated")
    if "stale_after" in metadata:
        errors.extend(validate_datetime(metadata["stale_after"], "stale_after", rel))
    return errors


def validate_reserved(path: Path, bundle: Path) -> list[str]:
    rel = label(path, bundle)
    metadata, body, error = parse_frontmatter(path)
    if error:
        return [f"{rel}: [OKF v0.2] {error}"]

    errors: list[str] = []
    if path.name == "index.md":
        if path == bundle / "index.md":
            if metadata is None:
                errors.append(f'{rel}: [software-project profile] bundle root must declare okf_version: "0.2"')
            else:
                if metadata.get("okf_version") != "0.2":
                    errors.append(f'{rel}: [software-project profile] okf_version must equal "0.2"')
                unexpected = set(metadata) - {"okf_version"}
                if unexpected:
                    errors.append(f"{rel}: [OKF v0.2] root index frontmatter may contain only okf_version")
        elif metadata is not None:
            errors.append(f"{rel}: [OKF v0.2] non-root index.md must not contain frontmatter")
    elif metadata is not None:
        errors.append(f"{rel}: [OKF v0.2] log.md must not contain frontmatter")

    if not body.strip():
        errors.append(f"{rel}: [OKF v0.2] reserved file body must not be empty")
    if path.name == "log.md":
        date_headings = [line for line in body.splitlines() if line.startswith("## ")]
        if not date_headings:
            errors.append(f"{rel}: [OKF v0.2] log.md requires at least one YYYY-MM-DD section")
        for heading in date_headings:
            match = DATE_HEADING_RE.fullmatch(heading)
            if not match:
                errors.append(f"{rel}: [OKF v0.2] invalid log date heading {heading!r}")
            else:
                try:
                    date.fromisoformat(match.group(1))
                except ValueError:
                    errors.append(f"{rel}: [OKF v0.2] invalid log calendar date {heading!r}")
    return errors


def validate_bundle(bundle: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    if not bundle.is_dir():
        return [f"{bundle}: [software-project profile] OKF bundle directory is missing"], 0

    root_index = bundle / "index.md"
    if not root_index.is_file():
        errors.append(f"{root_index}: [software-project profile] bundle root index.md is required")

    files = sorted(bundle.rglob("*.md"))
    for path in files:
        if path.name in RESERVED:
            errors.extend(validate_reserved(path, bundle))
            continue
        rel = label(path, bundle)
        metadata, _body, error = parse_frontmatter(path)
        if error:
            errors.append(f"{rel}: [OKF v0.2] {error}")
        elif metadata is None:
            errors.append(f"{rel}: [OKF v0.2] concept document requires YAML frontmatter")
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
