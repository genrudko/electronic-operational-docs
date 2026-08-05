#!/usr/bin/env python3
"""Single-owner project-state contract plus canonical planning validation."""

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
FIELD_RE = re.compile(r"(?m)^([a-z ]+):\s*(.+?)\s*$", re.IGNORECASE)
VOLATILE_FIELDS = (
    "accepted main baseline",
    "active work item",
    "active issue",
    "active pr",
    "active branch",
    "runtime impact",
    "preview",
)


@dataclass(frozen=True)
class CurrentState:
    repository: str
    accepted_main: str
    active_work_item: str | None
    active_issue: int | None
    active_pr: int | None
    active_branch: str | None
    runtime_impact: str
    preview: str


def _none_or_value(value: str) -> str | None:
    return None if value.strip().upper() == "NONE" else value.strip()


def parse_current_state(text: str) -> CurrentState:
    blocks = re.findall(r"```text\s*\n(.*?)```", text, flags=re.DOTALL)
    candidate: dict[str, str] | None = None
    for block in blocks:
        fields = {key.lower(): value for key, value in FIELD_RE.findall(block)}
        required = {
            "repository",
            "accepted main baseline",
            "active work item",
            "active issue",
            "active pr",
            "active branch",
            "runtime impact",
            "preview",
        }
        if required.issubset(fields):
            candidate = fields
            break
    if candidate is None:
        raise ValueError("CURRENT_STATE canonical state block missing")

    accepted_raw = candidate["accepted main baseline"]
    accepted_match = re.fullmatch(r"main\s*/\s*([0-9a-f]{40})", accepted_raw)
    if accepted_match is None:
        raise ValueError("CURRENT_STATE accepted main SHA invalid")
    accepted_main = accepted_match.group(1)

    work_item = _none_or_value(candidate["active work item"])
    issue_raw = _none_or_value(candidate["active issue"])
    pr_raw = _none_or_value(candidate["active pr"])
    branch = _none_or_value(candidate["active branch"])

    issue: int | None = None
    pr: int | None = None
    if issue_raw is not None:
        match = re.fullmatch(r"#(\d+)", issue_raw)
        if match is None:
            raise ValueError("CURRENT_STATE active issue invalid")
        issue = int(match.group(1))
    if pr_raw is not None:
        match = re.match(r"#(\d+)\b", pr_raw)
        if match is None:
            raise ValueError("CURRENT_STATE active PR invalid")
        pr = int(match.group(1))

    active_values = (work_item, issue, pr, branch)
    if any(value is None for value in active_values) and not all(
        value is None for value in active_values
    ):
        raise ValueError("CURRENT_STATE active tuple must be all set or all NONE")

    return CurrentState(
        repository=candidate["repository"],
        accepted_main=accepted_main,
        active_work_item=work_item,
        active_issue=issue,
        active_pr=pr,
        active_branch=branch,
        runtime_impact=candidate["runtime impact"],
        preview=candidate["preview"],
    )


def validate_handoff(text: str) -> list[str]:
    errors: list[str] = []
    required_markers = (
        "[`CURRENT_STATE.md`](CURRENT_STATE.md)",
        "[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml)",
    )
    for marker in required_markers:
        if marker not in text:
            errors.append(f"CURRENT_HANDOFF navigation marker missing: {marker}")
    if SHA_ANY_RE.search(text):
        errors.append("CURRENT_HANDOFF contains volatile SHA")
    lowered = text.lower()
    for field in VOLATILE_FIELDS:
        if re.search(rf"(?m)^\s*{re.escape(field)}\s*:", lowered):
            errors.append("CURRENT_HANDOFF contains volatile state field")
            break
    return errors


