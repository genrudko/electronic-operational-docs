from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from apps.organizations.models import Employee

from .models import (
    DataProfile,
    PowerSystemAliasProposal,
    PowerSystemAssetOccurrence,
    PowerSystemAuthorityOccurrence,
    PowerSystemImportIssue,
    PowerSystemPublication,
    PowerSystemSourceRevision,
)
from .services import can_publish_import, require_import_employee

MAX_POWER_SYSTEM_PACKAGE_SIZE = 25 * 1024 * 1024
MAX_POWER_SYSTEM_UNCOMPRESSED_SIZE = 120 * 1024 * 1024
POWER_SYSTEM_PUBLICATION_SCHEMA = "eod.power-system.publication.v1"
CONTROLLED_SHOT_TYPE_CODE = "dc_distribution_board"
CONTROLLED_SHOT_TYPE_NAME = "Шкаф оперативного тока"

ASSET_FILE = "eod_power_system_assets.csv"
AUTHORITY_FILE = "eod_operational_authority_assignments.csv"
ALIAS_FILE = "eod_asset_aliases.csv"
TYPE_FILE = "eod_asset_type_dictionary.csv"
ISSUE_FILE = "eod_import_issues.csv"
ANALYSIS_PREFIX = "eod_equipment_dispatching_analysis_"

REQUIRED_CSV_FILES = (ASSET_FILE, AUTHORITY_FILE, ALIAS_FILE, TYPE_FILE, ISSUE_FILE)

ASSET_HEADERS = (
    "occurrence_id",
    "source_sheet",
    "source_row",
    "source_item_number",
    "record_role",
    "domain",
    "asset_type_proposed",
    "asset_type_ru_proposed",
    "source_category_raw",
    "dispatcher_name_raw",
    "display_name_normalized_proposed",
    "comparison_key",
    "energy_facility_raw",
    "voltage_context_raw",
    "nominal_voltage_kv",
    "voltage_basis",
    "parent_raw",
    "hierarchy_path_raw",
    "management_raw",
    "conduct_raw",
    "note_raw",
    "is_primary_equipment_proposed",
    "is_secondary_device_proposed",
    "is_operational_control_object_candidate",
    "is_independent_dispatching_object_candidate",
    "classification_confidence",
    "hierarchy_confidence",
    "import_disposition",
    "duplicate_group",
    "related_primary_asset_raw",
    "relation_basis",
    "source_fact_notes",
)
AUTHORITY_HEADERS = (
    "occurrence_id",
    "source_sheet",
    "source_row",
    "dispatcher_name_raw",
    "authority_kind",
    "assignment_status",
    "authority_subject_raw",
    "authority_subject_normalized_proposed",
    "normalization_status",
    "source_cell_raw",
    "is_informational",
    "informational_basis",
)
ALIAS_HEADERS = (
    "alias_scope",
    "occurrence_id",
    "parent_context_raw",
    "alias_raw",
    "target_name_raw",
    "alias_kind",
    "normalization_rule",
    "confidence",
    "status",
    "note",
)
TYPE_HEADERS = (
    "type_code_proposed",
    "russian_label_proposed",
    "domain",
    "source_evidence",
    "is_primary_equipment_default",
    "is_secondary_device_default",
    "is_operational_control_object_default",
    "is_independent_dispatching_object_default",
    "status",
    "notes",
)
ISSUE_HEADERS = (
    "issue_code",
    "severity",
    "category",
    "source_sheet",
    "source_rows",
    "evidence",
    "import_risk",
    "recommended_handling",
    "blocks_automatic_import",
    "status",
)

HEADER_MAP = {
    ASSET_FILE: ASSET_HEADERS,
    AUTHORITY_FILE: AUTHORITY_HEADERS,
    ALIAS_FILE: ALIAS_HEADERS,
    TYPE_FILE: TYPE_HEADERS,
    ISSUE_FILE: ISSUE_HEADERS,
}


class PowerSystemPackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PowerSystemPublicationPreview:
    source_revision: PowerSystemSourceRevision
    effective_from: date
    occurrences: tuple[PowerSystemAssetOccurrence, ...]
    canonical_json: str
    digest: str
    summary: dict[str, int]


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_payload(value: object) -> tuple[str, str]:
    canonical = _canonical_json(value)
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_space(value: str) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def _comparison_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", _normalize_space(value)).casefold()
    normalized = normalized.replace("ё", "е")
    normalized = re.sub(r"[–—−]", "-", normalized)
    normalized = re.sub(r"\s*-\s*", "-", normalized)
    normalized = re.sub(r"(?<=\d)\s*,\s*(?=\d)", ",", normalized)
    return normalized


def _slug_hash(prefix: str, value: str, length: int = 16) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}-{digest}"


def _bool_token(value: str) -> bool:
    return _comparison_token(value) in {"true", "1", "да", "yes"}


def _positive_int(value: str, field_name: str) -> int:
    try:
        result = int(_normalize_space(value))
    except (TypeError, ValueError) as exc:
        raise PowerSystemPackageError(f"Поле {field_name} должно быть целым числом.") from exc
    if result < 1:
        raise PowerSystemPackageError(f"Поле {field_name} должно быть положительным числом.")
    return result


def _decimal_or_none(value: str) -> Decimal | None:
    normalized = _normalize_space(value).replace(",", ".")
    if not normalized:
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise PowerSystemPackageError(f"Некорректное напряжение: {value!r}.") from exc


def _read_upload(uploaded_file) -> bytes:
    chunks = uploaded_file.chunks() if hasattr(uploaded_file, "chunks") else (uploaded_file.read(),)
    data = bytearray()
    for chunk in chunks:
        data.extend(chunk)
        if len(data) > MAX_POWER_SYSTEM_PACKAGE_SIZE:
            raise PowerSystemPackageError("Размер ZIP-пакета превышает 25 МБ.")
    if not data:
        raise PowerSystemPackageError("Нельзя загрузить пустой ZIP-пакет.")
    return bytes(data)


