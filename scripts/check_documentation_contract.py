from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

try:
    import check_documentation_contract_core as core
except ModuleNotFoundError:  # imported as scripts.check_documentation_contract in tests
    from scripts import check_documentation_contract_core as core

ROOT = Path(__file__).resolve().parents[1]
MODULE_CONTRACT_PATH = (
    ROOT
    / "docs/work-items/active/MODULE-ACTIVATION-CONTRACT-001/"
    "MODULE_ACTIVATION_CONTRACT.json"
)
MODULE_FIXTURES_PATH = (
    ROOT / "tests/process/fixtures/module_activation_contract_cases.json"
)

EXPECTED_STATES = {
    "AVAILABLE",
    "CONFIGURED",
    "ACTIVE",
    "READ_ONLY",
    "INACTIVE",
    "RETIRED",
}
EXPECTED_SCOPES = ["ORGANIZATION", "ENERGY_SITE", "WORKPLACE"]
EXPECTED_PRECEDENCE = ["WORKPLACE", "ENERGY_SITE", "ORGANIZATION"]
EXPECTED_ENTRY_POINTS = {
    "NAVIGATION_UI",
    "HTTP_ROUTE",
    "SERVICE",
    "API",
    "ADMIN",
    "MANAGEMENT_COMMAND",
    "EXPORT",
    "BACKGROUND_JOB",
    "CROSS_MODULE_ACTION",
}
EXPECTED_NEGATIVE_IDS = {
    "N01_UI_HIDDEN_DIRECT_URL_MUST_DENY",
    "N02_ROUTE_DENIED_SERVICE_WRITE_MUST_DENY",
    "N03_OPTIONAL_INTEGRATION_MUST_NOT_BECOME_REQUIRED_WITHOUT_EVIDENCE",
    "N04_REQUIRED_DEPENDENCY_MISSING_MUST_BLOCK_ACTIVATION",
    "N05_DISABLE_MUST_NOT_DELETE_RECORDS",
    "N06_READ_ONLY_MUST_DENY_WRITE_TRANSITION",
    "N07_UPGRADE_MUST_NOT_AUTO_ACTIVATE",
    "N08_INACTIVE_MODULE_MUST_NOT_SKIP_SCHEMA_MIGRATIONS",
    "N09_SCOPE_CONFLICT_MUST_NOT_RESOLVE_RANDOMLY",
    "N10_REACTIVATION_MUST_PRESERVE_MODULE_IDENTITY",
}
EXPECTED_AUDIT_FIELDS = {
    "module_id",
    "scope_type",
    "scope_id",
    "organization_id",
    "previous_explicit_state",
    "previous_effective_state",
    "requested_new_state",
    "resulting_effective_state",
    "actor_identity",
    "occurred_at",
    "reason",
    "configuration_validation",
    "dependency_validation",
    "result",
    "denial_reason_code",
    "correlation_id",
    "manifest_contract_version",
}


def _module_error(rule: str, expected: Any, actual: Any) -> str:
    return (
        f"[MODULE-ACTIVATION-CONTRACT-001] rule={rule} "
        f"expected={expected!r} actual={actual!r}"
    )


