from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import stat
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import (
    Division,
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    OperationalRightDefinition,
    Position,
)

from .models import (
    DataProfile,
    PersonnelAuthorityCell,
    PersonnelPublication,
    PersonnelSourceRevision,
    PersonnelSourceRow,
)
from .services import can_publish_import, require_import_employee

MAX_PERSONNEL_SOURCE_SIZE = 10 * 1024 * 1024
MAX_PERSONNEL_XLSX_SIZE = MAX_PERSONNEL_SOURCE_SIZE
MAX_PERSONNEL_XLSX_UNCOMPRESSED_SIZE = 60 * 1024 * 1024
MAX_PERSONNEL_CSV_PACKAGE_UNCOMPRESSED_SIZE = 60 * 1024 * 1024
MAX_PERSONNEL_CSV_ENTRY_SIZE = 25 * 1024 * 1024
MAX_PERSONNEL_CSV_PACKAGE_ENTRIES = 16
PERSONNEL_PUBLICATION_SCHEMA = "eod.personnel-authority.publication.v1"

CURRENT_RIGHT_COLUMNS = (
    ("G", "dispatch_application_submit"),
    ("H", "dispatch_application_approve"),
    ("I", "operational_application_submit"),
    ("J", "operational_application_approve"),
    ("K", "interlock_bypass_authorization"),
    ("L", "worksite_preparation_and_admission_authorization"),
    ("M", "permit_and_order_issue"),
    ("N", "responsible_work_manager"),
    ("O", "admitting_person"),
    ("P", "work_supervisor"),
    ("Q", "observer"),
    ("R", "team_member"),
    ("S", "sole_inspection"),
    ("T", "operational_communications"),
    ("U", "switching_operation"),
    ("V", "switching_supervision"),
    ("X", "work_at_height"),
    ("Y", "live_work"),
    ("Z", "induced_voltage_work"),
    ("AA", "high_voltage_testing"),
    ("AB", "rza_maintenance_category"),
)

CSV_AUTHORITY_CODE_MAP = {
    "DISPATCH_REQUEST_SUBMIT": ("G", "dispatch_application_submit"),
    "DISPATCH_REQUEST_APPROVE": ("H", "dispatch_application_approve"),
    "OPERATIONAL_REQUEST_SUBMIT": ("I", "operational_application_submit"),
    "OPERATIONAL_REQUEST_APPROVE": ("J", "operational_application_approve"),
    "UNBLOCKING_PERMISSION_ISSUE": ("K", "interlock_bypass_authorization"),
    "WORKPLACE_PREPARATION_ADMISSION_PERMISSION_ISSUE": (
        "L",
        "worksite_preparation_and_admission_authorization",
    ),
    "WORK_PERMIT_OR_ORDER_ISSUE": ("M", "permit_and_order_issue"),
    "RESPONSIBLE_WORK_MANAGER": ("N", "responsible_work_manager"),
    "ADMITTING_PERSON": ("O", "admitting_person"),
    "WORK_SUPERVISOR": ("P", "work_supervisor"),
    "OBSERVER": ("Q", "observer"),
    "BRIGADE_MEMBER": ("R", "team_member"),
    "SOLE_INSPECTION": ("S", "sole_inspection"),
    "OPERATIONAL_NEGOTIATIONS": ("T", "operational_communications"),
    "SWITCHING_EXECUTION": ("U", "switching_operation"),
    "SWITCHING_CONTROL": ("V", "switching_supervision"),
    "WORK_AT_HEIGHT_QUALIFICATION": ("X", "work_at_height"),
    "LIVE_WORK_QUALIFICATION": ("Y", "live_work"),
    "INDUCED_VOLTAGE_WORK": ("Z", "induced_voltage_work"),
    "HIGH_VOLTAGE_TESTING": ("AA", "high_voltage_testing"),
    "RZA_MAINTENANCE_CATEGORY": ("AB", "rza_maintenance_category"),
}

PERSONNEL_CSV_REQUIRED_FILES = frozenset(
    {
        "eod_people.csv",
        "eod_positions.csv",
        "eod_operational_authorities.csv",
        "eod_person_authority_assignments.csv",
    }
)
PERSONNEL_CSV_OPTIONAL_FILES = frozenset({"eod_import_issues.csv"})
PERSONNEL_CSV_IGNORED_FILES = frozenset({"eod_workplace_document_register.csv"})
PERSONNEL_CSV_ALLOWED_FILES = (
    PERSONNEL_CSV_REQUIRED_FILES
    | PERSONNEL_CSV_OPTIONAL_FILES
    | PERSONNEL_CSV_IGNORED_FILES
)

PEOPLE_CSV_HEADER = (
    "source_sheet",
    "source_excel_row",
    "source_person_no",
    "full_name_raw",
    "full_name_normalized",
    "position_raw",
    "position_normalized_candidate",
    "organizational_unit_raw",
    "organizational_unit_normalized_candidate",
    "personnel_category_raw",
    "personnel_category_normalized_candidate",
    "electrical_safety_group_raw",
    "electrical_safety_group",
    "voltage_scope",
    "electrical_installation_scope_raw",
    "knowledge_check_date",
    "valid_until",
    "basis_document_date",
    "basis_document_number",
    "basis_document_title",
    "basis_metadata_status",
    "temporary_right_indicator",
)
POSITIONS_CSV_HEADER = (
    "position_key_proposed",
    "position_name_normalized_candidate",
    "source_variants",
    "person_count",
    "normalization_status",
)
AUTHORITIES_CSV_HEADER = (
    "authority_code_proposed",
    "source_excel_column",
    "source_label_normalized",
    "authority_category_proposed",
    "value_kind",
    "compound_decomposition",
    "notes",
)
ASSIGNMENTS_CSV_HEADER = (
    "source_person_no",
    "full_name_normalized",
    "authority_code_proposed",
    "source_excel_cell",
    "source_raw_value",
    "source_status",
    "qualifier_raw",
    "reference_marker",
    "reference_text_from_source_legend",
    "enum_value",
    "scope_raw",
    "effective_from",
    "effective_until",
    "basis_document_date",
    "basis_document_number",
    "import_action_proposed",
)
ISSUES_CSV_HEADER = (
    "issue_id",
    "source",
    "severity",
    "entity_ref",
    "field",
    "raw_value",
    "issue_type",
    "description",
    "recommended_action",
    "status",
)
LEGACY_RIGHT_COLUMNS = (
    ("F", "dispatch_application_submit"),
    ("G", "dispatch_application_approve"),
    ("H", "operational_application_submit"),
    ("I", "operational_application_approve"),
    ("J", "interlock_bypass_authorization"),
    ("K", "worksite_preparation_and_admission_authorization"),
    ("L", "permit_and_order_issue"),
    ("M", "responsible_work_manager"),
    ("N", "admitting_person"),
    ("O", "work_supervisor"),
    ("P", "observer"),
    ("Q", "team_member"),
    ("R", "sole_inspection"),
    ("S", "operational_communications"),
    ("T", "switching_operation"),
    ("U", "switching_supervision"),
)

CURRENT_FOOTNOTE_ROWS = range(85, 89)
LEGACY_FOOTNOTE_ROWS = range(81, 91)
EQUIPMENT_GROUP_TOKENS = ("ЭТО", "ВЭУ", "АСУ ТП", "РЗА")


class PersonnelWorkbookError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedAuthorityCell:
    source_column: str
    right_code: str
    source_header: str
    raw_marker: str
    grant_state: str
    qualifier: str
    footnote_numbers: tuple[int, ...]
    equipment_groups: tuple[str, ...]
    issues: tuple[str, ...]
    is_publishable: bool


@dataclass(frozen=True, slots=True)
class ParsedPersonRow:
    source_row_number: int
    source_sequence: int
    full_name_raw: str
    last_name: str
    first_name: str
    middle_name: str
    position_raw: str
    division_raw: str
    personnel_category_raw: str
    electrical_safety_raw: str
    electrical_safety_group: str
    voltage_scope: str
    installation_scope_raw: str
    rza_category_raw: str
    issues: tuple[str, ...]
    review_status: str
    fingerprint: str
    authority_cells: tuple[ParsedAuthorityCell, ...]


