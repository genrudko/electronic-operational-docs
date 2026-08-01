from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class MasterDataTarget(StrEnum):
    ORGANIZATION_STRUCTURE = "ORGANIZATION_STRUCTURE"
    PERSONNEL = "PERSONNEL"
    EQUIPMENT = "EQUIPMENT"
    DISPATCHING = "DISPATCHING"


class ReviewDisposition(StrEnum):
    READY = "READY"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


class IssueSeverity(StrEnum):
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class FieldContract:
    key: str
    label: str
    required: bool = False
    max_length: int = 1000
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProfileContract:
    target: MasterDataTarget
    label: str
    fields: tuple[FieldContract, ...]
    publication_enabled: bool = False

    @property
    def field_keys(self) -> frozenset[str]:
        return frozenset(field.key for field in self.fields)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    field: str
    severity: IssueSeverity
    message: str


@dataclass(frozen=True, slots=True)
class RowValidation:
    disposition: ReviewDisposition
    normalized: dict[str, str]
    issues: tuple[ValidationIssue, ...]


ORGANIZATION_STRUCTURE_PROFILE = ProfileContract(
    target=MasterDataTarget.ORGANIZATION_STRUCTURE,
    label="Организации, подразделения, рабочие места и энергообъекты",
    fields=(
        FieldContract(
            "organization_code",
            "Код организации",
            required=True,
            max_length=32,
            aliases=("код организации", "organization code"),
        ),
        FieldContract(
            "organization_name",
            "Наименование организации",
            required=True,
            max_length=255,
            aliases=("организация", "наименование организации"),
        ),
        FieldContract(
            "division_code",
            "Код подразделения",
            max_length=32,
            aliases=("код подразделения",),
        ),
        FieldContract(
            "division_name",
            "Подразделение",
            max_length=255,
            aliases=("подразделение", "наименование подразделения"),
        ),
        FieldContract(
            "parent_division_code",
            "Код вышестоящего подразделения",
            max_length=32,
            aliases=("вышестоящее подразделение", "родительское подразделение"),
        ),
        FieldContract(
            "workplace_code",
            "Код рабочего места",
            max_length=32,
            aliases=("код рабочего места",),
        ),
        FieldContract(
            "workplace_name",
            "Рабочее место",
            max_length=255,
            aliases=("рабочее место", "наименование рабочего места"),
        ),
        FieldContract(
            "site_code",
            "Код энергообъекта",
            max_length=64,
            aliases=("код энергообъекта", "код объекта"),
        ),
        FieldContract(
            "site_name",
            "Энергообъект",
            max_length=500,
            aliases=("энергообъект", "объект"),
        ),
        FieldContract(
            "site_type",
            "Вид энергообъекта",
            max_length=32,
            aliases=("вид энергообъекта", "тип объекта"),
        ),
    ),
)


PERSONNEL_PROFILE = ProfileContract(
    target=MasterDataTarget.PERSONNEL,
    label="Персонал",
    fields=(
        FieldContract("personnel_number", "Табельный номер", required=True, max_length=64),
        FieldContract("last_name", "Фамилия", required=True, max_length=150),
        FieldContract("first_name", "Имя", required=True, max_length=150),
        FieldContract("middle_name", "Отчество", max_length=150),
        FieldContract("division", "Подразделение", required=True, max_length=255),
        FieldContract("position", "Должность", required=True, max_length=255),
    ),
)


EQUIPMENT_PROFILE = ProfileContract(
    target=MasterDataTarget.EQUIPMENT,
    label="Оборудование и иерархия",
    fields=(
        FieldContract("code", "Стабильный код", required=True, max_length=96),
        FieldContract("technical_name", "Техническое наименование", required=True, max_length=500),
        FieldContract("dispatcher_name", "Диспетчерское наименование", max_length=1000),
        FieldContract("type", "Вид оборудования", required=True, max_length=255),
        FieldContract("family_code", "Код технической группы", max_length=64),
        FieldContract("source_designation", "Исходное обозначение", max_length=64),
        FieldContract("variant", "Исполнение", max_length=255),
        FieldContract("site", "Энергообъект", required=True, max_length=500),
        FieldContract("parent_code", "Код родительского оборудования", max_length=96),
        FieldContract("aliases", "Варианты наименования", max_length=2000),
        FieldContract("source_occurrence_id", "Идентификатор строки источника", max_length=128),
        FieldContract("source_revision_id", "Идентификатор редакции источника", max_length=128),
        FieldContract("status", "Состояние", max_length=24),
        FieldContract("voltage_level", "Класс напряжения", max_length=64),
    ),
)