def load_module_activation_contract(root: Path = ROOT) -> dict[str, Any]:
    path = (
        root
        / "docs/work-items/active/MODULE-ACTIVATION-CONTRACT-001/"
        "MODULE_ACTIVATION_CONTRACT.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def validate_module_activation_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    architecture = contract.get("architecture", {})
    expected_architecture = {
        "style": "MODULAR_DJANGO_MONOLITH",
        "deployable_products": 1,
        "application_versions_per_release": 1,
        "database_model": "ONE_SHARED_DATABASE",
        "separate_module_deployments": False,
        "activation_changes_product_version": False,
    }
    for field, expected in expected_architecture.items():
        if architecture.get(field) != expected:
            errors.append(
                _module_error(f"architecture-{field}", expected, architecture.get(field))
            )

    manifest = contract.get("manifest", {})
    required_manifest_fields = {
        "module_id",
        "human_name",
        "manifest_contract_version",
        "activation_policy",
        "supported_scopes",
        "required_dependencies",
        "optional_integrations",
        "capabilities",
        "activation_prerequisites",
        "history_policy",
        "migration_policy",
        "lifecycle_contract_version",
    }
    actual_manifest_fields = set(manifest.get("required_fields", []))
    if not required_manifest_fields.issubset(actual_manifest_fields):
        errors.append(
            _module_error(
                "manifest-required-fields",
                sorted(required_manifest_fields),
                sorted(actual_manifest_fields),
            )
        )
    if manifest.get("supported_scope_types_v1") != EXPECTED_SCOPES:
        errors.append(
            _module_error(
                "manifest-scope-types",
                EXPECTED_SCOPES,
                manifest.get("supported_scope_types_v1"),
            )
        )
    if manifest.get("default_scoped_optional_state") != "AVAILABLE":
        errors.append(
            _module_error(
                "manifest-default-fail-closed",
                "AVAILABLE",
                manifest.get("default_scoped_optional_state"),
            )
        )
    if manifest.get("history_policy_required") != "PRESERVE":
        errors.append(
            _module_error(
                "manifest-history-preservation",
                "PRESERVE",
                manifest.get("history_policy_required"),
            )
        )
    if manifest.get("migration_policy_required") != "ALWAYS_WITH_PRODUCT":
        errors.append(
            _module_error(
                "manifest-migration-participation",
                "ALWAYS_WITH_PRODUCT",
                manifest.get("migration_policy_required"),
            )
        )

    lifecycle = contract.get("lifecycle", {})
    actual_states = set(lifecycle.get("states", []))
    if actual_states != EXPECTED_STATES:
        errors.append(
            _module_error("lifecycle-states", sorted(EXPECTED_STATES), sorted(actual_states))
        )
    forbidden = set(lifecycle.get("forbidden_direct_transitions", []))
    for transition in {"AVAILABLE->ACTIVE", "INACTIVE->ACTIVE", "RETIRED->ACTIVE"}:
        if transition not in forbidden:
            errors.append(
                _module_error("forbidden-reactivation-transition", transition, sorted(forbidden))
            )
    transitions = lifecycle.get("allowed_transitions", {})
    if "ACTIVE" in transitions.get("RETIRED", []):
        errors.append(
            _module_error(
                "retired-reactivation-path",
                "RETIRED->CONFIGURED->ACTIVE",
                transitions.get("RETIRED"),
            )
        )
    if lifecycle.get("disable_is_delete") is not False:
        errors.append(
            _module_error("disable-preserves-history", False, lifecycle.get("disable_is_delete"))
        )
    if lifecycle.get("retire_is_delete") is not False:
        errors.append(
            _module_error("retire-preserves-history", False, lifecycle.get("retire_is_delete"))
        )

    scope = contract.get("scope_resolution", {})
    if scope.get("ordinary_precedence") != EXPECTED_PRECEDENCE:
        errors.append(
            _module_error(
                "scope-precedence", EXPECTED_PRECEDENCE, scope.get("ordinary_precedence")
            )
        )
    if scope.get("same_scope_duplicate_result") != "DENY":
        errors.append(
            _module_error(
                "ambiguous-scope-fail-closed",
                "DENY",
                scope.get("same_scope_duplicate_result"),
            )
        )
    if scope.get("invalid_or_missing_required_scope_result") != "DENY":
        errors.append(
            _module_error(
                "invalid-scope-fail-closed",
                "DENY",
                scope.get("invalid_or_missing_required_scope_result"),
            )
        )
    if scope.get("workplace_is_child_of_energy_site") is not False:
        errors.append(
            _module_error(
                "actual-scope-topology",
                False,
                scope.get("workplace_is_child_of_energy_site"),
            )
        )
    if scope.get("restrictive_caps") != ["READ_ONLY", "RETIRED"]:
        errors.append(
            _module_error(
                "restrictive-scope-caps",
                ["READ_ONLY", "RETIRED"],
                scope.get("restrictive_caps"),
            )
        )
    if scope.get("child_may_override_parent_inactive_to_active") is not True:
        errors.append(
            _module_error(
                "phased-child-activation",
                True,
                scope.get("child_may_override_parent_inactive_to_active"),
            )
        )

    dependencies = contract.get("dependencies", {})
    required = dependencies.get("required_dependency", {})
    optional = dependencies.get("optional_integration", {})
    if required.get("fail_closed") is not True:
        errors.append(
            _module_error("required-dependency-fail-closed", True, required.get("fail_closed"))
        )
    if required.get("checked_before_active_transition") is not True:
        errors.append(
            _module_error(
                "required-dependency-activation-check",
                True,
                required.get("checked_before_active_transition"),
            )
        )
    if optional.get("blocks_primary_module_activation") is not False:
        errors.append(
            _module_error(
                "optional-integration-non-blocking",
                False,
                optional.get("blocks_primary_module_activation"),
            )
        )
    if optional.get("historical_links_preserved") is not True:
        errors.append(
            _module_error(
                "optional-integration-history",
                True,
                optional.get("historical_links_preserved"),
            )
        )

    decision = contract.get("access_decision", {})
    actual_entry_points = set(decision.get("entry_point_classes", []))
    if not EXPECTED_ENTRY_POINTS.issubset(actual_entry_points):
        errors.append(
            _module_error(
                "entry-point-coverage",
                sorted(EXPECTED_ENTRY_POINTS),
                sorted(actual_entry_points),
            )
        )
    if decision.get("ui_visibility_is_security_boundary") is not False:
        errors.append(
            _module_error(
                "ui-not-security-boundary",
                False,
                decision.get("ui_visibility_is_security_boundary"),
            )
        )
    if decision.get("route_only_guard_is_complete") is not False:
        errors.append(
            _module_error(
                "route-only-not-complete",
                False,
                decision.get("route_only_guard_is_complete"),
            )
        )
    if decision.get("mutation_service_guard_required") is not True:
        errors.append(
            _module_error(
                "service-mutation-guard",
                True,
                decision.get("mutation_service_guard_required"),
            )
        )

    matrix = contract.get("behavior_matrix", {})
    for state in ("READ_ONLY", "INACTIVE", "RETIRED", "CONFIGURED", "AVAILABLE"):
        row = matrix.get(state, {})
        for operation in ("create", "edit_transition", "delete", "background_mutate"):
            if row.get(operation) != "DENY":
                errors.append(
                    _module_error(
                        f"{state.lower()}-{operation}-denied",
                        "DENY",
                        row.get(operation),
                    )
                )
    if matrix.get("READ_ONLY", {}).get("detail_history") != "ALLOW":
        errors.append(
            _module_error(
                "read-only-history-readable",
                "ALLOW",
                matrix.get("READ_ONLY", {}).get("detail_history"),
            )
        )
    for state in ("INACTIVE", "RETIRED", "CONFIGURED"):
        if "ALLOW_RETAINED_HISTORY" not in str(
            matrix.get(state, {}).get("detail_history", "")
        ):
            errors.append(
                _module_error(
                    f"{state.lower()}-history-retained",
                    "ALLOW_RETAINED_HISTORY",
                    matrix.get(state, {}).get("detail_history"),
                )
            )

    history = contract.get("history_and_reactivation", {})
    false_history_fields = (
        "deactivation_deletes_records",
        "deactivation_deletes_snapshots",
        "deactivation_deletes_audit",
        "deactivation_breaks_relations",
        "module_id_changes_on_reactivation",
        "reactivation_creates_new_module_identity",
        "direct_inactive_or_retired_to_active",
    )
    for field in false_history_fields:
        if history.get(field) is not False:
            errors.append(_module_error(f"history-{field}", False, history.get(field)))
    if history.get("reactivation_uses_retained_history") is not True:
        errors.append(
            _module_error(
                "reactivation-uses-history",
                True,
                history.get("reactivation_uses_retained_history"),
            )
        )
    if history.get("stale_configuration_revalidated_before_active") is not True:
        errors.append(
            _module_error(
                "reactivation-revalidates-configuration",
                True,
                history.get("stale_configuration_revalidated_before_active"),
            )
        )

    migrations = contract.get("migrations", {})
    migration_expectations = {
        "owned_by_product_version": True,
        "conditioned_on_module_activation": False,
        "inactive_module_migrations_apply": True,
        "same_product_version_requires_compatible_schema": True,
        "upgrade_activates_module": False,
        "upgrade_preserves_explicit_activation_state": True,
        "inactive_data_migrates_safely": True,
    }
    for field, expected in migration_expectations.items():
        if migrations.get(field) is not expected:
            errors.append(
                _module_error(f"migration-{field}", expected, migrations.get(field))
            )

    audit = contract.get("activation_audit", {})
    actual_audit_fields = set(audit.get("required_fields", []))
    if not EXPECTED_AUDIT_FIELDS.issubset(actual_audit_fields):
        errors.append(
            _module_error(
                "activation-audit-fields",
                sorted(EXPECTED_AUDIT_FIELDS),
                sorted(actual_audit_fields),
            )
        )
    if audit.get("append_only_required") is not True:
        errors.append(
            _module_error(
                "activation-audit-append-only",
                True,
                audit.get("append_only_required"),
            )
        )

    actual_negative_ids = set(contract.get("negative_architecture_invariants", []))
    if actual_negative_ids != EXPECTED_NEGATIVE_IDS:
        errors.append(
            _module_error(
                "negative-architecture-invariants",
                sorted(EXPECTED_NEGATIVE_IDS),
                sorted(actual_negative_ids),
            )
        )

    boundary = contract.get("implementation_boundary", {})
    for field in (
        "product_models_changed",
        "domain_migrations_changed",
        "runtime_preview_changed",
    ):
        if boundary.get(field) is not False:
            errors.append(
                _module_error(f"architecture-only-{field}", False, boundary.get(field))
            )

    return errors


def apply_module_fixture_mutation(
    contract: dict[str, Any], mutation: dict[str, Any]
) -> dict[str, Any]:
    mutated = copy.deepcopy(contract)
    path = mutation["path"].split(".")
    target: Any = mutated
    for part in path[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    key = path[-1]
    if mutation["op"] == "set":
        if isinstance(target, list):
            target[int(key)] = mutation["value"]
        else:
            target[key] = mutation["value"]
    elif mutation["op"] == "remove":
        if isinstance(target, list):
            target.pop(int(key))
        else:
            target.pop(key, None)
    elif mutation["op"] == "append":
        target[key].append(mutation["value"])
    else:
        raise ValueError(f"Unsupported fixture mutation: {mutation['op']}")
    return mutated


def validate_module_negative_fixtures(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    catalog = json.loads(MODULE_FIXTURES_PATH.read_text(encoding="utf-8"))
    fixture_negative_ids = {
        case["id"] for case in catalog["cases"] if case["id"].startswith("N")
    }
    if fixture_negative_ids != EXPECTED_NEGATIVE_IDS:
        errors.append(
            _module_error(
                "negative-fixture-coverage",
                sorted(EXPECTED_NEGATIVE_IDS),
                sorted(fixture_negative_ids),
            )
        )
    for case in catalog["cases"]:
        candidate = copy.deepcopy(contract)
        if case["mutation"] is not None:
            candidate = apply_module_fixture_mutation(candidate, case["mutation"])
        case_errors = validate_module_activation_contract(candidate)
        expected_rule = case["expected_rule"]
        if expected_rule is None:
            if case_errors:
                errors.append(
                    _module_error(
                        f"fixture-{case['id']}",
                        "valid baseline",
                        case_errors,
                    )
                )
            continue
        if not any(f"rule={expected_rule}" in error for error in case_errors):
            errors.append(
                _module_error(
                    f"fixture-{case['id']}",
                    expected_rule,
                    case_errors,
                )
            )
    return errors


def run_module_activation_contract_gate() -> int:
    contract = load_module_activation_contract()
    errors = validate_module_activation_contract(contract)
    errors.extend(validate_module_negative_fixtures(contract))
    if errors:
        print("Module activation architecture contract: FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Module activation architecture contract: OK")
    print(f"Contract: {MODULE_CONTRACT_PATH.relative_to(ROOT)}")
    print(f"Lifecycle states: {len(EXPECTED_STATES)}")
    print(f"Entry-point classes: {len(EXPECTED_ENTRY_POINTS)}")
    print(f"Negative invariants: {len(EXPECTED_NEGATIVE_IDS)}")
    return 0


def main() -> int:
    result = core.main()
    if result != 0:
        return result
    return run_module_activation_contract_gate()


if __name__ == "__main__":
    raise SystemExit(main())
