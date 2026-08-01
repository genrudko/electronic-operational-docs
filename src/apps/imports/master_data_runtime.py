from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import services
from .master_data_contract import (
    PROFILE_CONTRACTS,
    IssueSeverity,
    MasterDataTarget,
    validate_profile_row,
)

_REVIEW_PREFIX = "[MASTER_DATA_REVIEW:"
_BLOCKED_PREFIX = "[MASTER_DATA_BLOCKED:"
_INSTALLED_ATTRIBUTE = "_master_data_contracts_installed"
_PLATFORM_PROVENANCE_ISSUES = frozenset({"SOURCE_OCCURRENCE_MISSING"})

_TARGET_MAP = {
    services.ImportBatch.TargetRegistry.ORGANIZATION: MasterDataTarget.PERSONNEL,
    services.ImportBatch.TargetRegistry.EQUIPMENT: MasterDataTarget.EQUIPMENT,
    services.ImportBatch.TargetRegistry.DISPATCHING: MasterDataTarget.DISPATCHING,
}

_EXTRA_FIELD_SPECS = {
    services.ImportBatch.TargetRegistry.EQUIPMENT: (
        services.ImportFieldSpec(
            "family_code",
            "Код технической группы",
            max_length=64,
            aliases=("код технической группы", "группа оборудования", "family code"),
        ),
        services.ImportFieldSpec(
            "source_designation",
            "Исходное обозначение",
            max_length=64,
            aliases=("исходное обозначение", "обозначение источника", "source designation"),
        ),
        services.ImportFieldSpec(
            "variant",
            "Исполнение",
            max_length=255,
            aliases=("исполнение", "вариант исполнения", "variant"),
        ),
        services.ImportFieldSpec(
            "parent_code",
            "Код родительского оборудования",
            kind="code",
            max_length=96,
            aliases=("код родителя", "родительское оборудование", "parent code"),
        ),
        services.ImportFieldSpec(
            "aliases",
            "Варианты наименования",
            max_length=2000,
            aliases=("алиасы", "варианты наименования", "aliases"),
        ),
        services.ImportFieldSpec(
            "source_occurrence_id",
            "Идентификатор строки источника",
            max_length=128,
            aliases=("идентификатор строки источника", "source occurrence id"),
        ),
        services.ImportFieldSpec(
            "source_revision_id",
            "Идентификатор редакции источника",
            max_length=128,
            aliases=("идентификатор редакции источника", "source revision id"),
        ),
    ),
    services.ImportBatch.TargetRegistry.DISPATCHING: (
        services.ImportFieldSpec(
            "source_occurrence_id",
            "Идентификатор строки источника",
            max_length=128,
            aliases=("идентификатор строки источника", "source occurrence id"),
        ),
    ),
}


def _register_field_specs() -> None:
    for target, extra_specs in _EXTRA_FIELD_SPECS.items():
        current = services.REGISTRY_FIELD_SPECS[target]
        existing = {spec.key for spec in current}
        additions = tuple(spec for spec in extra_specs if spec.key not in existing)
        if additions:
            services.REGISTRY_FIELD_SPECS[target] = current + additions


def _contract_values(
    target: MasterDataTarget,
    normalized: dict[str, str],
) -> dict[str, str]:
    allowed = PROFILE_CONTRACTS[target].field_keys
    return {key: value for key, value in normalized.items() if key in allowed}


def _issue_message(issue) -> str:
    prefix = (
        _BLOCKED_PREFIX
        if issue.severity is IssueSeverity.BLOCKED
        else _REVIEW_PREFIX
    )
    return f"{prefix}{issue.code}] {issue.message}"


def _extend_validator(
    original: Callable[[str, dict[str, str]], tuple[dict[str, str], list[str]]],
):
    def validate_mapped_values(
        target_registry: str,
        values: dict[str, str],
    ) -> tuple[dict[str, str], list[str]]:
        normalized, issues = original(target_registry, values)
        contract_target = _TARGET_MAP.get(target_registry)
        if contract_target is None:
            return normalized, issues

        validation = validate_profile_row(
            contract_target,
            _contract_values(contract_target, normalized),
        )
        valid_keys = {spec.key for spec in services.registry_field_specs(target_registry)}
        for key, value in validation.normalized.items():
            if key in valid_keys:
                normalized[key] = value
        for issue in validation.issues:
            if issue.code in _PLATFORM_PROVENANCE_ISSUES:
                # Legacy ImportRow already preserves batch + row_number + publication-row
                # identity, so the platform provenance is reproducible even without a
                # source-owned occurrence identifier.
                continue
            message = _issue_message(issue)
            if message not in issues:
                issues.append(message)
        return normalized, issues

    return validate_mapped_values


def _extend_review_status(original: Callable[..., str]):
    def review_status(row, validation_issues: list[str], conflicts: list[str]) -> str:
        blocked = [
            issue
            for issue in validation_issues
            if not issue.startswith(_REVIEW_PREFIX)
        ]
        if blocked:
            return original(row, blocked, conflicts)
        if conflicts:
            return original(row, [], conflicts)
        if validation_issues:
            return services.ImportRow.ReviewStatus.REVIEW
        return original(row, [], [])

    return review_status


def install_master_data_contracts() -> None:
    if getattr(services, _INSTALLED_ATTRIBUTE, False):
        return
    _register_field_specs()
    services.validate_mapped_values = _extend_validator(
        services.validate_mapped_values
    )
    services._review_status = _extend_review_status(services._review_status)
    setattr(services, _INSTALLED_ATTRIBUTE, True)


def installation_state() -> dict[str, Any]:
    return {
        "installed": bool(getattr(services, _INSTALLED_ATTRIBUTE, False)),
        "equipment_fields": tuple(
            spec.key
            for spec in services.registry_field_specs(
                services.ImportBatch.TargetRegistry.EQUIPMENT
            )
        ),
        "dispatching_fields": tuple(
            spec.key
            for spec in services.registry_field_specs(
                services.ImportBatch.TargetRegistry.DISPATCHING
            )
        ),
    }
