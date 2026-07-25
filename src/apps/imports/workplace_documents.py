from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from apps.organizations.models import Employee, RoleAssignment, Workplace
from apps.workplace_docs.models import (
    ElectronicStorageInterpretation,
    RequirementKind,
    SourceKind,
    StorageForm,
    WorkplaceDocumentEntry,
    WorkplaceDocumentList,
    WorkplaceDocumentRevision,
)
from apps.workplace_docs.services import approve_revision

from .models import (
    DataProfile,
    WorkplaceDocumentPublication,
    WorkplaceDocumentSourceRevision,
    WorkplaceDocumentSourceRow,
)
from .services import require_import_employee

MAX_WORKPLACE_DOCUMENT_CSV_SIZE = 5 * 1024 * 1024
WORKPLACE_DOCUMENT_HEADER = (
    "register_entry_no",
    "section_no",
    "section_name",
    "subsection_no",
    "subsection_name",
    "source_document_no",
    "document_title_raw",
    "document_type_proposed",
    "electronic_storage_mark",
    "electronic_storage_interpretation",
    "review_period_raw",
    "review_interval_years_proposed",
    "approval_date_from_title_page",
    "approving_role_from_title_page",
    "approver_from_title_page",
    "workplace_scope",
    "source_pdf_page",
    "source_notes",
)
DIRECT_PUBLISHER_ROLE = "organization_admin"
CONTROLLED_WORKPLACE_ALIASES = {
    "рабочее место оперативного персонала кочубеевской вэс": "KOCH_CONTROL_ROOM",
}


class WorkplaceDocumentRegisterError(ValueError):
    """Контролируемая ошибка структуры или значений CSV-реестра."""


@dataclass(frozen=True)
class ParsedWorkplaceDocumentRow:
    source_row_number: int
    source_index: int
    register_entry_no: int
    section_no: str
    section_name: str
    subsection_no: str
    subsection_name: str
    source_document_no: str
    document_title_raw: str
    document_type_proposed: str
    electronic_storage_mark: str
    electronic_storage_interpretation: str
    review_period_raw: str
    review_interval_years_raw: str
    review_interval_months: int | None
    approval_date: date | None
    approval_date_raw: str
    approving_role: str
    approver_name: str
    workplace_scope: str
    source_pdf_page: int | None
    source_notes: str
    review_status: str
    issues: tuple[str, ...]
    fingerprint: str


@dataclass(frozen=True)
class ParsedWorkplaceDocumentRegister:
    rows: tuple[ParsedWorkplaceDocumentRow, ...]
    header_signature: str
    encoding: str
    workplace_scope: str
    manifest: dict[str, Any]


def _normalize_space(value: str) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def _comparison_token(value: str) -> str:
    return _normalize_space(value).casefold().replace("ё", "е")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_payload(value: object) -> tuple[str, str]:
    canonical = _canonical_json(value)
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_upload(uploaded_file) -> bytes:
    size = int(getattr(uploaded_file, "size", 0) or 0)
    if size <= 0:
        raise WorkplaceDocumentRegisterError("Нельзя загрузить пустой CSV-файл.")
    if size > MAX_WORKPLACE_DOCUMENT_CSV_SIZE:
        raise WorkplaceDocumentRegisterError("Размер CSV-файла превышает 5 МБ.")
    data = uploaded_file.read(MAX_WORKPLACE_DOCUMENT_CSV_SIZE + 1)
    if len(data) > MAX_WORKPLACE_DOCUMENT_CSV_SIZE:
        raise WorkplaceDocumentRegisterError("Размер CSV-файла превышает 5 МБ.")
    try:
        uploaded_file.seek(0)
    except (AttributeError, OSError):
        pass
    return data


def _decode_csv(data: bytes) -> tuple[str, str]:
    if b"\x00" in data:
        raise WorkplaceDocumentRegisterError("CSV содержит нулевые байты и не может быть разобран.")
    encoding = "utf-8-sig" if data.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        return data.decode(encoding), encoding
    except UnicodeDecodeError as exc:
        raise WorkplaceDocumentRegisterError(
            "CSV должен быть сохранён в UTF-8 или UTF-8 с BOM."
        ) from exc


def _positive_integer(value: str, *, label: str, allow_zero: bool = False) -> int:
    normalized = _normalize_space(value)
    if not re.fullmatch(r"\d+", normalized):
        raise WorkplaceDocumentRegisterError(f"{label}: требуется целое число.")
    result = int(normalized)
    minimum = 0 if allow_zero else 1
    if result < minimum:
        raise WorkplaceDocumentRegisterError(f"{label}: значение должно быть не меньше {minimum}.")
    return result


def _optional_positive_integer(value: str, *, label: str) -> int | None:
    normalized = _normalize_space(value)
    if not normalized:
        return None
    return _positive_integer(normalized, label=label)