def _safe_zip_entries(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    entries: dict[str, zipfile.ZipInfo] = {}
    total_size = 0
    for info in archive.infolist():
        if info.is_dir():
            continue
        path = PurePosixPath(info.filename)
        if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
            raise PowerSystemPackageError("ZIP-пакет содержит недопустимый путь файла.")
        if info.filename in entries:
            raise PowerSystemPackageError(f"ZIP-пакет содержит дублирующий файл {info.filename}.")
        total_size += info.file_size
        if total_size > MAX_POWER_SYSTEM_UNCOMPRESSED_SIZE:
            raise PowerSystemPackageError("Распакованный ZIP-пакет превышает 120 МБ.")
        entries[info.filename] = info
    for required in REQUIRED_CSV_FILES:
        if required not in entries:
            raise PowerSystemPackageError(f"В ZIP-пакете отсутствует обязательный файл {required}.")
    reports = [
        name
        for name in entries
        if name.startswith(ANALYSIS_PREFIX) and name.lower().endswith(".md")
    ]
    if len(reports) != 1:
        raise PowerSystemPackageError(
            "ZIP-пакет должен содержать ровно один аналитический MD-файл оборудования."
        )
    return entries


def _csv_rows(archive: zipfile.ZipFile, filename: str) -> list[dict[str, str]]:
    try:
        text = archive.read(filename).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PowerSystemPackageError(f"Файл {filename} должен быть UTF-8.") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    headers = tuple(reader.fieldnames or ())
    expected = HEADER_MAP[filename]
    if headers != expected:
        missing = [header for header in expected if header not in headers]
        extra = [header for header in headers if header not in expected]
        raise PowerSystemPackageError(
            f"Структура {filename} не соответствует контракту. "
            f"Отсутствуют: {missing or 'нет'}; лишние: {extra or 'нет'}."
        )
    rows: list[dict[str, str]] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise PowerSystemPackageError(
                f"Файл {filename}, строка {row_number}: обнаружены лишние значения."
            )
        rows.append({key: str(value or "") for key, value in row.items()})
    return rows


def _analysis_metadata(text: str) -> tuple[str, str]:
    source_name = ""
    source_sha = ""
    source_match = re.search(r"^\*\*Источник:\*\*\s*`([^`]+)`", text, flags=re.MULTILINE)
    sha_match = re.search(r"^\*\*SHA-256 источника:\*\*\s*`([0-9a-fA-F]{64})`", text, flags=re.MULTILINE)
    if source_match:
        source_name = source_match.group(1).strip()
    if sha_match:
        source_sha = sha_match.group(1).lower()
    return source_name, source_sha


def _site_external_key(facility: str) -> str:
    return f"SITE:{_slug_hash('facility', _comparison_token(facility), 20)}"


def _node_external_key(facility: str, type_code: str, name: str) -> str:
    seed = f"{_comparison_token(facility)}|{type_code}|{_comparison_token(name)}"
    return f"NODE:{_slug_hash('node', seed, 24)}"


def _occurrence_external_key(occurrence_id: str) -> str:
    return f"OCC:{_slug_hash('source', occurrence_id, 24)}"


def _source_facility(row: dict[str, str]) -> str:
    return _normalize_space(
        row.get("energy_facility_raw", "") or row.get("dispatcher_name_raw", "")
    )


def _is_controlled_shot_row(row: dict[str, str]) -> bool:
    return (
        _comparison_token(row.get("dispatcher_name_raw", "")) == "шот"
        and bool(
            re.fullmatch(
                r"ктп-?\s*\d+",
                _comparison_token(row.get("parent_raw", "")),
            )
        )
        and _normalize_space(row.get("record_role", ""))
        == PowerSystemAssetOccurrence.RecordRole.DISPATCHING_OBJECT_OCCURRENCE
    )


def _normalized_type_values(row: dict[str, str]) -> tuple[str, str, str]:
    if _is_controlled_shot_row(row):
        return CONTROLLED_SHOT_TYPE_CODE, CONTROLLED_SHOT_TYPE_NAME, "HIGH"
    return (
        _normalize_space(row.get("asset_type_proposed", "")),
        _normalize_space(row.get("asset_type_ru_proposed", "")),
        _normalize_space(row.get("classification_confidence", "")),
    )


def _normalized_source_row(row: dict[str, str]) -> dict[str, str]:
    normalized = dict(row)
    type_code, type_name, classification = _normalized_type_values(normalized)
    normalized["asset_type_proposed"] = type_code
    normalized["asset_type_ru_proposed"] = type_name
    normalized["classification_confidence"] = classification
    return normalized


def _normalized_voltage_label(value: str) -> str:
    token = _normalize_space(value).replace(".", ",")
    match = re.search(r"(?<!\d)(\d+(?:,\d+)?)\s*кв\b", token, flags=re.IGNORECASE)
    if not match:
        return ""
    number = match.group(1)
    try:
        decimal = Decimal(number.replace(",", "."))
    except InvalidOperation:
        return ""
    if decimal == decimal.to_integral_value():
        formatted = str(int(decimal))
    else:
        formatted = format(decimal.normalize(), "f").replace(".", ",")
    return f"{formatted} кВ"


def _row_voltage_label(row: dict[str, str]) -> str:
    for value in (
        row.get("voltage_context_raw", ""),
        row.get("dispatcher_name_raw", ""),
        row.get("parent_raw", ""),
        row.get("hierarchy_path_raw", ""),
    ):
        label = _normalized_voltage_label(value)
        if label:
            return label
    nominal = _normalize_space(row.get("nominal_voltage_kv", ""))
    if nominal:
        return _normalized_voltage_label(f"{nominal} кВ")
    return ""


def _hierarchy_keys(asset_rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for row in asset_rows:
        if row["record_role"] != PowerSystemAssetOccurrence.RecordRole.HIERARCHY_NODE:
            continue
        facility = _source_facility(row)
        name = _normalize_space(row["dispatcher_name_raw"])
        type_code = _normalize_space(row["asset_type_proposed"])
        if not facility or not name:
            continue
        external = (
            _site_external_key(facility)
            if type_code == "energy_facility"
            else _node_external_key(facility, type_code, name)
        )
        key = (_comparison_token(facility), _comparison_token(name))
        existing = result.get(key)
        if existing and existing != external:
            raise PowerSystemPackageError(
                f"Иерархия содержит неоднозначный узел {facility} / {name}."
            )
        result[key] = external
    return result


def _parent_external_key(
    row: dict[str, str],
    hierarchy: dict[tuple[str, str], str],
) -> str:
    facility = _source_facility(row)
    type_code = _normalize_space(row["asset_type_proposed"])
    site_key = _site_external_key(facility) if facility else ""
    if type_code == "energy_facility":
        return ""
    if not facility:
        return ""

    voltage_label = _row_voltage_label(row)
    voltage_key = hierarchy.get(
        (_comparison_token(facility), _comparison_token(voltage_label)),
        "",
    )
    if row["record_role"] == PowerSystemAssetOccurrence.RecordRole.HIERARCHY_NODE:
        if type_code == "voltage_level":
            return site_key
        if type_code == "control_building":
            explicit_parent = _normalize_space(row.get("parent_raw", ""))
            explicit_key = hierarchy.get(
                (_comparison_token(facility), _comparison_token(explicit_parent)),
                "",
            )
            return explicit_key or site_key
        if type_code == "unit_substation":
            return voltage_key or hierarchy.get(
                (_comparison_token(facility), _comparison_token("35 кВ")),
                site_key,
            )
        if type_code == "asset_group":
            return site_key
        if type_code == "wind_turbine":
            return hierarchy.get(
                (_comparison_token(facility), _comparison_token("ВЭУ")),
                site_key,
            )
        return voltage_key or site_key

    if type_code in {"overhead_line", "cable_line"} and voltage_key:
        return voltage_key

    candidates = [_normalize_space(row["parent_raw"])]
    candidates.extend(
        reversed(
            [
                _normalize_space(part)
                for part in (row["hierarchy_path_raw"] or "").split("/")
                if _normalize_space(part)
            ]
        )
    )
    for candidate in candidates:
        key = (_comparison_token(facility), _comparison_token(candidate))
        if candidate and key in hierarchy:
            return hierarchy[key]

    return voltage_key or site_key


def _logical_key(row: dict[str, str], parent_external_key: str) -> str:
    disposition = _normalize_space(row["import_disposition"])
    duplicate_group = _normalize_space(row["duplicate_group"])
    if duplicate_group and disposition == "MERGE_CANDIDATE":
        return f"MERGE:{_slug_hash('group', duplicate_group, 24)}"
    seed = "|".join(
        (
            parent_external_key,
            _normalize_space(row["asset_type_proposed"]),
            _comparison_token(row["comparison_key"] or row["dispatcher_name_raw"]),
        )
    )
    return f"LOGICAL:{_slug_hash('asset', seed, 24)}"


def _initial_review_status(row: dict[str, str]) -> str:
    disposition = _normalize_space(row["import_disposition"]).upper()
    classification = _normalize_space(row["classification_confidence"]).upper()
    hierarchy = _normalize_space(row["hierarchy_confidence"]).upper()
    if not _normalize_space(row["dispatcher_name_raw"]):
        return PowerSystemAssetOccurrence.ReviewStatus.BLOCKED
    if disposition in {"REVIEW_CONFLICT", "REVIEW_DUPLICATE"}:
        return PowerSystemAssetOccurrence.ReviewStatus.BLOCKED
    if disposition == "MERGE_CANDIDATE":
        return PowerSystemAssetOccurrence.ReviewStatus.REVIEW_REQUIRED
    if classification == "LOW" or hierarchy == "LOW":
        return PowerSystemAssetOccurrence.ReviewStatus.REVIEW_REQUIRED
    return PowerSystemAssetOccurrence.ReviewStatus.READY


def _alias_review_status(row: dict[str, str], occurrence_exists: bool) -> str:
    safe_kinds = {
        "SEARCH_NORMALIZED_VARIANT",
        "WHITESPACE_VARIANT",
        "SPACING_VARIANT",
    }
    if (
        occurrence_exists
        and row["alias_scope"] == "ASSET"
        and row["confidence"] == "HIGH"
        and row["status"] == "PROPOSED"
        and row["alias_kind"] in safe_kinds
    ):
        return PowerSystemAliasProposal.ReviewStatus.AUTO_SAFE
    if row["status"] in {"PROPOSED", "PROPOSED_REVIEW_REQUIRED"}:
        return PowerSystemAliasProposal.ReviewStatus.REVIEW_REQUIRED
    return PowerSystemAliasProposal.ReviewStatus.BLOCKED


def _conduct_mode(value: str, authority_kind: str) -> str:
    if authority_kind == PowerSystemAuthorityOccurrence.AuthorityKind.OPERATIONAL_MANAGEMENT:
        return PowerSystemAuthorityOccurrence.ConductMode.UNKNOWN
    token = _normalize_space(value).upper()
    if token == "TRUE":
        return PowerSystemAuthorityOccurrence.ConductMode.INFORMATIONAL
    if token == "FALSE":
        return PowerSystemAuthorityOccurrence.ConductMode.OPERATIONAL
    return PowerSystemAuthorityOccurrence.ConductMode.UNKNOWN


def _revision_counts(revision: PowerSystemSourceRevision) -> dict[str, int]:
    statuses = defaultdict(int)
    for status in revision.asset_occurrences.values_list("review_status", flat=True):
        statuses[status] += 1
    counts = {
        "ready_count": statuses[PowerSystemAssetOccurrence.ReviewStatus.READY],
        "review_count": statuses[PowerSystemAssetOccurrence.ReviewStatus.REVIEW_REQUIRED],
        "blocked_count": statuses[PowerSystemAssetOccurrence.ReviewStatus.BLOCKED],
        "excluded_count": statuses[PowerSystemAssetOccurrence.ReviewStatus.EXCLUDED],
        "published_count": statuses[PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED],
    }
    PowerSystemSourceRevision.objects.filter(pk=revision.pk).update(**counts)
    for field_name, value in counts.items():
        setattr(revision, field_name, value)
    return counts


def _occurrence_source_row(occurrence: PowerSystemAssetOccurrence) -> dict[str, str]:
    return {
        "occurrence_id": occurrence.occurrence_id,
        "record_role": occurrence.record_role,
        "asset_type_proposed": occurrence.asset_type_code,
        "asset_type_ru_proposed": occurrence.asset_type_name,
        "classification_confidence": occurrence.classification_confidence,
        "hierarchy_confidence": occurrence.hierarchy_confidence,
        "dispatcher_name_raw": occurrence.dispatcher_name_raw,
        "comparison_key": occurrence.comparison_key,
        "energy_facility_raw": occurrence.energy_facility_raw,
        "voltage_context_raw": occurrence.voltage_context_raw,
        "nominal_voltage_kv": ""
        if occurrence.nominal_voltage_kv is None
        else str(occurrence.nominal_voltage_kv),
        "parent_raw": occurrence.parent_raw,
        "hierarchy_path_raw": occurrence.hierarchy_path_raw,
        "import_disposition": occurrence.import_disposition,
        "duplicate_group": occurrence.duplicate_group,
    }


@transaction.atomic
def reanalyze_power_system_revision(
    revision: PowerSystemSourceRevision,
) -> dict[str, int]:
    locked = PowerSystemSourceRevision.objects.select_for_update().get(pk=revision.pk)
    occurrences = list(
        locked.asset_occurrences.select_for_update().order_by(
            "source_sheet",
            "source_row",
            "occurrence_id",
        )
    )
    normalized_rows = [
        _normalized_source_row(_occurrence_source_row(occurrence))
        for occurrence in occurrences
    ]
    hierarchy = _hierarchy_keys(normalized_rows)
    changed: list[PowerSystemAssetOccurrence] = []
    counters = defaultdict(int)
    for occurrence, row in zip(occurrences, normalized_rows, strict=True):
        if occurrence.review_status == PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED:
            counters["published_unchanged"] += 1
            continue

        old_values = (
            occurrence.parent_external_key,
            occurrence.logical_key,
            occurrence.asset_type_code,
            occurrence.asset_type_name,
            occurrence.classification_confidence,
            occurrence.initial_review_status,
            occurrence.review_status,
            occurrence.source_flags,
        )
        parent_key = _parent_external_key(row, hierarchy)
        logical_key = _logical_key(row, parent_key)
        type_code, type_name, classification = _normalized_type_values(row)
        occurrence.parent_external_key = parent_key
        occurrence.logical_key = logical_key
        if _is_controlled_shot_row(row):
            occurrence.source_flags = {
                **occurrence.source_flags,
                "source_asset_type_proposed": occurrence.source_flags.get(
                    "source_asset_type_proposed", old_values[2]
                ),
                "source_asset_type_ru_proposed": occurrence.source_flags.get(
                    "source_asset_type_ru_proposed", old_values[3]
                ),
                "source_classification_confidence": occurrence.source_flags.get(
                    "source_classification_confidence", old_values[4]
                ),
                "controlled_type_normalization": "SHOT_EXACT_UNDER_KTP",
            }
        occurrence.asset_type_code = type_code
        occurrence.asset_type_name = type_name
        occurrence.classification_confidence = classification

        normalized_initial_status = _initial_review_status(row)
        occurrence.initial_review_status = normalized_initial_status
        if occurrence.review_decision == PowerSystemAssetOccurrence.ReviewDecision.NONE:
            occurrence.review_status = normalized_initial_status

        if old_values[0] != parent_key:
            counters["parent_changed"] += 1
        if old_values[1] != logical_key:
            counters["logical_key_changed"] += 1
        if old_values[2] != type_code:
            counters["type_changed"] += 1
        if old_values[6] != occurrence.review_status:
            counters["review_status_changed"] += 1

        if occurrence.asset_type_code == "energy_facility" and not parent_key:
            counters["root_without_parent"] += 1
        elif parent_key:
            counters["resolved_parent"] += 1
        else:
            counters["orphan_parent"] += 1

        new_values = (
            occurrence.parent_external_key,
            occurrence.logical_key,
            occurrence.asset_type_code,
            occurrence.asset_type_name,
            occurrence.classification_confidence,
            occurrence.initial_review_status,
            occurrence.review_status,
            occurrence.source_flags,
        )
        if old_values != new_values:
            changed.append(occurrence)

    if changed:
        PowerSystemAssetOccurrence.objects.bulk_update(
            changed,
            (
                "parent_external_key",
                "logical_key",
                "asset_type_code",
                "asset_type_name",
                "classification_confidence",
                "initial_review_status",
                "review_status",
                "source_flags",
            ),
        )
    counters["updated_rows"] = len(changed)
    _revision_counts(locked)
    return dict(counters)


def reanalyze_staged_power_system_revisions() -> dict[str, int]:
    totals = defaultdict(int)
    queryset = PowerSystemSourceRevision.objects.exclude(
        status=PowerSystemSourceRevision.Status.DISCARDED,
    ).order_by("pk")
    for revision in queryset:
        result = reanalyze_power_system_revision(revision)
        totals["revisions"] += 1
        for key, value in result.items():
            totals[key] += value
    return dict(totals)


@transaction.atomic
def stage_power_system_package(
    *,
    uploaded_file,
    employee: Employee,
    data_profile: DataProfile | None = None,
    source_reference: str = "",
    source_approval_status: str = PowerSystemSourceRevision.SourceApprovalStatus.UNKNOWN,
    effective_from: date | None = None,
) -> tuple[PowerSystemSourceRevision, bool]:
    if not employee.is_active:
        raise PermissionDenied("Недействующий сотрудник не может загружать источники.")
    filename = _normalize_space(getattr(uploaded_file, "name", ""))
    if not filename.lower().endswith(".zip"):
        raise PowerSystemPackageError("Пакет объектов диспетчеризации должен быть ZIP-файлом.")
    data = _read_upload(uploaded_file)
    package_sha = _sha256_bytes(data)
    existing = PowerSystemSourceRevision.objects.filter(
        organization=employee.organization,
        file_sha256=package_sha,
    ).first()
    if existing is not None:
        return existing, False

    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise PowerSystemPackageError("Файл не является корректным ZIP-пакетом.") from exc
    with archive:
        entries = _safe_zip_entries(archive)
        analysis_name = next(
            name
            for name in entries
            if name.startswith(ANALYSIS_PREFIX) and name.lower().endswith(".md")
        )
        try:
            analysis_text = archive.read(analysis_name).decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise PowerSystemPackageError("Аналитический отчёт должен быть UTF-8.") from exc
        source_document_name, source_document_sha = _analysis_metadata(analysis_text)
        asset_rows = _csv_rows(archive, ASSET_FILE)
        authority_rows = _csv_rows(archive, AUTHORITY_FILE)
        alias_rows = _csv_rows(archive, ALIAS_FILE)
        type_rows = _csv_rows(archive, TYPE_FILE)
        issue_rows = _csv_rows(archive, ISSUE_FILE)
        file_manifest = {
            name: {
                "size": entries[name].file_size,
                "sha256": _sha256_bytes(archive.read(name)),
            }
            for name in entries
        }

    occurrence_ids = [row["occurrence_id"] for row in asset_rows]
    duplicates = sorted(
        occurrence_id
        for occurrence_id in set(occurrence_ids)
        if occurrence_ids.count(occurrence_id) > 1
    )
    if duplicates:
        raise PowerSystemPackageError(
            "В assets-файле повторяются occurrence_id: " + ", ".join(duplicates[:10])
        )
    hierarchy = _hierarchy_keys(asset_rows)
    referenced = {row["occurrence_id"] for row in authority_rows if row["occurrence_id"]}
    referenced.update(row["occurrence_id"] for row in alias_rows if row["occurrence_id"])
    unknown_references = sorted(referenced - set(occurrence_ids))
    if unknown_references:
        raise PowerSystemPackageError(
            "Полномочия или алиасы ссылаются на отсутствующие occurrence_id: "
            + ", ".join(unknown_references[:10])
        )

    profile = data_profile or DataProfile.default_for_organization(employee.organization)
    if profile.organization_id != employee.organization_id or not profile.is_active:
        raise ValidationError("Выбран недоступный профиль данных.")
    reference = _normalize_space(source_reference) or source_document_name or filename
    previous = (
        PowerSystemSourceRevision.objects.filter(
            organization=employee.organization,
            source_reference=reference,
        )
        .order_by("-created_at", "-id")
        .first()
    )
    previous_fingerprints = (
        {
            occurrence_id: fingerprint
            for occurrence_id, fingerprint in previous.asset_occurrences.values_list(
                "occurrence_id",
                "row_fingerprint",
            )
        }
        if previous is not None
        else {}
    )

    revision = PowerSystemSourceRevision.objects.create(
        organization=employee.organization,
        data_profile=profile,
        uploaded_by=employee,
        source_reference=reference,
        source_approval_status=source_approval_status,
        effective_from=effective_from,
        original_filename=filename,
        file_size=len(data),
        file_sha256=package_sha,
        source_document_name=source_document_name,
        source_document_sha256=source_document_sha,
        analysis_filename=analysis_name,
        supersedes=previous,
        manifest={
            "schema": "eod.power-system.package.v1",
            "files": file_manifest,
            "analysis_excerpt_sha256": _sha256_bytes(analysis_text.encode("utf-8")),
        },
        type_dictionary=type_rows,
    )

    occurrences: list[PowerSystemAssetOccurrence] = []
    current_fingerprints: dict[str, str] = {}
    for source_row_data in asset_rows:
        row = _normalized_source_row(source_row_data)
        source_row = _positive_int(row["source_row"], "source_row")
        parent_key = _parent_external_key(row, hierarchy)
        type_code, type_name, classification_confidence = _normalized_type_values(row)
        facility = _source_facility(row)
        external_key = (
            _site_external_key(facility)
            if type_code == "energy_facility"
            else (
                _node_external_key(facility, type_code, row["dispatcher_name_raw"])
                if row["record_role"] == PowerSystemAssetOccurrence.RecordRole.HIERARCHY_NODE
                else _occurrence_external_key(row["occurrence_id"])
            )
        )
        fingerprint = _sha256_bytes(_canonical_json(source_row_data).encode("utf-8"))
        current_fingerprints[row["occurrence_id"]] = fingerprint
        previous_fingerprint = previous_fingerprints.get(row["occurrence_id"])
        if previous_fingerprint is None:
            diff_state = PowerSystemAssetOccurrence.DiffState.ADDED
        elif previous_fingerprint == fingerprint:
            diff_state = PowerSystemAssetOccurrence.DiffState.UNCHANGED
        else:
            diff_state = PowerSystemAssetOccurrence.DiffState.CHANGED
        initial_status = _initial_review_status(row)
        occurrences.append(
            PowerSystemAssetOccurrence(
                source_revision=revision,
                occurrence_id=row["occurrence_id"],
                source_sheet=row["source_sheet"],
                source_row=source_row,
                source_item_number=row["source_item_number"],
                record_role=row["record_role"],
                domain=row["domain"],
                asset_type_code=type_code,
                asset_type_name=type_name,
                source_category_raw=row["source_category_raw"],
                dispatcher_name_raw=row["dispatcher_name_raw"],
                display_name_normalized=row["display_name_normalized_proposed"],
                comparison_key=row["comparison_key"],
                energy_facility_raw=facility,
                voltage_context_raw=row["voltage_context_raw"],
                nominal_voltage_kv=_decimal_or_none(row["nominal_voltage_kv"]),
                voltage_basis=row["voltage_basis"],
                parent_raw=row["parent_raw"],
                hierarchy_path_raw=row["hierarchy_path_raw"],
                external_key=external_key,
                parent_external_key=parent_key,
                logical_key=_logical_key(row, parent_key),
                management_raw=row["management_raw"],
                conduct_raw=row["conduct_raw"],
                note_raw=row["note_raw"],
                source_flags={
                    "is_primary_equipment_proposed": row["is_primary_equipment_proposed"],
                    "is_secondary_device_proposed": row["is_secondary_device_proposed"],
                    "is_operational_control_object_candidate": row[
                        "is_operational_control_object_candidate"
                    ],
                    "is_independent_dispatching_object_candidate": row[
                        "is_independent_dispatching_object_candidate"
                    ],
                    "source_asset_type_proposed": source_row_data["asset_type_proposed"],
                    "source_asset_type_ru_proposed": source_row_data[
                        "asset_type_ru_proposed"
                    ],
                    "source_classification_confidence": source_row_data[
                        "classification_confidence"
                    ],
                    "controlled_type_normalization": (
                        "SHOT_EXACT_UNDER_KTP"
                        if _is_controlled_shot_row(row)
                        else ""
                    ),
                },
                classification_confidence=classification_confidence,
                hierarchy_confidence=row["hierarchy_confidence"],
                import_disposition=row["import_disposition"],
                duplicate_group=row["duplicate_group"],
                related_primary_asset_raw=row["related_primary_asset_raw"],
                relation_basis=row["relation_basis"],
                source_fact_notes=row["source_fact_notes"],
                row_fingerprint=fingerprint,
                diff_state=diff_state,
                initial_review_status=initial_status,
                review_status=initial_status,
            )
        )
    PowerSystemAssetOccurrence.objects.bulk_create(occurrences, batch_size=500)
    occurrence_by_id = {
        occurrence.occurrence_id: occurrence
        for occurrence in revision.asset_occurrences.all()
    }

    sequence_counter: dict[tuple[str, str], int] = defaultdict(int)
    authorities: list[PowerSystemAuthorityOccurrence] = []
    for row in authority_rows:
        if row["occurrence_id"] not in occurrence_by_id:
            raise PowerSystemPackageError(
                f"Назначение ссылается на отсутствующую строку: {row['occurrence_id']}."
            )
        if row["authority_kind"] not in PowerSystemAuthorityOccurrence.AuthorityKind.values:
            raise PowerSystemPackageError(
                f"Неизвестный вид полномочия: {row['authority_kind']}."
            )
        if row["assignment_status"] not in PowerSystemAuthorityOccurrence.AssignmentStatus.values:
            raise PowerSystemPackageError(
                f"Неизвестный статус назначения: {row['assignment_status']}."
            )
        occurrence = occurrence_by_id[row["occurrence_id"]]
        key = (row["occurrence_id"], row["authority_kind"])
        sequence_counter[key] += 1
        authorities.append(
            PowerSystemAuthorityOccurrence(
                source_revision=revision,
                asset_occurrence=occurrence,
                sequence=sequence_counter[key],
                source_sheet=row["source_sheet"],
                source_row=_positive_int(row["source_row"], "authority source_row"),
                dispatcher_name_raw=row["dispatcher_name_raw"],
                authority_kind=row["authority_kind"],
                assignment_status=row["assignment_status"],
                authority_subject_raw=row["authority_subject_raw"],
                authority_subject_normalized=row[
                    "authority_subject_normalized_proposed"
                ],
                normalization_status=row["normalization_status"],
                source_cell_raw=row["source_cell_raw"],
                conduct_mode=_conduct_mode(row["is_informational"], row["authority_kind"]),
                informational_basis=row["informational_basis"],
                row_fingerprint=_sha256_bytes(_canonical_json(row).encode("utf-8")),
            )
        )
    PowerSystemAuthorityOccurrence.objects.bulk_create(authorities, batch_size=500)

    proposals: list[PowerSystemAliasProposal] = []
    for row in alias_rows:
        occurrence = occurrence_by_id.get(row["occurrence_id"])
        proposals.append(
            PowerSystemAliasProposal(
                source_revision=revision,
                asset_occurrence=occurrence,
                alias_scope=row["alias_scope"],
                occurrence_id_raw=row["occurrence_id"],
                parent_context_raw=row["parent_context_raw"],
                alias_raw=row["alias_raw"],
                target_name_raw=row["target_name_raw"],
                alias_kind=row["alias_kind"],
                normalization_rule=row["normalization_rule"],
                confidence=row["confidence"],
                proposal_status=row["status"],
                note=row["note"],
                row_fingerprint=_sha256_bytes(_canonical_json(row).encode("utf-8")),
                review_status=_alias_review_status(row, occurrence is not None),
            )
        )
    PowerSystemAliasProposal.objects.bulk_create(proposals, batch_size=500)

    issues: list[PowerSystemImportIssue] = []
    for row in issue_rows:
        severity = row["severity"]
        if severity not in PowerSystemImportIssue.Severity.values:
            raise PowerSystemPackageError(f"Неизвестная важность проблемы: {severity}.")
        issues.append(
            PowerSystemImportIssue(
                source_revision=revision,
                issue_code=row["issue_code"],
                severity=severity,
                category=row["category"],
                source_sheet=row["source_sheet"],
                source_rows=row["source_rows"],
                evidence=row["evidence"],
                import_risk=row["import_risk"],
                recommended_handling=row["recommended_handling"],
                blocks_automatic_import=_bool_token(row["blocks_automatic_import"]),
                status=(
                    row["status"]
                    if row["status"] in PowerSystemImportIssue.Status.values
                    else PowerSystemImportIssue.Status.OPEN
                ),
                row_fingerprint=_sha256_bytes(_canonical_json(row).encode("utf-8")),
            )
        )
    PowerSystemImportIssue.objects.bulk_create(issues, batch_size=200)

    missing_count = len(set(previous_fingerprints) - set(current_fingerprints))
    diff_counts = {
        "added": sum(
            occurrence.diff_state == PowerSystemAssetOccurrence.DiffState.ADDED
            for occurrence in occurrences
        ),
        "unchanged": sum(
            occurrence.diff_state == PowerSystemAssetOccurrence.DiffState.UNCHANGED
            for occurrence in occurrences
        ),
        "changed": sum(
            occurrence.diff_state == PowerSystemAssetOccurrence.DiffState.CHANGED
            for occurrence in occurrences
        ),
        "missing_from_previous": missing_count,
    }
    revision.total_occurrences = len(occurrences)
    revision.hierarchy_nodes = sum(
        occurrence.record_role == PowerSystemAssetOccurrence.RecordRole.HIERARCHY_NODE
        for occurrence in occurrences
    )
    revision.authority_rows = len(authorities)
    revision.alias_rows = len(proposals)
    revision.issue_rows = len(issues)
    revision.diff_counts = diff_counts
    revision.save(
        update_fields=(
            "total_occurrences",
            "hierarchy_nodes",
            "authority_rows",
            "alias_rows",
            "issue_rows",
            "diff_counts",
            "updated_at",
        )
    )
    _revision_counts(revision)
    return revision, True


@transaction.atomic
def decide_power_system_occurrence(
    *,
    occurrence: PowerSystemAssetOccurrence,
    employee: Employee,
    action: str,
    note: str = "",
    merge_target_occurrence_id: str = "",
) -> PowerSystemAssetOccurrence:
    locked = (
        PowerSystemAssetOccurrence.objects.select_for_update()
        .select_related("source_revision", "merge_target")
        .get(pk=occurrence.pk)
    )
    revision = locked.source_revision
    if revision.organization_id != employee.organization_id:
        raise PermissionDenied("Строка относится к другой организации.")
    if revision.status == PowerSystemSourceRevision.Status.DISCARDED:
        raise ValidationError("Убранную редакцию нельзя проверять.")
    if locked.review_status == PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED:
        raise ValidationError("Опубликованная строка неизменяема.")

    normalized_action = action.strip().upper()
    if normalized_action == "RESET":
        locked.review_decision = PowerSystemAssetOccurrence.ReviewDecision.NONE
        locked.review_status = locked.initial_review_status
        locked.merge_target = None
        locked.review_note = ""
        locked.reviewed_by = None
        locked.reviewed_at = None
    elif normalized_action == "EXCLUDE":
        locked.review_decision = PowerSystemAssetOccurrence.ReviewDecision.EXCLUDE
        locked.review_status = PowerSystemAssetOccurrence.ReviewStatus.EXCLUDED
        locked.merge_target = None
        locked.review_note = note.strip()
        locked.reviewed_by = employee
        locked.reviewed_at = timezone.now()
    elif normalized_action == "ACCEPT_AS_NEW":
        locked.review_decision = PowerSystemAssetOccurrence.ReviewDecision.ACCEPT_AS_NEW
        locked.review_status = PowerSystemAssetOccurrence.ReviewStatus.READY
        locked.merge_target = None
        locked.review_note = note.strip()
        locked.reviewed_by = employee
        locked.reviewed_at = timezone.now()
    elif normalized_action == "MERGE_WITH":
        target = get_merge_target(
            revision=revision,
            occurrence_id=merge_target_occurrence_id,
            excluded_pk=locked.pk,
        )
        locked.review_decision = PowerSystemAssetOccurrence.ReviewDecision.MERGE_WITH
        locked.review_status = PowerSystemAssetOccurrence.ReviewStatus.READY
        locked.merge_target = target
        locked.review_note = note.strip()
        locked.reviewed_by = employee
        locked.reviewed_at = timezone.now()
    else:
        raise ValidationError("Неизвестное решение по строке.")
    locked.save(
        update_fields=(
            "review_decision",
            "review_status",
            "merge_target",
            "review_note",
            "reviewed_by",
            "reviewed_at",
        )
    )
    _revision_counts(revision)
    return locked


@transaction.atomic
def decide_power_system_duplicate_group(
    *,
    revision: PowerSystemSourceRevision,
    employee: Employee,
    duplicate_group: str,
    action: str,
    primary_occurrence_id: str = "",
    note: str = "",
) -> tuple[PowerSystemAssetOccurrence, ...]:
    locked_revision = PowerSystemSourceRevision.objects.select_for_update().get(
        pk=revision.pk
    )
    if locked_revision.organization_id != employee.organization_id:
        raise PermissionDenied("Редакция относится к другой организации.")
    if locked_revision.status == PowerSystemSourceRevision.Status.DISCARDED:
        raise ValidationError("Убранную редакцию нельзя проверять.")

    group_token = _normalize_space(duplicate_group)
    rows = list(
        locked_revision.asset_occurrences.select_for_update()
        .filter(duplicate_group=group_token)
        .order_by("source_sheet", "source_row", "occurrence_id")
    )
    if len(rows) < 2:
        raise ValidationError("Группа содержит меньше двух исходных строк.")
    if any(
        row.review_status == PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED
        for row in rows
    ):
        raise ValidationError("Опубликованную группу нельзя изменить.")

    normalized_action = action.strip().upper()
    now = timezone.now()
    primary = next(
        (
            row
            for row in rows
            if row.occurrence_id == _normalize_space(primary_occurrence_id)
        ),
        None,
    )
    if normalized_action in {"MERGE", "KEEP_PRIMARY"} and primary is None:
        raise ValidationError("Выберите основную строку группы.")

    if normalized_action == "RESET":
        for row in rows:
            row.review_decision = PowerSystemAssetOccurrence.ReviewDecision.NONE
            row.review_status = row.initial_review_status
            row.merge_target = None
            row.review_note = ""
            row.reviewed_by = None
            row.reviewed_at = None
    elif normalized_action == "KEEP_SEPARATE":
        for row in rows:
            row.review_decision = PowerSystemAssetOccurrence.ReviewDecision.ACCEPT_AS_NEW
            row.review_status = PowerSystemAssetOccurrence.ReviewStatus.READY
            row.merge_target = None
            row.review_note = note.strip()
            row.reviewed_by = employee
            row.reviewed_at = now
    elif normalized_action == "MERGE":
        assert primary is not None
        primary.review_decision = PowerSystemAssetOccurrence.ReviewDecision.ACCEPT_AS_NEW
        primary.review_status = PowerSystemAssetOccurrence.ReviewStatus.READY
        primary.merge_target = None
        primary.review_note = note.strip()
        primary.reviewed_by = employee
        primary.reviewed_at = now
        for row in rows:
            if row.pk == primary.pk:
                continue
            row.review_decision = PowerSystemAssetOccurrence.ReviewDecision.MERGE_WITH
            row.review_status = PowerSystemAssetOccurrence.ReviewStatus.READY
            row.merge_target = primary
            row.review_note = note.strip()
            row.reviewed_by = employee
            row.reviewed_at = now
    elif normalized_action == "KEEP_PRIMARY":
        assert primary is not None
        primary.review_decision = PowerSystemAssetOccurrence.ReviewDecision.ACCEPT_AS_NEW
        primary.review_status = PowerSystemAssetOccurrence.ReviewStatus.READY
        primary.merge_target = None
        primary.review_note = note.strip()
        primary.reviewed_by = employee
        primary.reviewed_at = now
        for row in rows:
            if row.pk == primary.pk:
                continue
            row.review_decision = PowerSystemAssetOccurrence.ReviewDecision.EXCLUDE
            row.review_status = PowerSystemAssetOccurrence.ReviewStatus.EXCLUDED
            row.merge_target = None
            row.review_note = note.strip()
            row.reviewed_by = employee
            row.reviewed_at = now
    else:
        raise ValidationError("Неизвестное решение по группе.")

    PowerSystemAssetOccurrence.objects.bulk_update(
        rows,
        (
            "review_decision",
            "review_status",
            "merge_target",
            "review_note",
            "reviewed_by",
            "reviewed_at",
        ),
    )
    _revision_counts(locked_revision)
    return tuple(rows)


def get_merge_target(
    *,
    revision: PowerSystemSourceRevision,
    occurrence_id: str,
    excluded_pk: int | None = None,
) -> PowerSystemAssetOccurrence:
    token = _normalize_space(occurrence_id)
    if not token:
        raise ValidationError("Укажите occurrence_id целевой строки.")
    queryset = revision.asset_occurrences.filter(occurrence_id=token)
    if excluded_pk is not None:
        queryset = queryset.exclude(pk=excluded_pk)
    target = queryset.select_related("merge_target").first()
    if target is None:
        raise ValidationError("Целевая строка объединения не найдена в этой редакции.")
    if target.review_status not in {
        PowerSystemAssetOccurrence.ReviewStatus.READY,
        PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED,
    }:
        raise ValidationError("Сначала примите или опубликуйте целевую строку объединения.")
    return target


@transaction.atomic
def discard_power_system_revision(
    *,
    revision: PowerSystemSourceRevision,
    employee: Employee,
) -> PowerSystemSourceRevision:
    locked = PowerSystemSourceRevision.objects.select_for_update().get(pk=revision.pk)
    if locked.organization_id != employee.organization_id:
        raise PermissionDenied("Редакция относится к другой организации.")
    if locked.published_count:
        raise ValidationError("Редакцию с опубликованными строками нельзя убрать из списка.")
    if locked.status == PowerSystemSourceRevision.Status.DISCARDED:
        return locked
    locked.status = PowerSystemSourceRevision.Status.DISCARDED
    locked.discarded_at = timezone.now()
    locked.save(update_fields=("status", "discarded_at", "updated_at"))
    return locked


def build_power_system_publication_preview(
    *,
    revision: PowerSystemSourceRevision,
    effective_from: date,
) -> PowerSystemPublicationPreview:
    if revision.status == PowerSystemSourceRevision.Status.DISCARDED:
        raise ValidationError("Убранную редакцию нельзя публиковать.")
    occurrences = tuple(
        revision.asset_occurrences.filter(
            review_status=PowerSystemAssetOccurrence.ReviewStatus.READY,
            )
        .select_related("merge_target")
        .order_by("record_role", "source_sheet", "source_row", "occurrence_id")
    )
    if not occurrences:
        raise ValidationError("Нет готовых неопубликованных строк.")
    unexpected_roots = [
        occurrence.occurrence_id
        for occurrence in occurrences
        if occurrence.asset_type_code != "energy_facility"
        and not occurrence.parent_external_key
    ]
    if unexpected_roots:
        raise ValidationError(
            "Нельзя публиковать строки без определённого родителя: "
            + ", ".join(unexpected_roots[:10])
        )
    selected_ids = {occurrence.pk for occurrence in occurrences}
    unresolved_parent_keys = {
        occurrence.parent_external_key
        for occurrence in occurrences
        if occurrence.parent_external_key.startswith("NODE:")
        and not revision.asset_occurrences.filter(
            external_key=occurrence.parent_external_key,
        ).filter(
            Q(pk__in=selected_ids)
            | Q(review_status=PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED)
        ).exists()
    }
    if unresolved_parent_keys:
        raise ValidationError(
            "Нельзя публиковать строки без готовых родительских узлов: "
            + ", ".join(sorted(unresolved_parent_keys)[:5])
        )
    payload = {
        "schema": POWER_SYSTEM_PUBLICATION_SCHEMA,
        "source_revision_public_id": str(revision.public_id),
        "organization_id": revision.organization_id,
        "data_profile": revision.data_profile.code,
        "package_sha256": revision.file_sha256,
        "source_document_sha256": revision.source_document_sha256,
        "effective_from": effective_from.isoformat(),
        "occurrences": [
            {
                "id": occurrence.pk,
                "occurrence_id": occurrence.occurrence_id,
                "external_key": occurrence.external_key,
                "parent_external_key": occurrence.parent_external_key,
                "logical_key": occurrence.effective_logical_key,
                "type": occurrence.asset_type_code,
                "dispatcher_name_raw": occurrence.dispatcher_name_raw,
                "row_fingerprint": occurrence.row_fingerprint,
                "review_decision": occurrence.review_decision,
                "merge_target_id": occurrence.merge_target_id,
            }
            for occurrence in occurrences
        ],
    }
    canonical, digest = _sha256_payload(payload)
    summary = {
        "selected": len(occurrences),
        "hierarchy": sum(
            occurrence.record_role == PowerSystemAssetOccurrence.RecordRole.HIERARCHY_NODE
            for occurrence in occurrences
        ),
        "objects": sum(
            occurrence.record_role
            == PowerSystemAssetOccurrence.RecordRole.DISPATCHING_OBJECT_OCCURRENCE
            for occurrence in occurrences
        ),
        "root_sites": sum(
            occurrence.asset_type_code == "energy_facility"
            and not occurrence.parent_external_key
            for occurrence in occurrences
        ),
        "orphan_rows": sum(
            occurrence.asset_type_code != "energy_facility"
            and not occurrence.parent_external_key
            for occurrence in occurrences
        ),
        "shot_rows": sum(
            occurrence.asset_type_code == CONTROLLED_SHOT_TYPE_CODE
            for occurrence in occurrences
        ),
        "quarantined": revision.review_count + revision.blocked_count,
        "duplicate_groups_pending": revision.asset_occurrences.filter(
            duplicate_group__gt="",
            review_status__in=(
                PowerSystemAssetOccurrence.ReviewStatus.REVIEW_REQUIRED,
                PowerSystemAssetOccurrence.ReviewStatus.BLOCKED,
            ),
        )
        .values("duplicate_group")
        .distinct()
        .count(),
        "excluded": revision.excluded_count,
    }
    return PowerSystemPublicationPreview(
        source_revision=revision,
        effective_from=effective_from,
        occurrences=occurrences,
        canonical_json=canonical,
        digest=digest,
        summary=summary,
    )


def _equipment_category(type_code: str, domain: str) -> str:
    from apps.equipment.models import EquipmentType

    if type_code == "unit_substation":
        return EquipmentType.Category.KTP
    if type_code == "wind_turbine":
        return EquipmentType.Category.WTG
    if domain == "POWER_LINE" or type_code in {"overhead_line", "cable_line"}:
        return EquipmentType.Category.LINE
    if domain == "RELAY_PROTECTION_AUTOMATION":
        return EquipmentType.Category.RPA
    if domain == "SDTU":
        return EquipmentType.Category.SDTU
    if type_code in {"voltage_level", "asset_group", "bus_section", "low_voltage_bus_section"}:
        return EquipmentType.Category.SWITCHGEAR
    if type_code in {
        "control_building",
        "battery_bank",
        "charger",
        "metering_system",
        CONTROLLED_SHOT_TYPE_CODE,
    }:
        return EquipmentType.Category.AUXILIARY
    if domain == "PRIMARY_EQUIPMENT":
        return EquipmentType.Category.SUBSTATION
    return EquipmentType.Category.OTHER


def _type_dictionary_by_code(revision: PowerSystemSourceRevision) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for item in revision.type_dictionary:
        if isinstance(item, dict):
            code = _normalize_space(str(item.get("type_code_proposed", "")))
            if code:
                result[code] = {str(key): str(value or "") for key, value in item.items()}
    return result


def _resolve_or_create_equipment_type(
    occurrence: PowerSystemAssetOccurrence,
    dictionary: dict[str, dict[str, str]],
):
    from apps.equipment.models import EquipmentType

    type_code = occurrence.asset_type_code
    type_row = dictionary.get(type_code, {})
    name = _normalize_space(
        type_row.get("russian_label_proposed", "") or occurrence.asset_type_name or type_code
    )
    category = _equipment_category(type_code, occurrence.domain)
    existing = EquipmentType.objects.filter(code=type_code).first()
    if existing is not None:
        if existing.name != name or existing.category != category:
            raise ValidationError(
                f"Вид оборудования {type_code} уже существует с другой семантикой."
            )
        return existing
    return EquipmentType.objects.create(
        code=type_code,
        name=name,
        category=category,
        description=(
            "Создано контролируемой публикацией пакета объектов диспетчеризации. "
            "Английский код имеет статус предметного идентификатора системы."
        ),
    )


def _resolve_or_create_site(revision: PowerSystemSourceRevision, name: str):
    from apps.equipment.models import EnergySite

    normalized = _normalize_space(name)
    matches = list(
        EnergySite.objects.filter(organization=revision.organization)
        .filter(Q(name__iexact=normalized) | Q(short_name__iexact=normalized))
        .distinct()[:2]
    )
    if len(matches) > 1:
        raise ValidationError(f"Энергообъект {normalized!r} найден неоднозначно.")
    if matches:
        return matches[0]
    token = _comparison_token(normalized)
    if "вэс" in token:
        site_type = EnergySite.SiteType.WIND_POWER_PLANT
    elif token.startswith("пс ") or "подстанц" in token:
        site_type = EnergySite.SiteType.SUBSTATION
    else:
        site_type = EnergySite.SiteType.OTHER
    return EnergySite.objects.create(
        organization=revision.organization,
        code=_slug_hash("import-site", token, 16),
        name=normalized,
        short_name=normalized,
        site_type=site_type,
        is_external=False,
    )


def _dispatcher_name_revision(asset, occurrence, actor: Employee, effective_from: date):
    from apps.equipment.models import EquipmentNameRevision, PublicationStatus
    from apps.equipment.services import publish_equipment_name_revision

    desired = _normalize_space(occurrence.dispatcher_name_raw)
    current = (
        asset.dispatcher_name_revisions.filter(status=PublicationStatus.PUBLISHED)
        .order_by("-effective_from", "-revision_number")
        .first()
    )
    if current is not None and current.dispatcher_name == desired:
        return current
    next_number = (
        asset.dispatcher_name_revisions.aggregate(value=Max("revision_number"))["value"] or 0
    ) + 1
    revision = EquipmentNameRevision.objects.create(
        equipment=asset,
        revision_number=next_number,
        dispatcher_name=desired,
        effective_from=effective_from,
        basis_reference=(
            f"Пакет объектов диспетчеризации {occurrence.source_revision.original_filename}; "
            f"SHA-256 {occurrence.source_revision.file_sha256}"
        )[:1000],
    )
    return publish_equipment_name_revision(revision=revision, actor=actor)


def _existing_or_create_asset(
    *,
    occurrence: PowerSystemAssetOccurrence,
    logical_key: str,
    site,
    equipment_type,
    parent,
):
    from apps.equipment.models import EquipmentAsset

    code = _slug_hash("PSA", logical_key, 20).upper()
    existing = EquipmentAsset.objects.filter(
        organization=occurrence.source_revision.organization,
        code=code,
    ).first()
    if existing is not None:
        if existing.attributes.get("power_system_logical_key") != logical_key:
            raise ValidationError(f"Стабильный код {code} занят другим объектом.")
        return existing, False
    voltage_label = occurrence.voltage_context_raw
    if not voltage_label and occurrence.nominal_voltage_kv is not None:
        voltage_label = f"{occurrence.nominal_voltage_kv.normalize()} кВ"
    asset = EquipmentAsset(
        organization=occurrence.source_revision.organization,
        site=site,
        equipment_type=equipment_type,
        parent=parent,
        code=code,
        technical_name=(
            _normalize_space(occurrence.display_name_normalized)
            or _normalize_space(occurrence.dispatcher_name_raw)
        ),
        status=EquipmentAsset.Status.ACTIVE,
        voltage_level=voltage_label[:64],
        attributes={
            "power_system_logical_key": logical_key,
            "source_domain": occurrence.domain,
            "source_category_raw": occurrence.source_category_raw,
            "source_revision_public_id": str(occurrence.source_revision.public_id),
            "source_occurrence_ids": [occurrence.occurrence_id],
            "classification_confidence": occurrence.classification_confidence,
            "hierarchy_confidence": occurrence.hierarchy_confidence,
        },
        is_external=False,
    )
    asset.save()
    return asset, True


def _append_occurrence_provenance(asset, occurrence: PowerSystemAssetOccurrence) -> None:
    ids = list(asset.attributes.get("source_occurrence_ids", []))
    if occurrence.occurrence_id in ids:
        return
    if asset.dispatcher_name_revisions.filter(status="PUBLISHED").exists():
        # Published equipment structure is immutable; provenance remains complete in
        # PowerSystemAssetOccurrence and must not mutate the registered asset.
        return
    ids.append(occurrence.occurrence_id)
    asset.attributes = {**asset.attributes, "source_occurrence_ids": ids}
    asset.save(update_fields=("attributes",))


def _resolve_dispatch_subject(revision: PowerSystemSourceRevision, authority):
    from apps.dispatching.models import DispatchSubject
    from apps.equipment.models import EnergySite

    raw = _normalize_space(authority.authority_subject_raw)
    proposed = _normalize_space(authority.authority_subject_normalized)
    token = proposed or raw
    if authority.normalization_status == "PROPOSED_TYPO_CORRECTION":
        existing = (
            DispatchSubject.objects.filter(organization=revision.organization)
            .filter(Q(name__iexact=proposed) | Q(short_name__iexact=proposed))
            .first()
        )
        site_exists = EnergySite.objects.filter(
            organization=revision.organization,
            name__iexact=proposed,
        ).exists()
        if existing is None and not site_exists:
            return None
    matches = list(
        DispatchSubject.objects.filter(organization=revision.organization)
        .filter(Q(name__iexact=token) | Q(short_name__iexact=token))
        .distinct()[:2]
    )
    if len(matches) > 1:
        return None
    if matches:
        return matches[0]
    site_match = EnergySite.objects.filter(
        organization=revision.organization,
        name__iexact=token,
    ).exists()
    comparison = _comparison_token(token)
    if site_match:
        subject_type = DispatchSubject.SubjectType.INTERNAL
        is_external = False
    elif any(marker in comparison for marker in ("цду", "оду", "рду")):
        subject_type = DispatchSubject.SubjectType.HIGHER
        is_external = True
    elif comparison.startswith("пс ") or "диспетчер" in comparison:
        subject_type = DispatchSubject.SubjectType.ADJACENT
        is_external = True
    else:
        subject_type = DispatchSubject.SubjectType.OTHER
        is_external = True
    return DispatchSubject.objects.create(
        organization=revision.organization,
        code=_slug_hash("import-subject", comparison, 18),
        name=token,
        short_name=token[:255],
        subject_type=subject_type,
        is_external=is_external,
        description="Создано из контролируемого пакета объектов диспетчеризации.",
    )


def _source_dispatch_level(revision: PowerSystemSourceRevision):
    from apps.dispatching.models import DispatchLevel

    level, _created = DispatchLevel.objects.get_or_create(
        organization=revision.organization,
        code="source-operational-level",
        defaults={
            "name": "Оперативный уровень исходного перечня",
            "level_type": DispatchLevel.LevelType.TECHNOLOGICAL,
            "rank": 100,
            "description": (
                "Промежуточный уровень для назначений, источник которых не содержит "
                "явной классификации диспетчерского или технологического уровня."
            ),
        },
    )
    return level


def _publish_authority(
    *,
    authority: PowerSystemAuthorityOccurrence,
    asset,
    actor: Employee,
    effective_from: date,
) -> tuple[str, str] | None:
    from apps.dispatching.models import (
        ManagementObject,
        ManagementRevision,
        PublicationStatus,
        SupervisionObject,
        SupervisionRevision,
    )
    from apps.dispatching.services import (
        publish_management_revision,
        publish_supervision_revision,
    )

    if authority.assignment_status != PowerSystemAuthorityOccurrence.AssignmentStatus.ASSIGNED:
        authority.publication_status = PowerSystemAuthorityOccurrence.PublicationStatus.SKIPPED
        authority.publication_note = authority.get_assignment_status_display()
        authority.save(update_fields=("publication_status", "publication_note"))
        return None
    subject = _resolve_dispatch_subject(authority.source_revision, authority)
    if subject is None:
        authority.publication_status = (
            PowerSystemAuthorityOccurrence.PublicationStatus.REVIEW_REQUIRED
        )
        authority.publication_note = "Субъект не разрешён однозначно; raw сохранён."
        authority.save(update_fields=("publication_status", "publication_note"))
        return None
    level = _source_dispatch_level(authority.source_revision)
    basis = (
        f"Пакет {authority.source_revision.original_filename}; "
        f"SHA-256 {authority.source_revision.file_sha256}; "
        f"исходная ячейка: {authority.source_cell_raw}"
    )[:1000]
    if authority.authority_kind == PowerSystemAuthorityOccurrence.AuthorityKind.OPERATIONAL_MANAGEMENT:
        management_object, _created = ManagementObject.objects.get_or_create(
            organization=authority.source_revision.organization,
            equipment=asset,
            defaults={"notes": "Создано из пакета объектов диспетчеризации."},
        )
        existing = management_object.revisions.filter(
            level=level,
            subject=subject,
            status=PublicationStatus.PUBLISHED,
            effective_from__lte=effective_from,
        ).filter(Q(effective_until__isnull=True) | Q(effective_until__gte=effective_from)).first()
        if existing is None:
            conflict = management_object.revisions.filter(
                level=level,
                status=PublicationStatus.PUBLISHED,
                effective_from__lte=effective_from,
            ).filter(Q(effective_until__isnull=True) | Q(effective_until__gte=effective_from)).exists()
            if conflict:
                authority.publication_status = (
                    PowerSystemAuthorityOccurrence.PublicationStatus.REVIEW_REQUIRED
                )
                authority.publication_note = "В реестре уже действует другой управляющий субъект."
                authority.save(update_fields=("publication_status", "publication_note"))
                return None
            number = management_object.revisions.aggregate(value=Max("revision_number"))["value"] or 0
            existing = ManagementRevision.objects.create(
                management_object=management_object,
                revision_number=number + 1,
                level=level,
                subject=subject,
                effective_from=effective_from,
                basis_reference=basis,
                change_summary="Создано контролируемой публикацией источника.",
            )
            existing = publish_management_revision(revision=existing, actor=actor)
        target_model = "dispatching.ManagementRevision"
    else:
        supervision_object, _created = SupervisionObject.objects.get_or_create(
            organization=authority.source_revision.organization,
            equipment=asset,
            defaults={"notes": "Создано из пакета объектов диспетчеризации."},
        )
        mode_map = {
            PowerSystemAuthorityOccurrence.ConductMode.OPERATIONAL: (
                SupervisionRevision.ConductMode.OPERATIONAL
            ),
            PowerSystemAuthorityOccurrence.ConductMode.INFORMATIONAL: (
                SupervisionRevision.ConductMode.INFORMATIONAL
            ),
            PowerSystemAuthorityOccurrence.ConductMode.UNKNOWN: (
                SupervisionRevision.ConductMode.UNKNOWN
            ),
        }
        conduct_mode = mode_map[authority.conduct_mode]
        existing = supervision_object.revisions.filter(
            level=level,
            subject=subject,
            conduct_mode=conduct_mode,
            status=PublicationStatus.PUBLISHED,
            effective_from__lte=effective_from,
        ).filter(Q(effective_until__isnull=True) | Q(effective_until__gte=effective_from)).first()
        if existing is None:
            number = supervision_object.revisions.aggregate(value=Max("revision_number"))["value"] or 0
            existing = SupervisionRevision.objects.create(
                supervision_object=supervision_object,
                revision_number=number + 1,
                level=level,
                subject=subject,
                conduct_mode=conduct_mode,
                effective_from=effective_from,
                basis_reference=basis,
                change_summary="Создано контролируемой публикацией источника.",
            )
            existing = publish_supervision_revision(revision=existing, actor=actor)
        target_model = "dispatching.SupervisionRevision"
    authority.publication_status = PowerSystemAuthorityOccurrence.PublicationStatus.PUBLISHED
    authority.published_target_model = target_model
    authority.published_target_id = str(existing.pk)
    authority.publication_note = ""
    authority.save(
        update_fields=(
            "publication_status",
            "published_target_model",
            "published_target_id",
            "publication_note",
        )
    )
    return target_model, str(existing.pk)


def _publish_safe_aliases(
    *,
    revision: PowerSystemSourceRevision,
    actor: Employee,
    effective_from: date,
    occurrence_asset_map: dict[int, object],
) -> int:
    from apps.equipment.models import EquipmentAlias

    count = 0
    proposals = revision.alias_proposals.filter(
        review_status=PowerSystemAliasProposal.ReviewStatus.AUTO_SAFE,
        publication_status=PowerSystemAliasProposal.PublicationStatus.PENDING,
        asset_occurrence_id__in=occurrence_asset_map,
    ).select_related("asset_occurrence")
    for proposal in proposals:
        asset = occurrence_asset_map[proposal.asset_occurrence_id]
        alias = _normalize_space(proposal.alias_raw)
        normalized = alias.casefold()
        if normalized == _normalize_space(proposal.target_name_raw).casefold():
            proposal.publication_status = PowerSystemAliasProposal.PublicationStatus.SKIPPED
            proposal.save(update_fields=("publication_status",))
            continue
        scope_parent = asset.parent
        scope_site = None if scope_parent is not None else asset.site
        existing = EquipmentAlias.objects.filter(
            organization=revision.organization,
            normalized_alias=normalized,
            valid_from=effective_from,
            scope_parent=scope_parent,
            scope_site=scope_site,
        ).first()
        if existing is None:
            existing = EquipmentAlias.objects.create(
                organization=revision.organization,
                equipment=asset,
                scope_site=scope_site,
                scope_parent=scope_parent,
                alias=alias,
                alias_type=EquipmentAlias.AliasType.SEARCH,
                valid_from=effective_from,
                basis_reference=(
                    f"Предложение алиаса из пакета {revision.original_filename}; "
                    f"SHA-256 {revision.file_sha256}"
                )[:1000],
                created_by=actor,
            )
            count += 1
        elif existing.equipment_id != asset.pk:
            proposal.publication_status = PowerSystemAliasProposal.PublicationStatus.SKIPPED
            proposal.save(update_fields=("publication_status",))
            continue
        proposal.publication_status = PowerSystemAliasProposal.PublicationStatus.PUBLISHED
        proposal.published_alias = existing
        proposal.save(update_fields=("publication_status", "published_alias"))
    return count


@transaction.atomic
def publish_power_system_revision(
    *,
    revision: PowerSystemSourceRevision,
    actor: Employee,
    user,
    password: str,
    effective_from: date,
    expected_digest: str,
) -> PowerSystemPublication:
    if user is None or not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Для публикации требуется персональная сессия.")
    session_employee = require_import_employee(user)
    if session_employee.pk != actor.pk or actor.user_id != getattr(user, "pk", None):
        raise PermissionDenied("Учётная запись не соответствует публикующему сотруднику.")
    if not can_publish_import(user):
        raise PermissionDenied(
            "Для публикации требуется действующая роль «Администратор справочников»."
        )
    if not password or not user.check_password(password):
        raise ValidationError({"password": "Неверный текущий пароль."})

    locked = (
        PowerSystemSourceRevision.objects.select_for_update()
        .select_related("organization", "data_profile")
        .get(pk=revision.pk)
    )
    list(locked.asset_occurrences.select_for_update().order_by("pk"))
    preview = build_power_system_publication_preview(
        revision=locked,
        effective_from=effective_from,
    )
    if expected_digest != preview.digest:
        raise ValidationError("Состав публикации изменился. Обновите страницу.")

    dictionary = _type_dictionary_by_code(locked)
    sites: dict[str, object] = {}
    for occurrence in preview.occurrences:
        facilities = _normalize_space(occurrence.energy_facility_raw)
        if facilities and facilities not in sites:
            sites[facilities] = _resolve_or_create_site(locked, facilities)

    selected = list(preview.occurrences)
    selected.sort(
        key=lambda occurrence: (
            0 if occurrence.asset_type_code == "energy_facility" else 1,
            0
            if occurrence.record_role == PowerSystemAssetOccurrence.RecordRole.HIERARCHY_NODE
            else 1,
            occurrence.source_sheet,
            occurrence.source_row,
            occurrence.occurrence_id,
        )
    )
    group_map: dict[str, list[PowerSystemAssetOccurrence]] = defaultdict(list)
    for occurrence in selected:
        group_map[occurrence.effective_logical_key].append(occurrence)

    external_asset_map: dict[str, object] = {}
    occurrence_asset_map: dict[int, object] = {}
    created_assets = 0
    reused_assets = 0
    published_sites = 0
    model_counts: dict[str, int] = defaultdict(int)

    def group_sort_key(item):
        _logical_key_value, group = item
        primary_item = min(group, key=lambda row: (row.source_row, row.pk))
        return (
            0 if primary_item.asset_type_code == "energy_facility" else 1,
            0
            if primary_item.record_role == PowerSystemAssetOccurrence.RecordRole.HIERARCHY_NODE
            else 1,
            primary_item.source_sheet,
            primary_item.source_row,
            primary_item.occurrence_id,
        )

    pending_groups = sorted(group_map.items(), key=group_sort_key)
    while pending_groups:
        progressed = False
        deferred_groups = []
        for logical_key, group in pending_groups:
            primary = min(group, key=lambda row: (row.source_row, row.pk))
            site = sites[primary.energy_facility_raw]
            if primary.asset_type_code == "energy_facility":
                published_sites += 1
                for occurrence in group:
                    occurrence.review_status = PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED
                    occurrence.publication_result = {
                        "target_model": "equipment.EnergySite",
                        "target_id": site.pk,
                        "site_code": site.code,
                    }
                    occurrence.save(update_fields=("review_status", "publication_result"))
                progressed = True
                continue

            parent = None
            if primary.parent_external_key.startswith("NODE:"):
                parent = external_asset_map.get(primary.parent_external_key)
                if parent is None:
                    existing_parent_occurrence = (
                        locked.asset_occurrences.filter(
                            external_key=primary.parent_external_key,
                            review_status=PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED,
                            published_asset__isnull=False,
                        )
                        .select_related("published_asset")
                        .first()
                    )
                    if existing_parent_occurrence is not None:
                        parent = existing_parent_occurrence.published_asset
                if parent is None:
                    deferred_groups.append((logical_key, group))
                    continue

            equipment_type = _resolve_or_create_equipment_type(primary, dictionary)
            asset, created = _existing_or_create_asset(
                occurrence=primary,
                logical_key=logical_key,
                site=site,
                equipment_type=equipment_type,
                parent=parent,
            )
            if created:
                created_assets += 1
            else:
                reused_assets += 1
            for occurrence in group:
                _append_occurrence_provenance(asset, occurrence)
            name_revision = _dispatcher_name_revision(asset, primary, actor, effective_from)
            for occurrence in group:
                occurrence.published_asset = asset
                occurrence.review_status = PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED
                occurrence.publication_result = {
                    "target_model": "equipment.EquipmentAsset",
                    "target_id": asset.pk,
                    "public_id": str(asset.public_id),
                    "code": asset.code,
                    "logical_key": logical_key,
                    "dispatcher_name_revision_id": name_revision.pk,
                    "dispatcher_name_digest": name_revision.digest,
                }
                occurrence.save(
                    update_fields=("published_asset", "review_status", "publication_result")
                )
                occurrence_asset_map[occurrence.pk] = asset
                external_asset_map[occurrence.external_key] = asset
            model_counts["equipment.EquipmentAsset"] += 1
            progressed = True

        if not progressed:
            unresolved = [
                f"{min(group, key=lambda row: (row.source_row, row.pk)).occurrence_id} "
                f"→ {min(group, key=lambda row: (row.source_row, row.pk)).parent_external_key}"
                for _logical_key_value, group in deferred_groups[:10]
            ]
            raise ValidationError(
                "Не удалось разрешить иерархию публикуемых строк: " + "; ".join(unresolved)
            )
        pending_groups = deferred_groups

    aliases_created = _publish_safe_aliases(
        revision=locked,
        actor=actor,
        effective_from=effective_from,
        occurrence_asset_map=occurrence_asset_map,
    )
    authority_published = 0
    authority_review = 0
    authority_skipped = 0
    authority_rows = locked.authority_occurrences.filter(
        asset_occurrence_id__in=occurrence_asset_map,
        publication_status=PowerSystemAuthorityOccurrence.PublicationStatus.PENDING,
    ).select_related("asset_occurrence", "source_revision")
    for authority in authority_rows:
        result = _publish_authority(
            authority=authority,
            asset=occurrence_asset_map[authority.asset_occurrence_id],
            actor=actor,
            effective_from=effective_from,
        )
        authority.refresh_from_db(fields=("publication_status",))
        if result is not None:
            authority_published += 1
            model_counts[result[0]] += 1
        elif authority.publication_status == PowerSystemAuthorityOccurrence.PublicationStatus.REVIEW_REQUIRED:
            authority_review += 1
        else:
            authority_skipped += 1

    _revision_counts(locked)
    locked.refresh_from_db()
    unresolved = locked.ready_count + locked.review_count + locked.blocked_count
    locked.status = (
        PowerSystemSourceRevision.Status.PUBLISHED
        if unresolved == 0
        else PowerSystemSourceRevision.Status.PARTIALLY_PUBLISHED
    )
    locked.publication_digest = preview.digest
    locked.published_at = timezone.now()
    locked.published_by = actor
    locked.save(
        update_fields=(
            "status",
            "publication_digest",
            "published_at",
            "published_by",
            "updated_at",
        )
    )
    result_summary = {
        **preview.summary,
        "sites": published_sites,
        "assets_created": created_assets,
        "assets_reused": reused_assets,
        "aliases_created": aliases_created,
        "authority_published": authority_published,
        "authority_review_required": authority_review,
        "authority_skipped": authority_skipped,
        "models": dict(model_counts),
        "remaining_ready": locked.ready_count,
        "remaining_review": locked.review_count,
        "remaining_blocked": locked.blocked_count,
    }
    return PowerSystemPublication.objects.create(
        source_revision=locked,
        actor=actor,
        schema_version=POWER_SYSTEM_PUBLICATION_SCHEMA,
        canonical_json=preview.canonical_json,
        digest=preview.digest,
        result_summary=result_summary,
    )


def available_power_system_profiles(organization) -> tuple[DataProfile, ...]:
    DataProfile.ensure_for_organization(organization)
    return tuple(
        DataProfile.objects.filter(organization=organization, is_active=True).order_by(
            "-is_default",
            "name",
        )
    )


def power_system_revision_for_user(user, public_id) -> tuple[Employee, PowerSystemSourceRevision]:
    employee = require_import_employee(user)
    try:
        revision = PowerSystemSourceRevision.objects.select_related(
            "organization",
            "data_profile",
            "uploaded_by",
            "published_by",
            "supersedes",
        ).get(public_id=public_id, organization=employee.organization)
    except PowerSystemSourceRevision.DoesNotExist as exc:
        raise PermissionDenied("Редакция источника не найдена в вашей организации.") from exc
    return employee, revision


def power_system_type_counts(revision: PowerSystemSourceRevision) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for code, name in revision.asset_occurrences.values_list("asset_type_code", "asset_type_name"):
        counts[(code, name)] += 1
    return [
        {"code": code, "name": name, "count": count}
        for (code, name), count in sorted(counts.items(), key=lambda item: (-item[1], item[0][1]))
    ]


def source_revision_queryset_for_employee(employee: Employee):
    return PowerSystemSourceRevision.objects.filter(
        organization=employee.organization,
    ).select_related("data_profile", "uploaded_by", "published_by", "supersedes")


def review_status_summary(
    occurrences: Iterable[PowerSystemAssetOccurrence],
) -> dict[str, int]:
    result: dict[str, int] = defaultdict(int)
    for occurrence in occurrences:
        result[occurrence.review_status] += 1
    return dict(result)
