"""Fail-closed validation rules for canonical EOD planning state."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

try:
    from .release_plan_model import (
        ALLOWED_CODE_STATUSES,
        ALLOWED_STATUSES,
        MODULE_MARKERS,
        PLAN_PATH,
        PROGRAM_MD_PATH,
        PROGRAM_PATH,
        RISK_PATH,
        SHA_RE,
        WORK_ITEM_RE,
        Program,
        diagnostic,
        identifiers,
        load_plan,
        load_program,
    )
    from .release_plan_views import (
        render_checklist,
        render_module_map,
        render_program_markdown,
        render_sequence,
    )
except ImportError:
    from release_plan_model import (
        ALLOWED_CODE_STATUSES,
        ALLOWED_STATUSES,
        MODULE_MARKERS,
        PLAN_PATH,
        PROGRAM_MD_PATH,
        PROGRAM_PATH,
        RISK_PATH,
        SHA_RE,
        WORK_ITEM_RE,
        Program,
        diagnostic,
        identifiers,
        load_plan,
        load_program,
    )
    from release_plan_views import (
        render_checklist,
        render_module_map,
        render_program_markdown,
        render_sequence,
    )


def validate_plan(plan: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if plan.get("schema") != 2:
        errors.append(
            diagnostic(PLAN_PATH, "schema", "plan-schema", 2, plan.get("schema"))
        )
    if plan.get("baseline_status") != "ACCEPTED":
        errors.append(
            diagnostic(
                PLAN_PATH,
                "DEMO-RELEASE",
                "baseline-status",
                "ACCEPTED",
                plan.get("baseline_status"),
            )
        )
    modules = plan.get("modules", [])
    work_items = plan.get("work_items", [])
    module_ids = identifiers(modules)
    work_item_ids = identifiers(work_items)
    if len(module_ids) != len(set(module_ids)):
        errors.append(
            diagnostic(
                PLAN_PATH,
                "modules",
                "module-id-uniqueness",
                "unique",
                module_ids,
            )
        )
    if len(work_item_ids) != len(set(work_item_ids)):
        errors.append(
            diagnostic(
                PLAN_PATH,
                "work_items",
                "work-item-id-uniqueness",
                "unique",
                work_item_ids,
            )
        )
    work_by_id = {
        item["id"]: item
        for item in work_items
        if isinstance(item, dict) and "id" in item
    }
    module_by_id = {
        item["id"]: item
        for item in modules
        if isinstance(item, dict) and "id" in item
    }
    for work_item_id, item in work_by_id.items():
        if not WORK_ITEM_RE.fullmatch(work_item_id):
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    work_item_id,
                    "work-item-id-format",
                    WORK_ITEM_RE.pattern,
                    work_item_id,
                )
            )
        status = item.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    work_item_id,
                    "work-item-status",
                    sorted(ALLOWED_STATUSES),
                    status,
                )
            )
        if status == "ACCEPTED":
            evidence = item.get("evidence")
            if not isinstance(evidence, dict):
                errors.append(
                    diagnostic(
                        PLAN_PATH,
                        work_item_id,
                        "accepted-evidence",
                        "mapping",
                        evidence,
                    )
                )
                continue
            for key in ("exact_head", "merge_commit"):
                actual = evidence.get(key)
                if not SHA_RE.fullmatch(str(actual or "")):
                    errors.append(
                        diagnostic(
                            PLAN_PATH,
                            work_item_id,
                            f"accepted-{key}",
                            "40 lowercase hex",
                            actual,
                        )
                    )
    reconciled = set(
        plan.get("reconciliation", {}).get("accepted_work_items", [])
    )
    for module_id, module in module_by_id.items():
        work_item_id = module.get("work_item")
        module_status = module.get("status")
        work_item_status = work_by_id.get(work_item_id, {}).get("status")
        code_status = module.get("code")
        if module_status not in ALLOWED_STATUSES:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    module_id,
                    "module-status",
                    sorted(ALLOWED_STATUSES),
                    module_status,
                )
            )
        if code_status not in ALLOWED_CODE_STATUSES:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    module_id,
                    "module-code-status",
                    sorted(ALLOWED_CODE_STATUSES),
                    code_status,
                )
            )
        if work_item_id not in work_by_id:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    module_id,
                    "module-work-item-reference",
                    "existing work item",
                    work_item_id,
                )
            )
        accepted_mismatch = (
            module_status == "ACCEPTED" and work_item_status != "ACCEPTED"
        )
        if work_item_id in reconciled:
            accepted_mismatch = accepted_mismatch or module_status != "ACCEPTED"
        if accepted_mismatch:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    module_id,
                    "stale-accepted-status",
                    "reconciled module/work-item accepted state",
                    {
                        "module": module_status,
                        "work_item": work_item_status,
                    },
                )
            )
        contract = root / str(module.get("contract", ""))
        if not contract.is_file():
            errors.append(
                diagnostic(
                    str(module.get("contract")),
                    module_id,
                    "module-contract-exists",
                    "file",
                    "missing",
                )
            )
            continue
        text = contract.read_text(encoding="utf-8")
        for marker in MODULE_MARKERS:
            if marker not in text:
                errors.append(
                    diagnostic(
                        str(module["contract"]),
                        module_id,
                        "module-contract-marker",
                        marker,
                        "missing",
                    )
                )
    _validate_module_order(plan, module_by_id, module_ids, errors)
    _validate_queue(plan, work_by_id, errors)
    return errors


def _validate_module_order(
    plan: dict[str, Any],
    module_by_id: dict[str, dict[str, Any]],
    module_ids: list[str],
    errors: list[str],
) -> None:
    order = plan.get("dependency_order", [])
    if set(order) != set(module_ids) or len(order) != len(set(order)):
        errors.append(
            diagnostic(
                PLAN_PATH,
                "dependency_order",
                "dependency-order-membership",
                sorted(module_ids),
                order,
            )
        )
        return
    position = {module_id: number for number, module_id in enumerate(order)}
    for module_id, module in module_by_id.items():
        for dependency in module.get("deps", []):
            if dependency not in module_by_id:
                errors.append(
                    diagnostic(
                        PLAN_PATH,
                        module_id,
                        "module-dependency-reference",
                        "existing module",
                        dependency,
                    )
                )
            elif position[dependency] >= position[module_id]:
                errors.append(
                    diagnostic(
                        PLAN_PATH,
                        module_id,
                        "dependency-topology",
                        f"{dependency} before {module_id}",
                        order,
                    )
                )


def _validate_queue(
    plan: dict[str, Any],
    work_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    queue = plan.get("execution", {}).get("domain_queue", [])
    actual_order = [item.get("order") for item in queue]
    expected_order = list(range(1, len(queue) + 1))
    if actual_order != expected_order:
        errors.append(
            diagnostic(
                PLAN_PATH,
                "domain_queue",
                "queue-order",
                expected_order,
                actual_order,
            )
        )
    for item in queue:
        work_item_id = item.get("work_item")
        if work_item_id not in work_by_id:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    work_item_id,
                    "queue-work-item-reference",
                    "existing work item",
                    work_item_id,
                )
            )
        elif work_by_id[work_item_id].get("status") == "ACCEPTED":
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    work_item_id,
                    "accepted-work-item-not-queued",
                    "absent from queue",
                    "present",
                )
            )
    safe_required = (
        "PROJECT-STATE-RECONCILIATION-001",
        "INDUSTRIALIZATION-PROGRAM-EXECUTION-001",
        "MODULE-ACTIVATION-CONTRACT-001",
        "SECRET-HYGIENE-001",
        "DEPENDENCY-PROVENANCE-001",
        "DEPLOYMENT-PROFILE-001",
        "BACKUP-RESTORE-DRILL-001",
        "SECURITY-BASELINE-001",
    )
    safe_complete = all(
        work_by_id.get(item_id, {}).get("status") == "ACCEPTED"
        for item_id in safe_required
    )
    registry_complete = (
        work_by_id.get("MODULE-REGISTRY-001", {}).get("status") == "ACCEPTED"
    )
    ux_foundations_complete = all(
        work_by_id.get(item_id, {}).get("status") == "ACCEPTED"
        for item_id in (
            "UX-PLATFORM-FOUNDATION-001",
            "PAGE-TEMPLATE-LIBRARY-001",
        )
    )
    if not safe_complete:
        expected_status = (
            "PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION"
        )
    elif not registry_complete:
        expected_status = "PAUSED_PENDING_MODULE_REGISTRY_AND_UX_FOUNDATIONS"
    elif not ux_foundations_complete:
        expected_status = "PAUSED_PENDING_UX_PLATFORM_AND_PAGE_TEMPLATES"
    else:
        expected_status = "READY_FOR_PRODUCT_MODULE_DEVELOPMENT"
    actual_status = plan.get("execution", {}).get("domain_queue_status")
    if actual_status != expected_status:
        errors.append(
            diagnostic(
                PLAN_PATH,
                "domain_queue",
                "domain-queue-state",
                expected_status,
                actual_status,
            )
        )


def _closure(program: Program, start: set[str]) -> set[str]:
    found: set[str] = set()
    stack = list(start)
    while stack:
        item = program.items.get(stack.pop())
        if item is None:
            continue
        for dependency in item.dependencies:
            if dependency not in found:
                found.add(dependency)
                stack.append(dependency)
    return found


def _split_references(value: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"\s*->\s*|\s*\|\s*", value or "")
        if part.strip()
    ]


def validate_program(
    program: Program, plan: dict[str, Any], root: Path
) -> list[str]:
    errors: list[str] = []
    if program.version != "1.0":
        errors.append(
            diagnostic(
                PROGRAM_PATH,
                "version",
                "accepted-program-version",
                "1.0",
                program.version,
            )
        )
    if program.status != "ACCEPTED":
        errors.append(
            diagnostic(
                PROGRAM_PATH,
                "status",
                "accepted-program-status",
                "ACCEPTED",
                program.status,
            )
        )
    if len(program.items) != 30:
        errors.append(
            diagnostic(
                PROGRAM_PATH,
                "phases",
                "program-work-item-count",
                30,
                len(program.items),
            )
        )
    planning_ids = set(identifiers(plan.get("work_items", [])))
    for work_item_id, item in program.items.items():
        if work_item_id not in planning_ids:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    work_item_id,
                    "industrialization-status-projection",
                    "work item status exists",
                    "missing",
                )
            )
        for dependency in item.dependencies:
            if dependency not in program.items:
                errors.append(
                    diagnostic(
                        PROGRAM_PATH,
                        work_item_id,
                        "dependency-reference",
                        "existing work item",
                        dependency,
                    )
                )
            elif program.items[dependency].phase > item.phase:
                errors.append(
                    diagnostic(
                        PROGRAM_PATH,
                        work_item_id,
                        "phase-order",
                        f"dependency phase <= {item.phase}",
                        f"{dependency} phase {program.items[dependency].phase}",
                    )
                )
    for gate_id in ("SAFE-CONTINUATION", "PILOT-READY"):
        gate = program.gates.get(gate_id)
        if gate is None:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    gate_id,
                    "gate-exists",
                    "present",
                    "missing",
                )
            )
            continue
        for work_item_id in gate.required:
            if work_item_id not in program.items:
                errors.append(
                    diagnostic(
                        PROGRAM_PATH,
                        gate_id,
                        "gate-work-item-reference",
                        "existing work item",
                        work_item_id,
                    )
                )
    pilot_gate = program.gates.get("PILOT-READY")
    if pilot_gate:
        mandatory_core = set(pilot_gate.required)
        for dependency in sorted(_closure(program, mandatory_core)):
            if dependency not in program.items or dependency in mandatory_core:
                continue
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    "PILOT-READY",
                    "mandatory-core-transitive-closure",
                    "dependency inside required_core_work_items",
                    dependency,
                )
            )
            if dependency in program.scope_dependent:
                errors.append(
                    diagnostic(
                        PROGRAM_PATH,
                        "PILOT-READY",
                        "hidden-scope-dependent-dependency",
                        "no scope-dependent dependency in mandatory core closure",
                        dependency,
                    )
                )
    _validate_risk_register(program, root, errors)
    return errors


def _validate_risk_register(
    program: Program, root: Path, errors: list[str]
) -> None:
    path = root / RISK_PATH
    if not path.is_file():
        errors.append(
            diagnostic(
                RISK_PATH,
                "risk-register",
                "risk-register-exists",
                "file",
                "missing",
            )
        )
        return
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            for work_item_id in _split_references(
                row.get("proposed_work_item", "")
            ):
                if work_item_id not in program.items:
                    errors.append(
                        diagnostic(
                            RISK_PATH,
                            row.get("identifier", "<unknown>"),
                            "risk-proposed-work-item-reference",
                            "existing program work item",
                            work_item_id,
                        )
                    )


def validate_views(
    plan: dict[str, Any], program: Program, root: Path
) -> list[str]:
    expected = {
        plan["views"]["module_map"]: render_module_map(plan),
        plan["views"]["sequence"]: render_sequence(plan, program),
        plan["views"]["checklist"]: render_checklist(plan, program),
        PROGRAM_MD_PATH: render_program_markdown(program.raw),
    }
    errors: list[str] = []
    for relative, expected_content in expected.items():
        path = root / relative
        actual_content = (
            path.read_text(encoding="utf-8") if path.is_file() else None
        )
        if actual_content != expected_content:
            errors.append(
                diagnostic(
                    relative,
                    "derived-view",
                    "exact-generated-projection",
                    "generator output",
                    "missing or stale",
                )
            )
    return errors


def validate_repository(root: Path) -> list[str]:
    try:
        plan = load_plan(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [
            diagnostic(
                PLAN_PATH,
                "load",
                "plan-load",
                "valid JSON object",
                str(exc),
            )
        ]
    errors = validate_plan(plan, root)
    try:
        program = load_program(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return errors + [
            diagnostic(
                PROGRAM_PATH,
                "load",
                "program-load",
                "valid JSON object",
                str(exc),
            )
        ]
    errors.extend(validate_program(program, plan, root))
    errors.extend(validate_views(plan, program, root))
    return errors