def _optional_iso_date(value: str, *, label: str) -> date | None:
    normalized = _normalize_space(value)
    if not normalized:
        return None
    try:
        return date.fromisoformat(normalized)
    except ValueError as exc:
        raise WorkplaceDocumentRegisterError(f"{label}: ожидается дата ГГГГ-ММ-ДД.") from exc


def _review_months(years_raw: str, period_raw: str) -> tuple[int | None, list[str]]:
    years = _normalize_space(years_raw)
    period = _normalize_space(period_raw)
    issues: list[str] = []
    if not years:
        if period not in {"", "-", "–"}:
            issues.append(
                "Периодичность указана текстом, но нормализованный интервал отсутствует."
            )
        return None, issues
    try:
        decimal_years = Decimal(years.replace(",", "."))
    except InvalidOperation:
        issues.append("Предложенный период пересмотра не является числом.")
        return None, issues
    months = decimal_years * 12
    if months != months.to_integral_value() or not 1 <= int(months) <= 120:
        issues.append("Предложенный период нельзя безопасно преобразовать в целые месяцы.")
        return None, issues
    if period in {"", "-", "–"}:
        issues.append("Числовой период указан при отсутствии периодичности в исходной колонке.")
    return int(months), issues


def _base_row(raw: dict[str, str], source_row_number: int) -> ParsedWorkplaceDocumentRow:
    source_index = source_row_number - 2
    register_entry_no = _positive_integer(
        raw["register_entry_no"],
        label=f"Строка {source_row_number}, register_entry_no",
    )
    section_no = _normalize_space(raw["section_no"])
    section_name = _normalize_space(raw["section_name"])
    title = _normalize_space(raw["document_title_raw"])
    workplace_scope = _normalize_space(raw["workplace_scope"])
    issues: list[str] = []
    blocked = False
    if not section_no:
        issues.append("Не указан номер раздела.")
        blocked = True
    if not section_name:
        issues.append("Не указано наименование раздела.")
        blocked = True
    if not title:
        issues.append("Не указано наименование документа.")
        blocked = True
    elif len(title) > 500:
        issues.append("Наименование превышает 500 символов и не помещается в рабочую карточку.")
        blocked = True
    if not workplace_scope:
        issues.append("Не указана область рабочего места.")
        blocked = True

    mark = _normalize_space(raw["electronic_storage_mark"])
    interpretation = _normalize_space(raw["electronic_storage_interpretation"])
    allowed_interpretations = {
        ElectronicStorageInterpretation.INDICATED,
        ElectronicStorageInterpretation.NOT_INDICATED,
    }
    if interpretation not in allowed_interpretations:
        issues.append("Неизвестная интерпретация отметки электронной формы.")
        blocked = True
    expected_pair = {
        "+": ElectronicStorageInterpretation.INDICATED,
        "-": ElectronicStorageInterpretation.NOT_INDICATED,
        "–": ElectronicStorageInterpretation.NOT_INDICATED,
    }.get(mark)
    if expected_pair is None:
        issues.append("Неизвестная исходная отметка электронной формы.")
        blocked = True
    elif interpretation != expected_pair:
        issues.append("Исходная отметка и её интерпретация противоречат друг другу.")
        blocked = True

    review_months, review_issues = _review_months(
        raw["review_interval_years_proposed"],
        raw["review_period_raw"],
    )
    issues.extend(review_issues)
    approval_raw = _normalize_space(raw["approval_date_from_title_page"])
    try:
        approval_date = _optional_iso_date(
            approval_raw,
            label=f"Строка {source_row_number}, approval_date_from_title_page",
        )
    except WorkplaceDocumentRegisterError as exc:
        approval_date = None
        issues.append(str(exc))
        blocked = True
    try:
        source_pdf_page = _optional_positive_integer(
            raw["source_pdf_page"],
            label=f"Строка {source_row_number}, source_pdf_page",
        )
    except WorkplaceDocumentRegisterError as exc:
        source_pdf_page = None
        issues.append(str(exc))
        blocked = True

    document_type = _normalize_space(raw["document_type_proposed"])
    if not document_type:
        issues.append("Тип документа не предложен; требуется ручная классификация.")
    source_notes = _normalize_space(raw["source_notes"])
    if source_notes:
        issues.append(f"Замечание источника: {source_notes}")

    status = WorkplaceDocumentSourceRow.ReviewStatus.BLOCKED if blocked else (
        WorkplaceDocumentSourceRow.ReviewStatus.REVIEW_REQUIRED
        if issues
        else WorkplaceDocumentSourceRow.ReviewStatus.READY
    )
    fingerprint_payload = {
        key: _normalize_space(value)
        for key, value in raw.items()
    }
    fingerprint = hashlib.sha256(
        _canonical_json(fingerprint_payload).encode("utf-8")
    ).hexdigest()
    return ParsedWorkplaceDocumentRow(
        source_row_number=source_row_number,
        source_index=source_index,
        register_entry_no=register_entry_no,
        section_no=section_no,
        section_name=section_name,
        subsection_no=_normalize_space(raw["subsection_no"]),
        subsection_name=_normalize_space(raw["subsection_name"]),
        source_document_no=_normalize_space(raw["source_document_no"]),
        document_title_raw=title,
        document_type_proposed=document_type,
        electronic_storage_mark=mark,
        electronic_storage_interpretation=interpretation,
        review_period_raw=_normalize_space(raw["review_period_raw"]),
        review_interval_years_raw=_normalize_space(raw["review_interval_years_proposed"]),
        review_interval_months=review_months,
        approval_date=approval_date,
        approval_date_raw=approval_raw,
        approving_role=_normalize_space(raw["approving_role_from_title_page"]),
        approver_name=_normalize_space(raw["approver_from_title_page"]),
        workplace_scope=workplace_scope,
        source_pdf_page=source_pdf_page,
        source_notes=source_notes,
        review_status=status,
        issues=tuple(issues),
        fingerprint=fingerprint,
    )


