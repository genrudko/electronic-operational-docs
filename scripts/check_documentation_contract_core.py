#!/usr/bin/env python3
"""Validate the canonical EOD documentation contract.

The checker intentionally uses only the Python standard library so it can run
both in GitHub Actions and in the project containers without extra packages.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import project_state_contract

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/documentation-contract.yml",
    "docs/INDEX.md",
    "docs/project/CURRENT_STATE.md",
    "docs/project/MASTER_PLAN.md",
    "docs/project/ROADMAP.md",
    "docs/project/SCOPE_AND_BOUNDARIES.md",
    "docs/project/DOMAIN_INVARIANTS.md",
    "docs/project/SYSTEM_ARCHITECTURE.md",
    "docs/project/MODULE_MAP.md",
    "docs/project/DATA_AND_PRIVACY_POLICY.md",
    "docs/project/DECISION_LOG.md",
    "docs/project/OPEN_ITEMS.md",
    "docs/project/PATCH_HISTORY.md",
    "docs/project/BASELINE_HISTORY.md",
    "docs/project/ACCEPTANCE_HISTORY.md",
    "docs/project/CURRENT_HANDOFF.md",
    "docs/project/NEW_CHAT_STARTER.md",
    "docs/process/PROJECT_OPERATING_SYSTEM.md",
    "docs/process/DEVELOPMENT_WORKFLOW.md",
    "docs/process/GIT_WORKFLOW.md",
    "docs/process/BRANCH_AND_PR_POLICY.md",
    "docs/process/CI_AND_QUALITY_GATES.md",
    "docs/process/DEFINITION_OF_DONE.md",
    "docs/process/RELEASE_PROCESS.md",
    "docs/process/DOCUMENTATION_MAINTENANCE.md",
    "docs/process/PARALLEL_CHAT_WORKFLOW.md",
    "docs/runbooks/PREVIEW_RUNBOOK.md",
    "docs/runbooks/DEVELOPMENT_RUNBOOK.md",
    "docs/runbooks/DATABASE_BACKUP_AND_RESTORE.md",
    "docs/runbooks/PRESENTATION_DATA_RESET.md",
    "docs/runbooks/SSH_TUNNEL_ACCESS.md",
    "docs/runbooks/BRANCH_SWITCHING.md",
    "docs/runbooks/POST_MERGE_DEPLOYMENT.md",
    "docs/runbooks/INCIDENT_AND_ROLLBACK.md",
    "docs/acceptance/INTERNAL_PROTOTYPE_ACCEPTANCE.md",
    "docs/acceptance/DEMONSTRATION_SCENARIOS.md",
    "docs/acceptance/REGRESSION_CHECKLIST.md",
    "docs/acceptance/KNOWN_LIMITATIONS.md",
    "docs/releases/RELEASE_NOTES.md",
)

CANONICAL_LEGACY_SCAN = (
    "README.md",
    "AGENTS.md",
    "docs/project/CURRENT_STATE.md",
    "docs/project/CURRENT_HANDOFF.md",
    "docs/process/PROJECT_OPERATING_SYSTEM.md",
    "docs/process/DEVELOPMENT_WORKFLOW.md",
)

FORBIDDEN_LEGACY_PHRASES = (
    "Ассистент самостоятельно проектирует изменения и выдаёт один полный автономный Python-скрипт",
    "Каждый Patch/Repair должен быть единым полным Python-скриптом",
    "автоматический push запрещён",
    "SQLite остаётся локальной СУБД прототипа, PostgreSQL — целевой",
)

PROHIBITED_TRACKED_SUFFIXES = (
    ".sqlite",
    ".sqlite3",
    ".dump",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
)

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def validate_required_files(errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            errors.append(f"empty required file: {relative}")
        if "\r" in content:
            errors.append(f"CR character found, LF required: {relative}")


def normalize_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target and not target.startswith(("http://", "https://")):
        target = target.split(" ", 1)[0]
    target = unquote(target)
    if not target or target.startswith(("#", "http://", "https://", "mailto:")):
        return None
    return target.split("#", 1)[0].split("?", 1)[0]


def validate_markdown_links(errors: list[str]) -> None:
    markdown_files = [ROOT / relative for relative in REQUIRED_FILES if relative.endswith(".md")]
    for path in markdown_files:
        content = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(content):
            target = normalize_link_target(match.group(1))
            if target is None:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"link escapes repository: {path.relative_to(ROOT)} -> {target}")
                continue
            if not resolved.exists():
                errors.append(f"broken link: {path.relative_to(ROOT)} -> {target}")


def validate_legacy_phrases(errors: list[str]) -> None:
    for relative in CANONICAL_LEGACY_SCAN:
        content = read_text(relative)
        for phrase in FORBIDDEN_LEGACY_PHRASES:
            if phrase in content:
                errors.append(f"legacy workflow phrase in {relative}: {phrase}")


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def validate_tracked_sensitive_paths(errors: list[str]) -> None:
    for relative in tracked_files():
        lower = relative.lower()
        name = Path(relative).name.lower()
        if name == ".env" or (name.startswith(".env.") and not name.endswith(".example")):
            errors.append(f"tracked environment secret path: {relative}")
        if lower.endswith(PROHIBITED_TRACKED_SUFFIXES):
            errors.append(f"prohibited tracked binary/secret path: {relative}")


def validate_legacy_tree_removed(errors: list[str]) -> None:
    legacy = ROOT / "docs" / "project_state"
    if legacy.exists():
        remaining = sorted(path.relative_to(ROOT).as_posix() for path in legacy.rglob("*"))
        if remaining:
            errors.append("legacy docs/project_state tree still present: " + ", ".join(remaining))


def main() -> int:
    errors: list[str] = []
    validate_required_files(errors)
    if not errors:
        validate_markdown_links(errors)
        errors.extend(project_state_contract.validate_repository(ROOT, verify_context=True))
        validate_legacy_phrases(errors)
    validate_tracked_sensitive_paths(errors)
    validate_legacy_tree_removed(errors)

    if errors:
        print("Documentation contract: FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    state = project_state_contract.parse_current_state(
        read_text("docs/project/CURRENT_STATE.md")
    )
    print("Documentation contract: OK")
    print(f"Required files: {len(REQUIRED_FILES)}")
    print(f"Accepted baseline: {state.accepted_main}")
    print(f"Active work item: {state.active_work_item or 'NONE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
