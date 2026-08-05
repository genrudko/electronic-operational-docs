"""Compatibility checks retained from the accepted schema-1 release plan."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

try:
    from .release_plan_model import (
        ALLOWED_CODE_STATUSES,
        ALLOWED_DEPTHS,
        ALLOWED_GROUPS,
        ALLOWED_STATUSES,
        COMPETITOR_MATRIX_PATH,
        COVERAGE_DECISIONS_PATH,
        COVERAGE_SOURCE_PATH,
        DECISION_PROFILES_PATH,
        EXPECTED_MODULE_IDS,
        EXPECTED_POST_DEMO,
        EXPECTED_SCENARIOS,
        LEGAL_MODE_MATRIX_PATH,
        MODULE_MARKERS,
        PERSONNEL_AUTHORITY_MATRIX_PATH,
        PLAN_PATH,
        REJECTED_CONTRACT_BOILERPLATE,
        SOURCE_REGISTRY_PATH,
        split_pipe,
    )
except ImportError:
    from release_plan_model import (
        ALLOWED_CODE_STATUSES,
        ALLOWED_DEPTHS,
        ALLOWED_GROUPS,
        ALLOWED_STATUSES,
        COMPETITOR_MATRIX_PATH,
        COVERAGE_DECISIONS_PATH,
        COVERAGE_SOURCE_PATH,
        DECISION_PROFILES_PATH,
        EXPECTED_MODULE_IDS,
        EXPECTED_POST_DEMO,
        EXPECTED_SCENARIOS,
        LEGAL_MODE_MATRIX_PATH,
        MODULE_MARKERS,
        PERSONNEL_AUTHORITY_MATRIX_PATH,
        PLAN_PATH,
        REJECTED_CONTRACT_BOILERPLATE,
        SOURCE_REGISTRY_PATH,
        split_pipe,
    )

EXPECTED_OWNERS = {
    "state": "docs/project/CURRENT_STATE.md",
    "plan": PLAN_PATH,
    "coverage_source": COVERAGE_SOURCE_PATH,
    "coverage_decisions": COVERAGE_DECISIONS_PATH,
}
EXPECTED_REFERENCE_IDS = [f"REF-OD-{number:03d}" for number in range(1, 67)]
EXPECTED_COMPETITOR_DECISIONS = [f"D-{number:02d}" for number in range(1, 17)]
REQUIRED_COMPETITOR_MAPPINGS = {
    "D-08": "DEFECT",
    "D-11": "GROUNDING",
    "D-14": "NORMATIVE-EVIDENCE",
}
PERSONNEL_AUTHORITY_MARKERS = (
    "operational right",
    "action_time_evaluation",
    "immutable_snapshot",
    "contractor_seconded_semantics",
)
STATUS_PROJECTION_RE = re.compile(
    r"`(?P<code>IMPLEMENTED-[A-Z]+|FOUNDATION-ONLY|PRESENTATION-ONLY|"
    r"PLANNED-ONLY|ABSENT|VERIFY)`; release `(?P<status>[A-Z_]+)`"
)
CAPABILITY_RE = re.compile(r"\bCAP-[A-Z0-9-]+\b")
ACCEPTANCE_RE = re.compile(r"\bAC-[A-Z0-9-]+\b")
WORK_ITEM_RE = re.compile(r"\b(?:[A-Z][A-Z0-9]*-)+\d{3}\b")


def _error(
    file: str,
    identifier: object,
    rule: str,
    expected: object,
    actual: object,
) -> str:
    return (
        f"{file}: [{identifier}] rule={rule}; "
        f"expected={expected!r}; actual={actual!r}"
    )


def _rows(root: Path, relative: str) -> list[dict[str, str]]:
    with (root / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def _validate_identity(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_identity = {
        "schema": 2,
        "version": "1.0",
        "release": "DEMO-RELEASE",
        "baseline_status": "ACCEPTED",
    }
    for key, expected in expected_identity.items():
        actual = plan.get(key)
        if actual != expected:
            errors.append(
                _error(
                    PLAN_PATH,
                    key,
                    f"release-{key}",
                    expected,
                    actual,
                )
            )
    if plan.get("owners") != EXPECTED_OWNERS:
        errors.append(
            _error(
                PLAN_PATH,
                "owners",
                "canonical-release-plan-owners",
                EXPECTED_OWNERS,
                plan.get("owners"),
            )
        )
    vocabularies = (
        ("statuses", ALLOWED_STATUSES),
        ("depths", ALLOWED_DEPTHS),
        ("code_statuses", ALLOWED_CODE_STATUSES),
    )
    for key, expected in vocabularies:
        actual = plan.get(key)
        if actual != list(expected):
            errors.append(
                _error(
                    PLAN_PATH,
                    key,
                    f"{key}-vocabulary",
                    list(expected),
                    actual,
                )
            )
    return errors


def _validate_catalog(
    plan: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    errors: list[str] = []
    modules = [
        module
        for module in plan.get("modules", [])
        if isinstance(module, dict)
    ]
    module_ids = [module.get("id") for module in modules]
    expected_ids = list(EXPECTED_MODULE_IDS)
    if module_ids != expected_ids:
        errors.append(
            _error(
                PLAN_PATH,
                "modules",
                "exact-demo-module-catalog",
                expected_ids,
                module_ids,
            )
        )
    if len(module_ids) != len(set(module_ids)):
        errors.append(
            _error(
                PLAN_PATH,
                "modules",
                "module-id-uniqueness",
                "unique",
                module_ids,
            )
        )
    orders = [module.get("order") for module in modules]
    integer_orders = sorted(
        order for order in orders if isinstance(order, int)
    )
    expected_orders = list(range(1, 28))
    if integer_orders != expected_orders:
        errors.append(
            _error(
                PLAN_PATH,
                "modules",
                "module-catalog-orders",
                expected_orders,
                orders,
            )
        )
    if len(orders) != len(set(orders)):
        errors.append(
            _error(
                PLAN_PATH,
                "modules",
                "module-order-uniqueness",
                "unique",
                orders,
            )
        )
    modules_by_id = {
        str(module["id"]): module
        for module in modules
        if isinstance(module.get("id"), str)
    }
    return errors, modules, modules_by_id


def _validate_module_contract(
    root: Path,
    module_id: str,
    module: dict[str, Any],
    protected_slices: dict[str, Any],
    detail_markers: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    contract_path = str(module.get("contract", ""))
    path = root / contract_path
    if not path.is_file():
        return [
            _error(
                contract_path,
                module_id,
                "module-contract-exists",
                "file",
                "missing",
            )
        ]

    text = path.read_text(encoding="utf-8")
    if f"`{module_id}`" not in text:
        errors.append(
            _error(
                contract_path,
                module_id,
                "module-contract-id-marker",
                f"`{module_id}`",
                "missing",
            )
        )
    for marker in MODULE_MARKERS:
        if marker not in text:
            errors.append(
                _error(
                    contract_path,
                    module_id,
                    "module-contract-marker",
                    marker,
                    "missing",
                )
            )
    for boilerplate in REJECTED_CONTRACT_BOILERPLATE:
        if boilerplate in text:
            errors.append(
                _error(
                    contract_path,
                    module_id,
                    "rejected-generic-boilerplate",
                    "absent",
                    boilerplate,
                )
            )

    capabilities = set(CAPABILITY_RE.findall(text))
    acceptances = set(ACCEPTANCE_RE.findall(text))
    work_items = set(WORK_ITEM_RE.findall(text))
    detail_markers["capability"].update(capabilities)
    detail_markers["acceptance"].update(acceptances)
    detail_markers["work_item"].update(work_items)

    expected_slices = set(protected_slices.get(module_id, []))
    actual_slices = set(split_pipe(module.get("accepted")))
    if actual_slices != expected_slices:
        errors.append(
            _error(
                PLAN_PATH,
                module_id,
                "protected-accepted-slices",
                sorted(expected_slices),
                sorted(actual_slices),
            )
        )
    for capability in expected_slices:
        if capability not in capabilities:
            errors.append(
                _error(
                    contract_path,
                    module_id,
                    "accepted-slice-evidence-marker",
                    capability,
                    "missing",
                )
            )

    status_owner_marker = "Текущий planning status принадлежит только"
    if status_owner_marker in text:
        section = text.split(
            "## CURRENT CODE STATUS / CAPABILITIES", 1
        )[-1].split("\n## ", 1)[0]
        match = STATUS_PROJECTION_RE.search(section)
        actual_projection = (
            None
            if match is None
            else (match.group("code"), match.group("status"))
        )
        expected_projection = (module.get("code"), module.get("status"))
        if actual_projection != expected_projection:
            errors.append(
                _error(
                    contract_path,
                    module_id,
                    "module-current-status-projection",
                    expected_projection,
                    actual_projection,
                )
            )
    return errors


def _validate_modules(
    plan: dict[str, Any],
    root: Path,
    modules: list[dict[str, Any]],
    modules_by_id: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[str, set[str]]]:
    errors: list[str] = []
    identifiers: dict[str, list[str]] = {
        "capability": [],
        "acceptance": [],
        "work_item": [],
    }
    detail_markers: dict[str, set[str]] = {
        "capability": set(),
        "acceptance": set(),
        "work_item": set(),
    }
    protected_slices = plan.get("reconciliation", {}).get(
        "accepted_slices", {}
    )
    vocabularies = (
        ("status", ALLOWED_STATUSES),
        ("depth", ALLOWED_DEPTHS),
        ("code", ALLOWED_CODE_STATUSES),
        ("group", ALLOWED_GROUPS),
    )

    for module_id, module in modules_by_id.items():
        for field, vocabulary in vocabularies:
            actual = module.get(field)
            if actual not in vocabulary:
                errors.append(
                    _error(
                        PLAN_PATH,
                        module_id,
                        f"module-{field}-vocabulary",
                        list(vocabulary),
                        actual,
                    )
                )
        for field in identifiers:
            value = module.get(field)
            if not isinstance(value, str) or not value:
                errors.append(
                    _error(
                        PLAN_PATH,
                        module_id,
                        f"module-{field}-required",
                        "non-empty unique identifier",
                        value,
                    )
                )
            else:
                identifiers[field].append(value)
        if not split_pipe(module.get("sources")):
            errors.append(
                _error(
                    PLAN_PATH,
                    module_id,
                    "module-sources-required",
                    "one or more source IDs",
                    module.get("sources"),
                )
            )
        errors.extend(
            _validate_module_contract(
                root,
                module_id,
                module,
                protected_slices,
                detail_markers,
            )
        )

    for field, values in identifiers.items():
        if len(values) != len(set(values)):
            errors.append(
                _error(
                    PLAN_PATH,
                    field,
                    f"module-{field}-uniqueness",
                    "unique",
                    values,
                )
            )
    return errors, detail_markers


def _validate_topology(
    plan: dict[str, Any],
    modules_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    order = plan.get("dependency_order", [])
    valid_membership = (
        len(order) == 27
        and set(order) == set(EXPECTED_MODULE_IDS)
        and len(order) == len(set(order))
    )
    if not valid_membership:
        return [
            _error(
                PLAN_PATH,
                "dependency_order",
                "dependency-order-membership",
                list(EXPECTED_MODULE_IDS),
                order,
            )
        ]

    position = {
        module_id: index for index, module_id in enumerate(order)
    }
    for module_id, module in modules_by_id.items():
        for dependency in module.get("deps", []):
            if dependency not in position:
                errors.append(
                    _error(
                        PLAN_PATH,
                        module_id,
                        "module-dependency-reference",
                        "existing module",
                        dependency,
                    )
                )
            elif position[dependency] >= position[module_id]:
                errors.append(
                    _error(
                        PLAN_PATH,
                        module_id,
                        "dependency-topology",
                        f"{dependency} before {module_id}",
                        order,
                    )
                )
    return errors


def _validate_static_sets(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_post_demo = list(EXPECTED_POST_DEMO)
    if plan.get("post_demo") != expected_post_demo:
        errors.append(
            _error(
                PLAN_PATH,
                "post_demo",
                "post-demo-contour-set",
                expected_post_demo,
                plan.get("post_demo"),
            )
        )
    expected_scenarios = list(EXPECTED_SCENARIOS)
    if plan.get("scenarios") != expected_scenarios:
        errors.append(
            _error(
                PLAN_PATH,
                "scenarios",
                "presentation-scenario-set",
                expected_scenarios,
                plan.get("scenarios"),
            )
        )
    return errors


def _load_evidence_inputs(
    root: Path,
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    return (
        _rows(root, COVERAGE_SOURCE_PATH),
        _rows(root, COVERAGE_DECISIONS_PATH),
        _rows(root, DECISION_PROFILES_PATH),
        _rows(root, SOURCE_REGISTRY_PATH),
    )


def _validate_coverage_rows(
    coverage: list[dict[str, str]],
    decisions: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    checks = (
        (
            coverage,
            COVERAGE_SOURCE_PATH,
            "coverage-exact-66-rows",
        ),
        (
            decisions,
            COVERAGE_DECISIONS_PATH,
            "coverage-decisions-exact-66-rows",
        ),
    )
    for rows, path, rule in checks:
        actual = [row.get("reference_id") for row in rows]
        if actual != EXPECTED_REFERENCE_IDS:
            errors.append(
                _error(
                    path,
                    "reference_id",
                    rule,
                    EXPECTED_REFERENCE_IDS,
                    actual,
                )
            )
    return errors


def _validate_decision_profiles(
    profiles: list[dict[str, str]],
    decisions: list[dict[str, str]],
    modules_by_id: dict[str, dict[str, Any]],
    detail_markers: dict[str, set[str]],
    modules: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    profiles_by_id = {
        row.get("profile_id"): row for row in profiles
    }
    if len(profiles_by_id) != len(profiles):
        errors.append(
            _error(
                DECISION_PROFILES_PATH,
                "profiles",
                "decision-profile-uniqueness",
                "unique profile_id",
                [row.get("profile_id") for row in profiles],
            )
        )
    for row in decisions:
        profile_id = row.get("profile_id")
        if profile_id not in profiles_by_id:
            errors.append(
                _error(
                    COVERAGE_DECISIONS_PATH,
                    row.get("reference_id"),
                    "decision-profile-reference",
                    "existing profile_id",
                    profile_id,
                )
            )

    aggregate_work_items = {
        module.get("work_item") for module in modules
    }
    for profile_id, profile in profiles_by_id.items():
        for module_id in split_pipe(profile.get("module_ids")):
            if module_id not in modules_by_id:
                errors.append(
                    _error(
                        DECISION_PROFILES_PATH,
                        profile_id,
                        "profile-module-reference",
                        "accepted module ID",
                        module_id,
                    )
                )
        for capability in split_pipe(profile.get("capability_ids")):
            if capability not in detail_markers["capability"]:
                errors.append(
                    _error(
                        DECISION_PROFILES_PATH,
                        profile_id,
                        "profile-capability-reference",
                        "capability marker",
                        capability,
                    )
                )
        for acceptance in split_pipe(profile.get("acceptance_ids")):
            if acceptance not in detail_markers["acceptance"]:
                errors.append(
                    _error(
                        DECISION_PROFILES_PATH,
                        profile_id,
                        "profile-acceptance-reference",
                        "acceptance marker",
                        acceptance,
                    )
                )
        for work_item in split_pipe(profile.get("planned_work_items")):
            known = (
                work_item in detail_markers["work_item"]
                or work_item in aggregate_work_items
            )
            if not known:
                errors.append(
                    _error(
                        DECISION_PROFILES_PATH,
                        profile_id,
                        "profile-work-item-reference",
                        "known work item",
                        work_item,
                    )
                )
        if profile.get("proven_legal_mode") != "VERIFY":
            errors.append(
                _error(
                    DECISION_PROFILES_PATH,
                    profile_id,
                    "decision-profile-proven-legal-mode",
                    "VERIFY",
                    profile.get("proven_legal_mode"),
                )
            )
    return errors


def _validate_special_reference_boundaries(
    profiles: list[dict[str, str]],
    decisions: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    profiles_by_id = {
        row.get("profile_id"): row for row in profiles
    }
    decisions_by_reference = {
        row.get("reference_id"): row for row in decisions
    }

    profile_059_id = decisions_by_reference.get(
        "REF-OD-059", {}
    ).get("profile_id")
    profile_059 = profiles_by_id.get(profile_059_id, {})
    actual_059 = (
        set(split_pipe(profile_059.get("module_ids"))),
        set(split_pipe(profile_059.get("product_target_modes"))),
    )
    expected_059 = (
        {"PERMIT-WORK-JOURNAL", "ORDER-WORK-JOURNAL"},
        {"ELECTRONIC_ORIGINAL_TARGET", "PAPER_MIRROR"},
    )
    if actual_059 != expected_059:
        errors.append(
            _error(
                DECISION_PROFILES_PATH,
                "REF-OD-059",
                "ref-od-059-split",
                expected_059,
                actual_059,
            )
        )

    profile_063_id = decisions_by_reference.get(
        "REF-OD-063", {}
    ).get("profile_id")
    profile_063 = profiles_by_id.get(profile_063_id, {})
    actual_063 = profile_063.get("post_demo_contour")
    if actual_063 != "KEYS":
        errors.append(
            _error(
                DECISION_PROFILES_PATH,
                "REF-OD-063",
                "ref-od-063-keys-boundary",
                "KEYS",
                actual_063,
            )
        )
    return errors


def _validate_source_ids(
    registry: list[dict[str, str]],
    modules_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    known_sources = {
        row.get("source_id") for row in registry
    } | set(EXPECTED_REFERENCE_IDS)
    for module_id, module in modules_by_id.items():
        for source_id in split_pipe(module.get("sources")):
            if source_id not in known_sources:
                errors.append(
                    _error(
                        PLAN_PATH,
                        module_id,
                        "module-source-reference",
                        "SOURCE_REGISTRY.csv or REF-OD-001..066",
                        source_id,
                    )
                )
    return errors


def _validate_competitor_matrix(
    root: Path,
    modules_by_id: dict[str, dict[str, Any]],
    detail_markers: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    try:
        rows = _rows(root, COMPETITOR_MATRIX_PATH)
    except OSError as exc:
        return [
            _error(
                COMPETITOR_MATRIX_PATH,
                "matrix",
                "competitor-matrix-readable",
                "readable CSV",
                str(exc),
            )
        ]

    actual_decisions = [row.get("decision_id") for row in rows]
    if actual_decisions != EXPECTED_COMPETITOR_DECISIONS:
        errors.append(
            _error(
                COMPETITOR_MATRIX_PATH,
                "decision_id",
                "competitor-decision-catalog",
                EXPECTED_COMPETITOR_DECISIONS,
                actual_decisions,
            )
        )
    for row in rows:
        decision_id = row.get("decision_id")
        module_ids = split_pipe(row.get("module_ids"))
        for module_id in module_ids:
            if module_id not in modules_by_id:
                errors.append(
                    _error(
                        COMPETITOR_MATRIX_PATH,
                        decision_id,
                        "competitor-module-reference",
                        "accepted module ID",
                        module_id,
                    )
                )
        for capability in split_pipe(row.get("capability_ids")):
            if capability not in detail_markers["capability"]:
                errors.append(
                    _error(
                        COMPETITOR_MATRIX_PATH,
                        decision_id,
                        "competitor-capability-reference",
                        "capability marker",
                        capability,
                    )
                )
        required_module = REQUIRED_COMPETITOR_MAPPINGS.get(decision_id)
        if required_module and required_module not in module_ids:
            errors.append(
                _error(
                    COMPETITOR_MATRIX_PATH,
                    decision_id,
                    "competitor-required-mapping",
                    required_module,
                    module_ids,
                )
            )
    return errors


def _validate_legal_mode_matrix(root: Path) -> list[str]:
    try:
        rows = _rows(root, LEGAL_MODE_MATRIX_PATH)
    except OSError as exc:
        return [
            _error(
                LEGAL_MODE_MATRIX_PATH,
                "matrix",
                "legal-mode-matrix-readable",
                "readable CSV",
                str(exc),
            )
        ]
    invalid = [
        row for row in rows if row.get("proven_legal_mode") != "VERIFY"
    ]
    if not invalid:
        return []
    return [
        _error(
            LEGAL_MODE_MATRIX_PATH,
            "proven_legal_mode",
            "legal-mode-remains-verify",
            "VERIFY for every row",
            invalid,
        )
    ]


def _validate_personnel_authority_matrix(root: Path) -> list[str]:
    try:
        content = (root / PERSONNEL_AUTHORITY_MATRIX_PATH).read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        return [
            _error(
                PERSONNEL_AUTHORITY_MATRIX_PATH,
                "matrix",
                "personnel-authority-matrix-readable",
                "readable CSV",
                str(exc),
            )
        ]
    errors: list[str] = []
    for marker in PERSONNEL_AUTHORITY_MARKERS:
        if marker not in content:
            errors.append(
                _error(
                    PERSONNEL_AUTHORITY_MATRIX_PATH,
                    marker,
                    "personnel-authority-evidence-marker",
                    marker,
                    "missing",
                )
            )
    return errors


def _validate_evidence(
    plan: dict[str, Any],
    root: Path,
    modules: list[dict[str, Any]],
    modules_by_id: dict[str, dict[str, Any]],
    detail_markers: dict[str, set[str]],
) -> list[str]:
    del plan
    try:
        coverage, decisions, profiles, registry = _load_evidence_inputs(root)
    except OSError as exc:
        return [
            _error(
                PLAN_PATH,
                "coverage",
                "coverage-inputs-readable",
                "readable CSV inputs",
                str(exc),
            )
        ]
    errors = _validate_coverage_rows(coverage, decisions)
    errors.extend(
        _validate_decision_profiles(
            profiles,
            decisions,
            modules_by_id,
            detail_markers,
            modules,
        )
    )
    errors.extend(
        _validate_special_reference_boundaries(profiles, decisions)
    )
    errors.extend(_validate_source_ids(registry, modules_by_id))
    errors.extend(
        _validate_competitor_matrix(
            root,
            modules_by_id,
            detail_markers,
        )
    )
    errors.extend(_validate_legal_mode_matrix(root))
    errors.extend(_validate_personnel_authority_matrix(root))
    return errors


def validate_release_plan_compatibility(
    plan: dict[str, Any], root: Path
) -> list[str]:
    """Run the applicable schema-1 guarantees against the schema-2 superset."""
    errors = _validate_identity(plan)
    catalog_errors, modules, modules_by_id = _validate_catalog(plan)
    errors.extend(catalog_errors)
    module_errors, detail_markers = _validate_modules(
        plan,
        root,
        modules,
        modules_by_id,
    )
    errors.extend(module_errors)
    errors.extend(_validate_topology(plan, modules_by_id))
    errors.extend(_validate_static_sets(plan))
    errors.extend(
        _validate_evidence(
            plan,
            root,
            modules,
            modules_by_id,
            detail_markers,
        )
    )
    return errors