def _add_issue(
    row: ParsedWorkplaceDocumentRow,
    issue: str,
    *,
    blocked: bool = False,
) -> ParsedWorkplaceDocumentRow:
    issues = (*row.issues, issue)
    if blocked:
        status = WorkplaceDocumentSourceRow.ReviewStatus.BLOCKED
    elif row.review_status == WorkplaceDocumentSourceRow.ReviewStatus.READY:
        status = WorkplaceDocumentSourceRow.ReviewStatus.REVIEW_REQUIRED
    else:
        status = row.review_status
    return replace(row, issues=issues, review_status=status)


def parse_workplace_document_register(data: bytes) -> ParsedWorkplaceDocumentRegister:
    text, encoding = _decode_csv(data)
    reader = csv.DictReader(io.StringIO(text, newline=""))
    actual_header = tuple(reader.fieldnames or ())
    if actual_header != WORKPLACE_DOCUMENT_HEADER:
        raise WorkplaceDocumentRegisterError(
            "Заголовок eod_workplace_document_register.csv не соответствует "
            "утверждённому контракту Patch 011.6.2."
        )
    raw_rows: list[dict[str, str]] = []
    for row_number, raw in enumerate(reader, start=2):
        if None in raw:
            raise WorkplaceDocumentRegisterError(
                f"Строка {row_number}: обнаружены значения вне утверждённых колонок."
            )
        if all(not _normalize_space(value) for value in raw.values()):
            continue
        raw_rows.append({key: value or "" for key, value in raw.items()})
    if not raw_rows:
        raise WorkplaceDocumentRegisterError("CSV не содержит позиций реестра.")
    if len(raw_rows) > 1000:
        raise WorkplaceDocumentRegisterError("CSV содержит более 1000 позиций.")

    rows = [_base_row(raw, row_number) for row_number, raw in enumerate(raw_rows, start=2)]

    entry_counts = Counter(row.register_entry_no for row in rows)
    section_names: dict[str, set[str]] = defaultdict(set)
    subsection_names: dict[tuple[str, str], set[str]] = defaultdict(set)
    source_number_groups: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    group_numeric_numbers: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    workplace_scopes = {_comparison_token(row.workplace_scope) for row in rows}

    for index, row in enumerate(rows):
        section_names[row.section_no].add(_comparison_token(row.section_name))
        if row.subsection_no:
            subsection_names[(row.section_no, row.subsection_no)].add(
                _comparison_token(row.subsection_name)
            )
        if row.source_document_no:
            source_number_groups[
                (row.section_no, row.subsection_no, row.source_document_no)
            ].append(index)
            if re.fullmatch(r"\d+", row.source_document_no):
                group_numeric_numbers[(row.section_no, row.subsection_no)].append(
                    (int(row.source_document_no), index)
                )

    for index, row in enumerate(rows):
        if entry_counts[row.register_entry_no] > 1:
            rows[index] = _add_issue(
                rows[index],
                "Сквозной номер позиции повторяется в источнике.",
                blocked=True,
            )
        if len(section_names[row.section_no]) > 1:
            rows[index] = _add_issue(
                rows[index],
                "Одному номеру раздела соответствуют разные наименования.",
                blocked=True,
            )
        if row.subsection_no and len(subsection_names[(row.section_no, row.subsection_no)]) > 1:
            rows[index] = _add_issue(
                rows[index],
                "Одному номеру подраздела соответствуют разные наименования.",
                blocked=True,
            )

    for positions in source_number_groups.values():
        if len(positions) > 1:
            for index in positions:
                rows[index] = _add_issue(
                    rows[index],
                    "Номер документа повторяется внутри того же раздела или подраздела.",
                )

    for values in group_numeric_numbers.values():
        numbers = sorted({number for number, _index in values})
        expected = list(range(1, max(numbers) + 1)) if numbers else []
        if numbers != expected:
            for _number, index in values:
                rows[index] = _add_issue(
                    rows[index],
                    "Нумерация документов в разделе или подразделе имеет пропуск или начинается не с 1.",
                )

    expected_entries = list(range(1, len(rows) + 1))
    actual_entries = [row.register_entry_no for row in rows]
    if actual_entries != expected_entries:
        for index, row in enumerate(rows):
            if row.register_entry_no != index + 1:
                rows[index] = _add_issue(
                    rows[index],
                    "Сквозная нумерация позиций имеет пропуск или нарушенный порядок.",
                )

    if len(workplace_scopes) != 1:
        for index in range(len(rows)):
            rows[index] = _add_issue(
                rows[index],
                "В одном файле указаны разные рабочие места.",
                blocked=True,
            )
    workplace_scope = rows[0].workplace_scope if rows else ""
    header_signature = hashlib.sha256(
        _canonical_json(WORKPLACE_DOCUMENT_HEADER).encode("utf-8")
    ).hexdigest()
    manifest = {
        "schema_version": "eod.workplace-document-register.csv.v1",
        "source_format": "CSV",
        "row_count": len(rows),
        "section_count": len({row.section_no for row in rows}),
        "workplace_scope": workplace_scope,
        "electronic_indicated_count": sum(
            row.electronic_storage_interpretation
            == ElectronicStorageInterpretation.INDICATED
            for row in rows
        ),
        "header": list(WORKPLACE_DOCUMENT_HEADER),
        "header_signature": header_signature,
    }
    return ParsedWorkplaceDocumentRegister(
        rows=tuple(rows),
        header_signature=header_signature,
        encoding=encoding,
        workplace_scope=workplace_scope,
        manifest=manifest,
    )


