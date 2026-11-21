#!/usr/bin/env python3
"""Validate and run reproducible Codex Skill evaluation scenarios."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

try:
    from validation_utils import non_empty_string
except ImportError:  # pragma: no cover - used when imported as scripts.eval_codex_skills
    from .validation_utils import non_empty_string

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS_PATH = ROOT / "evals" / "codex-scenarios.yaml"
SCHEMA_VERSION = 1
SUPPORTED_HOSTS = {"codex"}
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

TOP_KEYS = {"schema_version", "host", "defaults", "scenarios"}
DEFAULT_KEYS = {"skill_dir", "timeout_seconds"}
SCENARIO_KEYS = {
    "id",
    "skill",
    "title",
    "description",
    "prompt",
    "timeout_seconds",
    "workspace",
    "assertions",
}
WORKSPACE_KEYS = {"fixture", "copy_skills", "files", "working_tree_files"}
ASSERTION_KEYS = {
    "files_must_exist",
    "files_must_not_exist",
    "files_must_change",
    "files_must_not_change",
    "max_changed_files",
    "forbidden_paths",
    "file_contains",
    "file_not_contains",
    "commands",
    "response_contains",
    "response_not_contains",
}
FILE_MATCH_KEYS = {"path", "pattern", "literal", "name"}
RESPONSE_MATCH_KEYS = {"pattern", "literal", "name"}
COMMAND_CHECK_KEYS = {"name", "cmd", "expect_exit_code", "stdout_contains", "stderr_contains"}

IGNORED_SNAPSHOT_DIRS = {".git", "__pycache__"}
IGNORED_SNAPSHOT_FILES = {".DS_Store"}

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai-api-key", re.compile(r"\bsk-(?:proj-|live-|test-)?[A-Za-z0-9_-]{20,}\b")),
    ("anthropic-api-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("bearer-token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b")),
]
SENSITIVE_ENV_VARS = (
    "OPENAI_API_KEY",
    "CODEX_API_KEY",
    "ANTHROPIC_API_KEY",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
)


def canonical_skills(root: Path = ROOT) -> set[str]:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return set()
    return {
        path.parent.name
        for path in skills_dir.glob("*/SKILL.md")
        if path.is_file()
    }


def is_safe_relative_path(value: Any, *, allow_glob: bool = False) -> bool:
    if not non_empty_string(value):
        return False
    if "\\" in value:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    if parts[0] == ".git":
        return False
    if not allow_glob and any(ch in value for ch in ("*", "?", "[")):
        return False
    return True


def detect_secrets(text: str) -> list[str]:
    found: list[str] = []
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            found.append(label)
    return found


def redact_secrets(text: str, env: dict[str, str] | None = None) -> str:
    redacted = text
    for _label, pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    active_env = env if env is not None else os.environ
    for var_name in SENSITIVE_ENV_VARS:
        secret_val = active_env.get(var_name, "")
        if len(secret_val) >= 8 and secret_val in redacted:
            redacted = redacted.replace(secret_val, "[REDACTED]")
    return redacted


def _validate_regex(pattern: Any, label: str) -> list[str]:
    if not non_empty_string(pattern):
        return [f"{label} must be a non-empty string"]
    try:
        re.compile(pattern)
    except re.error as exc:
        return [f"{label} has invalid regex {pattern!r}: {exc}"]
    return []


def _validate_string_path_list(
    value: Any,
    label: str,
    *,
    allow_glob: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be a list of relative paths"]
    errors: list[str] = []
    for index, item in enumerate(value):
        if not is_safe_relative_path(item, allow_glob=allow_glob):
            errors.append(f"{label}[{index}] must be a safe relative POSIX path")
    return errors


def _validate_file_match_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be a list of mappings"]
    errors: list[str] = []
    for index, entry in enumerate(value):
        prefix = f"{label}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        unknown = sorted(set(entry) - FILE_MATCH_KEYS)
        if unknown:
            errors.append(f"{prefix} contains unknown keys: {', '.join(unknown)}")
        if not is_safe_relative_path(entry.get("path")):
            errors.append(f"{prefix}.path must be a safe relative POSIX path")
        literal = entry.get("literal", False)
        if not isinstance(literal, bool):
            errors.append(f"{prefix}.literal must be a boolean")
        pattern = entry.get("pattern")
        if literal:
            if not non_empty_string(pattern):
                errors.append(f"{prefix}.pattern must be a non-empty string")
        else:
            errors.extend(_validate_regex(pattern, f"{prefix}.pattern"))
        if "name" in entry and not non_empty_string(entry["name"]):
            errors.append(f"{prefix}.name must be a non-empty string")
    return errors


def _validate_response_match_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be a list of mappings"]
    errors: list[str] = []
    for index, entry in enumerate(value):
        prefix = f"{label}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        unknown = sorted(set(entry) - RESPONSE_MATCH_KEYS)
        if unknown:
            errors.append(f"{prefix} contains unknown keys: {', '.join(unknown)}")
        literal = entry.get("literal", False)
        if not isinstance(literal, bool):
            errors.append(f"{prefix}.literal must be a boolean")
        pattern = entry.get("pattern")
        if literal:
            if not non_empty_string(pattern):
                errors.append(f"{prefix}.pattern must be a non-empty string")
        else:
            errors.extend(_validate_regex(pattern, f"{prefix}.pattern"))
        if "name" in entry and not non_empty_string(entry["name"]):
            errors.append(f"{prefix}.name must be a non-empty string")
    return errors


def _validate_command_checks(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be a list of command check mappings"]
    errors: list[str] = []
    for index, entry in enumerate(value):
        prefix = f"{label}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        unknown = sorted(set(entry) - COMMAND_CHECK_KEYS)
        if unknown:
            errors.append(f"{prefix} contains unknown keys: {', '.join(unknown)}")
        if not non_empty_string(entry.get("name")):
            errors.append(f"{prefix}.name must be a non-empty string")
        cmd = entry.get("cmd")
        if not isinstance(cmd, list) or not cmd or not all(non_empty_string(part) for part in cmd):
            errors.append(f"{prefix}.cmd must be a non-empty list of non-empty strings")
        if "expect_exit_code" in entry:
            code = entry["expect_exit_code"]
            if not isinstance(code, int) or isinstance(code, bool):
                errors.append(f"{prefix}.expect_exit_code must be an integer")
        for stream_key in ("stdout_contains", "stderr_contains"):
            if stream_key in entry:
                errors.extend(_validate_regex(entry[stream_key], f"{prefix}.{stream_key}"))
    return errors


def validate_scenarios_data(
    data: Any,
    *,
    source_label: str = "evals/codex-scenarios.yaml",
    root: Path = ROOT,
    available_skills: set[str] | None = None,
) -> list[str]:
    """Validate parsed Codex evaluation scenario YAML data."""
    if not isinstance(data, dict):
        return [f"{source_label}: top-level document must be a mapping"]

    errors: list[str] = []
    unknown_top = sorted(set(data) - TOP_KEYS)
    if unknown_top:
        errors.append(f"{source_label}: unknown top-level keys: {', '.join(unknown_top)}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{source_label}: schema_version must equal {SCHEMA_VERSION}")

    host = data.get("host")
    if not isinstance(host, str) or host not in SUPPORTED_HOSTS:
        errors.append(f"{source_label}: host must be one of {sorted(SUPPORTED_HOSTS)}")

    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict):
        errors.append(f"{source_label}: defaults must be a mapping")
    else:
        unknown_defaults = sorted(set(defaults) - DEFAULT_KEYS)
        if unknown_defaults:
            errors.append(f"{source_label}: unknown defaults keys: {', '.join(unknown_defaults)}")
        if "skill_dir" in defaults and not is_safe_relative_path(defaults["skill_dir"]):
            errors.append(f"{source_label}: defaults.skill_dir must be a safe relative POSIX path")
        if "timeout_seconds" in defaults:
            timeout = defaults["timeout_seconds"]
            if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
                errors.append(f"{source_label}: defaults.timeout_seconds must be a positive integer")

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append(f"{source_label}: scenarios must be a non-empty list")
        return errors

    known_skills = available_skills if available_skills is not None else canonical_skills(root)
    seen_ids: set[str] = set()
    covered_skills: set[str] = set()

    for index, scenario in enumerate(scenarios):
        prefix = f"{source_label}: scenarios[{index}]"
        if not isinstance(scenario, dict):
            errors.append(f"{prefix} must be a mapping")
            continue

        unknown_keys = sorted(set(scenario) - SCENARIO_KEYS)
        if unknown_keys:
            errors.append(f"{prefix} contains unknown keys: {', '.join(unknown_keys)}")

        scenario_id = scenario.get("id")
        if not non_empty_string(scenario_id) or not KEBAB_RE.fullmatch(scenario_id):
            errors.append(f"{prefix}.id must be a kebab-case string")
        elif scenario_id in seen_ids:
            errors.append(f"{prefix}.id duplicates {scenario_id!r}")
        else:
            seen_ids.add(scenario_id)
            prefix = f"{source_label}: scenario {scenario_id!r}"

        skill = scenario.get("skill")
        if not non_empty_string(skill):
            errors.append(f"{prefix}.skill must be a non-empty string")
        elif known_skills and skill not in known_skills:
            errors.append(f"{prefix}.skill references unknown Skill {skill!r}")
        else:
            covered_skills.add(skill)

        for text_field in ("title", "description", "prompt"):
            val = scenario.get(text_field)
            if not non_empty_string(val):
                errors.append(f"{prefix}.{text_field} must be a non-empty string")
            else:
                for secret_kind in detect_secrets(val):
                    errors.append(f"{prefix}.{text_field} appears to contain a secret ({secret_kind})")

        if "timeout_seconds" in scenario:
            timeout = scenario["timeout_seconds"]
            if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
                errors.append(f"{prefix}.timeout_seconds must be a positive integer")

        workspace = scenario.get("workspace")
        if not isinstance(workspace, dict):
            errors.append(f"{prefix}.workspace must be a mapping")
        else:
            unknown_ws = sorted(set(workspace) - WORKSPACE_KEYS)
            if unknown_ws:
                errors.append(f"{prefix}.workspace contains unknown keys: {', '.join(unknown_ws)}")

            fixture = workspace.get("fixture")
            if fixture is not None:
                if not is_safe_relative_path(fixture):
                    errors.append(f"{prefix}.workspace.fixture must be a safe relative POSIX path")
                elif not (root / fixture).is_dir():
                    errors.append(f"{prefix}.workspace.fixture directory does not exist: {fixture}")

            copy_skills = workspace.get("copy_skills")
            if not isinstance(copy_skills, list) or not copy_skills:
                errors.append(f"{prefix}.workspace.copy_skills must be a non-empty list")
            else:
                seen_copy: set[str] = set()
                for c_idx, copy_skill in enumerate(copy_skills):
                    if not non_empty_string(copy_skill):
                        errors.append(f"{prefix}.workspace.copy_skills[{c_idx}] must be a non-empty string")
                    elif known_skills and copy_skill not in known_skills:
                        errors.append(f"{prefix}.workspace.copy_skills[{c_idx}] references unknown Skill {copy_skill!r}")
                    elif copy_skill in seen_copy:
                        errors.append(f"{prefix}.workspace.copy_skills duplicates {copy_skill!r}")
                    else:
                        seen_copy.add(copy_skill)
                if non_empty_string(skill) and skill not in seen_copy:
                    errors.append(f"{prefix}.workspace.copy_skills must include target skill {skill!r}")

            files = workspace.get("files")
            if fixture is None and (not isinstance(files, dict) or not files):
                errors.append(f"{prefix}.workspace.files must be a non-empty mapping when workspace.fixture is omitted")
            elif files is not None and not isinstance(files, dict):
                errors.append(f"{prefix}.workspace.files must be a mapping")

            for map_name in ("files", "working_tree_files"):
                file_map = workspace.get(map_name)
                if file_map is None:
                    continue
                if not isinstance(file_map, dict):
                    errors.append(f"{prefix}.workspace.{map_name} must be a mapping")
                    continue
                for rel_path, content in file_map.items():
                    if not is_safe_relative_path(rel_path):
                        errors.append(f"{prefix}.workspace.{map_name} has unsafe path {rel_path!r}")
                    if not isinstance(content, str):
                        errors.append(f"{prefix}.workspace.{map_name}[{rel_path!r}] content must be a string")
                    else:
                        for secret_kind in detect_secrets(content):
                            errors.append(
                                f"{prefix}.workspace.{map_name}[{rel_path!r}] appears to contain a secret ({secret_kind})"
                            )

        assertions = scenario.get("assertions")
        if not isinstance(assertions, dict) or not assertions:
            errors.append(f"{prefix}.assertions must be a non-empty mapping")
        else:
            unknown_assert = sorted(set(assertions) - ASSERTION_KEYS)
            if unknown_assert:
                errors.append(f"{prefix}.assertions contains unknown keys: {', '.join(unknown_assert)}")

            for path_list_key in ("files_must_exist", "files_must_not_exist", "files_must_change", "files_must_not_change"):
                if path_list_key in assertions:
                    errors.extend(_validate_string_path_list(assertions[path_list_key], f"{prefix}.assertions.{path_list_key}"))

            if "forbidden_paths" in assertions:
                errors.extend(
                    _validate_string_path_list(
                        assertions["forbidden_paths"],
                        f"{prefix}.assertions.forbidden_paths",
                        allow_glob=True,
                    )
                )

            if "max_changed_files" in assertions:
                limit = assertions["max_changed_files"]
                if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
                    errors.append(f"{prefix}.assertions.max_changed_files must be a non-negative integer")

            if isinstance(assertions.get("files_must_change"), list) and isinstance(
                assertions.get("files_must_not_change"), list
            ):
                overlap = sorted(set(assertions["files_must_change"]) & set(assertions["files_must_not_change"]))
                if overlap:
                    errors.append(
                        f"{prefix}.assertions lists overlapping paths in files_must_change and files_must_not_change: {', '.join(overlap)}"
                    )

            for match_key in ("file_contains", "file_not_contains"):
                if match_key in assertions:
                    errors.extend(_validate_file_match_list(assertions[match_key], f"{prefix}.assertions.{match_key}"))

            if "commands" in assertions:
                errors.extend(_validate_command_checks(assertions["commands"], f"{prefix}.assertions.commands"))

            for resp_key in ("response_contains", "response_not_contains"):
                if resp_key in assertions:
                    errors.extend(
                        _validate_response_match_list(assertions[resp_key], f"{prefix}.assertions.{resp_key}")
                    )

    if known_skills:
        missing = sorted(known_skills - covered_skills)
        for skill_name in missing:
            errors.append(f"{source_label}: missing evaluation scenario for canonical Skill {skill_name!r}")

    return errors


def load_scenarios(path: Path = DEFAULT_SCENARIOS_PATH, root: Path = ROOT) -> dict[str, Any]:
    """Load and validate a Codex evaluation scenarios YAML file."""
    try:
        raw_text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text)
    except OSError as exc:
        raise ValueError(f"unable to read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        detail = str(exc).splitlines()[0]
        raise ValueError(f"invalid YAML in {path}: {detail}") from exc

    try:
        label = str(path.relative_to(root))
    except ValueError:
        label = str(path)

    errors = validate_scenarios_data(data, source_label=label, root=root)
    if errors:
        raise ValueError("Scenario validation failed:\n" + "\n".join(f"- {err}" for err in errors))
    return data


def snapshot_workspace(workspace: Path) -> dict[str, str]:
    """Return a deterministic mapping of relative POSIX file paths to SHA-256 digests."""
    snapshot: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(workspace):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_SNAPSHOT_DIRS)
        for filename in sorted(filenames):
            if filename in IGNORED_SNAPSHOT_FILES or filename.endswith(".pyc"):
                continue
            full_path = Path(dirpath) / filename
            if full_path.is_symlink():
                continue
            rel = full_path.relative_to(workspace).as_posix()
            snapshot[rel] = hashlib.sha256(full_path.read_bytes()).hexdigest()
    return snapshot


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> dict[str, list[str]]:
    before_keys = set(before)
    after_keys = set(after)
    added = sorted(after_keys - before_keys)
    deleted = sorted(before_keys - after_keys)
    modified = sorted(key for key in (before_keys & after_keys) if before[key] != after[key])
    return {"added": added, "modified": modified, "deleted": deleted}


def _run_git(workspace: Path, args: list[str]) -> None:
    completed = subprocess.run(
        ["git", *args],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed in {workspace}: {detail}")


def stage_scenario_workspace(
    scenario: dict[str, Any],
    destination: Path,
    *,
    skill_dir: str = ".agents/skills",
    root: Path = ROOT,
) -> dict[str, str]:
    """Materialize a clean git-backed workspace for a scenario and return its pre-run snapshot."""
    destination.mkdir(parents=True, exist_ok=True)
    workspace_cfg = scenario["workspace"]

    fixture = workspace_cfg.get("fixture")
    if fixture:
        shutil.copytree(root / fixture, destination, dirs_exist_ok=True)

    for rel_path, content in (workspace_cfg.get("files") or {}).items():
        target = destination / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    for skill_name in workspace_cfg["copy_skills"]:
        source_skill = root / "skills" / skill_name / "SKILL.md"
        target_skill = destination / skill_dir / skill_name / "SKILL.md"
        target_skill.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_skill, target_skill)

    _run_git(destination, ["init", "-q"])
    _run_git(destination, ["config", "user.name", "OKF Eval Harness"])
    _run_git(destination, ["config", "user.email", "eval-harness@example.invalid"])
    _run_git(destination, ["add", "-A"])
    _run_git(destination, ["commit", "-q", "-m", "chore: initial evaluation baseline"])

    for rel_path, content in (workspace_cfg.get("working_tree_files") or {}).items():
        target = destination / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return snapshot_workspace(destination)


def _substitute_tokens(tokens: list[str], mapping: dict[str, str]) -> list[str]:
    result: list[str] = []
    for token in tokens:
        expanded = token
        for key, val in mapping.items():
            expanded = expanded.replace(f"{{{key}}}", val)
        result.append(expanded)
    return result


def _matches(text: str, pattern: str, *, literal: bool = False) -> bool:
    if literal:
        return pattern in text
    return re.search(pattern, text) is not None


def evaluate_assertions(
    assertions: dict[str, Any],
    *,
    workspace: Path,
    changed: dict[str, list[str]],
    response_text: str,
    root: Path = ROOT,
    command_timeout: int = 60,
) -> list[dict[str, Any]]:
    """Evaluate all observable assertions for a scenario workspace."""
    checks: list[dict[str, Any]] = []
    added_or_modified = set(changed["added"]) | set(changed["modified"])
    all_changed = added_or_modified | set(changed["deleted"])

    for rel in assertions.get("files_must_exist", []):
        exists = (workspace / rel).exists()
        checks.append(
            {
                "kind": "file_exists",
                "name": rel,
                "passed": exists,
                "detail": "exists" if exists else f"expected file {rel!r} does not exist",
            }
        )

    for rel in assertions.get("files_must_not_exist", []):
        exists = (workspace / rel).exists()
        checks.append(
            {
                "kind": "file_not_exists",
                "name": rel,
                "passed": not exists,
                "detail": "absent" if not exists else f"unexpected file {rel!r} exists",
            }
        )

    for rel in assertions.get("files_must_change", []):
        ok = rel in added_or_modified
        checks.append(
            {
                "kind": "file_changed",
                "name": rel,
                "passed": ok,
                "detail": "modified or added" if ok else f"expected {rel!r} to be modified or added",
            }
        )

    for rel in assertions.get("files_must_not_change", []):
        ok = rel not in all_changed
        checks.append(
            {
                "kind": "file_unchanged",
                "name": rel,
                "passed": ok,
                "detail": "unchanged" if ok else f"file {rel!r} was modified unexpectedly",
            }
        )

    if "max_changed_files" in assertions:
        limit = assertions["max_changed_files"]
        count = len(all_changed)
        ok = count <= limit
        checks.append(
            {
                "kind": "max_changed_files",
                "name": f"<= {limit}",
                "passed": ok,
                "detail": f"{count} changed file(s) (limit {limit})",
            }
        )

    for pattern in assertions.get("forbidden_paths", []):
        matches = sorted(
            rel
            for rel in all_changed
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(Path(rel).name, pattern)
        )
        ok = not matches
        checks.append(
            {
                "kind": "forbidden_path",
                "name": pattern,
                "passed": ok,
                "detail": "no forbidden changes" if ok else f"forbidden path(s) changed: {', '.join(matches)}",
            }
        )

    for entry in assertions.get("file_contains", []):
        rel = entry["path"]
        pattern = entry["pattern"]
        literal = entry.get("literal", False)
        name = entry.get("name") or f"{rel}: {pattern}"
        target = workspace / rel
        if not target.is_file():
            checks.append(
                {
                    "kind": "file_contains",
                    "name": name,
                    "passed": False,
                    "detail": f"file {rel!r} does not exist",
                }
            )
            continue
        content = target.read_text(encoding="utf-8", errors="replace")
        ok = _matches(content, pattern, literal=literal)
        checks.append(
            {
                "kind": "file_contains",
                "name": name,
                "passed": ok,
                "detail": "matched" if ok else f"pattern {pattern!r} not found in {rel!r}",
            }
        )

    for entry in assertions.get("file_not_contains", []):
        rel = entry["path"]
        pattern = entry["pattern"]
        literal = entry.get("literal", False)
        name = entry.get("name") or f"{rel}: !{pattern}"
        target = workspace / rel
        if not target.is_file():
            checks.append(
                {
                    "kind": "file_not_contains",
                    "name": name,
                    "passed": True,
                    "detail": f"file {rel!r} does not exist",
                }
            )
            continue
        content = target.read_text(encoding="utf-8", errors="replace")
        ok = not _matches(content, pattern, literal=literal)
        checks.append(
            {
                "kind": "file_not_contains",
                "name": name,
                "passed": ok,
                "detail": "absent" if ok else f"disallowed pattern {pattern!r} matched in {rel!r}",
            }
        )

    substitutions = {
        "python": sys.executable,
        "repo_root": str(root),
        "workspace": str(workspace),
    }
    for entry in assertions.get("commands", []):
        name = entry["name"]
        expect_code = entry.get("expect_exit_code", 0)
        argv = _substitute_tokens(entry["cmd"], substitutions)
        try:
            completed = subprocess.run(
                argv,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=command_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            checks.append(
                {
                    "kind": "command",
                    "name": name,
                    "passed": False,
                    "detail": f"command timed out after {command_timeout}s",
                }
            )
            continue
        except OSError as exc:
            checks.append(
                {
                    "kind": "command",
                    "name": name,
                    "passed": False,
                    "detail": f"failed to launch command: {exc}",
                }
            )
            continue

        reasons: list[str] = []
        if completed.returncode != expect_code:
            reasons.append(f"exit code {completed.returncode} != expected {expect_code}")
        stdout_pattern = entry.get("stdout_contains")
        if stdout_pattern and not re.search(stdout_pattern, completed.stdout):
            reasons.append(f"stdout did not match {stdout_pattern!r}")
        stderr_pattern = entry.get("stderr_contains")
        if stderr_pattern and not re.search(stderr_pattern, completed.stderr):
            reasons.append(f"stderr did not match {stderr_pattern!r}")

        ok = not reasons
        if ok:
            detail = f"exit code {completed.returncode}"
        else:
            snippet = redact_secrets((completed.stderr or completed.stdout).strip())
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            detail = "; ".join(reasons) + (f" | output: {snippet}" if snippet else "")

        checks.append(
            {
                "kind": "command",
                "name": name,
                "passed": ok,
                "detail": detail,
            }
        )

    for entry in assertions.get("response_contains", []):
        pattern = entry["pattern"]
        literal = entry.get("literal", False)
        name = entry.get("name") or pattern
        ok = _matches(response_text, pattern, literal=literal)
        checks.append(
            {
                "kind": "response_contains",
                "name": name,
                "passed": ok,
                "detail": "matched" if ok else f"pattern {pattern!r} not found in agent response",
            }
        )

    for entry in assertions.get("response_not_contains", []):
        pattern = entry["pattern"]
        literal = entry.get("literal", False)
        name = entry.get("name") or f"!{pattern}"
        ok = not _matches(response_text, pattern, literal=literal)
        checks.append(
            {
                "kind": "response_not_contains",
                "name": name,
                "passed": ok,
                "detail": "absent" if ok else f"disallowed pattern {pattern!r} matched in agent response",
            }
        )

    return checks


def _build_runner_command(
    mode: str,
    *,
    workspace: Path,
    prompt_file: Path,
    response_file: Path,
    scenario: dict[str, Any],
    root: Path,
    command_template: str | None,
    codex_args: list[str],
) -> list[str]:
    if mode == "codex":
        return [
            "codex",
            "exec",
            "--full-auto",
            "--color",
            "never",
            "-C",
            str(workspace),
            "-o",
            str(response_file),
            *codex_args,
            "-",
        ]
    if mode == "command":
        if not command_template:
            raise ValueError("--command is required when --mode=command")
        raw_tokens = shlex.split(command_template)
        substitutions = {
            "workspace": str(workspace),
            "prompt_file": str(prompt_file),
            "response_file": str(response_file),
            "repo_root": str(root),
            "python": sys.executable,
            "scenario_id": scenario["id"],
            "skill": scenario["skill"],
        }
        return _substitute_tokens(raw_tokens, substitutions)
    raise ValueError(f"unsupported execution mode: {mode}")


def run_scenario(
    scenario: dict[str, Any],
    *,
    mode: str = "dry-run",
    skill_dir: str = ".agents/skills",
    default_timeout: int = 300,
    timeout_override: int | None = None,
    command_template: str | None = None,
    codex_args: list[str] | None = None,
    workdir: Path | None = None,
    keep_workspace: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Stage and evaluate a single Codex Skill scenario."""
    started = time.monotonic()
    timeout = timeout_override or scenario.get("timeout_seconds") or default_timeout
    extra_codex_args = list(codex_args or [])

    ephemeral_root: Path | None = None
    if workdir is not None:
        scenario_root = workdir / scenario["id"]
        if scenario_root.exists():
            shutil.rmtree(scenario_root)
        scenario_root.mkdir(parents=True, exist_ok=True)
    else:
        ephemeral_root = Path(tempfile.mkdtemp(prefix=f"okf-eval-{scenario['id']}-"))
        scenario_root = ephemeral_root

    workspace = scenario_root / "workspace"
    meta_dir = scenario_root / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = meta_dir / "prompt.txt"
    response_file = meta_dir / "response.txt"
    prompt_file.write_text(scenario["prompt"], encoding="utf-8")

    try:
        before_snapshot = stage_scenario_workspace(
            scenario,
            workspace,
            skill_dir=skill_dir,
            root=root,
        )

        if mode == "dry-run":
            preview_cmd = _build_runner_command(
                "command" if command_template else "codex",
                workspace=workspace,
                prompt_file=prompt_file,
                response_file=response_file,
                scenario=scenario,
                root=root,
                command_template=command_template,
                codex_args=extra_codex_args,
            )
            return {
                "id": scenario["id"],
                "skill": scenario["skill"],
                "title": scenario["title"],
                "status": "dry-run",
                "duration_seconds": round(time.monotonic() - started, 3),
                "workspace": str(workspace) if (keep_workspace or workdir is not None) else None,
                "runner": {
                    "mode": "dry-run",
                    "command_preview": " ".join(shlex.quote(part) for part in preview_cmd),
                },
                "changed_files": {"added": [], "modified": [], "deleted": []},
                "checks": [
                    {
                        "kind": "staging",
                        "name": "workspace-staged",
                        "passed": True,
                        "detail": f"staged {len(before_snapshot)} file(s) with skills: {', '.join(scenario['workspace']['copy_skills'])}",
                    }
                ],
            }

        argv = _build_runner_command(
            mode,
            workspace=workspace,
            prompt_file=prompt_file,
            response_file=response_file,
            scenario=scenario,
            root=root,
            command_template=command_template,
            codex_args=extra_codex_args,
        )

        run_env = os.environ.copy()
        run_env.update(
            {
                "OKF_EVAL_SCENARIO_ID": scenario["id"],
                "OKF_EVAL_SKILL": scenario["skill"],
                "OKF_EVAL_WORKSPACE": str(workspace),
                "OKF_EVAL_PROMPT_FILE": str(prompt_file),
                "OKF_EVAL_RESPONSE_FILE": str(response_file),
                "OKF_EVAL_REPO_ROOT": str(root),
            }
        )

        exit_code: int | None = None
        timed_out = False
        launch_error: str | None = None
        stdout_text = ""
        stderr_text = ""

        try:
            completed = subprocess.run(
                argv,
                cwd=workspace,
                input=scenario["prompt"],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=run_env,
                check=False,
            )
            exit_code = completed.returncode
            stdout_text = completed.stdout
            stderr_text = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout_text = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr_text = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        except FileNotFoundError:
            launch_error = f"executable not found: {argv[0]!r}"
        except OSError as exc:
            launch_error = str(exc)

        after_snapshot = snapshot_workspace(workspace)
        changed = diff_snapshots(before_snapshot, after_snapshot)

        if response_file.is_file():
            raw_response = response_file.read_text(encoding="utf-8", errors="replace")
        else:
            raw_response = stdout_text
        if not raw_response.strip():
            raw_response = stdout_text

        redacted_response = redact_secrets(raw_response, env=run_env)
        redacted_stderr = redact_secrets(stderr_text, env=run_env)

        checks: list[dict[str, Any]] = []
        if launch_error is not None:
            checks.append(
                {
                    "kind": "runner",
                    "name": mode,
                    "passed": False,
                    "detail": launch_error,
                }
            )
            status = "error"
        elif timed_out:
            checks.append(
                {
                    "kind": "runner",
                    "name": mode,
                    "passed": False,
                    "detail": f"runner timed out after {timeout}s",
                }
            )
            status = "error"
        else:
            if exit_code != 0:
                stderr_hint = redacted_stderr.strip()[:240]
                checks.append(
                    {
                        "kind": "runner",
                        "name": mode,
                        "passed": False,
                        "detail": f"runner exited with code {exit_code}" + (f" | {stderr_hint}" if stderr_hint else ""),
                    }
                )
            else:
                checks.append(
                    {
                        "kind": "runner",
                        "name": mode,
                        "passed": True,
                        "detail": "runner exited with code 0",
                    }
                )
            checks.extend(
                evaluate_assertions(
                    scenario["assertions"],
                    workspace=workspace,
                    changed=changed,
                    response_text=redacted_response,
                    root=root,
                )
            )
            status = "passed" if all(check["passed"] for check in checks) else "failed"

        excerpt = redacted_response.strip()
        if len(excerpt) > 600:
            excerpt = excerpt[:600] + "..."

        return {
            "id": scenario["id"],
            "skill": scenario["skill"],
            "title": scenario["title"],
            "status": status,
            "duration_seconds": round(time.monotonic() - started, 3),
            "workspace": str(workspace) if (keep_workspace or workdir is not None) else None,
            "runner": {
                "mode": mode,
                "exit_code": exit_code,
                "timed_out": timed_out,
                "launch_error": launch_error,
            },
            "changed_files": changed,
            "checks": checks,
            "response_excerpt": excerpt,
        }
    finally:
        if ephemeral_root is not None and not keep_workspace:
            shutil.rmtree(ephemeral_root, ignore_errors=True)


