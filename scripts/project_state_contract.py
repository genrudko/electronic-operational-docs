#!/usr/bin/env python3
"""Validate canonical current state and the single-owner documentation contract."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = "docs/project/CURRENT_STATE.md"
HANDOFF_PATH = "docs/project/CURRENT_HANDOFF.md"
PLAN_PATH = "docs/project/DEMO_RELEASE_PLAN.yaml"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA_ANY_RE = re.compile(r"\b[0-9a-f]{40}\b")
WORK_ITEM_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}$")
ISSUE_RE = re.compile(r"^#[1-9][0-9]*$")
PR_RE = re.compile(
    r"^#(?P<number>[1-9][0-9]*) / (?P<state>OPEN|CLOSED) / "
    r"(?P<review>DRAFT|READY) / (?P<merge>NOT MERGED|MERGED)$"
)
BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
VOLATILE_FIELD_RE = re.compile(
    r"(?im)^\s*(accepted main baseline|active work item|active issue|"
    r"active pr|active branch|runtime impact|preview)\s*:"
)
REQUIRED_STATE_KEYS = (
    "repository",
    "accepted main baseline",
    "active work item",
    "active issue",
    "active PR",
    "active branch",
    "runtime impact",
    "preview",
)
EXPECTED_OWNERS = {
    "state": STATE_PATH,
    "plan": PLAN_PATH,
    "coverage_source": (
        "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv"
    ),
    "coverage_decisions": (
        "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISIONS.csv"
    ),
}
VOLATILE_OWNER_ALLOWLIST = {
    STATE_PATH,
    "docs/project/ACCEPTANCE_HISTORY.md",
    "docs/project/BASELINE_HISTORY.md",
}


@dataclass(frozen=True)
class CurrentState:
    repository: str
    accepted_main: str
    active_work_item: str | None
    active_issue: int | None
    active_pr: int | None
    active_pr_state: str | None
    active_pr_review: str | None
    active_pr_merge: str | None
    active_branch: str | None
    runtime_impact: str
    preview: str


def _state_block(text: str) -> str:
    for match in re.finditer(
        r"```text\s*\n(?P<body>.*?)\n```", text, re.DOTALL
    ):
        body = match.group("body")
        if "repository:" in body and "accepted main baseline:" in body:
            return body
    raise ValueError("CURRENT_STATE canonical text block not found")


def _key_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw_line in enumerate(block.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(
                f"CURRENT_STATE line {number} is not key/value"
            )
        key, value = (part.strip() for part in line.split(":", 1))
        if key in values:
            raise ValueError(f"CURRENT_STATE duplicate key: {key}")
        values[key] = value
    missing = [key for key in REQUIRED_STATE_KEYS if key not in values]
    if missing:
        raise ValueError(
            "CURRENT_STATE missing keys: " + ", ".join(missing)
        )
    return values


def _valid_branch(value: str) -> bool:
    if not BRANCH_RE.fullmatch(value):
        return False
    if value.startswith("/") or value.endswith("/"):
        return False
    if value.startswith(".") or value.endswith("."):
        return False
    if "//" in value or ".." in value or "@{" in value:
        return False
    return not any(part.endswith(".lock") for part in value.split("/"))


def parse_current_state(text: str) -> CurrentState:
    values = _key_values(_state_block(text))
    repository = values["repository"]
    if repository != "genrudko/electronic-operational-docs":
        raise ValueError("CURRENT_STATE repository invalid")

    baseline_prefix = "main / "
    baseline = values["accepted main baseline"]
    if not baseline.startswith(baseline_prefix):
        raise ValueError(
            "CURRENT_STATE accepted main must use 'main / <sha>'"
        )
    accepted_main = baseline.removeprefix(baseline_prefix)
    if not SHA_RE.fullmatch(accepted_main):
        raise ValueError("CURRENT_STATE accepted main SHA invalid")

    work_item_raw = values["active work item"]
    issue_raw = values["active issue"]
    pr_raw = values["active PR"]
    branch_raw = values["active branch"]
    active_values = (work_item_raw, issue_raw, pr_raw, branch_raw)
    inactive = all(value == "NONE" for value in active_values)
    partially_inactive = any(value == "NONE" for value in active_values)
    if partially_inactive and not inactive:
        raise ValueError(
            "CURRENT_STATE active work item/issue/PR/branch must be "
            "all set or all NONE"
        )

    if inactive:
        work_item = None
        issue = None
        pr_number = None
        pr_state = None
        pr_review = None
        pr_merge = None
        branch = None
    else:
        if not WORK_ITEM_RE.fullmatch(work_item_raw):
            raise ValueError("CURRENT_STATE active work item ID invalid")
        if not ISSUE_RE.fullmatch(issue_raw):
            raise ValueError("CURRENT_STATE active issue invalid")
        pr_match = PR_RE.fullmatch(pr_raw)
        if pr_match is None:
            raise ValueError("CURRENT_STATE active PR descriptor invalid")
        if not _valid_branch(branch_raw):
            raise ValueError("CURRENT_STATE active branch invalid")
        work_item = work_item_raw
        issue = int(issue_raw.removeprefix("#"))
        pr_number = int(pr_match.group("number"))
        pr_state = pr_match.group("state")
        pr_review = pr_match.group("review")
        pr_merge = pr_match.group("merge")
        branch = branch_raw

    runtime_impact = values["runtime impact"]
    valid_runtime = {"NONE", "DEVELOPMENT", "PREVIEW", "BOTH"}
    if runtime_impact not in valid_runtime:
        raise ValueError("CURRENT_STATE runtime impact invalid")
    preview = values["preview"]
    valid_preview = {"UNTOUCHED", "CURRENT", "DRIFT", "UNKNOWN"}
    if preview not in valid_preview:
        raise ValueError("CURRENT_STATE preview status invalid")

    return CurrentState(
        repository=repository,
        accepted_main=accepted_main,
        active_work_item=work_item,
        active_issue=issue,
        active_pr=pr_number,
        active_pr_state=pr_state,
        active_pr_review=pr_review,
        active_pr_merge=pr_merge,
        active_branch=branch,
        runtime_impact=runtime_impact,
        preview=preview,
    )


def validate_handoff(text: str) -> list[str]:
    errors: list[str] = []
    required_markers = (
        "[`CURRENT_STATE.md`](CURRENT_STATE.md)",
        "[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml)",
    )
    for marker in required_markers:
        if marker not in text:
            errors.append(
                f"CURRENT_HANDOFF navigation marker missing: {marker}"
            )
    if SHA_ANY_RE.search(text):
        errors.append("CURRENT_HANDOFF contains volatile SHA")
    if VOLATILE_FIELD_RE.search(text):
        errors.append("CURRENT_HANDOFF contains volatile state field")
    return errors


def validate_plan_ownership(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("owners") != EXPECTED_OWNERS:
        errors.append("canonical owners invalid")
    forbidden = (
        "accepted_main",
        "active",
        "runtime",
        "preview",
        "active_pr",
        "active_branch",
    )
    for key in forbidden:
        if key not in plan:
            continue
        if key == "accepted_main":
            errors.append(
                "DEMO_RELEASE_PLAN duplicates accepted main owned by "
                "CURRENT_STATE"
            )
        elif key == "active":
            errors.append(
                "DEMO_RELEASE_PLAN duplicates active work owned by "
                "CURRENT_STATE"
            )
        else:
            errors.append(
                "DEMO_RELEASE_PLAN duplicates volatile state owned by "
                f"CURRENT_STATE: {key}"
            )
    return errors


def validate_execution_context(
    state: CurrentState,
    *,
    event: dict[str, Any] | None = None,
    origin_main: str | None = None,
) -> list[str]:
    errors: list[str] = []
    pull_request = event.get("pull_request") if event else None
    if isinstance(pull_request, dict):
        head = pull_request.get("head", {})
        head_ref = head.get("ref") if isinstance(head, dict) else None
        number = event.get("number")
        event_state = str(pull_request.get("state", "")).upper()
        event_review = "DRAFT" if pull_request.get("draft") else "READY"
        event_merge = (
            "MERGED" if pull_request.get("merged", False) else "NOT MERGED"
        )
        checks = (
            (
                state.active_pr,
                number,
                "CURRENT_STATE active PR does not match workflow pull request",
            ),
            (
                state.active_branch,
                head_ref,
                "CURRENT_STATE active branch does not match workflow "
                "pull request",
            ),
            (
                state.active_pr_state,
                event_state,
                "CURRENT_STATE active PR state does not match workflow "
                "pull request",
            ),
            (
                state.active_pr_review,
                event_review,
                "CURRENT_STATE active PR review state does not match "
                "workflow pull request",
            ),
            (
                state.active_pr_merge,
                event_merge,
                "CURRENT_STATE active PR merge state does not match "
                "workflow pull request",
            ),
        )
        for expected, actual, message in checks:
            if expected != actual:
                errors.append(message)
    if origin_main is not None and not SHA_RE.fullmatch(origin_main):
        errors.append("origin/main SHA invalid")
    return errors


def _load_event() -> dict[str, Any] | None:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        return None
    event_path = Path(path)
    if not event_path.is_file():
        return None
    loaded = json.loads(event_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def _documentation_markdown_paths(root: Path) -> list[Path]:
    paths = list((root / "docs").rglob("*.md"))
    paths.extend(root.glob("*.md"))
    return sorted({path.resolve() for path in paths if path.is_file()})


def validate_duplicate_volatile_owners(root: Path) -> list[str]:
    """Scan all applicable Markdown for a second volatile-state owner."""
    errors: list[str] = []
    for file_path in _documentation_markdown_paths(root):
        relative = file_path.relative_to(root).as_posix()
        if relative in VOLATILE_OWNER_ALLOWLIST:
            continue
        text = file_path.read_text(encoding="utf-8")
        for match in VOLATILE_FIELD_RE.finditer(text):
            field = match.group(1).lower()
            errors.append(
                f"{relative}: [{field}] rule=single-volatile-owner; "
                f"expected='owned only by {STATE_PATH} or explicit "
                "historical-ledger allowlist'; "
                "actual='owner-style field present'"
            )
    return errors


def validate_repository(
    root: Path = ROOT, *, verify_context: bool = False
) -> list[str]:
    errors: list[str] = []
    try:
        state = parse_current_state(
            (root / STATE_PATH).read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        return [
            f"{STATE_PATH}: [state] rule=current-state-parse; "
            f"expected='valid canonical block'; actual={str(exc)!r}"
        ]

    try:
        handoff = (root / HANDOFF_PATH).read_text(encoding="utf-8")
    except OSError as exc:
        return [
            f"{HANDOFF_PATH}: [handoff] rule=handoff-exists; "
            f"expected='file'; actual={str(exc)!r}"
        ]
    errors.extend(validate_handoff(handoff))

    try:
        plan = json.loads(
            (root / PLAN_PATH).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [
            f"{PLAN_PATH}: [load] rule=plan-load; "
            "expected='valid JSON-compatible YAML'; "
            f"actual={str(exc)!r}"
        ]
    if not isinstance(plan, dict):
        return errors + [
            f"{PLAN_PATH}: [root] rule=plan-root; "
            f"expected='object'; actual={type(plan).__name__!r}"
        ]
    errors.extend(validate_plan_ownership(plan))
    errors.extend(validate_duplicate_volatile_owners(root))

    if verify_context:
        errors.extend(
            validate_execution_context(
                state,
                event=_load_event(),
                origin_main=os.environ.get("EOD_ORIGIN_MAIN_SHA"),
            )
        )

    try:
        from demo_release_plan import (
            validate_repository as validate_release_repository,
        )
    except ModuleNotFoundError:
        from scripts.demo_release_plan import (
            validate_repository as validate_release_repository,
        )
    errors.extend(validate_release_repository(root))

    work_item_status = {
        item["id"]: item.get("status")
        for item in plan.get("work_items", [])
        if isinstance(item, dict) and "id" in item
    }
    if state.active_work_item is not None:
        actual = work_item_status.get(state.active_work_item)
        if actual != "IN_PROGRESS":
            errors.append(
                f"{PLAN_PATH}: [{state.active_work_item}] "
                "rule=active-work-item-status; expected='IN_PROGRESS'; "
                f"actual={actual!r}"
            )
    return errors


def require_repository(
    root: Path = ROOT, *, verify_context: bool = False
) -> CurrentState:
    errors = validate_repository(root, verify_context=verify_context)
    if errors:
        raise AssertionError(
            "Project state contract failed: " + "; ".join(errors)
        )
    return parse_current_state(
        (root / STATE_PATH).read_text(encoding="utf-8")
    )


def main() -> int:
    errors = validate_repository(ROOT)
    if errors:
        print("Project state contract: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    state = parse_current_state(
        (ROOT / STATE_PATH).read_text(encoding="utf-8")
    )
    print("Project state contract: OK")
    print(f"Accepted main baseline: {state.accepted_main}")
    print(f"Active work item: {state.active_work_item or 'NONE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