def available_workplace_document_profiles(organization) -> tuple[DataProfile, ...]:
    DataProfile.ensure_for_organization(organization)
    return tuple(
        DataProfile.objects.filter(
            organization=organization,
            code="local-validation",
            kind=DataProfile.Kind.LOCAL_VALIDATION,
            is_active=True,
            allows_real_personal_data=True,
            export_policy=DataProfile.ExportPolicy.PROHIBITED,
        ).order_by("name")
    )


def _require_development_database() -> None:
    if getattr(settings, "EOD_DATABASE_PROFILE", "presentation") != "development":
        raise PermissionDenied(
            "Реальный реестр документации загружается только в локальную development-базу. "
            "Презентационная база не изменена."
        )


def _match_workplace(organization, source_name: str) -> tuple[Workplace | None, str]:
    token = _comparison_token(source_name)
    exact = [
        workplace
        for workplace in Workplace.objects.filter(organization=organization, is_active=True)
        if _comparison_token(workplace.name) == token
    ]
    if len(exact) == 1:
        return exact[0], "EXACT"
    alias_code = CONTROLLED_WORKPLACE_ALIASES.get(token)
    if alias_code:
        alias_match = Workplace.objects.filter(
            organization=organization,
            code=alias_code,
            is_active=True,
        ).first()
        if alias_match is not None:
            return alias_match, "CONTROLLED_ALIAS"
    return None, "NOT_FOUND" if not exact else "AMBIGUOUS"


def source_revision_queryset_for_employee(employee: Employee):
    return WorkplaceDocumentSourceRevision.objects.filter(
        organization=employee.organization
    ).select_related(
        "data_profile",
        "uploaded_by",
        "published_by",
        "matched_workplace",
        "target_document_list",
        "target_revision",
    )


def workplace_document_revision_for_user(user, public_id):
    employee = require_import_employee(user)
    try:
        revision = source_revision_queryset_for_employee(employee).get(public_id=public_id)
    except WorkplaceDocumentSourceRevision.DoesNotExist as exc:
        raise PermissionDenied(
            "Редакция реестра документации недоступна для вашей организации."
        ) from exc
    return employee, revision