DISPATCHING_PROFILE = ProfileContract(
    target=MasterDataTarget.DISPATCHING,
    label="Оперативное управление и ведение",
    fields=(
        FieldContract("equipment_code", "Код оборудования", required=True, max_length=96),
        FieldContract("relation_kind", "Управление или ведение", required=True, max_length=16),
        FieldContract("subject", "Субъект", required=True, max_length=1000),
        FieldContract("level", "Уровень", required=True, max_length=500),
        FieldContract("effective_from", "Действует с", max_length=10),
        FieldContract("effective_until", "Действует по", max_length=10),
        FieldContract("information_only", "Только информационное ведение", max_length=5),
        FieldContract("basis_reference", "Документ-основание", max_length=1000),
        FieldContract("source_occurrence_id", "Идентификатор строки источника", max_length=128),
    ),
)


PROFILE_CONTRACTS: Mapping[MasterDataTarget, ProfileContract] = {
    profile.target: profile
    for profile in (
        ORGANIZATION_STRUCTURE_PROFILE,
        PERSONNEL_PROFILE,
        EQUIPMENT_PROFILE,
        DISPATCHING_PROFILE,
    )
}

DC_DISTRIBUTION_FAMILY_CODE = "dc_distribution_board"
DC_DISTRIBUTION_FAMILY_NAME = "Щит или шкаф оперативного постоянного тока"
DC_SOURCE_DESIGNATIONS = frozenset({"ЩПТ", "ШОТ"})

_SPACE_RE = re.compile(r"\s+")
_ALIAS_SPLIT_RE = re.compile(r"[;|\n]+")


def normalize_text(value: object) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u00a0", " ")).strip()


def normalize_source_designation(value: object) -> str:
    return normalize_text(value).upper()


def equipment_family(
    *,
    source_designation: object,
    family_code: object = "",
) -> tuple[str, str]:
    designation = normalize_source_designation(source_designation)
    explicit_family = normalize_text(family_code).lower()
    if designation in DC_SOURCE_DESIGNATIONS:
        if explicit_family and explicit_family != DC_DISTRIBUTION_FAMILY_CODE:
            raise ValueError(
                "ЩПТ/ШОТ должны относиться к technical family "
                f"{DC_DISTRIBUTION_FAMILY_CODE}."
            )
        return DC_DISTRIBUTION_FAMILY_CODE, DC_DISTRIBUTION_FAMILY_NAME
    return explicit_family, ""


def normalize_aliases(value: object) -> tuple[str, ...]:
    aliases: list[str] = []
    seen: set[str] = set()
    for raw_alias in _ALIAS_SPLIT_RE.split(str(value or "")):
        alias = normalize_text(raw_alias)
        token = alias.casefold()
        if alias and token not in seen:
            aliases.append(alias)
            seen.add(token)
    return tuple(aliases)


def _issue(
    code: str,
    field: str,
    severity: IssueSeverity,
    message: str,
) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, severity=severity, message=message)