@dataclass(frozen=True, slots=True)
class ParsedPersonnelWorkbook:
    sheet_name: str
    layout_version: str
    document_date: date | None
    document_number: str
    footnotes: dict[str, str]
    manifest: dict[str, object]
    rows: tuple[ParsedPersonRow, ...]


@dataclass(frozen=True, slots=True)
class PersonnelPublicationPreview:
    source_revision: PersonnelSourceRevision
    rows: tuple[PersonnelSourceRow, ...]
    canonical_json: str
    digest: str
    summary: dict[str, int]


def _normalize_space(value: str) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def _comparison_token(value: str) -> str:
    token = unicodedata.normalize("NFKC", _normalize_space(value)).casefold()
    token = token.replace("ё", "е")
    token = re.sub(r"[–—−]", "-", token)
    return token


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    )


def _sha256_payload(value: object) -> tuple[str, str]:
    canonical = _canonical_json(value)
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_upload(uploaded_file) -> bytes:
    chunks = uploaded_file.chunks() if hasattr(uploaded_file, "chunks") else (uploaded_file.read(),)
    data = bytearray()
    for chunk in chunks:
        data.extend(chunk)
        if len(data) > MAX_PERSONNEL_SOURCE_SIZE:
            raise PersonnelWorkbookError("Размер источника персонала превышает 10 МБ.")
    if not data:
        raise PersonnelWorkbookError("Нельзя загрузить пустой источник персонала.")
    return bytes(data)


def _safe_xlsx_entries(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    entries: dict[str, zipfile.ZipInfo] = {}
    total_size = 0
    for info in archive.infolist():
        if info.is_dir():
            continue
        path = PurePosixPath(info.filename)
        if path.is_absolute() or ".." in path.parts:
            raise PersonnelWorkbookError("XLSX содержит недопустимый путь файла.")
        total_size += info.file_size
        if total_size > MAX_PERSONNEL_XLSX_UNCOMPRESSED_SIZE:
            raise PersonnelWorkbookError("Распакованный XLSX превышает 60 МБ.")
        entries[info.filename] = info
    required = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
    if not required.issubset(entries):
        raise PersonnelWorkbookError("Файл повреждён или не является XLSX.")
    return entries


def _xml(archive: zipfile.ZipFile, name: str) -> ElementTree.Element:
    try:
        return ElementTree.fromstring(archive.read(name))
    except (KeyError, ElementTree.ParseError) as exc:
        raise PersonnelWorkbookError(f"Не удалось прочитать структуру XLSX: {name}.") from exc


def _workbook_cells(data: bytes) -> tuple[str, dict[str, str]]:
    spreadsheet_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    relationships_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package_relationships_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    ns = {"m": spreadsheet_ns, "r": relationships_ns, "p": package_relationships_ns}

    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise PersonnelWorkbookError("Файл повреждён или не является XLSX.") from exc
    with archive:
        entries = _safe_xlsx_entries(archive)
        if any(info.flag_bits & 0x1 for info in entries.values()):
            raise PersonnelWorkbookError("Зашифрованные XLSX-файлы не поддерживаются.")

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in entries:
            root = _xml(archive, "xl/sharedStrings.xml")
            for item in root.findall("m:si", ns):
                shared_strings.append("".join(node.text or "" for node in item.iterfind(".//m:t", ns)))

        workbook = _xml(archive, "xl/workbook.xml")
        relationships = _xml(archive, "xl/_rels/workbook.xml.rels")
        relationship_targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships.findall("p:Relationship", ns)
        }
        sheets = workbook.find("m:sheets", ns)
        if sheets is None or not list(sheets):
            raise PersonnelWorkbookError("В XLSX не найдено листов.")
        sheet = list(sheets)[0]
        sheet_name = sheet.attrib.get("name", "Лист1")
        relation_id = sheet.attrib.get(f"{{{relationships_ns}}}id", "")
        target = relationship_targets.get(relation_id, "")
        if not target:
            raise PersonnelWorkbookError("Не удалось определить XML первого листа.")
        worksheet_name = target if target.startswith("xl/") else f"xl/{target.lstrip('/')}"
        worksheet = _xml(archive, worksheet_name)

        values: dict[str, str] = {}
        for cell in worksheet.findall(".//m:sheetData/m:row/m:c", ns):
            reference = cell.attrib.get("r", "")
            if not reference:
                continue
            cell_type = cell.attrib.get("t", "")
            value_node = cell.find("m:v", ns)
            if cell_type == "inlineStr":
                value = "".join(node.text or "" for node in cell.iterfind(".//m:t", ns))
            elif value_node is None:
                value = ""
            else:
                raw = value_node.text or ""
                if cell_type == "s":
                    try:
                        value = shared_strings[int(raw)]
                    except (ValueError, IndexError) as exc:
                        raise PersonnelWorkbookError("XLSX содержит некорректную общую строку.") from exc
                elif cell_type == "b":
                    value = "Да" if raw == "1" else "Нет"
                else:
                    value = raw
            values[reference.upper()] = value
        return sheet_name, values


def _cell(cells: dict[str, str], column: str, row: int) -> str:
    return _normalize_space(cells.get(f"{column}{row}", ""))


def _detect_layout(cells: dict[str, str]) -> str:
    division = _comparison_token(_cell(cells, "D", 7))
    rza = _comparison_token(_cell(cells, "AB", 7))
    legacy_category = _comparison_token(_cell(cells, "D", 7))
    legacy_scope = _comparison_token(_cell(cells, "V", 7))
    if "структур" in division and "подраздел" in division and "рза" in rza:
        return PersonnelSourceRevision.LayoutVersion.CURRENT_28_COLUMNS
    if "категория персонала" in legacy_category and "электроустанов" in legacy_scope:
        return PersonnelSourceRevision.LayoutVersion.LEGACY_22_COLUMNS
    raise PersonnelWorkbookError(
        "Структура XLSX не распознана. Ожидается матрица прав с двухстрочным заголовком в строках 7–8."
    )


def _combined_header(cells: dict[str, str], column: str) -> str:
    values = [_cell(cells, column, 7), _cell(cells, column, 8)]
    return " · ".join(value for value in values if value)


def _document_details(cells: dict[str, str]) -> tuple[date | None, str]:
    detail_columns = ("Q", "R", "S", "T", "U", "V", "Y", "Z", "AA", "AB")
    row_text = " ".join(_cell(cells, column, 4) for column in detail_columns)
    date_match = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", row_text)
    document_date = None
    if date_match:
        try:
            document_date = datetime.strptime(date_match.group(1), "%d.%m.%Y").date()
        except ValueError:
            document_date = None
    number_match = re.search(r"№\s*([^\s].*?)$", row_text)
    document_number = _normalize_space(number_match.group(1)) if number_match else ""
    return document_date, document_number


def _footnotes(cells: dict[str, str], layout: str) -> dict[str, str]:
    rows = (
        CURRENT_FOOTNOTE_ROWS
        if layout == PersonnelSourceRevision.LayoutVersion.CURRENT_28_COLUMNS
        else LEGACY_FOOTNOTE_ROWS
    )
    result: dict[str, str] = {}
    for row_number in rows:
        text = _cell(cells, "B", row_number)
        match = re.match(r"(\d+)\s*[–—-]\s*(.+)", text)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def _parse_name(value: str) -> tuple[str, str, str, list[str]]:
    parts = _normalize_space(value).split()
    issues: list[str] = []
    if len(parts) < 2:
        return "", "", "", ["ФИО не удалось разделить минимум на фамилию и имя."]
    if len(parts) > 4:
        issues.append("ФИО содержит более четырёх частей и требует проверки.")
    last_name = parts[0]
    first_name = parts[1]
    middle_name = " ".join(parts[2:])
    return last_name, first_name, middle_name, issues