@transaction.atomic
def stage_workplace_document_register(
    *,
    uploaded_file,
    employee: Employee,
    data_profile: DataProfile,
    source_reference: str,
    effective_from: date,
    list_review_period_months: int,
    target_workplace: Workplace | None = None,
) -> WorkplaceDocumentSourceRevision:
    _require_development_database()
    if employee.organization_id != data_profile.organization_id:
        raise ValidationError("Профиль данных относится к другой организации.")
    if (
        data_profile.code != "local-validation"
        or data_profile.kind != DataProfile.Kind.LOCAL_VALIDATION
        or not data_profile.allows_real_personal_data
        or data_profile.export_policy != DataProfile.ExportPolicy.PROHIBITED
    ):
        raise ValidationError(
            "Реестр с реквизитами утверждения допускается только в профиле local-validation."
        )
    if not 1 <= list_review_period_months <= 60:
        raise ValidationError("Период пересмотра перечня должен быть от 1 до 60 месяцев.")
    if target_workplace is not None:
        if target_workplace.organization_id != employee.organization_id:
            raise ValidationError("Выбранное рабочее место относится к другой организации.")
        if not target_workplace.is_active:
            raise ValidationError("Выбранное рабочее место не является действующим.")

    data = _read_upload(uploaded_file)
    digest = hashlib.sha256(data).hexdigest()
    normalized_reference = _normalize_space(source_reference)
    parsed = parse_workplace_document_register(data)
    automatic_workplace, automatic_match_kind = _match_workplace(
        employee.organization,
        parsed.workplace_scope,
    )
    if target_workplace is not None:
        if (
            automatic_workplace is not None
            and automatic_workplace.pk != target_workplace.pk
        ):
            raise ValidationError(
                "Выбранное рабочее место противоречит однозначному "
                "сопоставлению области из CSV."
            )
        workplace = target_workplace
        match_kind = (
            automatic_match_kind
            if automatic_workplace is not None
            else "MANUAL_SELECTION"
        )
    else:
        workplace = automatic_workplace
        match_kind = automatic_match_kind

    existing = WorkplaceDocumentSourceRevision.objects.filter(
        organization=employee.organization,
        file_sha256=digest,
        source_reference=normalized_reference,
        effective_from=effective_from,
        list_review_period_months=list_review_period_months,
        matched_workplace=workplace,
    ).first()
    if existing is not None:
        return existing

    manifest = {
        **parsed.manifest,
        "source_sha256": digest,
        "source_size": len(data),
        "workplace_match_kind": match_kind,
        "automatic_workplace_match_kind": automatic_match_kind,
        "selected_workplace_code": (
            target_workplace.code if target_workplace is not None else None
        ),
        "matched_workplace_code": workplace.code if workplace else None,
        "source_bytes_persisted": False,
    }
    revision = WorkplaceDocumentSourceRevision.objects.create(
        organization=employee.organization,
        data_profile=data_profile,
        uploaded_by=employee,
        source_reference=normalized_reference,
        effective_from=effective_from,
        list_review_period_months=list_review_period_months,
        original_filename=getattr(uploaded_file, "name", "eod_workplace_document_register.csv"),
        file_size=len(data),
        file_sha256=digest,
        header_signature=parsed.header_signature,
        source_encoding=parsed.encoding,
        workplace_scope_raw=parsed.workplace_scope,
        matched_workplace=workplace,
        manifest=manifest,
        total_rows=len(parsed.rows),
        section_count=len({row.section_no for row in parsed.rows}),
        electronic_indicated_rows=sum(
            row.electronic_storage_interpretation
            == ElectronicStorageInterpretation.INDICATED
            for row in parsed.rows
        ),
    )

    ready = review = blocked = 0
    for parsed_row in parsed.rows:
        issues = list(parsed_row.issues)
        status = parsed_row.review_status
        if workplace is None:
            issues.append(
                "Рабочее место не сопоставлено однозначно с действующим справочником организации."
            )
            status = WorkplaceDocumentSourceRow.ReviewStatus.BLOCKED
        stored = WorkplaceDocumentSourceRow.objects.create(
            source_revision=revision,
            source_row_number=parsed_row.source_row_number,
            source_index=parsed_row.source_index,
            register_entry_no=parsed_row.register_entry_no,
            section_no=parsed_row.section_no,
            section_name=parsed_row.section_name,
            subsection_no=parsed_row.subsection_no,
            subsection_name=parsed_row.subsection_name,
            source_document_no=parsed_row.source_document_no,
            document_title_raw=parsed_row.document_title_raw,
            document_type_proposed=parsed_row.document_type_proposed,
            electronic_storage_mark=parsed_row.electronic_storage_mark,
            electronic_storage_interpretation=parsed_row.electronic_storage_interpretation,
            review_period_raw=parsed_row.review_period_raw,
            review_interval_years_raw=parsed_row.review_interval_years_raw,
            review_interval_months=parsed_row.review_interval_months,
            approval_date=parsed_row.approval_date,
            approval_date_raw=parsed_row.approval_date_raw,
            approving_role=parsed_row.approving_role,
            approver_name=parsed_row.approver_name,
            workplace_scope=parsed_row.workplace_scope,
            source_pdf_page=parsed_row.source_pdf_page,
            source_notes=parsed_row.source_notes,
            initial_review_status=status,
            review_status=status,
            issues=issues,
            fingerprint=parsed_row.fingerprint,
        )
        stored.full_clean()
        if status == WorkplaceDocumentSourceRow.ReviewStatus.READY:
            ready += 1
        elif status == WorkplaceDocumentSourceRow.ReviewStatus.REVIEW_REQUIRED:
            review += 1
        else:
            blocked += 1

    revision.ready_rows = ready
    revision.review_rows = review
    revision.blocked_rows = blocked
    revision.excluded_rows = 0
    revision.save(
        update_fields=(
            "ready_rows",
            "review_rows",
            "blocked_rows",
            "excluded_rows",
            "updated_at",
        )
    )
    return revision


