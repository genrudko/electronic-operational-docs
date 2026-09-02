"""Executable industrialization backlog, gate and residual-risk contract.

The canonical split is intentional:
- DEMO_RELEASE_PLAN.yaml owns mutable work-item statuses and acceptance evidence;
- INDUSTRIALIZATION_PROGRAM.yaml owns stable phases, dependencies, execution
  policy, risk ownership requirements and gate boundaries;
- this module validates the join and renders a deterministic human view.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

try:
    from .release_plan_model import (
        ALLOWED_STATUSES,
        PLAN_PATH,
        PROGRAM_PATH,
        RISK_PATH,
        SHA_RE,
        diagnostic,
    )
except ImportError:
    from release_plan_model import (
        ALLOWED_STATUSES,
        PLAN_PATH,
        PROGRAM_PATH,
        RISK_PATH,
        SHA_RE,
        diagnostic,
    )

EXECUTION_VIEW_PATH = "docs/project/INDUSTRIALIZATION_EXECUTION_BACKLOG.md"

GATE_IMPACTS = (
    "SAFE-CONTINUATION",
    "PILOT-READY-MANDATORY-CORE",
    "PILOT-SCOPE-DEPENDENT",
    "FULL-PROGRAM-ONLY",
)
ACTIVE_STATES = frozenset({"IN_PROGRESS", "AT_REVIEW"})
STARTED_STATES = frozenset({"READY", "IN_PROGRESS", "AT_REVIEW", "ACCEPTED"})

EXPECTED_SAFE = (
    "PROJECT-STATE-RECONCILIATION-001",
    "INDUSTRIALIZATION-PROGRAM-EXECUTION-001",
    "MODULE-ACTIVATION-CONTRACT-001",
    "SECRET-HYGIENE-001",
    "DEPENDENCY-PROVENANCE-001",
    "DEPLOYMENT-PROFILE-001",
    "BACKUP-RESTORE-DRILL-001",
    "SECURITY-BASELINE-001",
)
EXPECTED_PILOT_CORE = (
    "PROJECT-STATE-RECONCILIATION-001",
    "INDUSTRIALIZATION-PROGRAM-EXECUTION-001",
    "MODULE-ACTIVATION-CONTRACT-001",
    "SECRET-HYGIENE-001",
    "DEPENDENCY-PROVENANCE-001",
    "DEPLOYMENT-PROFILE-001",
    "BACKUP-RESTORE-DRILL-001",
    "SECURITY-BASELINE-001",
    "MODULE-REGISTRY-001",
    "DATA-INTEGRITY-HARDENING-001",
    "MIGRATION-SAFETY-001",
    "MODULE-MIGRATION-COMPATIBILITY-001",
    "DATA-GOVERNANCE-001",
    "RELEASE-ROLLBACK-001",
    "OBSERVABILITY-001",
    "INCIDENT-RESPONSE-001",
    "AUTH-RBAC-HARDENING-001",
    "SECURITY-PIPELINE-001",
    "UX-BROWSER-GATES-001",
    "SUPPORT-HANDOVER-001",
    "PILOT-READINESS-001",
)
EXPECTED_SCOPE_DEPENDENT = (
    "UPLOAD-HARDENING-001",
    "DATA-PORTABILITY-001",
    "LEGACY-UX-MIGRATION-001",
    "UX-PLATFORM-FOUNDATION-001",
    "PAGE-TEMPLATE-LIBRARY-001",
    "MODULE-SOURCE-GOVERNANCE-001",
    "DRIVE-LIBRARY-GOVERNANCE-001",
    "PERFORMANCE-BASELINE-001",
)
EXPECTED_PHASE_ZERO = (
    "PROJECT-STATE-RECONCILIATION-001",
    "INDUSTRIALIZATION-PROGRAM-EXECUTION-001",
)

REQUIRED_RESIDUAL_FIELDS = (
    "risk_id",
    "applicability",
    "owner_role",
    "accountable_owner",
    "compensating_controls",
    "due_date",
    "review_condition",
    "affected_gate",
    "acceptance_authority",
    "acceptance_status",
    "evidence_reference",
    "expires_or_review_at",
)


def _program_items(program_raw: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    result: list[tuple[int, dict[str, Any]]] = []
    for phase in program_raw.get("phases", []):
        phase_id = int(phase.get("id", -1))
        for item in phase.get("work_items", []):
            if isinstance(item, dict):
                result.append((phase_id, item))
    return result


def _plan_items(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in plan.get("work_items", [])
        if isinstance(item, dict) and item.get("id")
    }


def _gate(program_raw: dict[str, Any], gate_id: str) -> dict[str, Any] | None:
    return next(
        (
            gate
            for gate in program_raw.get("gates", [])
            if isinstance(gate, dict) and gate.get("id") == gate_id
        ),
        None,
    )


def _required(gate: dict[str, Any] | None) -> tuple[str, ...]:
    if not gate:
        return ()
    values = gate.get("required_work_items")
    if values is None:
        values = gate.get("required_core_work_items", [])
    return tuple(str(value) for value in values)


def _scope_entries(gate: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not gate:
        return []
    return [
        entry
        for entry in gate.get("scope_dependent_work_items", [])
        if isinstance(entry, dict)
    ]


def risk_ids(root: Path) -> set[str]:
    path = root / RISK_PATH
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            str(row.get("identifier", "")).strip()
            for row in csv.DictReader(handle, delimiter=";")
            if str(row.get("identifier", "")).strip()
        }


def _status(plan_items: dict[str, dict[str, Any]], item_id: str) -> str:
    return str(plan_items.get(item_id, {}).get("status", "MISSING"))


def _phase_zero_complete(plan_items: dict[str, dict[str, Any]]) -> bool:
    return all(_status(plan_items, item_id) == "ACCEPTED" for item_id in EXPECTED_PHASE_ZERO)


def blockers(
    item_id: str,
    phase: int,
    item: dict[str, Any],
    plan_items: dict[str, dict[str, Any]],
) -> list[str]:
    found: list[str] = []
    if phase == 1 and not _phase_zero_complete(plan_items):
        found.append("PHASE_0_NOT_ACCEPTED")
    for dependency in item.get("dependencies", []):
        if _status(plan_items, str(dependency)) != "ACCEPTED":
            found.append(f"DEPENDENCY_NOT_ACCEPTED:{dependency}")
    return found


def _transition_map(program_raw: dict[str, Any], profile: str) -> dict[str, list[str]]:
    contract = program_raw.get("execution_contract", {})
    profiles = contract.get("transition_profiles", {})
    value = profiles.get(profile, {})
    return value if isinstance(value, dict) else {}


def _validate_gate_boundaries(program_raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    safe = _required(_gate(program_raw, "SAFE-CONTINUATION"))
    pilot_gate = _gate(program_raw, "PILOT-READY")
    pilot = _required(pilot_gate)
    scope = tuple(str(entry.get("id")) for entry in _scope_entries(pilot_gate))
    for identifier, actual, expected in (
        ("SAFE-CONTINUATION", safe, EXPECTED_SAFE),
        ("PILOT-READY", pilot, EXPECTED_PILOT_CORE),
        ("PILOT-READY.scope-dependent", scope, EXPECTED_SCOPE_DEPENDENT),
    ):
        if actual != expected:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "gate-membership-contract",
                    list(expected),
                    list(actual),
                )
            )
    contract_phase_zero = tuple(
        str(value)
        for value in program_raw.get("execution_contract", {}).get(
            "phase_zero_work_items", []
        )
    )
    if contract_phase_zero != EXPECTED_PHASE_ZERO:
        errors.append(
            diagnostic(
                PROGRAM_PATH,
                "Phase 0",
                "phase-zero-membership-contract",
                list(EXPECTED_PHASE_ZERO),
                list(contract_phase_zero),
            )
        )
    return errors


def _validate_item_metadata(
    program_raw: dict[str, Any],
    plan: dict[str, Any],
    known_risks: set[str],
) -> list[str]:
    errors: list[str] = []
    plan_items = _plan_items(plan)
    program_items = _program_items(program_raw)
    groups = program_raw.get("execution_contract", {}).get(
        "parallelization_groups", {}
    )
    for _phase, item in program_items:
        item_id = str(item.get("id", "<missing>"))
        required_text = (
            ("owner_role", "owner-role", "non-empty role"),
            (
                "acceptance_evidence_requirements",
                "acceptance-evidence-contract",
                "non-empty list",
            ),
            ("gate_impact", "gate-classification", list(GATE_IMPACTS)),
            ("transition_profile", "transition-profile", "defined profile"),
            (
                "parallelization_group",
                "parallelization-classification",
                "defined group",
            ),
            (
                "sequential_constraint",
                "sequential-constraint",
                "non-empty rule",
            ),
            ("blocking_rule", "blocking-rule", "non-empty rule"),
        )
        for field, rule, expected in required_text:
            actual = item.get(field)
            empty = actual in (None, "", [])
            if empty:
                errors.append(
                    diagnostic(PROGRAM_PATH, item_id, rule, expected, actual)
                )
        evidence_requirements = item.get("acceptance_evidence_requirements")
        if not isinstance(evidence_requirements, list) or not evidence_requirements:
            if not any(
                f"[{item_id}] rule=acceptance-evidence-contract" in error
                for error in errors
            ):
                errors.append(
                    diagnostic(
                        PROGRAM_PATH,
                        item_id,
                        "acceptance-evidence-contract",
                        "non-empty list",
                        evidence_requirements,
                    )
                )
        risks = item.get("risks")
        if not isinstance(risks, list) or not risks:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    item_id,
                    "risk-classification",
                    "at least one risk ID",
                    risks,
                )
            )
        else:
            for risk_id in risks:
                if str(risk_id) not in known_risks:
                    errors.append(
                        diagnostic(
                            PROGRAM_PATH,
                            item_id,
                            "risk-reference",
                            "existing risk ID",
                            risk_id,
                        )
                    )
        gate_impact = item.get("gate_impact")
        if gate_impact not in GATE_IMPACTS:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    item_id,
                    "gate-classification",
                    list(GATE_IMPACTS),
                    gate_impact,
                )
            )
        profile = str(item.get("transition_profile", ""))
        if not _transition_map(program_raw, profile):
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    item_id,
                    "transition-profile",
                    "defined non-empty profile",
                    profile,
                )
            )
        group = str(item.get("parallelization_group", ""))
        if group not in groups:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    item_id,
                    "parallelization-classification",
                    sorted(groups),
                    group,
                )
            )
        if item_id not in plan_items:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    item_id,
                    "execution-state-projection",
                    "status owned by DEMO_RELEASE_PLAN.yaml",
                    "missing",
                )
            )
        for forbidden in ("status", "execution_state", "planning_status"):
            if forbidden in item:
                errors.append(
                    diagnostic(
                        PROGRAM_PATH,
                        item_id,
                        "single-planning-state-owner",
                        f"{PLAN_PATH} only",
                        f"program item contains {forbidden}",
                    )
                )
    if len(program_items) != 30:
        errors.append(
            diagnostic(
                PROGRAM_PATH,
                "work_items",
                "execution-metadata-count",
                30,
                len(program_items),
            )
        )
    return errors


def _validated_acceptance_evidence(
    item_id: str, evidence: dict[str, Any]
) -> dict[str, Any]:
    """Return the evidence mapping with one bounded accepted-name alias.

    PR #68 was accepted with the runtime proof stored as ``module_registry_runtime``
    before the industrialization requirement named the same proof
    ``mixed_scope_activation_evidence``. Preserve the immutable accepted payload
    while keeping the newer requirement fail-closed and Registry-specific.
    """
    if (
        item_id == "MODULE-REGISTRY-001"
        and evidence.get("module_registry_runtime")
        and not evidence.get("mixed_scope_activation_evidence")
    ):
        normalized = dict(evidence)
        normalized["mixed_scope_activation_evidence"] = evidence[
            "module_registry_runtime"
        ]
        return normalized
    return evidence


def _validate_transitions_and_dependencies(
    program_raw: dict[str, Any], plan: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    plan_items = _plan_items(plan)
    for phase, item in _program_items(program_raw):
        item_id = str(item.get("id"))
        plan_item = plan_items.get(item_id, {})
        status = plan_item.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    item_id,
                    "execution-state",
                    list(ALLOWED_STATUSES),
                    status,
                )
            )
            continue
        profile = str(item.get("transition_profile", ""))
        transition_map = _transition_map(program_raw, profile)
        transition = plan_item.get("transition")
        if transition is not None:
            if not isinstance(transition, dict):
                errors.append(
                    diagnostic(
                        PLAN_PATH,
                        item_id,
                        "state-transition-record",
                        "mapping",
                        transition,
                    )
                )
            else:
                from_state = str(transition.get("from", ""))
                to_state = str(transition.get("to", ""))
                allowed = transition_map.get(from_state, [])
                if to_state not in allowed:
                    errors.append(
                        diagnostic(
                            PLAN_PATH,
                            item_id,
                            "state-transition",
                            allowed,
                            f"{from_state}->{to_state}",
                        )
                    )
                if to_state != status:
                    errors.append(
                        diagnostic(
                            PLAN_PATH,
                            item_id,
                            "state-transition-target",
                            status,
                            to_state,
                        )
                    )
                if not str(transition.get("evidence_reference", "")).strip():
                    errors.append(
                        diagnostic(
                            PLAN_PATH,
                            item_id,
                            "state-transition-evidence",
                            "non-empty evidence reference",
                            transition.get("evidence_reference"),
                        )
                    )
        current_blockers = blockers(item_id, phase, item, plan_items)
        if status in STARTED_STATES and current_blockers:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    item_id,
                    "dependency-bypass",
                    "all start blockers cleared",
                    current_blockers,
                )
            )
        if status == "IN_PROGRESS" and current_blockers:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    item_id,
                    "in-progress-dependency-closure",
                    "dependencies ACCEPTED",
                    current_blockers,
                )
            )
        if status == "BLOCKED" and not str(
            plan_item.get("blocking_reason", "")
        ).strip():
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    item_id,
                    "blocked-reason",
                    "non-empty blocking_reason",
                    plan_item.get("blocking_reason"),
                )
            )
        if status == "ACCEPTED":
            evidence = plan_item.get("evidence")
            if not isinstance(evidence, dict):
                errors.append(
                    diagnostic(
                        PLAN_PATH,
                        item_id,
                        "accepted-execution-evidence",
                        "mapping with PR/exact head/merge commit",
                        evidence,
                    )
                )
            else:
                validated_evidence = _validated_acceptance_evidence(
                    item_id, evidence
                )
                expected_fields = item.get(
                    "acceptance_evidence_requirements", []
                )
                missing = [
                    field
                    for field in expected_fields
                    if not validated_evidence.get(field)
                ]
                if missing:
                    errors.append(
                        diagnostic(
                            PLAN_PATH,
                            item_id,
                            "accepted-execution-evidence",
                            expected_fields,
                            {"missing": missing, "evidence": evidence},
                        )
                    )
                for key in ("exact_head", "merge_commit"):
                    if key in expected_fields and not SHA_RE.fullmatch(
                        str(validated_evidence.get(key, ""))
                    ):
                        errors.append(
                            diagnostic(
                                PLAN_PATH,
                                item_id,
                                f"accepted-{key}",
                                "40 lowercase hex",
                                validated_evidence.get(key),
                            )
                        )
    return errors


def _validate_parallelization(
    program_raw: dict[str, Any], plan: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    plan_items = _plan_items(plan)
    groups = program_raw.get("execution_contract", {}).get(
        "parallelization_groups", {}
    )
    active_by_group: dict[str, list[str]] = defaultdict(list)
    for _, item in _program_items(program_raw):
        item_id = str(item.get("id"))
        if _status(plan_items, item_id) in ACTIVE_STATES:
            active_by_group[str(item.get("parallelization_group", ""))].append(
                item_id
            )
    for group_id, active in active_by_group.items():
        policy = groups.get(group_id, {})
        max_active = int(policy.get("max_active", 0) or 0)
        mode = policy.get("mode")
        if max_active < 1 or len(active) > max_active:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    group_id,
                    "parallelization-limit",
                    {"mode": mode, "max_active": max_active},
                    active,
                )
            )
    return errors


def _validate_residual_risks(
    program_raw: dict[str, Any], known_risks: set[str]
) -> list[str]:
    errors: list[str] = []
    contract = program_raw.get("residual_risk_contract", {})
    required = tuple(contract.get("required_fields", []))
    if required != REQUIRED_RESIDUAL_FIELDS:
        errors.append(
            diagnostic(
                PROGRAM_PATH,
                "residual-risk-contract",
                "residual-risk-required-fields",
                list(REQUIRED_RESIDUAL_FIELDS),
                list(required),
            )
        )
    allowed_applicability = set(contract.get("allowed_applicability", []))
    allowed_acceptance = set(contract.get("allowed_acceptance_status", []))
    placeholder = str(contract.get("accountable_owner_placeholder", ""))
    records = program_raw.get("residual_risks", [])
    if not isinstance(records, list):
        return errors + [
            diagnostic(
                PROGRAM_PATH,
                "residual_risks",
                "residual-risk-records",
                "list",
                records,
            )
        ]
    for number, record in enumerate(records, start=1):
        identifier = (
            str(record.get("risk_id"))
            if isinstance(record, dict)
            else f"record-{number}"
        )
        if not isinstance(record, dict):
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-record",
                    "mapping",
                    record,
                )
            )
            continue
        missing = [
            field
            for field in REQUIRED_RESIDUAL_FIELDS
            if field not in record
            or record.get(field) in (None, "", [])
        ]
        if missing:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-completeness",
                    list(REQUIRED_RESIDUAL_FIELDS),
                    {"missing": missing},
                )
            )
        risk_id = str(record.get("risk_id", ""))
        if risk_id not in known_risks:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-reference",
                    "existing risk ID",
                    risk_id,
                )
            )
        if record.get("applicability") not in allowed_applicability:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-applicability",
                    sorted(allowed_applicability),
                    record.get("applicability"),
                )
            )
        if record.get("acceptance_status") not in allowed_acceptance:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-acceptance-status",
                    sorted(allowed_acceptance),
                    record.get("acceptance_status"),
                )
            )
        owner = str(record.get("accountable_owner", ""))
        if not str(record.get("owner_role", "")).strip() or not owner:
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-owner",
                    "owner role and accountable owner",
                    {
                        "owner_role": record.get("owner_role"),
                        "accountable_owner": owner,
                    },
                )
            )
        if owner == placeholder and record.get("acceptance_status") == "ACCEPTED":
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-owner",
                    "named accountable owner before ACCEPTED",
                    owner,
                )
            )
        if not str(record.get("due_date", "")).strip():
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-due-date",
                    "non-empty due date",
                    record.get("due_date"),
                )
            )
        if not record.get("compensating_controls"):
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-controls",
                    "non-empty controls",
                    record.get("compensating_controls"),
                )
            )
        if not str(record.get("review_condition", "")).strip():
            errors.append(
                diagnostic(
                    PROGRAM_PATH,
                    identifier,
                    "residual-risk-review-condition",
                    "non-empty review condition",
                    record.get("review_condition"),
                )
            )
        if record.get("acceptance_status") == "ACCEPTED":
            acceptance_fields = (
                "acceptance_authority",
                "evidence_reference",
                "expires_or_review_at",
            )
            absent = [field for field in acceptance_fields if not record.get(field)]
            if absent:
                errors.append(
                    diagnostic(
                        PROGRAM_PATH,
                        identifier,
                        "residual-risk-explicit-acceptance",
                        list(acceptance_fields),
                        {"missing": absent},
                    )
                )
    return errors



def _validate_no_accepted_active_queue(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    plan_items = _plan_items(plan)
    execution = plan.get("execution", {})
    if not isinstance(execution, dict):
        return errors
    for queue_name, queue in execution.items():
        if not isinstance(queue, list):
            continue
        for entry in queue:
            if not isinstance(entry, dict) or "work_item" not in entry:
                continue
            item_id = str(entry.get("work_item"))
            if _status(plan_items, item_id) == "ACCEPTED":
                errors.append(
                    diagnostic(
                        PLAN_PATH,
                        item_id,
                        "accepted-work-item-not-queued",
                        "absent from active queues",
                        queue_name,
                    )
                )
    return errors


def validate_github_evidence(
    plan: dict[str, Any], github_evidence: dict[str, Any] | None
) -> list[str]:
    """Validate supplied GitHub facts without requiring a network.

    CI already validates the active PR via GITHUB_EVENT_PATH. This function is
    also used by offline fixtures to prove contradictory accepted/current facts
    fail closed.
    """
    if github_evidence is None:
        return []
    errors: list[str] = []
    plan_items = _plan_items(plan)
    for item_id, facts in github_evidence.items():
        if not isinstance(facts, dict) or item_id not in plan_items:
            continue
        canonical = plan_items[item_id]
        status = canonical.get("status")
        actual_status = facts.get("canonical_status")
        if actual_status is not None and actual_status != status:
            errors.append(
                diagnostic(
                    PLAN_PATH,
                    item_id,
                    "github-canonical-status",
                    actual_status,
                    status,
                )
            )
        evidence = canonical.get("evidence", {})
        for field in ("pr", "exact_head", "merge_commit"):
            if field in facts and facts[field] != evidence.get(field):
                errors.append(
                    diagnostic(
                        PLAN_PATH,
                        item_id,
                        "github-acceptance-evidence",
                        facts[field],
                        evidence.get(field),
                    )
                )
    return errors


def validate_execution_contract(
    program_raw: dict[str, Any],
    plan: dict[str, Any],
    root: Path,
    *,
    github_evidence: dict[str, Any] | None = None,
) -> list[str]:
    known_risks = risk_ids(root)
    errors = _validate_gate_boundaries(program_raw)
    errors.extend(_validate_item_metadata(program_raw, plan, known_risks))
    errors.extend(_validate_transitions_and_dependencies(program_raw, plan))
    errors.extend(_validate_parallelization(program_raw, plan))
    errors.extend(_validate_residual_risks(program_raw, known_risks))
    errors.extend(_validate_no_accepted_active_queue(plan))
    errors.extend(validate_github_evidence(plan, github_evidence))
    return errors


def _progress(ids: Iterable[str], statuses: dict[str, str]) -> tuple[int, int]:
    values = list(ids)
    return sum(statuses.get(item_id) == "ACCEPTED" for item_id in values), len(values)


def render_execution_backlog(
    program_raw: dict[str, Any], plan: dict[str, Any]
) -> str:
    plan_items = _plan_items(plan)
    statuses = {
        item_id: str(item.get("status", "MISSING"))
        for item_id, item in plan_items.items()
    }
    phase_items: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for phase, item in _program_items(program_raw):
        phase_items[phase].append(item)
    safe_done, safe_total = _progress(EXPECTED_SAFE, statuses)
    pilot_done, pilot_total = _progress(EXPECTED_PILOT_CORE, statuses)
    lines = [
        "# Исполнимый backlog программы индустриализации",
        "",
        "> GENERATED VIEW. Mutable execution state принадлежит только "
        "`docs/project/DEMO_RELEASE_PLAN.yaml`; phases, dependencies, risk and "
        "gate rules принадлежат `docs/project/INDUSTRIALIZATION_PROGRAM.yaml`. "
        "Ручное изменение файла отклоняется побайтной проверкой.",
        "",
        "## 1. Product-owner / operator summary",
        "",
        f"- Phase 0: `{'COMPLETE' if _phase_zero_complete(plan_items) else 'IN PROGRESS'}`.",
        f"- `SAFE-CONTINUATION`: `{safe_done}/{safe_total}` accepted; "
        f"**{'ACHIEVED' if safe_done == safe_total else 'NOT ACHIEVED'}**.",
        (
            "- `PILOT-READY` mandatory core: "
            f"`{pilot_done}/{pilot_total}` accepted; **NOT ACHIEVED**."
        ),
        "- Предметная очередь: "
        f"`{plan.get('execution', {}).get('domain_queue_status', 'UNKNOWN')}`.",
        "- `SHIFT-HANDOVER-001`: `NOT STARTED`; automatic start forbidden.",
        "- Достижение всех checklist items не заменяет отдельное решение владельца.",
        "",
        "## 2. Canonical ownership",
        "",
        "| Данные | Единственный владелец |",
        "|---|---|",
        "| Volatile active project state | `docs/project/CURRENT_STATE.md` |",
        (
            "| Work-item execution state and acceptance evidence | "
            "`docs/project/DEMO_RELEASE_PLAN.yaml` |"
        ),
        (
            "| Phases, dependencies, execution policy, risks and gate boundaries | "
            "`docs/project/INDUSTRIALIZATION_PROGRAM.yaml` |"
        ),
        "| Этот backlog и progress tables | generated projection only |",
        "",
        "## 3. Full industrial backlog",
        "",
        (
            "| Phase | Work item | Priority | Type | State | Risks | Dependencies | "
            "Owner role | Acceptance evidence | Gate impact | Parallel group | "
            "Sequential constraint | Current blocker |"
        ),
        "|---:|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for phase, item in _program_items(program_raw):
        item_id = str(item["id"])
        risk_text = ", ".join(f"`{risk}`" for risk in item.get("risks", [])) or "—"
        dependency_text = ", ".join(
            f"`{dependency}`" for dependency in item.get("dependencies", [])
        ) or "—"
        evidence_text = ", ".join(
            f"`{field}`"
            for field in item.get("acceptance_evidence_requirements", [])
        ) or "—"
        current_blockers = blockers(item_id, phase, item, plan_items)
        blocker_text = "; ".join(current_blockers) if current_blockers else "—"
        lines.append(
            f"| {phase} | `{item_id}` | `{item.get('priority')}` | "
            f"`{item.get('type')}` | `{statuses.get(item_id, 'MISSING')}` | "
            f"{risk_text} | {dependency_text} | `{item.get('owner_role')}` | "
            f"{evidence_text} | `{item.get('gate_impact')}` | "
            f"`{item.get('parallelization_group')}` | "
            f"`{item.get('sequential_constraint')}` | {blocker_text} |"
        )
    lines.extend(
        [
            "",
            "## 4. Progress by phase",
            "",
            "| Phase | Accepted | Active | Blocked | Not started/ready |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for phase in sorted(phase_items):
        values = [
            statuses.get(str(item["id"]), "MISSING")
            for item in phase_items[phase]
        ]
        lines.append(
            f"| {phase} | {values.count('ACCEPTED')}/{len(values)} | "
            f"{sum(value in ACTIVE_STATES for value in values)} | "
            f"{values.count('BLOCKED')} | "
            f"{sum(value in {'NOT_STARTED', 'READY'} for value in values)} |"
        )
    lines.extend(["", "## 5. SAFE-CONTINUATION progress", ""])
    for item_id in EXPECTED_SAFE:
        checked = "x" if statuses.get(item_id) == "ACCEPTED" else " "
        status = statuses.get(item_id, "MISSING")
        lines.append(f"- [{checked}] `{item_id}` — `{status}`.")
    lines.extend(
        [
            "",
            "SAFE-CONTINUATION is complete. The product owner explicitly selected "
            "MODULE-REGISTRY -> UX foundation/page templates -> product/module "
            "development before remaining risk-based PILOT-READY hardening.",
            "",
            "## 6. PILOT-READY mandatory core",
            "",
        ]
    )
    for item_id in EXPECTED_PILOT_CORE:
        checked = "x" if statuses.get(item_id) == "ACCEPTED" else " "
        status = statuses.get(item_id, "MISSING")
        lines.append(f"- [{checked}] `{item_id}` — `{status}`.")
    lines.extend(
        [
            "",
            "## 7. Pilot-scope-dependent triggers",
            "",
            "| Work item | Trigger | Current state |",
            "|---|---|---|",
        ]
    )
    for entry in _scope_entries(_gate(program_raw, "PILOT-READY")):
        item_id = str(entry["id"])
        status = statuses.get(item_id, "MISSING")
        lines.append(f"| `{item_id}` | {entry['trigger']} | `{status}` |")
    lines.extend(
        [
            "",
            "## 8. Dependency and parallelization",
            "",
            "### Phase 0 / Phase 1 order",
            "",
            "1. `PROJECT-STATE-RECONCILIATION-001` is the accepted prerequisite.",
            "2. `INDUSTRIALIZATION-PROGRAM-EXECUTION-001` completes Phase 0 "
            "only after its own acceptance.",
            "3. Phase 1 is not complete or started automatically by Phase 0 "
            "acceptance.",
            "4. After Phase 0 acceptance, `MODULE-ACTIVATION-CONTRACT-001` and "
            "`SECRET-HYGIENE-001` may start in parallel.",
            "5. `DEPENDENCY-PROVENANCE-001` follows `SECRET-HYGIENE-001`; "
            "`DEPLOYMENT-PROFILE-001` follows dependency provenance.",
            "6. `BACKUP-RESTORE-DRILL-001` and `SECURITY-BASELINE-001` may run "
            "in parallel after deployment profile acceptance.",
            "7. Dependency bypass and exceeding a parallel group limit are "
            "fail-closed.",
            "",
            "### Parallelization groups",
            "",
            "| Group | Mode | Max active | Members |",
            "|---|---|---:|---|",
        ]
    )
    groups = program_raw.get("execution_contract", {}).get(
        "parallelization_groups", {}
    )
    members: dict[str, list[str]] = defaultdict(list)
    for _, item in _program_items(program_raw):
        members[str(item.get("parallelization_group"))].append(str(item.get("id")))
    for group_id, policy in groups.items():
        lines.append(
            f"| `{group_id}` | `{policy.get('mode')}` | {policy.get('max_active')} | "
            + ", ".join(f"`{value}`" for value in members.get(group_id, []))
            + " |"
        )
    lines.extend(
        [
            "",
            "## 9. Risk-to-work-item ownership",
            "",
            "| Risk | Work items / owner roles |",
            "|---|---|",
        ]
    )
    risk_owners: dict[str, list[str]] = defaultdict(list)
    for _, item in _program_items(program_raw):
        for risk_id in item.get("risks", []):
            risk_owners[str(risk_id)].append(
                f"`{item['id']}` / `{item.get('owner_role')}`"
            )
    for risk_id in sorted(risk_owners):
        lines.append(f"| `{risk_id}` | {'; '.join(risk_owners[risk_id])} |")
    lines.extend(
        [
            "",
            "## 10. Residual-risk contract",
            "",
            "A risk is not accepted merely because a `status` field says so. "
            "Every accepted or temporarily retained risk must contain:",
            "",
        ]
    )
    for field in REQUIRED_RESIDUAL_FIELDS:
        lines.append(f"- `{field}`")
    records = program_raw.get("residual_risks", [])
    lines.extend(["", f"Current residual-risk records: `{len(records)}`.", ""])
    if records:
        lines.extend(
            [
                "| Risk | Applicability | Owner | Gate | Acceptance | Due/review |",
                "|---|---|---|---|---|---|",
            ]
        )
        for record in records:
            lines.append(
                f"| `{record.get('risk_id')}` | `{record.get('applicability')}` | "
                f"`{record.get('owner_role')}` / "
                f"`{record.get('accountable_owner')}` | "
                f"`{record.get('affected_gate')}` | "
                f"`{record.get('acceptance_status')}` | "
                f"`{record.get('due_date')}` / "
                f"`{record.get('expires_or_review_at')}` |"
            )
    lines.extend(
        [
            "",
            "## 11. Fail-closed rules",
            "",
            "- Missing owner/evidence/risk/gate/parallelization metadata is "
            "rejected.",
            "- Invalid states and transitions are rejected.",
            "- `ACCEPTED` requires the declared evidence fields.",
            "- Start or acceptance with an open dependency is rejected.",
            "- Phase 1 start before all Phase 0 items are accepted is rejected.",
            "- Gate membership is compared with the owner-approved frozen sets.",
            "- Residual risks require named accountability, controls, due/review "
            "and explicit authority.",
            "- A second mutable planning-state owner is rejected.",
            "- This generated file is compared byte-for-byte.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_execution_view(
    program_raw: dict[str, Any], plan: dict[str, Any], root: Path
) -> list[str]:
    path = root / EXECUTION_VIEW_PATH
    expected = render_execution_backlog(program_raw, plan)
    actual = path.read_text(encoding="utf-8") if path.is_file() else None
    if actual != expected:
        return [
            diagnostic(
                EXECUTION_VIEW_PATH,
                "industrialization-execution",
                "exact-generated-projection",
                expected,
                actual,
            )
        ]
    return []


def load_raw(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = json.loads((root / PLAN_PATH).read_text(encoding="utf-8"))
    program = json.loads((root / PROGRAM_PATH).read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or not isinstance(program, dict):
        raise ValueError("canonical roots must be objects")
    return program, plan