def validate_plan_ownership(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    owners = plan.get("owners")
    expected = {
        "state": STATE_PATH,
        "plan": PLAN_PATH,
    }
    if not isinstance(owners, dict):
        errors.append("DEMO_RELEASE_PLAN owners mapping missing")
    else:
        for key, value in expected.items():
            if owners.get(key) != value:
                errors.append(
                    f"DEMO_RELEASE_PLAN owner {key} must be {value}, got {owners.get(key)!r}"
                )
    forbidden = (
        "accepted_main",
        "active",
        "runtime",
        "preview",
        "active_pr",
        "active_branch",
    )
    for key in forbidden:
        if key in plan:
            if key == "accepted_main":
                errors.append(
                    "DEMO_RELEASE_PLAN duplicates accepted main owned by CURRENT_STATE"
                )
            elif key == "active":
                errors.append(
                    "DEMO_RELEASE_PLAN duplicates active work owned by CURRENT_STATE"
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
    if event and "pull_request" in event:
        pr = event["pull_request"]
        if state.active_pr is not None and int(event.get("number", -1)) != state.active_pr:
            errors.append("CURRENT_STATE active PR does not match workflow pull request")
        head_ref = pr.get("head", {}).get("ref")
        if state.active_branch is not None and head_ref != state.active_branch:
            errors.append("CURRENT_STATE active branch does not match workflow pull request")
        if pr.get("state") != "open":
            errors.append("CURRENT_STATE active PR is not open in workflow event")
        if not pr.get("draft", False):
            errors.append("CURRENT_STATE active PR must remain Draft")
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


def validate_duplicate_volatile_owners(
    root: Path, plan: dict[str, Any]
) -> list[str]:
    """Reject explicit owner-style volatile fields outside CURRENT_STATE.

    Historical SHAs and event ledgers are allowed. What is forbidden is a second
    file exposing the canonical owner field syntax.
    """
    errors: list[str] = []
    paths = {
        HANDOFF_PATH,
        "docs/project/INDUSTRIALIZATION_PROGRAM.md",
        *plan.get("views", {}).values(),
        *(module.get("contract", "") for module in plan.get("modules", [])),
    }
    pattern = re.compile(
        r"(?im)^\s*(accepted main baseline|active work item|active issue|"
        r"active pr|active branch|runtime impact|preview)\s*:"
    )
    for relative in sorted(path for path in paths if path and path != STATE_PATH):
        file_path = root / relative
        if not file_path.is_file():
            continue
        for match in pattern.finditer(file_path.read_text(encoding="utf-8")):
            field = match.group(1).lower()
            errors.append(
                f"{relative}: [{field}] rule=single-volatile-owner; "
                f"expected='owned only by {STATE_PATH}'; "
                "actual='owner-style field present'"
            )
    return errors


def validate_repository(root: Path = ROOT, *, verify_context: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        state = parse_current_state((root / STATE_PATH).read_text(encoding="utf-8"))
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
        plan = json.loads((root / PLAN_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [
            f"{PLAN_PATH}: [load] rule=plan-load; "
            f"expected='valid JSON-compatible YAML'; actual={str(exc)!r}"
        ]
    if not isinstance(plan, dict):
        return errors + [
            f"{PLAN_PATH}: [root] rule=plan-root; "
            f"expected='object'; actual={type(plan).__name__!r}"
        ]
    errors.extend(validate_plan_ownership(plan))
    errors.extend(validate_duplicate_volatile_owners(root, plan))

    if verify_context:
        event = _load_event()
        origin_main = os.environ.get("EOD_ORIGIN_MAIN_SHA")
        errors.extend(
            validate_execution_context(
                state, event=event, origin_main=origin_main
            )
        )

    try:
        from demo_release_plan import validate_repository as validate_release_repository
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
    """Compatibility wrapper for historical gates and current callers."""
    errors = validate_repository(root, verify_context=verify_context)
    if errors:
        raise AssertionError("Project state contract failed: " + "; ".join(errors))
    return parse_current_state((root / STATE_PATH).read_text(encoding="utf-8"))


def main() -> int:
    errors = validate_repository(ROOT)
    if errors:
        print("Project state contract: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    state = parse_current_state((ROOT / STATE_PATH).read_text(encoding="utf-8"))
    print("Project state contract: OK")
    print(f"Accepted main baseline: {state.accepted_main}")
    print(f"Active work item: {state.active_work_item or 'NONE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