def _refresh_workplace_document_revision_counts(
    revision: WorkplaceDocumentSourceRevision,
) -> None:
    counts = Counter(
        revision.source_rows.values_list("review_status", flat=True)
    )
    revision.ready_rows = counts[WorkplaceDocumentSourceRow.ReviewStatus.READY]
    revision.review_rows = counts[
        WorkplaceDocumentSourceRow.ReviewStatus.REVIEW_REQUIRED
    ]
    revision.blocked_rows = counts[WorkplaceDocumentSourceRow.ReviewStatus.BLOCKED]
    revision.excluded_rows = counts[WorkplaceDocumentSourceRow.ReviewStatus.EXCLUDED]
    revision.save(
        update_fields=(
            "ready_rows",
            "review_rows",
            "blocked_rows",
            "excluded_rows",
            "updated_at",
        )
    )


@transaction.atomic
def decide_workplace_document_source_row(
    *,
    source_revision: WorkplaceDocumentSourceRevision,
    row_id: int,
    actor: Employee,
    action: str,
    note: str,
) -> WorkplaceDocumentSourceRow:
    _require_development_database()
    revision = WorkplaceDocumentSourceRevision.objects.select_for_update().get(
        pk=source_revision.pk
    )
    if revision.organization_id != actor.organization_id:
        raise PermissionDenied("Нельзя проверять реестр другой организации.")
    if revision.status != WorkplaceDocumentSourceRevision.Status.STAGED:
        raise ValidationError("Решения доступны только для staging-редакции.")
    row = WorkplaceDocumentSourceRow.objects.select_for_update().get(
        pk=row_id,
        source_revision=revision,
    )
    normalized_note = _normalize_space(note)
    if action in {
        WorkplaceDocumentSourceRow.ReviewDecision.ACCEPT_AS_IS,
        WorkplaceDocumentSourceRow.ReviewDecision.EXCLUDE,
    } and not normalized_note:
        raise ValidationError("Для решения требуется содержательное обоснование.")
    if action == WorkplaceDocumentSourceRow.ReviewDecision.ACCEPT_AS_IS:
        if row.initial_review_status != WorkplaceDocumentSourceRow.ReviewStatus.REVIEW_REQUIRED:
            raise ValidationError(
                "Принять как есть можно только строку, изначально требующую проверки."
            )
        row.review_status = WorkplaceDocumentSourceRow.ReviewStatus.READY
        row.review_decision = WorkplaceDocumentSourceRow.ReviewDecision.ACCEPT_AS_IS
    elif action == WorkplaceDocumentSourceRow.ReviewDecision.EXCLUDE:
        if row.initial_review_status != WorkplaceDocumentSourceRow.ReviewStatus.REVIEW_REQUIRED:
            raise ValidationError(
                "Исключить можно только строку, изначально требующую проверки."
            )
        row.review_status = WorkplaceDocumentSourceRow.ReviewStatus.EXCLUDED
        row.review_decision = WorkplaceDocumentSourceRow.ReviewDecision.EXCLUDE
    elif action == "RESET":
        row.review_status = row.initial_review_status
        row.review_decision = WorkplaceDocumentSourceRow.ReviewDecision.NONE
        normalized_note = ""
        row.reviewed_by = None
        row.reviewed_at = None
    else:
        raise ValidationError("Неизвестное решение по строке реестра.")
    if action != "RESET":
        row.reviewed_by = actor
        row.reviewed_at = timezone.now()
    row.decision_note = normalized_note
    row.full_clean()
    row.save(
        update_fields=(
            "review_status",
            "review_decision",
            "decision_note",
            "reviewed_by",
            "reviewed_at",
        )
    )
    _refresh_workplace_document_revision_counts(revision)
    return row


