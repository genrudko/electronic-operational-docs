#!/usr/bin/env python3
"""Validate the single-owner contract for current EOD project state.

The current state is intentionally kept separate from release planning and from
historical records:

* ``CURRENT_STATE.md`` owns the accepted merge baseline, active work and runtime data;
* ``DEMO_RELEASE_PLAN.yaml`` owns release/module planning data;
* ``CURRENT_HANDOFF.md`` only points readers to those owners.

The accepted merge baseline is not required to equal the repository tip. A bounded
post-merge coordination commit necessarily follows the accepted merge and updates
active work without creating a self-referential SHA requirement.

The module uses only the Python standard library so every existing workflow can
reuse it without installing additional dependencies.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
WORK_ITEM_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
PR_RE = re.compile(
    r"^#(?P<number>[1-9][0-9]*) / (?P<state>OPEN|CLOSED) / "
    r"(?P<review>DRAFT|READY) / (?P<merge>NOT MERGED|MERGED)$"
)
ISSUE_RE = re.compile(r"^#[1-9][0-9]*$")
VOLATILE_HANDOFF_RE = re.compile(
    r"(?im)^\s*(?:accepted(?: application| main)? baseline|current process(?:/documentation)? head|"
    r"active work item|active issue|active pr|active branch|active development|runtime impact|preview)\s*:"
)
SHA_ANYWHERE_RE = re.compile(r"\b[0-9a-f]{40}\b")

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
    "state": "docs/project/CURRENT_STATE.md",
    "plan": "docs/project/DEMO_RELEASE_PLAN.yaml",
    "coverage_source": "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv",
    "coverage_decisions": "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISIONS.csv",
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
    for match in re.finditer(r"```text\n(?P<body>.*?)\n```", text, re.DOTALL):
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
            raise ValueError(f"CURRENT_STATE line {number} is not key/value")
        key, value = (part.strip() for part in line.split(":", 1))
        if key in values:
            raise ValueError(f"CURRENT_STATE duplicate key: {key}")
        values[key] = value
    missing = [key for key in REQUIRED_STATE_KEYS if key not in values]
    if missing:
        raise ValueError("CURRENT_STATE missing keys: " + ", ".join(missing))
    return values


def parse_current_state(text: str) -> CurrentState:
    values = _key_values(_state_block(text))

    repository = values["repository"]
    if repository != "genrudko/electronic-operational-docs":
        raise ValueError("CURRENT_STATE repository invalid")

    baseline_prefix = "main / "
    baseline = values["accepted main baseline"]
    if not baseline.startswith(baseline_prefix):
        raise ValueError("CURRENT_STATE accepted main must use 'main / <sha>'")
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
        raise ValueError("CURRENT_STATE active work item/issue/PR/branch must be all set or all NONE")

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
        if not BRANCH_RE.fullmatch(branch_raw) or ".." in branch_raw or branch_raw.endswith(".lock"):
            raise ValueError("CURRENT_STATE active branch invalid")
        work_item = work_item_raw
        issue = int(issue_raw.removeprefix("#"))
        pr_number = int(pr_match.group("number"))
        pr_state = pr_match.group("state")
        pr_review = pr_match.group("review")
        pr_merge = pr_match.group("merge")
        branch = branch_raw

    runtime_impact = values["runtime impact"]
    if runtime_impact not in {"NONE", "DEVELOPMENT", "PREVIEW", "BOTH"}:
        raise ValueError("CURRENT_STATE runtime impact invalid")
    preview = values["preview"]
    if preview not in {"UNTOUCHED", "CURRENT", "DRIFT", "UNKNOWN"}:
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
    for marker in (
        "[`CURRENT_STATE.md`](CURRENT_STATE.md)",
        "[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml)",
    ):
        if marker not in text:
            errors.append(f"CURRENT_HANDOFF navigation marker missing: {marker}")
    if SHA_ANYWHERE_RE.search(text):
        errors.append("CURRENT_HANDOFF contains volatile SHA")
    if VOLATILE_HANDOFF_RE.search(text):
        errors.append("CURRENT_HANDOFF contains volatile state field")
    return errors


def validate_plan_ownership(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("owners") != EXPECTED_OWNERS:
        errors.append("canonical owners invalid")
    if "accepted_main" in plan:
        errors.append("DEMO_RELEASE_PLAN duplicates accepted main owned by CURRENT_STATE")
    if "active" in plan:
        errors.append("DEMO_RELEASE_PLAN duplicates active work owned by CURRENT_STATE")
    return errors


def _load_event(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    event_path = Path(path)
    if not event_path.is_file():
        return None
    loaded = json.loads(event_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def validate_execution_context(
    state: CurrentState,
    *,
    event: dict[str, Any] | None = None,
    origin_main: str | None = None,
) -> list[str]:
    """Validate live PR identity without making accepted-main self-referential.

    ``accepted_main`` records the accepted merge baseline. The base branch may
    legitimately contain later bounded coordination commits, so equality with
    the pull-request base SHA or ``origin/main`` is intentionally not required.
    ``origin_main`` remains accepted for API compatibility with earlier callers.
    """

    del origin_main
    errors: list[str] = []
    pull_request = event.get("pull_request") if event else None
    if isinstance(pull_request, dict):
        head = pull_request.get("head", {})
        head_ref = head.get("ref") if isinstance(head, dict) else None
        number = event.get("number")
        draft = pull_request.get("draft")
        state_value = str(pull_request.get("state", "")).upper()

        if state.active_pr != number:
            errors.append("CURRENT_STATE active PR does not match workflow pull request")
        if state.active_branch != head_ref:
            errors.append("CURRENT_STATE active branch does not match workflow pull request")
        if state.active_pr_state != state_value:
            errors.append("CURRENT_STATE active PR state does not match workflow pull request")
        expected_review = "DRAFT" if draft else "READY"
        if state.active_pr_review != expected_review:
            errors.append("CURRENT_STATE active PR review state does not match workflow pull request")
        if state.active_pr_merge != "NOT MERGED":
            errors.append("CURRENT_STATE active pull request must be NOT MERGED")
    return errors


def validate_repository(root: Path, *, verify_context: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        state = parse_current_state(
            (root / "docs/project/CURRENT_STATE.md").read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        return [str(exc)]

    try:
        handoff = (root / "docs/project/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(str(exc))
    else:
        errors.extend(validate_handoff(handoff))

    try:
        plan = json.loads(
            (root / "docs/project/DEMO_RELEASE_PLAN.yaml").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"DEMO_RELEASE_PLAN load failed: {exc}")
    else:
        if not isinstance(plan, dict):
            errors.append("DEMO_RELEASE_PLAN root must be an object")
        else:
            errors.extend(validate_plan_ownership(plan))

    if verify_context:
        event = _load_event(os.environ.get("GITHUB_EVENT_PATH"))
        errors.extend(validate_execution_context(state, event=event))
    return errors


def require_repository(root: Path, *, verify_context: bool = False) -> CurrentState:
    errors = validate_repository(root, verify_context=verify_context)
    if errors:
        raise AssertionError("Project state contract failed: " + "; ".join(errors))
    return parse_current_state(
        (root / "docs/project/CURRENT_STATE.md").read_text(encoding="utf-8")
    )