def _parse_safety(value: str) -> tuple[str, str]:
    normalized = _normalize_space(value)
    match = re.search(r"\b(III|IV|V)\b", normalized.upper())
    group = match.group(1) if match else ""
    voltage_scope = normalized
    if match:
        voltage_scope = _normalize_space(normalized[: match.start()] + " " + normalized[match.end() :])
    return group, voltage_scope


def _parse_marker(
    raw_value: str,
    *,
    right_code: str,
    known_footnotes: set[int],
) -> tuple[str, str, tuple[int, ...], tuple[str, ...], tuple[str, ...], bool]:
    raw = _normalize_space(raw_value)
    token = _comparison_token(raw)
    if not raw:
        return PersonnelAuthorityCell.GrantState.BLANK, "", (), (), (), False
    if token in {"-", "нет"}:
        return PersonnelAuthorityCell.GrantState.NOT_GRANTED, "", (), (), (), False

    if right_code == "rza_maintenance_category":
        if re.fullmatch(r"\d+", raw):
            return (
                PersonnelAuthorityCell.GrantState.AMBIGUOUS,
                raw,
                (),
                (),
                ("Числовая категория РЗА сохранена как raw до утверждения словаря значений.",),
                False,
            )
        if token.startswith("+"):
            return (
                PersonnelAuthorityCell.GrantState.AMBIGUOUS,
                raw,
                (),
                (),
                ("Значение категории РЗА требует предметной проверки.",),
                False,
            )
        return (
            PersonnelAuthorityCell.GrantState.AMBIGUOUS,
            raw,
            (),
            (),
            ("Неизвестное значение категории РЗА.",),
            False,
        )

    if not token.startswith("+"):
        return (
            PersonnelAuthorityCell.GrantState.AMBIGUOUS,
            raw,
            (),
            (),
            ("Значение не соответствует отметкам «+», «–» или пустой ячейке.",),
            False,
        )

    remainder = raw[1:].strip()
    footnotes: list[int] = []
    issues: list[str] = []
    numeric_prefix = re.match(r"^\s*(\d+(?:\s*,\s*\d+)*)", remainder)
    if numeric_prefix:
        numbers = [int(item) for item in re.findall(r"\d+", numeric_prefix.group(1))]
        unknown = [number for number in numbers if number not in known_footnotes]
        if unknown:
            issues.append(
                "Не расшифрованы номера сносок: " + ", ".join(str(number) for number in unknown) + "."
            )
        else:
            footnotes.extend(numbers)
        remainder = remainder[numeric_prefix.end() :].strip(" ,;")

    parenthetical = re.findall(r"\(([^()]*)\)", remainder or raw)
    equipment_groups: list[str] = []
    qualifiers: list[str] = []
    for content in parenthetical:
        normalized_content = _normalize_space(content)
        matched_groups = [group for group in EQUIPMENT_GROUP_TOKENS if group in normalized_content.upper()]
        if matched_groups:
            equipment_groups.extend(group for group in matched_groups if group not in equipment_groups)
        elif normalized_content:
            qualifiers.append(normalized_content)
    remainder_without_parentheses = _normalize_space(re.sub(r"\([^()]*\)", " ", remainder))
    if remainder_without_parentheses:
        qualifiers.insert(0, remainder_without_parentheses)

    qualifier_parts = qualifiers[:]
    if equipment_groups:
        qualifier_parts.append("Группы оборудования: " + ", ".join(equipment_groups))
    if footnotes:
        qualifier_parts.append("Сноски: " + ", ".join(str(number) for number in footnotes))
    qualifier = "; ".join(part for part in qualifier_parts if part)

    if issues:
        return (
            PersonnelAuthorityCell.GrantState.AMBIGUOUS,
            qualifier or raw,
            tuple(footnotes),
            tuple(equipment_groups),
            tuple(issues),
            False,
        )
    state = (
        PersonnelAuthorityCell.GrantState.QUALIFIED
        if qualifier
        else PersonnelAuthorityCell.GrantState.GRANTED
    )
    return state, qualifier, tuple(footnotes), tuple(equipment_groups), (), True