def build_workplace_document_publication_preview(
    revision: WorkplaceDocumentSourceRevision,
) -> dict[str, Any]:
    rows = list(
        revision.source_rows.filter(
            review_status=WorkplaceDocumentSourceRow.ReviewStatus.READY
        ).order_by("register_entry_no", "source_index")
    )
    payload = {
        "schema_version": "eod.workplace-document-import.publication.v1",
        "source": {
            "revision_public_id": str(revision.public_id),
            "filename": revision.original_filename,
            "sha256": revision.file_sha256,
            "source_reference": revision.source_reference,
            "effective_from": revision.effective_from.isoformat(),
            "workplace_scope_raw": revision.workplace_scope_raw,
            "matched_workplace_id": revision.matched_workplace_id,
            "matched_workplace": (
                revision.matched_workplace.name if revision.matched_workplace_id else None
            ),
        },
        "entries": [
            {
                "register_entry_no": row.register_entry_no,
                "section_no": row.section_no,
                "section_name": row.section_name,
                "subsection_no": row.subsection_no,
                "subsection_name": row.subsection_name,
                "source_document_no": row.source_document_no,
                "title": row.document_title_raw,
                "document_type": row.document_type_proposed,
                "electronic_storage_mark": row.electronic_storage_mark,
                "electronic_storage_interpretation": row.electronic_storage_interpretation,
                "review_period_raw": row.review_period_raw,
                "review_interval_months": row.review_interval_months,
                "approval_date": row.approval_date.isoformat() if row.approval_date else None,
                "approving_role": row.approving_role,
                "approver_name": row.approver_name,
                "source_pdf_page": row.source_pdf_page,
                "review_decision": row.review_decision,
                "decision_note": row.decision_note,
                "reviewed_by_id": row.reviewed_by_id,
                "reviewed_at": (
                    row.reviewed_at.isoformat() if row.reviewed_at else None
                ),
            }
            for row in rows
        ],
        "excluded": [
            {
                "register_entry_no": row.register_entry_no,
                "status": row.review_status,
                "issues": row.issues,
                "review_decision": row.review_decision,
                "decision_note": row.decision_note,
                "reviewed_by_id": row.reviewed_by_id,
                "reviewed_at": (
                    row.reviewed_at.isoformat() if row.reviewed_at else None
                ),
            }
            for row in revision.source_rows.exclude(
                review_status=WorkplaceDocumentSourceRow.ReviewStatus.READY
            ).order_by("register_entry_no", "source_index")
        ],
    }
    canonical, digest = _sha256_payload(payload)
    return {
        "payload": payload,
        "canonical_json": canonical,
        "digest": digest,
        "summary": {
            "publishable_rows": len(rows),
            "review_rows": revision.review_rows,
            "blocked_rows": revision.blocked_rows,
            "excluded_rows": revision.excluded_rows,
            "sections": len({row.section_no for row in rows}),
            "electronic_indicated": sum(
                row.electronic_storage_interpretation
                == ElectronicStorageInterpretation.INDICATED
                for row in rows
            ),
        },
    }


def _has_direct_publisher_role(actor: Employee) -> bool:
    current = timezone.localdate()
    return (
        RoleAssignment.objects.filter(
            employee=actor,
            role__code=DIRECT_PUBLISHER_ROLE,
            is_active=True,
            valid_from__lte=current,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=current))
        .exists()
    )


def can_publish_workplace_document_register(actor: Employee) -> bool:
    return _has_direct_publisher_role(actor)


def _document_list_code(workplace: Workplace) -> str:
    return f"workplace-documents-{workplace.code.lower()}"[:96]