def run_suite(
    data: dict[str, Any],
    *,
    mode: str = "dry-run",
    scenario_ids: list[str] | None = None,
    skills: list[str] | None = None,
    timeout_override: int | None = None,
    command_template: str | None = None,
    codex_args: list[str] | None = None,
    workdir: Path | None = None,
    keep_workspace: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Run all matching scenarios and build a structured evaluation report."""
    defaults = data.get("defaults") or {}
    skill_dir = defaults.get("skill_dir", ".agents/skills")
    default_timeout = defaults.get("timeout_seconds", 300)

    selected = list(data["scenarios"])
    if scenario_ids:
        wanted_ids = set(scenario_ids)
        known_ids = {s["id"] for s in selected}
        unknown_ids = sorted(wanted_ids - known_ids)
        if unknown_ids:
            raise ValueError(f"unknown scenario id(s): {', '.join(unknown_ids)}")
        selected = [s for s in selected if s["id"] in wanted_ids]

    if skills:
        wanted_skills = set(skills)
        selected = [s for s in selected if s["skill"] in wanted_skills]

    if not selected:
        raise ValueError("no scenarios matched the provided filters")

    results = [
        run_scenario(
            scenario,
            mode=mode,
            skill_dir=skill_dir,
            default_timeout=default_timeout,
            timeout_override=timeout_override,
            command_template=command_template,
            codex_args=codex_args,
            workdir=workdir,
            keep_workspace=keep_workspace,
            root=root,
        )
        for scenario in selected
    ]

    counts = {
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "passed"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "error": sum(1 for r in results if r["status"] == "error"),
        "dry_run": sum(1 for r in results if r["status"] == "dry-run"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "host": data["host"],
        "mode": mode,
        "summary": counts,
        "scenarios": results,
    }


def format_scenario_list(data: dict[str, Any], fmt: str = "text") -> str:
    rows = [
        {
            "id": s["id"],
            "skill": s["skill"],
            "title": s["title"],
            "commands": len(s["assertions"].get("commands", [])),
        }
        for s in data["scenarios"]
    ]
    if fmt == "json":
        return json.dumps({"schema_version": data["schema_version"], "host": data["host"], "scenarios": rows}, indent=2)
    if fmt == "markdown":
        lines = [
            "## Codex Skill Evaluation Scenarios",
            "",
            "| ID | Skill | Title | Command checks |",
            "| --- | --- | --- | ---: |",
        ]
        for row in rows:
            lines.append(f"| `{row['id']}` | `{row['skill']}` | {row['title']} | {row['commands']} |")
        return "\n".join(lines)

    lines = [f"Codex evaluation scenarios ({len(rows)} total):"]
    for row in rows:
        lines.append(f"- {row['id']} [{row['skill']}]: {row['title']}")
    return "\n".join(lines)


def format_report(report: dict[str, Any], fmt: str = "text") -> str:
    if fmt == "json":
        return json.dumps(report, indent=2)

    summary = report["summary"]
    if fmt == "markdown":
        lines = [
            f"## Codex Skill Evaluation Report (`{report['mode']}`)",
            "",
            f"- Total: **{summary['total']}** | Passed: **{summary['passed']}** | Failed: **{summary['failed']}** | Errors: **{summary['error']}** | Dry-run: **{summary['dry_run']}**",
            "",
            "| Scenario | Skill | Status | Checks | Duration (s) |",
            "| --- | --- | --- | ---: | ---: |",
        ]
        for item in report["scenarios"]:
            passed_checks = sum(1 for c in item["checks"] if c["passed"])
            total_checks = len(item["checks"])
            lines.append(
                f"| `{item['id']}` | `{item['skill']}` | `{item['status']}` | {passed_checks}/{total_checks} | {item['duration_seconds']:.2f} |"
            )

        failures = [item for item in report["scenarios"] if item["status"] in ("failed", "error")]
        if failures:
            lines.extend(["", "### Failure Diagnostics", ""])
            for item in failures:
                lines.append(f"- **`{item['id']}`** (`{item['skill']}`, `{item['status']}`)")
                changed = item["changed_files"]
                lines.append(
                    f"  - Changed files: added={changed['added']}, modified={changed['modified']}, deleted={changed['deleted']}"
                )
                for check in item["checks"]:
                    if not check["passed"]:
                        lines.append(f"  - Failed `{check['kind']}` (`{check['name']}`): {check['detail']}")
        return "\n".join(lines)

    lines = [
        f"Codex Skill Evaluation ({report['mode']}): "
        f"total={summary['total']} passed={summary['passed']} failed={summary['failed']} "
        f"error={summary['error']} dry_run={summary['dry_run']}"
    ]
    for item in report["scenarios"]:
        passed_checks = sum(1 for c in item["checks"] if c["passed"])
        total_checks = len(item["checks"])
        lines.append(
            f"- [{item['status'].upper()}] {item['id']} ({item['skill']}) "
            f"{passed_checks}/{total_checks} checks in {item['duration_seconds']:.2f}s"
        )
        if item["status"] in ("failed", "error"):
            changed = item["changed_files"]
            lines.append(
                f"    changed: added={changed['added']} modified={changed['modified']} deleted={changed['deleted']}"
            )
            for check in item["checks"]:
                if not check["passed"]:
                    lines.append(f"    FAIL [{check['kind']}] {check['name']}: {check['detail']}")
        elif item["status"] == "dry-run":
            lines.append(f"    preview: {item['runner']['command_preview']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and run reproducible Codex Skill evaluation scenarios.",
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=DEFAULT_SCENARIOS_PATH,
        help="Path to the Codex evaluation scenarios YAML file.",
    )
    parser.add_argument(
        "--mode",
        choices=("validate", "dry-run", "codex", "command"),
        default="dry-run",
        help="Execution mode (default: dry-run, which stages workspaces without invoking Codex/APIs).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List scenarios and exit after validating the scenario file.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenario_ids",
        help="Filter by scenario ID (repeatable).",
    )
    parser.add_argument(
        "--skill",
        action="append",
        dest="skills",
        help="Filter by canonical Skill name (repeatable).",
    )
    parser.add_argument(
        "--command",
        dest="command_template",
        help="Command template for --mode command (supports {workspace}, {prompt_file}, {response_file}, {repo_root}, {python}, {scenario_id}, {skill}).",
    )
    parser.add_argument(
        "--codex-arg",
        action="append",
        dest="codex_args",
        default=[],
        help="Additional argument passed to `codex exec` (repeatable).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        dest="timeout_override",
        help="Override per-scenario execution timeout in seconds.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="Directory where staged scenario workspaces will be created (implies keeping workspaces).",
    )
    parser.add_argument(
        "--keep-workspaces",
        action="store_true",
        help="Keep temporary staged workspaces on disk for manual inspection.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the formatted report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        data = load_scenarios(args.scenarios)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.list:
        rendered = format_scenario_list(data, args.format)
        print(rendered)
        return 0

    if args.mode == "validate":
        count = len(data["scenarios"])
        skills = sorted({s["skill"] for s in data["scenarios"]})
        print(f"Validated {count} Codex evaluation scenarios covering {len(skills)} Skills.")
        return 0

    try:
        report = run_suite(
            data,
            mode=args.mode,
            scenario_ids=args.scenario_ids,
            skills=args.skills,
            timeout_override=args.timeout_override,
            command_template=args.command_template,
            codex_args=args.codex_args,
            workdir=args.workdir,
            keep_workspace=args.keep_workspaces,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    rendered = format_report(report, args.format)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)

    summary = report["summary"]
    return 1 if (summary["failed"] > 0 or summary["error"] > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