def _safe_package_member_name(info: zipfile.ZipInfo) -> str | None:
    path = PurePosixPath(info.filename.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise PersonnelWorkbookError("ZIP-пакет содержит недопустимый путь файла.")
    if info.is_dir():
        return None
    unix_mode = (info.external_attr >> 16) & 0o170000
    if unix_mode == stat.S_IFLNK:
        raise PersonnelWorkbookError("ZIP-пакет не должен содержать символические ссылки.")
    if len(path.parts) > 2:
        raise PersonnelWorkbookError(
            "CSV-файлы должны находиться в корне ZIP или в одном общем каталоге."
        )
    return path.name.casefold()


def _personnel_csv_package_entries(data: bytes) -> dict[str, bytes]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise PersonnelWorkbookError("Файл повреждён или не является ZIP-пакетом CSV.") from exc
    result: dict[str, bytes] = {}
    total_size = 0
    with archive:
        files = [info for info in archive.infolist() if not info.is_dir()]
        if len(files) > MAX_PERSONNEL_CSV_PACKAGE_ENTRIES:
            raise PersonnelWorkbookError("ZIP-пакет содержит слишком много файлов.")
        for info in files:
            name = _safe_package_member_name(info)
            if name is None:
                continue
            if info.flag_bits & 0x1:
                raise PersonnelWorkbookError("Зашифрованные ZIP-пакеты не поддерживаются.")
            if name in {".ds_store", "thumbs.db"} or name.startswith("._"):
                continue
            if name not in PERSONNEL_CSV_ALLOWED_FILES:
                raise PersonnelWorkbookError(f"Неожиданный файл в кадровом ZIP-пакете: {name}.")
            if name in result:
                raise PersonnelWorkbookError(f"В ZIP-пакете повторяется файл {name}.")
            if info.file_size > MAX_PERSONNEL_CSV_ENTRY_SIZE:
                raise PersonnelWorkbookError(f"Файл {name} превышает безопасный лимит 25 МБ.")
            total_size += info.file_size
            if total_size > MAX_PERSONNEL_CSV_PACKAGE_UNCOMPRESSED_SIZE:
                raise PersonnelWorkbookError("Распакованный ZIP-пакет превышает 60 МБ.")
            result[name] = archive.read(info)
    missing = sorted(PERSONNEL_CSV_REQUIRED_FILES - set(result))
    if missing:
        raise PersonnelWorkbookError(
            "В кадровом ZIP-пакете отсутствуют обязательные файлы: " + ", ".join(missing) + "."
        )
    return result


def _parse_csv_rows(data: bytes, *, filename: str, expected_header: tuple[str, ...]) -> list[dict[str, str]]:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise PersonnelWorkbookError(f"{filename}: требуется кодировка UTF-8, а не UTF-16.")
    if b"\x00" in data:
        raise PersonnelWorkbookError(f"{filename}: обнаружены нулевые байты.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PersonnelWorkbookError(f"{filename}: требуется кодировка UTF-8.") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    actual_header = tuple(reader.fieldnames or ())
    if actual_header != expected_header:
        raise PersonnelWorkbookError(
            f"{filename}: заголовок не соответствует утверждённому CSV-контракту."
        )
    rows: list[dict[str, str]] = []
    for line_number, raw_row in enumerate(reader, start=2):
        if None in raw_row:
            raise PersonnelWorkbookError(f"{filename}:{line_number}: лишние значения в строке.")
        row = {key: _normalize_space(value or "") for key, value in raw_row.items()}
        if not any(row.values()):
            continue
        rows.append(row)
    if not rows:
        raise PersonnelWorkbookError(f"{filename}: не найдено строк данных.")
    return rows


def _positive_integer(value: str, *, label: str) -> int:
    normalized = _normalize_space(value)
    if not normalized.isdigit() or int(normalized) <= 0:
        raise PersonnelWorkbookError(f"{label}: ожидается положительное целое число.")
    return int(normalized)


def _optional_iso_date(value: str, *, label: str) -> date | None:
    normalized = _normalize_space(value)
    if not normalized:
        return None
    try:
        return date.fromisoformat(normalized)
    except ValueError as exc:
        raise PersonnelWorkbookError(f"{label}: ожидается дата YYYY-MM-DD.") from exc


def _reference_number(value: str) -> int | None:
    normalized = _normalize_space(value).replace(",", ".")
    if not normalized:
        return None
    match = re.fullmatch(r"(\d+)(?:\.0+)?", normalized)
    return int(match.group(1)) if match else None


def _csv_source_cell(value: str, *, expected_column: str, expected_row: int) -> None:
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", _normalize_space(value))
    if not match:
        raise PersonnelWorkbookError(f"Некорректная ссылка исходной ячейки: {value!r}.")
    if match.group(1).upper() != expected_column or int(match.group(2)) != expected_row:
        raise PersonnelWorkbookError(
            f"Ссылка {value!r} не соответствует ожидаемой ячейке {expected_column}{expected_row}."
        )


def parse_personnel_csv_package(data: bytes) -> ParsedPersonnelWorkbook:
    entries = _personnel_csv_package_entries(data)
    people_rows = _parse_csv_rows(
        entries["eod_people.csv"], filename="eod_people.csv", expected_header=PEOPLE_CSV_HEADER
    )
    position_rows = _parse_csv_rows(
        entries["eod_positions.csv"],
        filename="eod_positions.csv",
        expected_header=POSITIONS_CSV_HEADER,
    )
    authority_rows = _parse_csv_rows(
        entries["eod_operational_authorities.csv"],
        filename="eod_operational_authorities.csv",
        expected_header=AUTHORITIES_CSV_HEADER,
    )
    assignment_rows = _parse_csv_rows(
        entries["eod_person_authority_assignments.csv"],
        filename="eod_person_authority_assignments.csv",
        expected_header=ASSIGNMENTS_CSV_HEADER,
    )
    issue_rows = (
        _parse_csv_rows(
            entries["eod_import_issues.csv"],
            filename="eod_import_issues.csv",
            expected_header=ISSUES_CSV_HEADER,
        )
        if "eod_import_issues.csv" in entries
        else []
    )

    positions: dict[str, dict[str, str]] = {}
    position_keys: set[str] = set()
    for row in position_rows:
        key = row["position_key_proposed"]
        name = row["position_name_normalized_candidate"]
        if not key or key in position_keys:
            raise PersonnelWorkbookError("eod_positions.csv: пустой или повторяющийся ключ должности.")
        if not name or _comparison_token(name) in positions:
            raise PersonnelWorkbookError("eod_positions.csv: пустая или повторяющаяся должность.")
        if not row["normalization_status"]:
            raise PersonnelWorkbookError("eod_positions.csv: не указан статус нормализации.")
        position_keys.add(key)
        positions[_comparison_token(name)] = row

    authority_catalog: dict[str, dict[str, str]] = {}
    for row in authority_rows:
        proposed = row["authority_code_proposed"]
        if proposed in authority_catalog:
            raise PersonnelWorkbookError("eod_operational_authorities.csv: повторяется код полномочия.")
        expected = CSV_AUTHORITY_CODE_MAP.get(proposed)
        if expected is None:
            raise PersonnelWorkbookError(
                f"eod_operational_authorities.csv: неизвестный код полномочия {proposed!r}."
            )
        if row["source_excel_column"].upper() != expected[0]:
            raise PersonnelWorkbookError(
                f"eod_operational_authorities.csv: код {proposed} привязан не к той колонке."
            )
        if not row["source_label_normalized"]:
            raise PersonnelWorkbookError(
                f"eod_operational_authorities.csv: для {proposed} отсутствует наименование."
            )
        authority_catalog[proposed] = row
    missing_authorities = sorted(set(CSV_AUTHORITY_CODE_MAP) - set(authority_catalog))
    if missing_authorities or len(authority_catalog) != len(CSV_AUTHORITY_CODE_MAP):
        raise PersonnelWorkbookError(
            "eod_operational_authorities.csv должен содержать ровно 21 утверждённый код."
        )

    people: dict[int, dict[str, str]] = {}
    source_rows: set[int] = set()
    for row in people_rows:
        person_no = _positive_integer(
            row["source_person_no"], label="eod_people.csv: source_person_no"
        )
        source_row = _positive_integer(
            row["source_excel_row"], label=f"eod_people.csv: работник {person_no}: source_excel_row"
        )
        if person_no in people or source_row in source_rows:
            raise PersonnelWorkbookError("eod_people.csv: повторяется номер работника или исходная строка.")
        full_name = row["full_name_normalized"] or row["full_name_raw"]
        if not full_name:
            raise PersonnelWorkbookError(f"eod_people.csv: у работника {person_no} отсутствует ФИО.")
        position_candidate = row["position_normalized_candidate"] or row["position_raw"]
        if _comparison_token(position_candidate) not in positions:
            raise PersonnelWorkbookError(
                f"eod_people.csv: должность работника {person_no} отсутствует в eod_positions.csv."
            )
        for field in ("knowledge_check_date", "valid_until", "basis_document_date"):
            _optional_iso_date(row[field], label=f"eod_people.csv: работник {person_no}: {field}")
        people[person_no] = row
        source_rows.add(source_row)

    footnotes: dict[str, str] = {}
    for row in assignment_rows:
        marker = _reference_number(row["reference_marker"])
        text = row["reference_text_from_source_legend"]
        if marker is None or not text:
            continue
        existing = footnotes.get(str(marker))
        if existing and existing != text:
            raise PersonnelWorkbookError(f"В пакете противоречиво расшифрована сноска {marker}.")
        footnotes[str(marker)] = text
    known_footnotes = {int(key) for key in footnotes}

    assignments: dict[tuple[int, str], dict[str, str]] = {}
    for row in assignment_rows:
        person_no = _positive_integer(
            row["source_person_no"],
            label="eod_person_authority_assignments.csv: source_person_no",
        )
        person = people.get(person_no)
        if person is None:
            raise PersonnelWorkbookError(
                f"eod_person_authority_assignments.csv: неизвестный работник {person_no}."
            )
        proposed = row["authority_code_proposed"]
        mapping = CSV_AUTHORITY_CODE_MAP.get(proposed)
        if mapping is None:
            raise PersonnelWorkbookError(
                f"eod_person_authority_assignments.csv: неизвестный код {proposed!r}."
            )
        key = (person_no, proposed)
        if key in assignments:
            raise PersonnelWorkbookError(
                f"eod_person_authority_assignments.csv: повторяется назначение {person_no}/{proposed}."
            )
        expected_name = person["full_name_normalized"] or person["full_name_raw"]
        if _comparison_token(row["full_name_normalized"]) != _comparison_token(expected_name):
            raise PersonnelWorkbookError(
                f"eod_person_authority_assignments.csv: ФИО не совпадает у работника {person_no}."
            )
        source_row = _positive_integer(
            person["source_excel_row"], label=f"eod_people.csv: работник {person_no}: source_excel_row"
        )
        _csv_source_cell(
            row["source_excel_cell"], expected_column=mapping[0], expected_row=source_row
        )
        if row["import_action_proposed"] not in {"CREATE_OR_UPDATE_ASSIGNMENT", "STAGING_ONLY"}:
            raise PersonnelWorkbookError(
                "eod_person_authority_assignments.csv: неизвестное предлагаемое действие импорта."
            )
        for field in ("effective_from", "effective_until", "basis_document_date"):
            _optional_iso_date(
                row[field], label=f"eod_person_authority_assignments.csv: {person_no}/{proposed}: {field}"
            )
        assignments[key] = row

    expected_assignment_count = len(people) * len(CSV_AUTHORITY_CODE_MAP)
    if len(assignments) != expected_assignment_count:
        raise PersonnelWorkbookError(
            "eod_person_authority_assignments.csv должен содержать по 21 строке на каждого работника."
        )

    parsed_rows: list[ParsedPersonRow] = []
    document_dates: set[date] = set()
    document_numbers: set[str] = set()
    for person_no in sorted(people):
        person = people[person_no]
        source_row = int(person["source_excel_row"])
        full_name_raw = person["full_name_raw"] or person["full_name_normalized"]
        last_name, first_name, middle_name, name_issues = _parse_name(full_name_raw)
        position_raw = person["position_normalized_candidate"] or person["position_raw"]
        division_raw = (
            person["organizational_unit_normalized_candidate"]
            or person["organizational_unit_raw"]
        )
        category_raw = (
            person["personnel_category_normalized_candidate"]
            or person["personnel_category_raw"]
        )
        safety_raw = person["electrical_safety_group_raw"]
        safety_group = person["electrical_safety_group"]
        voltage_scope = person["voltage_scope"]
        if not safety_group:
            safety_group, parsed_voltage = _parse_safety(safety_raw)
            voltage_scope = voltage_scope or parsed_voltage
        installation_scope = person["electrical_installation_scope_raw"]
        issues = list(name_issues)
        if not position_raw:
            issues.append("Не указана должность.")
        if not division_raw:
            issues.append("Не указано структурное подразделение.")
        if not category_raw:
            issues.append("Не указана категория персонала.")
        if not safety_group:
            issues.append("Не распознана группа по электробезопасности.")
        position_info = positions.get(_comparison_token(position_raw))
        if position_info and position_info["normalization_status"] != "DIRECT":
            issues.append("Нормализация наименования должности требует ручного подтверждения.")

        parsed_cells: list[ParsedAuthorityCell] = []
        rza_category = ""
        for proposed, (column, internal_code) in CSV_AUTHORITY_CODE_MAP.items():
            assignment = assignments[(person_no, proposed)]
            raw_marker = assignment["source_raw_value"]
            if internal_code == "rza_maintenance_category":
                rza_category = assignment["enum_value"] or raw_marker
            state, qualifier, marker_footnotes, equipment_groups, cell_issues, publishable = _parse_marker(
                raw_marker,
                right_code=internal_code,
                known_footnotes=known_footnotes,
            )
            extra_issues = list(cell_issues)
            if assignment["import_action_proposed"] == "STAGING_ONLY" and publishable:
                state = PersonnelAuthorityCell.GrantState.AMBIGUOUS
                publishable = False
                extra_issues.append(
                    "Нормализатор источника оставил положительное значение только в staging."
                )
            if assignment["import_action_proposed"] == "CREATE_OR_UPDATE_ASSIGNMENT" and not publishable:
                extra_issues.append(
                    "Предложение публикации отклонено: исходная отметка не является однозначной."
                )
            qualifier_parts = [qualifier]
            if assignment["qualifier_raw"] and assignment["qualifier_raw"] not in qualifier:
                qualifier_parts.append(assignment["qualifier_raw"])
            qualifier = "; ".join(_normalize_space(item) for item in qualifier_parts if item)
            parsed_cells.append(
                ParsedAuthorityCell(
                    source_column=column,
                    right_code=internal_code,
                    source_header=authority_catalog[proposed]["source_label_normalized"],
                    raw_marker=raw_marker,
                    grant_state=state,
                    qualifier=qualifier,
                    footnote_numbers=marker_footnotes,
                    equipment_groups=equipment_groups,
                    issues=tuple(extra_issues),
                    is_publishable=publishable,
                )
            )
            if assignment["basis_document_date"]:
                document_dates.add(
                    _optional_iso_date(
                        assignment["basis_document_date"],
                        label=f"назначение {person_no}/{proposed}: basis_document_date",
                    )
                )
            if assignment["basis_document_number"]:
                document_numbers.add(assignment["basis_document_number"])

        ambiguous_count = sum(
            cell.grant_state == PersonnelAuthorityCell.GrantState.AMBIGUOUS
            for cell in parsed_cells
        )
        if ambiguous_count:
            issues.append(f"Неоднозначных ячеек полномочий: {ambiguous_count}.")
        if not last_name or not first_name or not position_raw:
            review_status = PersonnelSourceRow.ReviewStatus.BLOCKED
        elif issues:
            review_status = PersonnelSourceRow.ReviewStatus.REVIEW_REQUIRED
        else:
            review_status = PersonnelSourceRow.ReviewStatus.READY
        fingerprint_payload = {
            "source_person_no": person_no,
            "source_row": source_row,
            "person": person,
            "assignments": [assignments[(person_no, code)] for code in CSV_AUTHORITY_CODE_MAP],
        }
        _canonical, fingerprint = _sha256_payload(fingerprint_payload)
        parsed_rows.append(
            ParsedPersonRow(
                source_row_number=source_row,
                source_sequence=person_no,
                full_name_raw=full_name_raw,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                position_raw=position_raw,
                division_raw=division_raw,
                personnel_category_raw=category_raw,
                electrical_safety_raw=safety_raw,
                electrical_safety_group=safety_group,
                voltage_scope=voltage_scope,
                installation_scope_raw=installation_scope,
                rza_category_raw=rza_category,
                issues=tuple(issues),
                review_status=review_status,
                fingerprint=fingerprint,
                authority_cells=tuple(parsed_cells),
            )
        )

    document_date = next(iter(document_dates)) if len(document_dates) == 1 else None
    document_number = next(iter(document_numbers)) if len(document_numbers) == 1 else ""
    severity_counts = dict(Counter(row["severity"] or "UNSPECIFIED" for row in issue_rows))
    manifest = {
        "schema": "eod.personnel-authority.normalized-csv-package.v1",
        "source_format": "NORMALIZED_CSV_PACKAGE",
        "layout_version": PersonnelSourceRevision.LayoutVersion.CURRENT_28_COLUMNS,
        "sheet_name": "eod_people.csv",
        "package_components": sorted(entries),
        "required_components": sorted(PERSONNEL_CSV_REQUIRED_FILES),
        "ignored_components": sorted(set(entries) & PERSONNEL_CSV_IGNORED_FILES),
        "person_count": len(parsed_rows),
        "position_count": len(position_rows),
        "authority_definition_count": len(authority_catalog),
        "authority_cell_count": len(assignments),
        "source_issue_count": len(issue_rows),
        "source_issue_severity_counts": severity_counts,
        "source_issues": issue_rows,
        "document_date": document_date.isoformat() if document_date else None,
        "document_number": document_number,
    }
    return ParsedPersonnelWorkbook(
        sheet_name="eod_people.csv",
        layout_version=PersonnelSourceRevision.LayoutVersion.CURRENT_28_COLUMNS,
        document_date=document_date,
        document_number=document_number,
        footnotes=footnotes,
        manifest=manifest,
        rows=tuple(parsed_rows),
    )

def parse_personnel_workbook(data: bytes) -> ParsedPersonnelWorkbook:
    sheet_name, cells = _workbook_cells(data)
    layout = _detect_layout(cells)
    document_date, document_number = _document_details(cells)
    footnotes = _footnotes(cells, layout)
    known_footnotes = {int(key) for key in footnotes}
    right_columns = (
        CURRENT_RIGHT_COLUMNS
        if layout == PersonnelSourceRevision.LayoutVersion.CURRENT_28_COLUMNS
        else LEGACY_RIGHT_COLUMNS
    )

    rows: list[ParsedPersonRow] = []
    for row_number in range(9, 5000):
        sequence_raw = _cell(cells, "A", row_number)
        full_name_raw = _cell(cells, "B", row_number)
        if not sequence_raw and not full_name_raw:
            if rows:
                break
            continue
        if not sequence_raw.isdigit():
            if rows:
                break
            continue
        source_sequence = int(sequence_raw)
        position_raw = _cell(cells, "C", row_number)
        if layout == PersonnelSourceRevision.LayoutVersion.CURRENT_28_COLUMNS:
            division_raw = _cell(cells, "D", row_number)
            category_raw = _cell(cells, "E", row_number)
            safety_raw = _cell(cells, "F", row_number)
            installation_scope = _cell(cells, "W", row_number)
            rza_category = _cell(cells, "AB", row_number)
        else:
            division_raw = ""
            category_raw = _cell(cells, "D", row_number)
            safety_raw = _cell(cells, "E", row_number)
            installation_scope = _cell(cells, "V", row_number)
            rza_category = ""

        last_name, first_name, middle_name, name_issues = _parse_name(full_name_raw)
        group, voltage_scope = _parse_safety(safety_raw)
        issues = list(name_issues)
        if not position_raw:
            issues.append("Не указана должность.")
        if not division_raw:
            issues.append(
                "В структуре источника отсутствует отдельное подразделение; требуется ручное сопоставление."
            )
        if not category_raw:
            issues.append("Не указана категория персонала.")
        if not group:
            issues.append("Не распознана группа по электробезопасности.")

        parsed_cells: list[ParsedAuthorityCell] = []
        for column, right_code in right_columns:
            raw_marker = _cell(cells, column, row_number)
            state, qualifier, marker_footnotes, equipment_groups, cell_issues, publishable = _parse_marker(
                raw_marker,
                right_code=right_code,
                known_footnotes=known_footnotes,
            )
            parsed_cells.append(
                ParsedAuthorityCell(
                    source_column=column,
                    right_code=right_code,
                    source_header=_combined_header(cells, column),
                    raw_marker=raw_marker,
                    grant_state=state,
                    qualifier=qualifier,
                    footnote_numbers=marker_footnotes,
                    equipment_groups=equipment_groups,
                    issues=cell_issues,
                    is_publishable=publishable,
                )
            )
        ambiguous_count = sum(
            cell.grant_state == PersonnelAuthorityCell.GrantState.AMBIGUOUS
            for cell in parsed_cells
        )
        if ambiguous_count:
            issues.append(f"Неоднозначных ячеек полномочий: {ambiguous_count}.")

        if not last_name or not first_name or not position_raw:
            review_status = PersonnelSourceRow.ReviewStatus.BLOCKED
        elif issues:
            review_status = PersonnelSourceRow.ReviewStatus.REVIEW_REQUIRED
        else:
            review_status = PersonnelSourceRow.ReviewStatus.READY

        fingerprint_payload = {
            "row": row_number,
            "sequence": source_sequence,
            "name": full_name_raw,
            "position": position_raw,
            "division": division_raw,
            "category": category_raw,
            "safety": safety_raw,
            "installation_scope": installation_scope,
            "rights": [
                {
                    "code": cell.right_code,
                    "marker": cell.raw_marker,
                    "state": cell.grant_state,
                    "qualifier": cell.qualifier,
                }
                for cell in parsed_cells
            ],
        }
        _canonical, fingerprint = _sha256_payload(fingerprint_payload)
        rows.append(
            ParsedPersonRow(
                source_row_number=row_number,
                source_sequence=source_sequence,
                full_name_raw=full_name_raw,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                position_raw=position_raw,
                division_raw=division_raw,
                personnel_category_raw=category_raw,
                electrical_safety_raw=safety_raw,
                electrical_safety_group=group,
                voltage_scope=voltage_scope,
                installation_scope_raw=installation_scope,
                rza_category_raw=rza_category,
                issues=tuple(issues),
                review_status=review_status,
                fingerprint=fingerprint,
                authority_cells=tuple(parsed_cells),
            )
        )

    if not rows:
        raise PersonnelWorkbookError("В матрице не найдено ни одной строки работника.")
    sequences = [row.source_sequence for row in rows]
    if len(sequences) != len(set(sequences)):
        raise PersonnelWorkbookError("В источнике повторяются номера работников.")

    manifest = {
        "schema": "eod.personnel-authority.source.v1",
        "source_format": "XLSX",
        "layout_version": layout,
        "sheet_name": sheet_name,
        "person_count": len(rows),
        "authority_definition_count": len(right_columns),
        "authority_cell_count": len(rows) * len(right_columns),
        "document_date": document_date.isoformat() if document_date else None,
        "document_number": document_number,
    }
    return ParsedPersonnelWorkbook(
        sheet_name=sheet_name,
        layout_version=layout,
        document_date=document_date,
        document_number=document_number,
        footnotes=footnotes,
        manifest=manifest,
        rows=tuple(rows),
    )


def available_personnel_profiles(organization) -> tuple[DataProfile, ...]:
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
            "Реальная матрица работников загружается только в локальную development-базу. "
            "Презентационная база не изменена."
        )


def source_revision_queryset_for_employee(employee: Employee):
    return PersonnelSourceRevision.objects.filter(organization=employee.organization).select_related(
        "data_profile", "uploaded_by", "published_by"
    )


def personnel_revision_for_user(user, public_id):
    employee = require_import_employee(user)
    try:
        revision = source_revision_queryset_for_employee(employee).get(public_id=public_id)
    except PersonnelSourceRevision.DoesNotExist as exc:
        raise PermissionDenied("Редакция персонала недоступна для вашей организации.") from exc
    return employee, revision


def _employee_name_token(employee: Employee) -> tuple[str, str, str]:
    return (
        _comparison_token(employee.last_name),
        _comparison_token(employee.first_name),
        _comparison_token(employee.middle_name),
    )


def _row_name_token(row: ParsedPersonRow | PersonnelSourceRow) -> tuple[str, str, str]:
    return (
        _comparison_token(row.last_name),
        _comparison_token(row.first_name),
        _comparison_token(row.middle_name),
    )


def _match_employee(organization, row: ParsedPersonRow) -> tuple[Employee | None, str]:
    target = _row_name_token(row)
    matches = [
        employee
        for employee in Employee.objects.filter(organization=organization).order_by("id")
        if _employee_name_token(employee) == target
    ][:3]
    if len(matches) == 1:
        return matches[0], PersonnelSourceRow.MatchKind.EXACT
    if len(matches) > 1:
        return None, PersonnelSourceRow.MatchKind.REVIEW_REQUIRED
    return None, PersonnelSourceRow.MatchKind.NONE


@transaction.atomic
def stage_personnel_workbook(
    *,
    uploaded_file,
    employee: Employee,
    data_profile: DataProfile,
    source_reference: str,
    effective_from: date,
) -> PersonnelSourceRevision:
    _require_development_database()
    if employee.organization_id != data_profile.organization_id:
        raise ValidationError("Профиль данных относится к другой организации.")
    if (
        data_profile.code != "local-validation"
        or data_profile.kind != DataProfile.Kind.LOCAL_VALIDATION
        or not data_profile.allows_real_personal_data
    ):
        raise ValidationError("Матрица персонала допускается только в профиле local-validation.")
    if data_profile.export_policy != DataProfile.ExportPolicy.PROHIBITED:
        raise ValidationError("Для персональных данных обычный экспорт должен быть запрещён.")

    data = _read_upload(uploaded_file)
    digest = hashlib.sha256(data).hexdigest()
    existing = PersonnelSourceRevision.objects.filter(
        organization=employee.organization,
        file_sha256=digest,
    ).first()
    if existing is not None:
        return existing

    extension = Path(getattr(uploaded_file, "name", "")).suffix.lower()
    if extension == ".zip":
        parsed = parse_personnel_csv_package(data)
    elif extension == ".xlsx":
        parsed = parse_personnel_workbook(data)
    else:
        raise PersonnelWorkbookError(
            "Допустимы ZIP-пакет нормализованных CSV или исходная матрица XLSX."
        )
    right_definitions = {
        item.code: item
        for item in OperationalRightDefinition.objects.filter(is_active=True)
    }
    expected_codes = {
        code
        for _column, code in (
            CURRENT_RIGHT_COLUMNS
            if parsed.layout_version == PersonnelSourceRevision.LayoutVersion.CURRENT_28_COLUMNS
            else LEGACY_RIGHT_COLUMNS
        )
    }
    missing = sorted(expected_codes - set(right_definitions))
    if missing:
        raise ValidationError("Не найдены виды оперативных прав: " + ", ".join(missing))

    revision = PersonnelSourceRevision.objects.create(
        organization=employee.organization,
        data_profile=data_profile,
        uploaded_by=employee,
        source_reference=_normalize_space(source_reference) or "Источник работников и предоставленных прав",
        effective_from=effective_from,
        original_filename=getattr(uploaded_file, "name", "personnel-source.zip"),
        file_size=len(data),
        file_sha256=digest,
        sheet_name=parsed.sheet_name,
        layout_version=parsed.layout_version,
        document_date=parsed.document_date,
        document_number=parsed.document_number,
        manifest={**parsed.manifest, "source_sha256": digest, "source_size": len(data)},
        footnotes=parsed.footnotes,
        total_people=len(parsed.rows),
        total_authority_cells=sum(len(row.authority_cells) for row in parsed.rows),
    )

    source_name_counts = Counter(_row_name_token(row) for row in parsed.rows)
    ready = review = blocked = publishable = ambiguous = 0
    for parsed_row in parsed.rows:
        matched_employee, match_kind = _match_employee(employee.organization, parsed_row)
        issues = list(parsed_row.issues)
        row_status = parsed_row.review_status
        if source_name_counts[_row_name_token(parsed_row)] > 1:
            issues.append("ФИО повторяется в источнике; требуется ручная идентификация работника.")
            matched_employee = None
            match_kind = PersonnelSourceRow.MatchKind.REVIEW_REQUIRED
            row_status = PersonnelSourceRow.ReviewStatus.REVIEW_REQUIRED
        if match_kind == PersonnelSourceRow.MatchKind.REVIEW_REQUIRED:
            issues.append("Найдено несколько сотрудников с одинаковым ФИО.")
            row_status = PersonnelSourceRow.ReviewStatus.REVIEW_REQUIRED
        stored_row = PersonnelSourceRow.objects.create(
            source_revision=revision,
            source_row_number=parsed_row.source_row_number,
            source_sequence=parsed_row.source_sequence,
            full_name_raw=parsed_row.full_name_raw,
            last_name=parsed_row.last_name,
            first_name=parsed_row.first_name,
            middle_name=parsed_row.middle_name,
            position_raw=parsed_row.position_raw,
            division_raw=parsed_row.division_raw,
            personnel_category_raw=parsed_row.personnel_category_raw,
            electrical_safety_raw=parsed_row.electrical_safety_raw,
            electrical_safety_group=parsed_row.electrical_safety_group,
            voltage_scope=parsed_row.voltage_scope,
            installation_scope_raw=parsed_row.installation_scope_raw,
            rza_category_raw=parsed_row.rza_category_raw,
            matched_employee=matched_employee,
            match_kind=match_kind,
            review_status=row_status,
            issues=issues,
            fingerprint=parsed_row.fingerprint,
        )
        for parsed_cell in parsed_row.authority_cells:
            PersonnelAuthorityCell.objects.create(
                person_row=stored_row,
                right_definition=right_definitions[parsed_cell.right_code],
                source_column=parsed_cell.source_column,
                source_header=parsed_cell.source_header,
                raw_marker=parsed_cell.raw_marker,
                grant_state=parsed_cell.grant_state,
                qualifier=parsed_cell.qualifier,
                footnote_numbers=list(parsed_cell.footnote_numbers),
                equipment_groups=list(parsed_cell.equipment_groups),
                issues=list(parsed_cell.issues),
                is_publishable=parsed_cell.is_publishable,
            )
            publishable += int(parsed_cell.is_publishable)
            ambiguous += int(
                parsed_cell.grant_state == PersonnelAuthorityCell.GrantState.AMBIGUOUS
            )
        if row_status == PersonnelSourceRow.ReviewStatus.READY:
            ready += 1
        elif row_status == PersonnelSourceRow.ReviewStatus.BLOCKED:
            blocked += 1
        else:
            review += 1

    revision.ready_rows = ready
    revision.review_rows = review
    revision.blocked_rows = blocked
    revision.publishable_grants = publishable
    revision.ambiguous_cells = ambiguous
    revision.save(
        update_fields=(
            "ready_rows",
            "review_rows",
            "blocked_rows",
            "publishable_grants",
            "ambiguous_cells",
            "updated_at",
        )
    )
    return revision


def build_personnel_publication_preview(
    revision: PersonnelSourceRevision,
) -> PersonnelPublicationPreview:
    rows = tuple(
        revision.person_rows.exclude(
            review_status__in={
                PersonnelSourceRow.ReviewStatus.BLOCKED,
                PersonnelSourceRow.ReviewStatus.EXCLUDED,
                PersonnelSourceRow.ReviewStatus.PUBLISHED,
            }
        )
        .exclude(match_kind=PersonnelSourceRow.MatchKind.REVIEW_REQUIRED)
        .exclude(division_raw="")
        .prefetch_related("authority_cells__right_definition")
        .select_related("matched_employee")
        .order_by("source_row_number")
    )
    payload_rows: list[dict[str, object]] = []
    grant_count = 0
    ambiguous_count = 0
    for row in rows:
        grants = []
        for cell in row.authority_cells.all():
            if cell.grant_state == PersonnelAuthorityCell.GrantState.AMBIGUOUS:
                ambiguous_count += 1
            if not cell.is_publishable:
                continue
            grant_count += 1
            grants.append(
                {
                    "right_code": cell.right_definition.code,
                    "marker": cell.raw_marker,
                    "qualifier": cell.qualifier,
                    "footnotes": cell.footnote_numbers,
                    "equipment_groups": cell.equipment_groups,
                }
            )
        payload_rows.append(
            {
                "source_row": row.source_row_number,
                "source_sequence": row.source_sequence,
                "name": {
                    "last_name": row.last_name,
                    "first_name": row.first_name,
                    "middle_name": row.middle_name,
                },
                "division": row.division_raw,
                "position": row.position_raw,
                "qualification": {
                    "personnel_category": row.personnel_category_raw,
                    "electrical_safety_group": row.electrical_safety_group,
                    "voltage_scope": row.voltage_scope,
                    "electrical_installation_scope": row.installation_scope_raw,
                },
                "matched_employee_public_id": (
                    str(row.matched_employee.public_id) if row.matched_employee_id else None
                ),
                "grants": grants,
            }
        )
    payload = {
        "schema": PERSONNEL_PUBLICATION_SCHEMA,
        "source": {
            "revision_public_id": str(revision.public_id),
            "filename": revision.original_filename,
            "sha256": revision.file_sha256,
            "effective_from": revision.effective_from.isoformat(),
            "document_date": revision.document_date.isoformat() if revision.document_date else None,
            "document_number": revision.document_number,
            "layout_version": revision.layout_version,
            "data_profile": revision.data_profile.code,
        },
        "rows": payload_rows,
    }
    canonical, digest = _sha256_payload(payload)
    summary = {
        "selected_people": len(rows),
        "publishable_grants": grant_count,
        "ambiguous_cells_left_in_staging": ambiguous_count,
        "blocked_people": revision.blocked_rows,
        "review_people": revision.review_rows,
    }
    return PersonnelPublicationPreview(
        source_revision=revision,
        rows=rows,
        canonical_json=canonical,
        digest=digest,
        summary=summary,
    )


def _stable_code(prefix: str, value: str, length: int = 18) -> str:
    digest = hashlib.sha256(_comparison_token(value).encode("utf-8")).hexdigest()[:length]
    return f"{prefix}-{digest}".upper()


def _division_for_row(revision: PersonnelSourceRevision, row: PersonnelSourceRow) -> Division:
    name = _normalize_space(row.division_raw)
    if not name:
        raise ValidationError(
            f"Строка {row.source_row_number}: без подразделения публикация сотрудника невозможна."
        )
    name_token = _comparison_token(name)
    existing = next(
        (
            item
            for item in Division.objects.filter(organization=revision.organization).order_by("id")
            if _comparison_token(item.name) == name_token
        ),
        None,
    )
    if existing is not None:
        return existing
    return Division.objects.create(
        organization=revision.organization,
        code=_stable_code("DIV", name),
        name=name,
        is_active=True,
    )


def _position_for_row(revision: PersonnelSourceRevision, row: PersonnelSourceRow) -> Position:
    name = _normalize_space(row.position_raw)
    name_token = _comparison_token(name)
    existing = next(
        (
            item
            for item in Position.objects.filter(organization=revision.organization).order_by("id")
            if _comparison_token(item.name) == name_token
        ),
        None,
    )
    if existing is not None:
        return existing
    operational_tokens = ("смен", "дежур", "диспетчер", "оператив")
    is_operational = any(token in _comparison_token(name) for token in operational_tokens)
    return Position.objects.create(
        organization=revision.organization,
        code=_stable_code("POS", name),
        name=name,
        is_operational=is_operational,
        is_active=True,
    )


def _employee_for_row(
    revision: PersonnelSourceRevision,
    row: PersonnelSourceRow,
    division: Division,
    position: Position,
) -> tuple[Employee, bool]:
    if row.matched_employee_id:
        employee = row.matched_employee
        created = False
    else:
        target = _row_name_token(row)
        matches = [
            employee
            for employee in Employee.objects.filter(organization=revision.organization).order_by("id")
            if _employee_name_token(employee) == target
        ][:2]
        if len(matches) > 1:
            raise ValidationError(
                f"Строка {row.source_row_number}: ФИО совпадает с несколькими сотрудниками."
            )
        if matches:
            employee = matches[0]
            created = False
        else:
            personnel_number = _stable_code(
                "IMP",
                f"{revision.organization_id}|{revision.file_sha256}|{row.source_row_number}",
                20,
            )
            employee = Employee(
                organization=revision.organization,
                division=division,
                position=position,
                personnel_number=personnel_number,
                last_name=row.last_name,
                first_name=row.first_name,
                middle_name=row.middle_name,
                employment_start=revision.effective_from,
                is_active=True,
            )
            employee.full_clean()
            employee.save()
            created = True
    changed_fields: list[str] = []
    if employee.division_id != division.pk:
        employee.division = division
        changed_fields.append("division")
    if employee.position_id != position.pk:
        employee.position = position
        changed_fields.append("position")
    if changed_fields:
        employee.full_clean()
        employee.save(update_fields=tuple(changed_fields))
    return employee, created


@transaction.atomic
def publish_personnel_revision(
    *,
    revision: PersonnelSourceRevision,
    actor: Employee,
    user,
    password: str,
    expected_digest: str,
) -> PersonnelPublication:
    _require_development_database()
    if user is None or not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Для публикации требуется действующая персональная сессия.")
    if actor.user_id != getattr(user, "pk", None):
        raise PermissionDenied("Учётная запись не соответствует публикующему сотруднику.")
    if not can_publish_import(user):
        raise PermissionDenied(
            "Для публикации требуется прямая действующая роль «Администратор справочников»."
        )
    if not password or not user.check_password(password):
        raise ValidationError({"password": "Неверный текущий пароль."})

    locked = PersonnelSourceRevision.objects.select_for_update(of=("self",)).select_related(
        "organization", "data_profile", "uploaded_by", "published_by"
    ).get(pk=revision.pk)
    if locked.status != PersonnelSourceRevision.Status.STAGED:
        raise ValidationError("Опубликовать можно только подготовленную редакцию.")
    if hasattr(locked, "publication"):
        raise ValidationError("Для этой редакции уже создан снимок публикации.")
    preview = build_personnel_publication_preview(locked)
    if not expected_digest or expected_digest != preview.digest:
        raise ValidationError("Состав публикации изменился. Обновите страницу и повторите проверку.")
    if not preview.rows:
        raise ValidationError("Нет строк, пригодных для частичной публикации.")

    definitions = {item.code: item for item in OperationalRightDefinition.objects.all()}
    created_people = reused_people = qualification_count = right_count = 0
    published_row_ids: list[int] = []
    for row in preview.rows:
        if not row.division_raw:
            continue
        division = _division_for_row(locked, row)
        position = _position_for_row(locked, row)
        employee, created = _employee_for_row(locked, row, division, position)
        created_people += int(created)
        reused_people += int(not created)
        _qualification, qualification_created = EmployeeQualification.objects.get_or_create(
            employee=employee,
            source_file_sha256=locked.file_sha256,
            source_row_number=row.source_row_number,
            defaults={
                "personnel_category": row.personnel_category_raw or "НЕ УКАЗАНА",
                "electrical_safety_group": row.electrical_safety_group,
                "voltage_scope": row.voltage_scope,
                "electrical_installation_scope": row.installation_scope_raw,
                "valid_from": locked.effective_from,
                "is_active": True,
                "source_reference": locked.source_reference,
            },
        )
        qualification_count += int(qualification_created)
        for cell in row.authority_cells.filter(is_publishable=True).select_related("right_definition"):
            right_definition = definitions[cell.right_definition.code]
            _grant, created_grant = EmployeeOperationalRight.objects.get_or_create(
                employee=employee,
                right_definition=right_definition,
                source_file_sha256=locked.file_sha256,
                source_row_number=row.source_row_number,
                defaults={
                    "qualifier": cell.qualifier,
                    "scope_text": row.installation_scope_raw,
                    "source_marker": cell.raw_marker,
                    "source_reference": locked.source_reference,
                    "valid_from": locked.effective_from,
                    "is_active": True,
                },
            )
            right_count += int(created_grant)
        row.published_employee = employee
        row.review_status = PersonnelSourceRow.ReviewStatus.PUBLISHED
        row.save(update_fields=("published_employee", "review_status"))
        published_row_ids.append(row.pk)

    if not published_row_ids:
        raise ValidationError(
            "Ни одна строка не опубликована: требуется устранить отсутствие подразделений."
        )

    unresolved_rows = locked.person_rows.exclude(
        review_status=PersonnelSourceRow.ReviewStatus.PUBLISHED
    ).count()
    unresolved_cells = PersonnelAuthorityCell.objects.filter(
        person_row__source_revision=locked,
        grant_state=PersonnelAuthorityCell.GrantState.AMBIGUOUS,
    ).count()
    result_summary = {
        "created_people": created_people,
        "reused_people": reused_people,
        "created_qualifications": qualification_count,
        "created_rights": right_count,
        "unresolved_rows": unresolved_rows,
        "ambiguous_cells_not_published": unresolved_cells,
        "withdrawals_automatically_applied": 0,
    }
    publication = PersonnelPublication.objects.create(
        source_revision=locked,
        actor=actor,
        schema_version=PERSONNEL_PUBLICATION_SCHEMA,
        canonical_json=preview.canonical_json,
        digest=preview.digest,
        result_summary=result_summary,
    )
    locked.status = (
        PersonnelSourceRevision.Status.PARTIALLY_PUBLISHED
        if unresolved_rows or unresolved_cells
        else PersonnelSourceRevision.Status.PUBLISHED
    )
    locked.publication_digest = publication.digest
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
    return publication


@transaction.atomic
def discard_personnel_revision(
    *, revision: PersonnelSourceRevision, employee: Employee
) -> PersonnelSourceRevision:
    locked = PersonnelSourceRevision.objects.select_for_update().get(pk=revision.pk)
    if locked.organization_id != employee.organization_id:
        raise PermissionDenied("Редакция относится к другой организации.")
    if locked.status in {
        PersonnelSourceRevision.Status.PUBLISHED,
        PersonnelSourceRevision.Status.PARTIALLY_PUBLISHED,
    }:
        raise ValidationError("Опубликованную редакцию нельзя убрать из рабочего списка.")
    locked.status = PersonnelSourceRevision.Status.DISCARDED
    locked.discarded_at = timezone.now()
    locked.save(update_fields=("status", "discarded_at", "updated_at"))
    return locked