@transaction.atomic
def publish_workplace_document_register(
    *,
    source_revision: WorkplaceDocumentSourceRevision,
    actor: Employee,
    expected_digest: str,
) -> WorkplaceDocumentPublication:
    _require_development_database()
    locked = (
        WorkplaceDocumentSourceRevision.objects.select_for_update(of=("self",))
        .select_related("matched_workplace", "organization", "data_profile")
        .get(pk=source_revision.pk)
    )
    if locked.organization_id != actor.organization_id:
        raise PermissionDenied("Нельзя публиковать реестр другой организации.")
    if locked.status != WorkplaceDocumentSourceRevision.Status.STAGED:
        raise ValidationError("Опубликовать можно только staging-редакцию.")
    if not _has_direct_publisher_role(actor):
        raise PermissionDenied(
            "Для публикации требуется прямая действующая роль «Администратор справочников»."
        )
    if locked.matched_workplace_id is None:
        raise ValidationError("Рабочее место не сопоставлено; публикация заблокирована.")
    if locked.review_rows or locked.blocked_rows:
        raise ValidationError(
            "Перед публикацией примите решение по всем строкам на проверке и "
            "исправьте заблокированные строки."
        )
    preview = build_workplace_document_publication_preview(locked)
    if preview["digest"] != expected_digest:
        raise ValidationError("Состав staging изменился после предварительного просмотра.")
    if preview["summary"]["publishable_rows"] <= 0:
        raise ValidationError("Нет готовых строк для публикации.")

    document_list, _created = WorkplaceDocumentList.objects.get_or_create(
        organization=locked.organization,
        code=_document_list_code(locked.matched_workplace),
        defaults={
            "workplace": locked.matched_workplace,
            "title": f"Перечень документации: {locked.workplace_scope_raw}",
            "is_active": True,
        },
    )
    if document_list.workplace_id != locked.matched_workplace_id:
        raise ValidationError("Код перечня уже занят другим рабочим местом.")
    next_revision = (
        document_list.revisions.aggregate(value=Max("revision_number"))["value"] or 0
    ) + 1
    target_revision = WorkplaceDocumentRevision.objects.create(
        document_list=document_list,
        revision_number=next_revision,
        effective_from=locked.effective_from,
        review_period_months=locked.list_review_period_months,
        change_summary=(
            f"Импорт из {locked.original_filename}. Основание: {locked.source_reference}"
        ),
    )

    created_entries = 0
    for row in locked.source_rows.filter(
        review_status=WorkplaceDocumentSourceRow.ReviewStatus.READY
    ).select_related("reviewed_by").order_by("register_entry_no", "source_index"):
        storage_form = StorageForm.UNKNOWN
        notes_parts = [row.source_notes] if row.source_notes else []
        if row.review_decision == WorkplaceDocumentSourceRow.ReviewDecision.ACCEPT_AS_IS:
            notes_parts.append(f"Ручная проверка: {row.decision_note}")
        if row.electronic_storage_interpretation == ElectronicStorageInterpretation.INDICATED:
            notes_parts.append(
                "Источник указывает электронную форму; это не отменяет требования "
                "к бумажному экземпляру."
            )
        entry = WorkplaceDocumentEntry.objects.create(
            revision=target_revision,
            code=f"WD-{row.register_entry_no:03d}",
            title=row.document_title_raw,
            source_kind=SourceKind.LOCAL,
            requirement_kind=RequirementKind.MANDATORY,
            applicability_text=row.workplace_scope,
            storage_form=storage_form,
            basis_text=locked.source_reference,
            notes=" ".join(part for part in notes_parts if part),
            source_register_entry_no=row.register_entry_no,
            section_no=row.section_no,
            section_name=row.section_name,
            subsection_no=row.subsection_no,
            subsection_name=row.subsection_name,
            source_document_no=row.source_document_no,
            document_type_label=row.document_type_proposed,
            electronic_storage_mark=row.electronic_storage_mark,
            electronic_storage_interpretation=row.electronic_storage_interpretation,
            review_period_raw=row.review_period_raw,
            review_interval_months=row.review_interval_months,
            approval_date=row.approval_date,
            approving_role=row.approving_role,
            approver_name=row.approver_name,
            source_pdf_page=row.source_pdf_page,
            display_order=row.register_entry_no,
        )
        row.review_status = WorkplaceDocumentSourceRow.ReviewStatus.PUBLISHED
        row.target_entry = entry
        row.save(update_fields=("review_status", "target_entry"))
        created_entries += 1

    _refresh_workplace_document_revision_counts(locked)
    approved_revision = approve_revision(revision=target_revision, actor=actor)
    result_summary = {
        "created_entries": created_entries,
        "review_rows_not_published": locked.review_rows,
        "blocked_rows_not_published": locked.blocked_rows,
        "excluded_rows_not_published": locked.excluded_rows,
        "created_list": _created,
        "target_list_id": document_list.pk,
        "target_revision_number": approved_revision.revision_number,
        "paper_storage_waivers_created": 0,
    }
    publication = WorkplaceDocumentPublication.objects.create(
        source_revision=locked,
        actor=actor,
        canonical_json=preview["canonical_json"],
        digest=preview["digest"],
        result_summary=result_summary,
    )
    locked.status = WorkplaceDocumentSourceRevision.Status.PUBLISHED
    locked.publication_digest = publication.digest
    locked.published_at = publication.created_at
    locked.published_by = actor
    locked.target_document_list = document_list
    locked.target_revision = approved_revision
    locked.save(
        update_fields=(
            "status",
            "publication_digest",
            "published_at",
            "published_by",
            "target_document_list",
            "target_revision",
            "updated_at",
        )
    )
    return publication


@transaction.atomic
def discard_workplace_document_revision(
    *,
    source_revision: WorkplaceDocumentSourceRevision,
    actor: Employee,
) -> WorkplaceDocumentSourceRevision:
    locked = WorkplaceDocumentSourceRevision.objects.select_for_update().get(
        pk=source_revision.pk
    )
    if locked.organization_id != actor.organization_id:
        raise PermissionDenied("Нельзя изменять редакцию другой организации.")
    if locked.status != WorkplaceDocumentSourceRevision.Status.STAGED:
        raise ValidationError("Убрать из рабочего списка можно только staging-редакцию.")
    locked.status = WorkplaceDocumentSourceRevision.Status.DISCARDED
    locked.discarded_at = timezone.now()
    locked.save(update_fields=("status", "discarded_at", "updated_at"))
    return locked