def validate_profile_row(
    target: MasterDataTarget | str,
    values: Mapping[str, object],
) -> RowValidation:
    profile = PROFILE_CONTRACTS[MasterDataTarget(target)]
    normalized = {
        key: normalize_text(value)
        for key, value in values.items()
        if key in profile.field_keys
    }
    issues: list[ValidationIssue] = []

    unknown_fields = sorted(set(values) - profile.field_keys)
    for field in unknown_fields:
        issues.append(
            _issue(
                "UNKNOWN_FIELD",
                field,
                IssueSeverity.REVIEW,
                "Поле не входит в выбранный master-data profile.",
            )
        )

    for field in profile.fields:
        value = normalized.get(field.key, "")
        if field.required and not value:
            issues.append(
                _issue(
                    "REQUIRED_FIELD_MISSING",
                    field.key,
                    IssueSeverity.BLOCKED,
                    f"Не заполнено обязательное поле «{field.label}».",
                )
            )
        if len(value) > field.max_length:
            issues.append(
                _issue(
                    "VALUE_TOO_LONG",
                    field.key,
                    IssueSeverity.BLOCKED,
                    f"Значение поля «{field.label}» превышает {field.max_length} символов.",
                )
            )

    if profile.target is MasterDataTarget.ORGANIZATION_STRUCTURE:
        division_code = normalized.get("division_code", "")
        division_name = normalized.get("division_name", "")
        workplace_code = normalized.get("workplace_code", "")
        workplace_name = normalized.get("workplace_name", "")
        site_code = normalized.get("site_code", "")
        site_name = normalized.get("site_name", "")
        if bool(division_code) != bool(division_name):
            issues.append(
                _issue(
                    "DIVISION_PAIR_INCOMPLETE",
                    "division_code",
                    IssueSeverity.BLOCKED,
                    "Код и наименование подразделения должны быть заполнены вместе.",
                )
            )
        if bool(workplace_code) != bool(workplace_name):
            issues.append(
                _issue(
                    "WORKPLACE_PAIR_INCOMPLETE",
                    "workplace_code",
                    IssueSeverity.BLOCKED,
                    "Код и наименование рабочего места должны быть заполнены вместе.",
                )
            )
        if bool(site_code) != bool(site_name):
            issues.append(
                _issue(
                    "SITE_PAIR_INCOMPLETE",
                    "site_code",
                    IssueSeverity.BLOCKED,
                    "Код и наименование энергообъекта должны быть заполнены вместе.",
                )
            )
        if normalized.get("parent_division_code") and not division_code:
            issues.append(
                _issue(
                    "PARENT_WITHOUT_DIVISION",
                    "parent_division_code",
                    IssueSeverity.BLOCKED,
                    "Вышестоящее подразделение нельзя указать без текущего подразделения.",
                )
            )

    if profile.target is MasterDataTarget.EQUIPMENT:
        designation = normalize_source_designation(normalized.get("source_designation", ""))
        normalized["source_designation"] = designation
        try:
            family_code, family_name = equipment_family(
                source_designation=designation,
                family_code=normalized.get("family_code", ""),
            )
        except ValueError as exc:
            issues.append(
                _issue(
                    "EQUIPMENT_FAMILY_CONFLICT",
                    "family_code",
                    IssueSeverity.BLOCKED,
                    str(exc),
                )
            )
        else:
            if family_code:
                normalized["family_code"] = family_code
            if family_name:
                normalized["family_name"] = family_name
        normalized["aliases"] = "; ".join(normalize_aliases(normalized.get("aliases", "")))
        if normalized.get("parent_code") == normalized.get("code") and normalized.get("code"):
            issues.append(
                _issue(
                    "EQUIPMENT_SELF_PARENT",
                    "parent_code",
                    IssueSeverity.BLOCKED,
                    "Оборудование не может быть родителем самому себе.",
                )
            )
        if not normalized.get("source_occurrence_id"):
            issues.append(
                _issue(
                    "SOURCE_OCCURRENCE_MISSING",
                    "source_occurrence_id",
                    IssueSeverity.REVIEW,
                    "Не указан воспроизводимый идентификатор строки источника.",
                )
            )

    if profile.target is MasterDataTarget.DISPATCHING:
        relation_kind = normalized.get("relation_kind", "").upper()
        normalized["relation_kind"] = relation_kind
        if relation_kind not in {"MANAGEMENT", "SUPERVISION"}:
            issues.append(
                _issue(
                    "RELATION_KIND_INVALID",
                    "relation_kind",
                    IssueSeverity.BLOCKED,
                    "Допустимы только MANAGEMENT и SUPERVISION.",
                )
            )
        information_only = normalized.get("information_only", "").casefold()
        normalized["information_only"] = information_only
        if information_only in {"1", "да", "true", "yes"} and relation_kind == "MANAGEMENT":
            issues.append(
                _issue(
                    "INFORMATION_ONLY_MANAGEMENT_FORBIDDEN",
                    "information_only",
                    IssueSeverity.BLOCKED,
                    "Информационное ведение не может быть оперативным управлением.",
                )
            )

    if any(issue.severity is IssueSeverity.BLOCKED for issue in issues):
        disposition = ReviewDisposition.BLOCKED
    elif issues:
        disposition = ReviewDisposition.REVIEW
    else:
        disposition = ReviewDisposition.READY
    return RowValidation(disposition, normalized, tuple(issues))
