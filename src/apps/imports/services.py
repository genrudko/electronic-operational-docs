from __future__ import annotations

import csv
import hashlib
import io
import json
import posixpath
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from apps.organizations.models import Employee, RoleAssignment

from .models import (
    ImportBatch,
    ImportColumn,
    ImportEvent,
    ImportPublication,
    ImportPublicationRow,
    ImportRow,
)

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_DATA_ROWS = 5000
MAX_COLUMNS = 100
MAX_XLSX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024

SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELATIONSHIP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_RELATIONSHIP_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

HEADER_ALIASES = {
    "код": "code",
    "системный код": "code",
    "стабильный код": "code",
    "code": "code",
    "наименование": "name",
    "название": "name",
    "диспетчерское наименование": "dispatcher_name",
    "name": "name",
    "тип": "type",
    "вид": "type",
    "вид оборудования": "type",
    "type": "type",
    "энергообъект": "site",
    "объект": "site",
    "site": "site",
    "статус": "status",
    "состояние": "status",
    "status": "status",
    "подразделение": "division",
    "должность": "position",
    "табельный номер": "personnel_number",
    "фамилия": "last_name",
    "имя": "first_name",
    "отчество": "middle_name",
    "дата приема": "employment_start",
    "дата приёма": "employment_start",
    "дата ввода": "commissioned_on",
    "класс напряжения": "voltage_level",
    "управление или ведение": "relation_kind",
    "вид отношения": "relation_kind",
    "субъект": "subject",
    "уровень": "level",
    "действует с": "effective_from",
    "действует по": "effective_until",
    "информационное ведение": "information_only",
    "ключ": "key",
    "примечание": "note",
}


class ImportParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedTable:
    rows: list[list[str]]
    row_widths: list[int]
    source_format: str
    sheet_name: str = ""
    encoding: str = ""
    delimiter: str = ""
    formula_cells: frozenset[tuple[int, int]] = frozenset()
    normalized_cells: dict[tuple[int, int], str] = field(default_factory=dict)


@dataclass(frozen=True)
class XlsxStyleCatalog:
    custom_formats: dict[int, str] = field(default_factory=dict)
    cell_format_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class ImportFieldSpec:
    key: str
    label: str
    required: bool = False
    kind: str = "text"
    max_length: int = 1000
    choices: tuple[tuple[str, str], ...] = ()
    aliases: tuple[str, ...] = ()


EQUIPMENT_STATUS_CHOICES = (
    ("ACTIVE", "В работе"),
    ("RESERVE", "Резерв"),
    ("OUT_OF_SERVICE", "Выведено из работы"),
    ("DECOMMISSIONED", "Выведено из эксплуатации"),
    ("PROJECT", "Проектное оборудование"),
)
RELATION_KIND_CHOICES = (
    ("MANAGEMENT", "Оперативное управление"),
    ("SUPERVISION", "Оперативное ведение"),
)

REGISTRY_FIELD_SPECS: dict[str, tuple[ImportFieldSpec, ...]] = {
    ImportBatch.TargetRegistry.ORGANIZATION: (
        ImportFieldSpec(
            "personnel_number",
            "Табельный номер",
            required=True,
            max_length=64,
            aliases=("табельный номер", "personnel number", "personnel_number"),
        ),
        ImportFieldSpec(
            "last_name",
            "Фамилия",
            required=True,
            max_length=150,
            aliases=("фамилия", "last name", "last_name"),
        ),
        ImportFieldSpec(
            "first_name",
            "Имя",
            required=True,
            max_length=150,
            aliases=("имя", "first name", "first_name"),
        ),
        ImportFieldSpec(
            "middle_name",
            "Отчество",
            max_length=150,
            aliases=("отчество", "middle name", "middle_name"),
        ),
        ImportFieldSpec(
            "division",
            "Подразделение",
            required=True,
            max_length=255,
            aliases=("подразделение", "division"),
        ),
        ImportFieldSpec(
            "position",
            "Должность",
            required=True,
            max_length=255,
            aliases=("должность", "position"),
        ),
        ImportFieldSpec(
            "employment_start",
            "Дата начала работы",
            kind="date",
            max_length=10,
            aliases=("дата приема", "дата приёма", "дата начала работы"),
        ),
        ImportFieldSpec(
            "is_active",
            "Действующий сотрудник",
            kind="boolean",
            max_length=3,
            aliases=("действующий", "активен", "is active", "is_active"),
        ),
    ),
    ImportBatch.TargetRegistry.EQUIPMENT: (
        ImportFieldSpec(
            "code",
            "Стабильный код",
            required=True,
            kind="code",
            max_length=96,
            aliases=("код", "системный код", "стабильный код", "code"),
        ),
        ImportFieldSpec(
            "technical_name",
            "Техническое наименование",
            required=True,
            max_length=500,
            aliases=("наименование", "название", "техническое наименование", "name"),
        ),
        ImportFieldSpec(
            "dispatcher_name",
            "Диспетчерское наименование",
            max_length=1000,
            aliases=("диспетчерское наименование",),
        ),
        ImportFieldSpec(
            "type",
            "Вид оборудования",
            required=True,
            max_length=255,
            aliases=("тип", "вид", "вид оборудования", "type"),
        ),
        ImportFieldSpec(
            "site",
            "Энергообъект",
            required=True,
            max_length=500,
            aliases=("энергообъект", "объект", "site"),
        ),
        ImportFieldSpec(
            "status",
            "Состояние",
            kind="choice",
            max_length=24,
            choices=EQUIPMENT_STATUS_CHOICES,
            aliases=("статус", "состояние", "status"),
        ),
        ImportFieldSpec(
            "voltage_level",
            "Класс напряжения",
            max_length=64,
            aliases=("класс напряжения", "напряжение"),
        ),
        ImportFieldSpec(
            "commissioned_on",
            "Дата ввода в эксплуатацию",
            kind="date",
            max_length=10,
            aliases=("дата ввода", "введено в эксплуатацию"),
        ),
    ),
    ImportBatch.TargetRegistry.DISPATCHING: (
        ImportFieldSpec(
            "equipment_code",
            "Код оборудования",
            required=True,
            kind="code",
            max_length=96,
            aliases=("код оборудования", "оборудование", "equipment code", "code"),
        ),
        ImportFieldSpec(
            "relation_kind",
            "Управление или ведение",
            required=True,
            kind="choice",
            max_length=16,
            choices=RELATION_KIND_CHOICES,
            aliases=("управление или ведение", "вид отношения", "relation kind"),
        ),
        ImportFieldSpec(
            "subject",
            "Субъект",
            required=True,
            max_length=1000,
            aliases=("субъект", "subject"),
        ),
        ImportFieldSpec(
            "level",
            "Уровень",
            required=True,
            max_length=500,
            aliases=("уровень", "level"),
        ),
        ImportFieldSpec(
            "effective_from",
            "Действует с",
            kind="date",
            max_length=10,
            aliases=("действует с", "effective from"),
        ),
        ImportFieldSpec(
            "effective_until",
            "Действует по",
            kind="date",
            max_length=10,
            aliases=("действует по", "effective until"),
        ),
        ImportFieldSpec(
            "information_only",
            "Только информационное ведение",
            kind="boolean",
            max_length=3,
            aliases=("информационное ведение", "только информация"),
        ),
        ImportFieldSpec(
            "basis_reference",
            "Документ-основание",
            max_length=1000,
            aliases=("основание", "документ-основание"),
        ),
    ),
    ImportBatch.TargetRegistry.OTHER: (
        ImportFieldSpec(
            "key",
            "Ключ записи",
            required=True,
            kind="code",
            max_length=128,
            aliases=("ключ", "код", "key", "code"),
        ),
        ImportFieldSpec(
            "name",
            "Наименование",
            required=True,
            max_length=1000,
            aliases=("наименование", "название", "name"),
        ),
        ImportFieldSpec(
            "status",
            "Состояние",
            max_length=255,
            aliases=("статус", "состояние", "status"),
        ),
        ImportFieldSpec(
            "note",
            "Примечание",
            max_length=2000,
            aliases=("примечание", "комментарий", "note"),
        ),
    ),
}


TRUE_VALUES = {"1", "да", "истина", "true", "yes", "y", "on"}
FALSE_VALUES = {"0", "нет", "ложь", "false", "no", "n", "off"}


def require_import_employee(user) -> Employee:
    try:
        employee = user.employee_profile
    except Employee.DoesNotExist as exc:
        raise PermissionDenied(
            "У пользователя нет персональной карточки сотрудника для импорта."
        ) from exc
    if not employee.is_active:
        raise PermissionDenied("Карточка сотрудника неактивна.")
    return employee


def normalize_cell(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.replace("\u00a0", " ").split())


def normalize_header(value: str) -> str:
    return normalize_cell(value).casefold()


def _safe_filename(name: str) -> str:
    filename = Path(name.replace("\\", "/")).name.strip()
    if not filename:
        raise ImportParseError("Не удалось определить имя исходного файла.")
    return filename[:255]


def _read_upload(uploaded_file) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in uploaded_file.chunks():
        total += len(chunk)
        if total > MAX_FILE_SIZE:
            raise ImportParseError("Размер файла превышает 10 МБ.")
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        raise ImportParseError("Файл пуст.")
    return data


def _parse_csv(data: bytes) -> ParsedTable:
    decoded: str | None = None
    encoding = ""
    for candidate in ("utf-8-sig", "cp1251"):
        try:
            decoded = data.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
    if decoded is None:
        raise ImportParseError("CSV должен быть сохранён в UTF-8 или Windows-1251.")
    if "\x00" in decoded:
        raise ImportParseError("CSV содержит нулевые байты и не может быть прочитан.")

    sample = decoded[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if ";" in sample else ","

    reader = csv.reader(io.StringIO(decoded, newline=""), delimiter=delimiter)
    rows: list[list[str]] = []
    widths: list[int] = []
    for number, row in enumerate(reader, start=1):
        if number > MAX_DATA_ROWS + 1:
            raise ImportParseError(
                f"Файл содержит больше {MAX_DATA_ROWS} строк данных."
            )
        if len(row) > MAX_COLUMNS:
            raise ImportParseError(f"Файл содержит больше {MAX_COLUMNS} колонок.")
        values = [str(value) for value in row]
        rows.append(values)
        widths.append(len(values))

    return ParsedTable(
        rows=rows,
        row_widths=widths,
        source_format=ImportBatch.SourceFormat.CSV,
        encoding=encoding,
        delimiter=delimiter,
    )


def _xlsx_column_index(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference.upper())
    if match is None:
        raise ImportParseError(f"Некорректная ссылка ячейки XLSX: {reference!r}.")
    result = 0
    for char in match.group(1):
        result = result * 26 + ord(char) - ord("A") + 1
    return result - 1



def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    path = "xl/sharedStrings.xml"
    if path not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read(path))
    strings: list[str] = []
    for item in root.findall(f"{{{SPREADSHEET_NS}}}si"):
        strings.append(
            "".join(
                node.text or ""
                for node in item.iter(f"{{{SPREADSHEET_NS}}}t")
            )
        )
    return strings


XLSX_BUILTIN_DATE_FORMATS = frozenset(
    {
        14,
        15,
        16,
        17,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
    }
)
XLSX_BUILTIN_TIME_FORMATS = frozenset({18, 19, 20, 21, 45, 46, 47})
XLSX_BUILTIN_DATETIME_FORMATS = frozenset({22})
MICROSECONDS_PER_DAY = 86_400_000_000


def _xlsx_style_catalog(archive: zipfile.ZipFile) -> XlsxStyleCatalog:
    path = "xl/styles.xml"
    if path not in archive.namelist():
        return XlsxStyleCatalog()

    root = ElementTree.fromstring(archive.read(path))
    custom_formats: dict[int, str] = {}
    number_formats = root.find(f"{{{SPREADSHEET_NS}}}numFmts")
    if number_formats is not None:
        for item in number_formats.findall(f"{{{SPREADSHEET_NS}}}numFmt"):
            try:
                number_format_id = int(item.attrib.get("numFmtId", ""))
            except ValueError:
                continue
            custom_formats[number_format_id] = item.attrib.get("formatCode", "")

    cell_format_ids: list[int] = []
    cell_formats = root.find(f"{{{SPREADSHEET_NS}}}cellXfs")
    if cell_formats is not None:
        for item in cell_formats.findall(f"{{{SPREADSHEET_NS}}}xf"):
            try:
                cell_format_ids.append(int(item.attrib.get("numFmtId", "0")))
            except ValueError:
                cell_format_ids.append(0)

    return XlsxStyleCatalog(
        custom_formats=custom_formats,
        cell_format_ids=tuple(cell_format_ids),
    )


def _xlsx_date_system_1904(workbook: ElementTree.Element) -> bool:
    properties = workbook.find(f"{{{SPREADSHEET_NS}}}workbookPr")
    if properties is None:
        return False
    return properties.attrib.get("date1904", "").strip().casefold() in {
        "1",
        "true",
        "yes",
    }


def _xlsx_clean_format_code(format_code: str) -> tuple[str, tuple[str, ...]]:
    lowered = format_code.casefold()
    duration_tokens = tuple(
        token.casefold()
        for token in re.findall(r"\[([hms]+)\]", lowered, flags=re.IGNORECASE)
    )
    lowered = re.sub(r'"(?:[^"]|"")*"', "", lowered)
    lowered = re.sub(r"\\.", "", lowered)
    lowered = re.sub(r"_.", "", lowered)
    lowered = re.sub(r"\*.", "", lowered)
    lowered = re.sub(r"\[[^\]]+\]", "", lowered)
    return lowered, duration_tokens


def _xlsx_temporal_kind(number_format_id: int, format_code: str) -> str:
    if number_format_id in XLSX_BUILTIN_DATETIME_FORMATS:
        return "datetime"
    if number_format_id in XLSX_BUILTIN_DATE_FORMATS:
        return "date"
    if number_format_id in XLSX_BUILTIN_TIME_FORMATS:
        return "time"
    if not format_code:
        return ""

    cleaned, duration_tokens = _xlsx_clean_format_code(format_code)
    has_date = bool(re.search(r"[yd]", cleaned))
    has_time = (
        bool(re.search(r"[hs]", cleaned))
        or bool(duration_tokens)
        or (has_date and "m" in cleaned and ":" in cleaned)
    )
    if has_date and has_time:
        return "datetime"
    if has_date:
        return "date"
    if has_time:
        return "time"
    return ""


def _xlsx_cell_temporal_kind(
    cell: ElementTree.Element,
    styles: XlsxStyleCatalog,
) -> str:
    try:
        style_index = int(cell.attrib.get("s", "0"))
    except ValueError:
        return ""
    if style_index < 0 or style_index >= len(styles.cell_format_ids):
        return ""
    number_format_id = styles.cell_format_ids[style_index]
    return _xlsx_temporal_kind(
        number_format_id,
        styles.custom_formats.get(number_format_id, ""),
    )


def _xlsx_serial_datetime(raw: str, *, date_system_1904: bool) -> datetime | None:
    try:
        serial = Decimal(raw)
    except InvalidOperation:
        return None
    if not serial.is_finite() or serial < 0:
        return None

    whole_days = int(serial)
    fraction = serial - Decimal(whole_days)
    if date_system_1904:
        epoch = datetime(1904, 1, 1)
    else:
        if whole_days == 60:
            return None
        epoch = datetime(1899, 12, 31) if whole_days < 60 else datetime(1899, 12, 30)

    microseconds = int(
        (fraction * Decimal(MICROSECONDS_PER_DAY)).to_integral_value()
    )
    return epoch + timedelta(days=whole_days, microseconds=microseconds)


def _xlsx_temporal_values(
    raw: str,
    *,
    kind: str,
    date_system_1904: bool,
) -> tuple[str, str] | None:
    value = _xlsx_serial_datetime(raw, date_system_1904=date_system_1904)
    if value is None:
        return None
    if kind == "date":
        return value.strftime("%d.%m.%Y"), value.date().isoformat()
    if kind == "time":
        clock = time(
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
        )
        display = clock.isoformat(timespec="seconds")
        normalized = clock.isoformat(timespec="microseconds").rstrip("0").rstrip(".")
        return display, normalized
    if kind == "datetime":
        display = value.strftime("%d.%m.%Y %H:%M:%S")
        normalized = value.isoformat(timespec="microseconds").rstrip("0").rstrip(".")
        return display, normalized
    return None


def _xlsx_iso_date_value(raw: str) -> tuple[str, str] | None:
    token = raw.strip()
    if not token:
        return None
    try:
        parsed = datetime.fromisoformat(token.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed_date = date.fromisoformat(token)
        except ValueError:
            return None
        return parsed_date.strftime("%d.%m.%Y"), parsed_date.isoformat()
    if parsed.time() == time.min:
        return parsed.strftime("%d.%m.%Y"), parsed.date().isoformat()
    return (
        parsed.strftime("%d.%m.%Y %H:%M:%S"),
        parsed.isoformat(timespec="microseconds").rstrip("0").rstrip("."),
    )


def _xlsx_cell_value(
    cell: ElementTree.Element,
    shared_strings: list[str],
    styles: XlsxStyleCatalog,
    *,
    date_system_1904: bool,
) -> tuple[str, str | None, bool]:
    formula = cell.find(f"{{{SPREADSHEET_NS}}}f")
    if formula is not None:
        return "=" + (formula.text or ""), None, True

    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        inline = cell.find(f"{{{SPREADSHEET_NS}}}is")
        if inline is None:
            return "", None, False
        return (
            "".join(
                node.text or ""
                for node in inline.iter(f"{{{SPREADSHEET_NS}}}t")
            ),
            None,
            False,
        )

    value_node = cell.find(f"{{{SPREADSHEET_NS}}}v")
    raw = "" if value_node is None else value_node.text or ""
    if cell_type == "s":
        try:
            return shared_strings[int(raw)], None, False
        except (ValueError, IndexError) as exc:
            raise ImportParseError(
                "XLSX содержит некорректную ссылку на общую строку."
            ) from exc
    if cell_type == "b":
        if raw == "1":
            return "ИСТИНА", "Да", False
        return "ЛОЖЬ", "Нет", False
    if cell_type == "d":
        converted = _xlsx_iso_date_value(raw)
        if converted is not None:
            return converted[0], converted[1], False
        return raw, None, False
    if cell_type in {"", "n"}:
        temporal_kind = _xlsx_cell_temporal_kind(cell, styles)
        if temporal_kind:
            converted = _xlsx_temporal_values(
                raw,
                kind=temporal_kind,
                date_system_1904=date_system_1904,
            )
            if converted is not None:
                return converted[0], converted[1], False
    return raw, None, False


def _xlsx_sheet_path(target: str) -> str:
    cleaned = target.replace("\\", "/").lstrip("/")
    if cleaned.startswith("xl/"):
        return posixpath.normpath(cleaned)
    return posixpath.normpath(posixpath.join("xl", cleaned))


def _parse_xlsx(data: bytes) -> ParsedTable:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ImportParseError("Файл XLSX повреждён или не является XLSX.") from exc

    with archive:
        infos = archive.infolist()
        if any(info.flag_bits & 0x1 for info in infos):
            raise ImportParseError("Зашифрованные XLSX-файлы не поддерживаются.")
        if sum(info.file_size for info in infos) > MAX_XLSX_UNCOMPRESSED_SIZE:
            raise ImportParseError("Распакованный XLSX превышает безопасный лимит 50 МБ.")

        required = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
        if not required.issubset(archive.namelist()):
            raise ImportParseError("В XLSX отсутствует структура рабочей книги.")

        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            relationship.attrib["Id"]: relationship.attrib["Target"]
            for relationship in relationships.findall(
                f"{{{PACKAGE_RELATIONSHIP_NS}}}Relationship"
            )
        }
        shared_strings = _xlsx_shared_strings(archive)
        styles = _xlsx_style_catalog(archive)
        date_system_1904 = _xlsx_date_system_1904(workbook)

        sheets = workbook.find(f"{{{SPREADSHEET_NS}}}sheets")
        if sheets is None:
            raise ImportParseError("В XLSX не найдено ни одного листа.")

        for sheet in sheets.findall(f"{{{SPREADSHEET_NS}}}sheet"):
            relationship_id = sheet.attrib.get(f"{{{RELATIONSHIP_NS}}}id", "")
            target = targets.get(relationship_id)
            if not target:
                continue
            sheet_path = _xlsx_sheet_path(target)
            if sheet_path not in archive.namelist():
                continue

            root = ElementTree.fromstring(archive.read(sheet_path))
            sheet_data = root.find(f"{{{SPREADSHEET_NS}}}sheetData")
            if sheet_data is None:
                continue

            rows: list[list[str]] = []
            widths: list[int] = []
            formula_cells: set[tuple[int, int]] = set()
            normalized_cells: dict[tuple[int, int], str] = {}
            for source_row_index, row_node in enumerate(
                sheet_data.findall(f"{{{SPREADSHEET_NS}}}row"),
                start=1,
            ):
                if source_row_index > MAX_DATA_ROWS + 1:
                    raise ImportParseError(
                        f"Файл содержит больше {MAX_DATA_ROWS} строк данных."
                    )
                row_values: list[str] = []
                for cell in row_node.findall(f"{{{SPREADSHEET_NS}}}c"):
                    reference = cell.attrib.get("r", "")
                    column_index = _xlsx_column_index(reference)
                    if column_index >= MAX_COLUMNS:
                        raise ImportParseError(
                            f"Файл содержит больше {MAX_COLUMNS} колонок."
                        )
                    while len(row_values) <= column_index:
                        row_values.append("")
                    value, normalized_value, is_formula = _xlsx_cell_value(
                        cell,
                        shared_strings,
                        styles,
                        date_system_1904=date_system_1904,
                    )
                    row_values[column_index] = value
                    if normalized_value is not None:
                        normalized_cells[(source_row_index, column_index)] = (
                            normalized_value
                        )
                    if is_formula:
                        formula_cells.add((source_row_index, column_index))
                rows.append(row_values)
                widths.append(len(row_values))

            if rows and any(any(value != "" for value in row) for row in rows):
                return ParsedTable(
                    rows=rows,
                    row_widths=widths,
                    source_format=ImportBatch.SourceFormat.XLSX,
                    sheet_name=sheet.attrib.get("name", "")[:255],
                    formula_cells=frozenset(formula_cells),
                    normalized_cells=normalized_cells,
                )

    raise ImportParseError("В XLSX не найден лист с данными.")


def parse_tabular_file(data: bytes, filename: str) -> ParsedTable:
    extension = Path(filename).suffix.lower()
    if extension == ".csv":
        parsed = _parse_csv(data)
    elif extension == ".xlsx":
        parsed = _parse_xlsx(data)
    else:
        raise ImportParseError("Допустимы только файлы CSV и XLSX.")

    if not parsed.rows:
        raise ImportParseError("В файле нет строк.")
    if not any(any(normalize_cell(value) for value in row) for row in parsed.rows):
        raise ImportParseError("В файле нет данных.")
    return parsed


def registry_field_specs(target_registry: str) -> tuple[ImportFieldSpec, ...]:
    try:
        return REGISTRY_FIELD_SPECS[target_registry]
    except KeyError as exc:
        raise ValidationError("Неизвестное назначение импорта.") from exc


def _field_spec_map(target_registry: str) -> dict[str, ImportFieldSpec]:
    return {spec.key: spec for spec in registry_field_specs(target_registry)}


def suggest_column_mapping(target_registry: str, normalized_name: str) -> str:
    header = normalize_header(normalized_name)
    specs = registry_field_specs(target_registry)
    for spec in specs:
        aliases = {normalize_header(alias) for alias in spec.aliases}
        aliases.add(normalize_header(spec.label))
        if header in aliases:
            return spec.key

    recognized = HEADER_ALIASES.get(header, "")
    translations = {
        ImportBatch.TargetRegistry.ORGANIZATION: {
            "personnel_number": "personnel_number",
            "division": "division",
            "position": "position",
            "last_name": "last_name",
            "first_name": "first_name",
            "middle_name": "middle_name",
            "employment_start": "employment_start",
        },
        ImportBatch.TargetRegistry.EQUIPMENT: {
            "code": "code",
            "name": "technical_name",
            "dispatcher_name": "dispatcher_name",
            "type": "type",
            "site": "site",
            "status": "status",
            "voltage_level": "voltage_level",
            "commissioned_on": "commissioned_on",
        },
        ImportBatch.TargetRegistry.DISPATCHING: {
            "code": "equipment_code",
            "relation_kind": "relation_kind",
            "subject": "subject",
            "level": "level",
            "effective_from": "effective_from",
            "effective_until": "effective_until",
            "information_only": "information_only",
        },
        ImportBatch.TargetRegistry.OTHER: {
            "code": "key",
            "name": "name",
            "status": "status",
            "note": "note",
        },
    }
    return translations.get(target_registry, {}).get(recognized, "")


def _column_payloads(
    parsed: ParsedTable,
    width: int,
    target_registry: str,
) -> list[dict[str, object]]:
    header = list(parsed.rows[0])
    header.extend("" for _ in range(width - len(header)))
    normalized_headers = [normalize_header(value) for value in header]
    duplicate_names = {
        value
        for value in normalized_headers
        if value and normalized_headers.count(value) > 1
    }

    payloads: list[dict[str, object]] = []
    used_suggestions: set[str] = set()
    for index, source_name in enumerate(header):
        if len(source_name) > 1000:
            raise ImportParseError(
                f"Заголовок колонки {index + 1} длиннее 1000 символов."
            )
        normalized_name = normalized_headers[index]
        issues: list[str] = []
        if not normalized_name:
            issues.append("Пустой заголовок колонки.")
            normalized_name = f"колонка {index + 1}"
        if normalized_headers[index] in duplicate_names:
            issues.append("Заголовок повторяется.")
        mapped_key = suggest_column_mapping(target_registry, normalized_name)
        if mapped_key in used_suggestions:
            mapped_key = ""
            issues.append("Автоматическое сопоставление неоднозначно.")
        if mapped_key:
            used_suggestions.add(mapped_key)
        payloads.append(
            {
                "position": index + 1,
                "source_name": source_name,
                "normalized_name": normalized_name,
                "recognized_key": HEADER_ALIASES.get(normalized_headers[index], ""),
                "mapped_key": mapped_key,
                "mapping_origin": ImportColumn.MappingOrigin.AUTO,
                "needs_review": bool(issues),
                "issues": issues,
            }
        )
    return payloads


def _row_payloads(
    parsed: ParsedTable,
    width: int,
    column_payloads: list[dict[str, object]],
) -> list[dict[str, object]]:
    recognized_columns = sum(
        1 for column in column_payloads if column["recognized_key"]
    )
    headers_need_review = any(column["needs_review"] for column in column_payloads)
    payloads: list[dict[str, object]] = []
    fingerprints: dict[str, list[int]] = {}

    for offset, source_row in enumerate(parsed.rows[1:], start=2):
        source_values = list(source_row)
        original_width = parsed.row_widths[offset - 1]
        source_values.extend("" for _ in range(width - len(source_values)))
        normalized_values = [
            normalize_cell(
                parsed.normalized_cells.get((offset, column_index), value)
            )
            for column_index, value in enumerate(source_values)
        ]
        issues: list[str] = []

        if not any(normalized_values):
            status = ImportRow.Status.REJECTED
            issues.append("Пустая строка.")
        else:
            status = (
                ImportRow.Status.RECOGNIZED
                if recognized_columns >= 2
                else ImportRow.Status.NEW
            )
            if original_width != width:
                status = ImportRow.Status.REVIEW
                issues.append("Количество значений отличается от структуры заголовков.")
            if headers_need_review:
                status = ImportRow.Status.REVIEW
                issues.append("Структура заголовков требует проверки.")
            if any(
                (offset, column_index) in parsed.formula_cells
                for column_index in range(width)
            ):
                status = ImportRow.Status.REVIEW
                issues.append(
                    "Формула сохранена как текст и не выполнялась системой."
                )
            elif any(
                value.lstrip().startswith(("=", "+", "@"))
                for value in source_values
                if value
            ):
                status = ImportRow.Status.REVIEW
                issues.append(
                    "Значение похоже на формулу и сохранено только как текст."
                )

        fingerprint = hashlib.sha256(
            json.dumps(
                normalized_values,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        payload = {
            "row_number": offset,
            "source_values": source_values,
            "normalized_values": normalized_values,
            "status": status,
            "issues": issues,
            "fingerprint": fingerprint,
        }
        payloads.append(payload)
        if status != ImportRow.Status.REJECTED:
            fingerprints.setdefault(fingerprint, []).append(len(payloads) - 1)

    for indexes in fingerprints.values():
        if len(indexes) < 2:
            continue
        for index in indexes:
            payloads[index]["status"] = ImportRow.Status.CONFLICT
            payloads[index]["issues"].append(
                "Полный дубль другой строки в этом файле."
            )

    return payloads


def _status_counts(row_payloads: list[dict[str, object]]) -> dict[str, int]:
    counts = {choice: 0 for choice, _label in ImportRow.Status.choices}
    for payload in row_payloads:
        counts[str(payload["status"])] += 1
    return counts


@transaction.atomic
def create_import_batch(
    *,
    uploaded_file,
    target_registry: str,
    employee: Employee,
) -> ImportBatch:
    filename = _safe_filename(uploaded_file.name)
    data = _read_upload(uploaded_file)
    digest = hashlib.sha256(data).hexdigest()
    extension = Path(filename).suffix.lower()
    if extension not in {".csv", ".xlsx"}:
        raise ImportParseError("Допустимы только файлы CSV и XLSX.")
    source_format = (
        ImportBatch.SourceFormat.CSV
        if extension == ".csv"
        else ImportBatch.SourceFormat.XLSX
    )

    batch = ImportBatch.objects.create(
        organization=employee.organization,
        created_by=employee,
        target_registry=target_registry,
        original_filename=filename,
        source_format=source_format,
        file_size=len(data),
        file_sha256=digest,
        status=ImportBatch.Status.PROCESSING,
    )
    ImportEvent.objects.create(
        batch=batch,
        event_type=ImportEvent.EventType.UPLOADED,
        actor=employee,
        details={
            "filename": filename,
            "size": len(data),
            "sha256": digest,
        },
    )

    try:
        parsed = parse_tabular_file(data, filename)
        width = max(len(row) for row in parsed.rows)
        if width == 0:
            raise ImportParseError("В файле не найдено колонок.")
        if width > MAX_COLUMNS:
            raise ImportParseError(f"Файл содержит больше {MAX_COLUMNS} колонок.")

        column_payloads = _column_payloads(parsed, width, target_registry)
        row_payloads = _row_payloads(parsed, width, column_payloads)

        ImportColumn.objects.bulk_create(
            [ImportColumn(batch=batch, **payload) for payload in column_payloads]
        )
        ImportRow.objects.bulk_create(
            [ImportRow(batch=batch, **payload) for payload in row_payloads]
        )

        counts = _status_counts(row_payloads)
        batch.sheet_name = parsed.sheet_name
        batch.source_encoding = parsed.encoding
        batch.source_delimiter = parsed.delimiter
        batch.status = ImportBatch.Status.READY
        batch.total_rows = len(parsed.rows)
        batch.data_rows = len(row_payloads)
        batch.column_count = width
        batch.status_counts = counts
        batch.warning_count = (
            counts[ImportRow.Status.REVIEW]
            + counts[ImportRow.Status.CONFLICT]
            + counts[ImportRow.Status.REJECTED]
        )
        batch.error_message = ""
        batch.save()
        ImportEvent.objects.create(
            batch=batch,
            event_type=ImportEvent.EventType.PARSED,
            actor=employee,
            details={
                "rows": batch.data_rows,
                "columns": batch.column_count,
                "status_counts": counts,
                "source_bytes_retained": False,
            },
        )
    except (ImportParseError, csv.Error, ElementTree.ParseError, zipfile.BadZipFile) as exc:
        batch.status = ImportBatch.Status.FAILED
        batch.error_message = str(exc)
        batch.save(update_fields=("status", "error_message", "updated_at"))
        ImportEvent.objects.create(
            batch=batch,
            event_type=ImportEvent.EventType.FAILED,
            actor=employee,
            details={"error": str(exc)},
        )

    return batch


@transaction.atomic
def discard_import_batch(*, batch: ImportBatch, employee: Employee) -> ImportBatch:
    if batch.organization_id != employee.organization_id:
        raise ValidationError("Загрузка относится к другой организации.")
    if batch.status == ImportBatch.Status.DISCARDED:
        return batch
    batch.mark_discarded()
    ImportEvent.objects.create(
        batch=batch,
        event_type=ImportEvent.EventType.DISCARDED,
        actor=employee,
        details={
            "rows_retained_for_audit": batch.rows.count(),
            "source_bytes_retained": False,
        },
    )
    return batch


def _mapping_payload(batch: ImportBatch) -> dict[int, str]:
    return {column.position: column.mapped_key for column in batch.columns.all()}


def _required_field_keys(target_registry: str) -> set[str]:
    return {spec.key for spec in registry_field_specs(target_registry) if spec.required}


def validate_column_mapping(
    batch: ImportBatch,
    mapping: dict[int, str],
) -> dict[int, str]:
    allowed = _field_spec_map(batch.target_registry)
    columns = list(batch.columns.all())
    expected_positions = {column.position for column in columns}
    if set(mapping) != expected_positions:
        raise ValidationError("Сопоставление должно содержать решение для каждой колонки.")

    cleaned: dict[int, str] = {}
    used: dict[str, int] = {}
    for position, raw_key in mapping.items():
        key = raw_key.strip()
        if key and key not in allowed:
            raise ValidationError(f"Поле {key!r} не относится к выбранному справочнику.")
        if key and key in used:
            raise ValidationError(
                f"Поле «{allowed[key].label}» назначено колонкам {used[key]} и {position}."
            )
        if key:
            used[key] = position
        cleaned[position] = key

    missing = _required_field_keys(batch.target_registry) - set(used)
    if missing:
        labels = ", ".join(allowed[key].label for key in sorted(missing))
        raise ValidationError(f"Не сопоставлены обязательные поля: {labels}.")
    return cleaned


def _normalize_date(value: str) -> str | None:
    for pattern in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    return None


def _choice_aliases(spec: ImportFieldSpec) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for code, label in spec.choices:
        aliases[normalize_header(code)] = code
        aliases[normalize_header(label)] = code
    if spec.key == "status":
        aliases.update(
            {
                "работа": "ACTIVE",
                "в работе": "ACTIVE",
                "резерв": "RESERVE",
                "выведено": "OUT_OF_SERVICE",
                "не в работе": "OUT_OF_SERVICE",
                "демонтировано": "DECOMMISSIONED",
                "проект": "PROJECT",
            }
        )
    if spec.key == "relation_kind":
        aliases.update(
            {
                "управление": "MANAGEMENT",
                "оперативное управление": "MANAGEMENT",
                "ведение": "SUPERVISION",
                "оперативное ведение": "SUPERVISION",
            }
        )
    return aliases


def normalize_field_value(spec: ImportFieldSpec, value: str) -> tuple[str, list[str]]:
    normalized = normalize_cell(value)
    issues: list[str] = []
    if not normalized:
        if spec.required:
            issues.append(f"Поле «{spec.label}» обязательно.")
        return "", issues
    if spec.kind == "code":
        normalized = normalized.upper()
    elif spec.kind == "date":
        parsed = _normalize_date(normalized)
        if parsed is None:
            issues.append(
                f"Поле «{spec.label}» должно быть датой ГГГГ-ММ-ДД или ДД.ММ.ГГГГ."
            )
        else:
            normalized = parsed
    elif spec.kind == "boolean":
        lookup = normalize_header(normalized)
        if lookup in TRUE_VALUES:
            normalized = "Да"
        elif lookup in FALSE_VALUES:
            normalized = "Нет"
        else:
            issues.append(f"Поле «{spec.label}» должно содержать Да или Нет.")
    elif spec.kind == "choice":
        canonical = _choice_aliases(spec).get(normalize_header(normalized))
        if canonical is None:
            labels = ", ".join(label for _code, label in spec.choices)
            issues.append(f"Поле «{spec.label}» допускает значения: {labels}.")
        else:
            normalized = canonical
    if len(normalized) > spec.max_length:
        issues.append(
            f"Поле «{spec.label}» длиннее допустимых {spec.max_length} символов."
        )
    return normalized, issues


def validate_mapped_values(
    target_registry: str,
    values: dict[str, str],
) -> tuple[dict[str, str], list[str]]:
    result: dict[str, str] = {}
    issues: list[str] = []
    for spec in registry_field_specs(target_registry):
        normalized, field_issues = normalize_field_value(spec, str(values.get(spec.key, "")))
        result[spec.key] = normalized
        issues.extend(field_issues)

    if target_registry == ImportBatch.TargetRegistry.DISPATCHING:
        start = result.get("effective_from", "")
        end = result.get("effective_until", "")
        if start and end and end < start:
            issues.append("Дата окончания не может быть раньше даты начала.")
    return result, issues


def _lookup_token(value: str) -> str:
    return normalize_header(value)


def _validation_context(batch: ImportBatch) -> dict[str, object]:
    organization = batch.organization
    if batch.target_registry == ImportBatch.TargetRegistry.ORGANIZATION:
        from apps.organizations.models import Division, Employee, Position

        division_tokens: set[str] = set()
        for item in Division.objects.filter(organization=organization, is_active=True):
            division_tokens.update({_lookup_token(item.code), _lookup_token(item.name)})
        position_tokens: set[str] = set()
        for item in Position.objects.filter(organization=organization, is_active=True):
            position_tokens.update({_lookup_token(item.code), _lookup_token(item.name)})
        return {
            "division_tokens": division_tokens,
            "position_tokens": position_tokens,
            "employee_numbers": {
                _lookup_token(value)
                for value in Employee.objects.filter(organization=organization).values_list(
                    "personnel_number", flat=True
                )
            },
        }

    if batch.target_registry == ImportBatch.TargetRegistry.EQUIPMENT:
        from apps.equipment.models import EnergySite, EquipmentAsset, EquipmentType

        site_tokens: set[str] = set()
        for item in EnergySite.objects.filter(organization=organization, is_active=True):
            site_tokens.update(
                {
                    _lookup_token(item.code),
                    _lookup_token(item.name),
                    _lookup_token(item.short_name),
                }
            )
        type_tokens: set[str] = set()
        for item in EquipmentType.objects.filter(is_active=True):
            type_tokens.update({_lookup_token(item.code), _lookup_token(item.name)})
        return {
            "site_tokens": site_tokens,
            "type_tokens": type_tokens,
            "asset_codes": {
                _lookup_token(value)
                for value in EquipmentAsset.objects.filter(organization=organization).values_list(
                    "code", flat=True
                )
            },
        }

    if batch.target_registry == ImportBatch.TargetRegistry.DISPATCHING:
        from apps.dispatching.models import (
            DispatchLevel,
            DispatchSubject,
            ManagementRevision,
            PublicationStatus,
            SupervisionRevision,
        )
        from apps.equipment.models import EquipmentAsset

        equipment = {
            _lookup_token(code): pk
            for pk, code in EquipmentAsset.objects.filter(organization=organization).values_list(
                "pk", "code"
            )
        }
        subject_tokens: set[str] = set()
        for item in DispatchSubject.objects.filter(organization=organization, is_active=True):
            subject_tokens.update(
                {
                    _lookup_token(item.code),
                    _lookup_token(item.name),
                    _lookup_token(item.short_name),
                }
            )
        level_tokens: set[str] = set()
        for item in DispatchLevel.objects.filter(organization=organization, is_active=True):
            level_tokens.update({_lookup_token(item.code), _lookup_token(item.name)})
        today = timezone.localdate()
        current_window = Q(effective_until__isnull=True) | Q(effective_until__gte=today)
        management_codes = {
            _lookup_token(value)
            for value in ManagementRevision.objects.filter(
                management_object__organization=organization,
                status=PublicationStatus.PUBLISHED,
                effective_from__lte=today,
            )
            .filter(current_window)
            .values_list("management_object__equipment__code", flat=True)
        }
        supervision_codes = {
            _lookup_token(value)
            for value in SupervisionRevision.objects.filter(
                supervision_object__organization=organization,
                status=PublicationStatus.PUBLISHED,
                effective_from__lte=today,
            )
            .filter(current_window)
            .values_list("supervision_object__equipment__code", flat=True)
        }
        return {
            "equipment": equipment,
            "subject_tokens": subject_tokens,
            "level_tokens": level_tokens,
            "management_codes": management_codes,
            "supervision_codes": supervision_codes,
        }
    return {}


def _reference_issues(
    batch: ImportBatch,
    values: dict[str, str],
    context: dict[str, object],
) -> list[str]:
    issues: list[str] = []
    if batch.target_registry == ImportBatch.TargetRegistry.ORGANIZATION:
        if _lookup_token(values.get("division", "")) not in context["division_tokens"]:
            issues.append("Подразделение не найдено в действующем справочнике организации.")
        if _lookup_token(values.get("position", "")) not in context["position_tokens"]:
            issues.append("Должность не найдена в действующем справочнике организации.")
    elif batch.target_registry == ImportBatch.TargetRegistry.EQUIPMENT:
        if _lookup_token(values.get("site", "")) not in context["site_tokens"]:
            issues.append("Энергообъект не найден в действующем справочнике.")
        if _lookup_token(values.get("type", "")) not in context["type_tokens"]:
            issues.append("Вид оборудования не найден в действующем справочнике.")
    elif batch.target_registry == ImportBatch.TargetRegistry.DISPATCHING:
        if _lookup_token(values.get("equipment_code", "")) not in context["equipment"]:
            issues.append("Оборудование не найдено в действующем реестре.")
        if _lookup_token(values.get("subject", "")) not in context["subject_tokens"]:
            issues.append("Субъект управления или ведения не найден в справочнике.")
        if _lookup_token(values.get("level", "")) not in context["level_tokens"]:
            issues.append("Уровень управления или ведения не найден в справочнике.")
    return issues


def _active_registry_conflicts(
    batch: ImportBatch,
    values: dict[str, str],
    context: dict[str, object],
) -> list[str]:
    conflicts: list[str] = []
    if batch.target_registry == ImportBatch.TargetRegistry.ORGANIZATION:
        number = _lookup_token(values.get("personnel_number", ""))
        if number and number in context["employee_numbers"]:
            conflicts.append("Сотрудник с таким табельным номером уже существует.")
    elif batch.target_registry == ImportBatch.TargetRegistry.EQUIPMENT:
        code = _lookup_token(values.get("code", ""))
        if code and code in context["asset_codes"]:
            conflicts.append("Оборудование с таким стабильным кодом уже существует.")
    elif batch.target_registry == ImportBatch.TargetRegistry.DISPATCHING:
        code = _lookup_token(values.get("equipment_code", ""))
        relation = values.get("relation_kind", "")
        if relation == "MANAGEMENT" and code in context["management_codes"]:
            conflicts.append("Для оборудования уже действует опубликованное управление.")
        if relation == "SUPERVISION" and code in context["supervision_codes"]:
            conflicts.append("Для оборудования уже действует опубликованное ведение.")
    return conflicts


def _record_key(target_registry: str, values: dict[str, str]) -> str:
    if target_registry == ImportBatch.TargetRegistry.ORGANIZATION:
        return _lookup_token(values.get("personnel_number", ""))
    if target_registry == ImportBatch.TargetRegistry.EQUIPMENT:
        return _lookup_token(values.get("code", ""))
    if target_registry == ImportBatch.TargetRegistry.DISPATCHING:
        return "|".join(
            (
                _lookup_token(values.get("equipment_code", "")),
                values.get("relation_kind", ""),
                _lookup_token(values.get("level", "")),
            )
        )
    return _lookup_token(values.get("key", ""))


def _review_status(
    row: ImportRow,
    validation_issues: list[str],
    conflicts: list[str],
) -> str:
    if validation_issues:
        return ImportRow.ReviewStatus.INVALID
    if conflicts:
        return ImportRow.ReviewStatus.CONFLICT
    if row.status == ImportRow.Status.REVIEW or row.issues:
        return ImportRow.ReviewStatus.REVIEW
    return ImportRow.ReviewStatus.VALID


def _review_counts(batch: ImportBatch) -> dict[str, int | bool]:
    rows = batch.rows.all()
    pending = rows.filter(decision=ImportRow.Decision.PENDING).count()
    accepted = rows.filter(decision=ImportRow.Decision.ACCEPTED).count()
    rejected = rows.filter(decision=ImportRow.Decision.REJECTED).count()
    blocked = rows.filter(
        decision=ImportRow.Decision.PENDING,
        review_status__in=(
            ImportRow.ReviewStatus.CONFLICT,
            ImportRow.ReviewStatus.INVALID,
        ),
    ).count()
    return {
        "total": rows.count(),
        "pending": pending,
        "accepted": accepted,
        "rejected": rejected,
        "blocked": blocked,
        "ready": pending == 0 and accepted > 0,
    }


def _save_review_counts(batch: ImportBatch) -> None:
    batch.review_counts = _review_counts(batch)
    batch.save(update_fields=("review_counts", "updated_at"))


@transaction.atomic
def recalculate_batch_review(
    *,
    batch: ImportBatch,
    employee: Employee,
    reset_decisions: bool = False,
    create_event: bool = True,
) -> ImportBatch:
    batch = ImportBatch.objects.select_for_update().get(pk=batch.pk)
    if batch.organization_id != employee.organization_id:
        raise ValidationError("Загрузка относится к другой организации.")
    if batch.status != ImportBatch.Status.READY:
        raise ValidationError("Проверка строк доступна только для разобранной загрузки.")
    if batch.mapping_completed_at is None:
        raise ValidationError("Сначала подтвердите сопоставление колонок.")

    columns = list(batch.columns.order_by("position"))
    mapped_columns = [column for column in columns if column.mapped_key]
    specs = _field_spec_map(batch.target_registry)
    context = _validation_context(batch)
    rows = list(batch.rows.order_by("row_number"))
    record_keys: dict[str, list[ImportRow]] = {}

    for row in rows:
        raw_values = {
            column.mapped_key: (
                row.normalized_values[column.position - 1]
                if column.position - 1 < len(row.normalized_values)
                else ""
            )
            for column in mapped_columns
        }
        values, validation_issues = validate_mapped_values(batch.target_registry, raw_values)
        validation_issues.extend(_reference_issues(batch, values, context))
        if row.status == ImportRow.Status.REJECTED:
            validation_issues.append("Исходная строка была отклонена при разборе файла.")
        conflicts = _active_registry_conflicts(batch, values, context)
        row.mapped_values = {key: values.get(key, "") for key in specs}
        row.validation_issues = validation_issues
        row.registry_conflicts = conflicts
        row.review_status = _review_status(row, validation_issues, conflicts)
        if reset_decisions:
            row.decision = ImportRow.Decision.PENDING
            row.decision_values = {}
            row.decision_note = ""
            row.decided_by = None
            row.decided_at = None
        key = _record_key(batch.target_registry, values)
        if key and not validation_issues:
            record_keys.setdefault(key, []).append(row)

    for duplicate_rows in record_keys.values():
        if len(duplicate_rows) < 2:
            continue
        numbers = ", ".join(str(row.row_number) for row in duplicate_rows)
        for row in duplicate_rows:
            message = f"Дублирующая запись внутри файла: строки {numbers}."
            if message not in row.registry_conflicts:
                row.registry_conflicts.append(message)
            row.review_status = ImportRow.ReviewStatus.CONFLICT

    ImportRow.objects.bulk_update(
        rows,
        (
            "mapped_values",
            "validation_issues",
            "registry_conflicts",
            "review_status",
            "decision",
            "decision_values",
            "decision_note",
            "decided_by",
            "decided_at",
        ),
    )
    batch.review_recalculated_at = timezone.now()
    batch.review_counts = _review_counts(batch)
    batch.save(
        update_fields=(
            "review_recalculated_at",
            "review_counts",
            "updated_at",
        )
    )
    if create_event:
        ImportEvent.objects.create(
            batch=batch,
            event_type=ImportEvent.EventType.REVIEW_RECALCULATED,
            actor=employee,
            details={
                "mapping_revision": batch.mapping_revision,
                "review_counts": batch.review_counts,
                "decisions_reset": reset_decisions,
            },
        )
    return batch


@transaction.atomic
def save_column_mapping(
    *,
    batch: ImportBatch,
    employee: Employee,
    mapping: dict[int, str],
) -> ImportBatch:
    batch = ImportBatch.objects.select_for_update().get(pk=batch.pk)
    if batch.organization_id != employee.organization_id:
        raise ValidationError("Загрузка относится к другой организации.")
    if batch.status != ImportBatch.Status.READY:
        raise ValidationError("Сопоставление доступно только для разобранной загрузки.")
    cleaned = validate_column_mapping(batch, mapping)
    columns = list(batch.columns.order_by("position"))
    previous = _mapping_payload(batch)
    for column in columns:
        column.mapped_key = cleaned[column.position]
        column.mapping_origin = (
            ImportColumn.MappingOrigin.MANUAL
            if column.mapped_key
            else ImportColumn.MappingOrigin.IGNORED
        )
    ImportColumn.objects.bulk_update(columns, ("mapped_key", "mapping_origin"))
    batch.mapping_revision += 1
    batch.mapping_completed_at = timezone.now()
    batch.save(
        update_fields=(
            "mapping_revision",
            "mapping_completed_at",
            "updated_at",
        )
    )
    ImportEvent.objects.create(
        batch=batch,
        event_type=ImportEvent.EventType.MAPPING_UPDATED,
        actor=employee,
        details={
            "revision": batch.mapping_revision,
            "previous": previous,
            "current": cleaned,
            "publication_performed": False,
        },
    )
    return recalculate_batch_review(
        batch=batch,
        employee=employee,
        reset_decisions=True,
    )


def _ensure_decision_allowed(batch: ImportBatch, employee: Employee) -> None:
    if batch.organization_id != employee.organization_id:
        raise ValidationError("Загрузка относится к другой организации.")
    if batch.status != ImportBatch.Status.READY or batch.mapping_completed_at is None:
        raise ValidationError("Решения доступны после разбора файла и сопоставления колонок.")


def _decision_event(
    *,
    row: ImportRow,
    employee: Employee,
    action: str,
    changed_fields: list[str] | None = None,
) -> None:
    ImportEvent.objects.create(
        batch=row.batch,
        event_type=ImportEvent.EventType.ROW_DECISION,
        actor=employee,
        details={
            "row_number": row.row_number,
            "action": action,
            "decision": row.decision,
            "changed_fields": changed_fields or [],
            "publication_performed": False,
        },
    )


@transaction.atomic
def decide_import_row(
    *,
    row: ImportRow,
    employee: Employee,
    action: str,
    note: str = "",
) -> ImportRow:
    row = (
        ImportRow.objects.select_for_update()
        .select_related("batch")
        .get(pk=row.pk)
    )
    _ensure_decision_allowed(row.batch, employee)
    action = action.strip().upper()
    if action == "ACCEPT":
        if row.review_status in {
            ImportRow.ReviewStatus.CONFLICT,
            ImportRow.ReviewStatus.INVALID,
            ImportRow.ReviewStatus.NOT_MAPPED,
        }:
            raise ValidationError("Строку с ошибками или конфликтами нельзя принять.")
        row.decision = ImportRow.Decision.ACCEPTED
        row.decision_values = {}
    elif action == "REJECT":
        row.decision = ImportRow.Decision.REJECTED
        row.decision_values = {}
    elif action == "RESET":
        row.decision = ImportRow.Decision.PENDING
        row.decision_values = {}
        row.decision_note = ""
        row.decided_by = None
        row.decided_at = None
        row.save(
            update_fields=(
                "decision",
                "decision_values",
                "decision_note",
                "decided_by",
                "decided_at",
            )
        )
        _decision_event(row=row, employee=employee, action=action)
        _save_review_counts(row.batch)
        return row
    else:
        raise ValidationError("Неизвестное решение по строке.")

    row.decision_note = normalize_cell(note)[:2000]
    row.decided_by = employee
    row.decided_at = timezone.now()
    row.save(
        update_fields=(
            "decision",
            "decision_values",
            "decision_note",
            "decided_by",
            "decided_at",
        )
    )
    _decision_event(row=row, employee=employee, action=action)
    _save_review_counts(row.batch)
    return row


def _edited_row_conflicts(
    row: ImportRow,
    values: dict[str, str],
    context: dict[str, object],
) -> list[str]:
    conflicts = _active_registry_conflicts(row.batch, values, context)
    key = _record_key(row.batch.target_registry, values)
    if not key:
        return conflicts
    for other in row.batch.rows.exclude(pk=row.pk):
        other_values = other.effective_values
        if _record_key(row.batch.target_registry, other_values) == key:
            conflicts.append(
                f"Исправленная запись совпадает со строкой {other.row_number} этого файла."
            )
            break
    return conflicts


@transaction.atomic
def save_row_correction(
    *,
    row: ImportRow,
    employee: Employee,
    values: dict[str, str],
    note: str = "",
) -> ImportRow:
    row = (
        ImportRow.objects.select_for_update()
        .select_related("batch")
        .get(pk=row.pk)
    )
    _ensure_decision_allowed(row.batch, employee)
    allowed = _field_spec_map(row.batch.target_registry)
    unknown = set(values) - set(allowed)
    if unknown:
        raise ValidationError("Переданы неизвестные поля исправления.")
    canonical, issues = validate_mapped_values(row.batch.target_registry, values)
    context = _validation_context(row.batch)
    issues.extend(_reference_issues(row.batch, canonical, context))
    conflicts = _edited_row_conflicts(row, canonical, context)
    if issues or conflicts:
        raise ValidationError(issues + conflicts)

    changed_fields = [
        key for key, value in canonical.items() if value != row.mapped_values.get(key, "")
    ]
    row.decision = ImportRow.Decision.ACCEPTED
    row.decision_values = canonical
    row.decision_note = normalize_cell(note)[:2000]
    row.decided_by = employee
    row.decided_at = timezone.now()
    row.save(
        update_fields=(
            "decision",
            "decision_values",
            "decision_note",
            "decided_by",
            "decided_at",
        )
    )
    _decision_event(
        row=row,
        employee=employee,
        action="EDIT_AND_ACCEPT",
        changed_fields=changed_fields,
    )
    _save_review_counts(row.batch)
    return row


@transaction.atomic
def bulk_decide_import_rows(
    *,
    batch: ImportBatch,
    employee: Employee,
    row_ids: list[int],
    action: str,
) -> dict[str, int]:
    batch = ImportBatch.objects.select_for_update().get(pk=batch.pk)
    _ensure_decision_allowed(batch, employee)
    unique_ids = list(dict.fromkeys(row_ids))
    if not unique_ids:
        raise ValidationError("Не выбрана ни одна строка.")
    if len(unique_ids) > 100:
        raise ValidationError("За одну операцию можно обработать не более 100 строк.")
    rows = list(
        batch.rows.filter(pk__in=unique_ids).select_related("batch").order_by("row_number")
    )
    if len(rows) != len(unique_ids):
        raise ValidationError("Часть выбранных строк не относится к этой загрузке.")

    result = {"processed": 0, "skipped": 0}
    for row in rows:
        try:
            decide_import_row(row=row, employee=employee, action=action)
        except ValidationError:
            result["skipped"] += 1
        else:
            result["processed"] += 1
    ImportEvent.objects.create(
        batch=batch,
        event_type=ImportEvent.EventType.BULK_DECISION,
        actor=employee,
        details={
            "action": action.strip().upper(),
            "selected": len(unique_ids),
            **result,
            "publication_performed": False,
        },
    )
    _save_review_counts(batch)
    return result


PUBLICATION_SCHEMA = "eod.import.publication.v1"
PUBLISHER_ROLE_CODE = "organization_admin"


@dataclass(frozen=True, slots=True)
class ImportPublicationPreview:
    batch: ImportBatch
    accepted_rows: tuple[ImportRow, ...]
    rejected_count: int
    canonical_json: str
    digest: str
    effects: tuple[dict[str, object], ...]


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_json(value: object) -> tuple[str, str]:
    canonical = _canonical_json(value)
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def can_publish_import(user) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    employee = getattr(user, "employee_profile", None)
    if employee is None or not employee.is_active or employee.user_id != getattr(user, "pk", None):
        return False
    today = timezone.localdate()
    return (
        RoleAssignment.objects.filter(
            employee=employee,
            role__code=PUBLISHER_ROLE_CODE,
            role__is_active=True,
            is_active=True,
            valid_from__lte=today,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=today))
        .exists()
    )


def require_import_publisher(user) -> Employee:
    employee = require_import_employee(user)
    if employee.user_id != getattr(user, "pk", None):
        raise PermissionDenied("Учётная запись не соответствует карточке сотрудника.")
    if not can_publish_import(user):
        raise PermissionDenied(
            "Для публикации требуется прямая действующая роль «Администратор справочников»."
        )
    return employee


def _parse_iso_date(value: str, *, default: date | None = None) -> date | None:
    normalized = normalize_cell(value)
    if not normalized:
        return default
    return date.fromisoformat(normalized)


def _boolean_value(value: str, *, default: bool = False) -> bool:
    normalized = normalize_header(value)
    if not normalized:
        return default
    if normalized in {_lookup_token(item) for item in TRUE_VALUES} | {"да"}:
        return True
    if normalized in {_lookup_token(item) for item in FALSE_VALUES} | {"нет"}:
        return False
    raise ValidationError("Логическое значение не удалось преобразовать.")


def _resolve_division(batch: ImportBatch, value: str):
    from apps.organizations.models import Division

    token = normalize_cell(value)
    queryset = Division.objects.filter(
        organization=batch.organization,
        is_active=True,
    )
    by_code = queryset.filter(code__iexact=token).first()
    if by_code is not None:
        return by_code
    matches = list(queryset.filter(name__iexact=token)[:2])
    if len(matches) != 1:
        raise ValidationError(
            f"Подразделение «{token}» не найдено однозначно в действующем справочнике."
        )
    return matches[0]


def _resolve_position(batch: ImportBatch, value: str):
    from apps.organizations.models import Position

    token = normalize_cell(value)
    queryset = Position.objects.filter(
        organization=batch.organization,
        is_active=True,
    )
    by_code = queryset.filter(code__iexact=token).first()
    if by_code is not None:
        return by_code
    matches = list(queryset.filter(name__iexact=token)[:2])
    if len(matches) != 1:
        raise ValidationError(
            f"Должность «{token}» не найдена однозначно в действующем справочнике."
        )
    return matches[0]


def _resolve_site(batch: ImportBatch, value: str):
    from apps.equipment.models import EnergySite

    token = normalize_cell(value)
    queryset = EnergySite.objects.filter(
        organization=batch.organization,
        is_active=True,
    )
    by_code = queryset.filter(code__iexact=token).first()
    if by_code is not None:
        return by_code
    matches = list(
        queryset.filter(Q(name__iexact=token) | Q(short_name__iexact=token)).distinct()[:2]
    )
    if len(matches) != 1:
        raise ValidationError(
            f"Энергообъект «{token}» не найден однозначно в действующем справочнике."
        )
    return matches[0]


def _resolve_equipment_type(value: str):
    from apps.equipment.models import EquipmentType

    token = normalize_cell(value)
    queryset = EquipmentType.objects.filter(is_active=True)
    by_code = queryset.filter(code__iexact=token).first()
    if by_code is not None:
        return by_code
    matches = list(queryset.filter(name__iexact=token)[:2])
    if len(matches) != 1:
        raise ValidationError(
            f"Вид оборудования «{token}» не найден однозначно в действующем справочнике."
        )
    return matches[0]


def _resolve_equipment(batch: ImportBatch, value: str):
    from apps.equipment.models import EquipmentAsset

    token = normalize_cell(value)
    matches = list(
        EquipmentAsset.objects.filter(
            organization=batch.organization,
            code__iexact=token,
        )[:2]
    )
    if len(matches) != 1:
        raise ValidationError(
            f"Оборудование «{token}» не найдено однозначно в действующем реестре."
        )
    return matches[0]


def _resolve_dispatch_subject(batch: ImportBatch, value: str):
    from apps.dispatching.models import DispatchSubject

    token = normalize_cell(value)
    queryset = DispatchSubject.objects.filter(
        organization=batch.organization,
        is_active=True,
    )
    by_code = queryset.filter(code__iexact=token).first()
    if by_code is not None:
        return by_code
    matches = list(
        queryset.filter(Q(name__iexact=token) | Q(short_name__iexact=token)).distinct()[:2]
    )
    if len(matches) != 1:
        raise ValidationError(
            f"Субъект «{token}» не найден однозначно в действующем справочнике."
        )
    return matches[0]


def _resolve_dispatch_level(batch: ImportBatch, value: str):
    from apps.dispatching.models import DispatchLevel

    token = normalize_cell(value)
    queryset = DispatchLevel.objects.filter(
        organization=batch.organization,
        is_active=True,
    )
    by_code = queryset.filter(code__iexact=token).first()
    if by_code is not None:
        return by_code
    matches = list(queryset.filter(name__iexact=token)[:2])
    if len(matches) != 1:
        raise ValidationError(
            f"Уровень «{token}» не найден однозначно в действующем справочнике."
        )
    return matches[0]


def _publication_basis(batch: ImportBatch, supplied: str = "") -> str:
    value = normalize_cell(supplied)
    if value:
        return value[:1000]
    return (
        f"Контролируемая публикация импорта «{batch.original_filename}», "
        f"SHA-256 {batch.file_sha256}"
    )[:1000]


def _publication_effect(
    batch: ImportBatch,
    row: ImportRow,
    values: dict[str, str],
) -> dict[str, object]:
    if batch.target_registry == ImportBatch.TargetRegistry.ORGANIZATION:
        division = _resolve_division(batch, values["division"])
        position = _resolve_position(batch, values["position"])
        return {
            "row_number": row.row_number,
            "action": "create",
            "target_model": "organizations.Employee",
            "label": (
                f"{values['personnel_number']} · {values['last_name']} "
                f"{values['first_name']} · {division.name} · {position.name}"
            ),
        }
    if batch.target_registry == ImportBatch.TargetRegistry.EQUIPMENT:
        site = _resolve_site(batch, values["site"])
        equipment_type = _resolve_equipment_type(values["type"])
        return {
            "row_number": row.row_number,
            "action": "create",
            "target_model": "equipment.EquipmentAsset",
            "label": (
                f"{values['code']} · {values['technical_name']} · "
                f"{site} · {equipment_type.name}"
            ),
            "publishes_dispatcher_name": bool(values.get("dispatcher_name")),
        }
    if batch.target_registry == ImportBatch.TargetRegistry.DISPATCHING:
        equipment = _resolve_equipment(batch, values["equipment_code"])
        subject = _resolve_dispatch_subject(batch, values["subject"])
        level = _resolve_dispatch_level(batch, values["level"])
        relation_label = (
            "оперативное управление"
            if values["relation_kind"] == "MANAGEMENT"
            else "оперативное ведение"
        )
        return {
            "row_number": row.row_number,
            "action": "publish_revision",
            "target_model": (
                "dispatching.ManagementRevision"
                if values["relation_kind"] == "MANAGEMENT"
                else "dispatching.SupervisionRevision"
            ),
            "label": (
                f"{equipment.code} · {relation_label} · {subject} · {level.name}"
            ),
        }
    raise ValidationError(
        "Назначение «Другой справочник» доступно только для staging и не публикуется."
    )


def _accepted_rows_and_effects(
    batch: ImportBatch,
) -> tuple[tuple[ImportRow, ...], tuple[dict[str, object], ...]]:
    persisted_status = (
        ImportBatch.objects.filter(pk=batch.pk)
        .values_list("status", flat=True)
        .first()
        if batch.pk
        else batch.status
    )
    if persisted_status == ImportBatch.Status.PUBLISHED:
        raise ValidationError("Эта загрузка уже опубликована.")
    if batch.status != ImportBatch.Status.READY:
        raise ValidationError("Публикация доступна только для разобранной загрузки.")
    if batch.mapping_completed_at is None:
        raise ValidationError("Сначала подтвердите сопоставление колонок.")
    if batch.target_registry == ImportBatch.TargetRegistry.OTHER:
        raise ValidationError(
            "Назначение «Другой справочник» не имеет рабочего реестра для публикации."
        )

    rows = tuple(batch.rows.select_related("decided_by").order_by("row_number"))
    pending = [row.row_number for row in rows if row.decision == ImportRow.Decision.PENDING]
    if pending:
        raise ValidationError(
            "До публикации требуется принять или отклонить решение по каждой строке."
        )
    accepted = tuple(row for row in rows if row.decision == ImportRow.Decision.ACCEPTED)
    if not accepted:
        raise ValidationError("Нет ни одной предварительно принятой строки.")

    context = _validation_context(batch)
    effects: list[dict[str, object]] = []
    for row in accepted:
        values, issues = validate_mapped_values(
            batch.target_registry,
            row.effective_values,
        )
        issues.extend(_reference_issues(batch, values, context))
        conflicts = _active_registry_conflicts(batch, values, context)
        if issues or conflicts:
            detail = "; ".join(issues + conflicts)
            raise ValidationError(
                f"Строка {row.row_number} больше не готова к публикации: {detail}"
            )
        effects.append(_publication_effect(batch, row, values))
    return accepted, tuple(effects)


def build_import_publication_preview(batch: ImportBatch) -> ImportPublicationPreview:
    accepted_rows, effects = _accepted_rows_and_effects(batch)
    payload = {
        "schema": PUBLICATION_SCHEMA,
        "batch_public_id": str(batch.public_id),
        "organization": {
            "id": batch.organization_id,
            "code": batch.organization.code,
        },
        "source": {
            "filename": batch.original_filename,
            "format": batch.source_format,
            "size": batch.file_size,
            "sha256": batch.file_sha256,
            "sheet": batch.sheet_name,
        },
        "target_registry": batch.target_registry,
        "mapping_revision": batch.mapping_revision,
        "rows": [
            {
                "row_id": row.pk,
                "row_number": row.row_number,
                "values": row.effective_values,
                "decision_note": row.decision_note,
                "decided_by_id": row.decided_by_id,
                "decided_at": (
                    row.decided_at.isoformat()
                    if row.decided_at is not None
                    else None
                ),
            }
            for row in accepted_rows
        ],
    }
    canonical, digest = _sha256_json(payload)
    return ImportPublicationPreview(
        batch=batch,
        accepted_rows=accepted_rows,
        rejected_count=batch.rows.filter(
            decision=ImportRow.Decision.REJECTED
        ).count(),
        canonical_json=canonical,
        digest=digest,
        effects=effects,
    )


def _create_employee_from_import(
    *,
    batch: ImportBatch,
    values: dict[str, str],
) -> tuple[str, str, dict[str, object]]:
    from apps.organizations.models import Employee

    division = _resolve_division(batch, values["division"])
    position = _resolve_position(batch, values["position"])
    employee = Employee(
        organization=batch.organization,
        division=division,
        position=position,
        personnel_number=values["personnel_number"],
        last_name=values["last_name"],
        first_name=values["first_name"],
        middle_name=values.get("middle_name", ""),
        employment_start=_parse_iso_date(
            values.get("employment_start", ""),
            default=timezone.localdate(),
        ),
        is_active=_boolean_value(values.get("is_active", ""), default=True),
    )
    employee.full_clean()
    employee.save()
    return (
        "organizations.Employee",
        str(employee.pk),
        {
            "employee_id": employee.pk,
            "personnel_number": employee.personnel_number,
            "full_name": employee.full_name,
        },
    )


def _create_equipment_from_import(
    *,
    batch: ImportBatch,
    actor: Employee,
    values: dict[str, str],
) -> tuple[str, str, dict[str, object]]:
    from apps.equipment.models import (
        EquipmentAsset,
        EquipmentNameRevision,
    )
    from apps.equipment.services import publish_equipment_name_revision

    site = _resolve_site(batch, values["site"])
    equipment_type = _resolve_equipment_type(values["type"])
    commissioned_on = _parse_iso_date(values.get("commissioned_on", ""))
    equipment = EquipmentAsset(
        organization=batch.organization,
        site=site,
        equipment_type=equipment_type,
        code=values["code"],
        technical_name=values["technical_name"],
        status=values.get("status") or EquipmentAsset.Status.ACTIVE,
        voltage_level=values.get("voltage_level", ""),
        commissioned_on=commissioned_on,
    )
    equipment.save()
    result: dict[str, object] = {
        "equipment_id": equipment.pk,
        "public_id": str(equipment.public_id),
        "code": equipment.code,
    }
    dispatcher_name = normalize_cell(values.get("dispatcher_name", ""))
    if dispatcher_name:
        revision = EquipmentNameRevision.objects.create(
            equipment=equipment,
            revision_number=1,
            dispatcher_name=dispatcher_name,
            effective_from=commissioned_on or timezone.localdate(),
            basis_reference=_publication_basis(batch),
        )
        revision = publish_equipment_name_revision(revision=revision, actor=actor)
        result["dispatcher_name_revision_id"] = revision.pk
        result["dispatcher_name_digest"] = revision.digest
    return "equipment.EquipmentAsset", str(equipment.pk), result


def _create_dispatching_from_import(
    *,
    batch: ImportBatch,
    actor: Employee,
    values: dict[str, str],
) -> tuple[str, str, dict[str, object]]:
    from apps.dispatching.models import (
        ManagementObject,
        ManagementRevision,
        SupervisionObject,
        SupervisionRevision,
    )
    from apps.dispatching.services import (
        publish_management_revision,
        publish_supervision_revision,
    )

    equipment = _resolve_equipment(batch, values["equipment_code"])
    subject = _resolve_dispatch_subject(batch, values["subject"])
    level = _resolve_dispatch_level(batch, values["level"])
    effective_from = _parse_iso_date(
        values.get("effective_from", ""),
        default=timezone.localdate(),
    )
    effective_until = _parse_iso_date(values.get("effective_until", ""))
    basis_reference = _publication_basis(batch, values.get("basis_reference", ""))
    if values["relation_kind"] == "MANAGEMENT":
        management_object, _created = ManagementObject.objects.get_or_create(
            organization=batch.organization,
            equipment=equipment,
            defaults={"notes": "Создано контролируемой публикацией импорта."},
        )
        revision_number = (
            management_object.revisions.aggregate(value=Max("revision_number"))["value"]
            or 0
        ) + 1
        revision = ManagementRevision.objects.create(
            management_object=management_object,
            revision_number=revision_number,
            level=level,
            subject=subject,
            effective_from=effective_from,
            effective_until=effective_until,
            basis_reference=basis_reference,
            change_summary="Создано контролируемой публикацией импорта.",
        )
        revision = publish_management_revision(revision=revision, actor=actor)
        return (
            "dispatching.ManagementRevision",
            str(revision.pk),
            {
                "revision_id": revision.pk,
                "equipment_id": equipment.pk,
                "revision_number": revision.revision_number,
                "digest": revision.digest,
            },
        )

    supervision_object, _created = SupervisionObject.objects.get_or_create(
        organization=batch.organization,
        equipment=equipment,
        defaults={"notes": "Создано контролируемой публикацией импорта."},
    )
    revision_number = (
        supervision_object.revisions.aggregate(value=Max("revision_number"))["value"]
        or 0
    ) + 1
    revision = SupervisionRevision.objects.create(
        supervision_object=supervision_object,
        revision_number=revision_number,
        level=level,
        subject=subject,
        is_information_only=_boolean_value(
            values.get("information_only", ""),
            default=False,
        ),
        effective_from=effective_from,
        effective_until=effective_until,
        basis_reference=basis_reference,
        change_summary="Создано контролируемой публикацией импорта.",
    )
    revision = publish_supervision_revision(revision=revision, actor=actor)
    return (
        "dispatching.SupervisionRevision",
        str(revision.pk),
        {
            "revision_id": revision.pk,
            "equipment_id": equipment.pk,
            "revision_number": revision.revision_number,
            "digest": revision.digest,
            "information_only": revision.is_information_only,
        },
    )


def _publish_row(
    *,
    batch: ImportBatch,
    row: ImportRow,
    actor: Employee,
) -> tuple[str, str, dict[str, object]]:
    values = row.effective_values
    if batch.target_registry == ImportBatch.TargetRegistry.ORGANIZATION:
        return _create_employee_from_import(batch=batch, values=values)
    if batch.target_registry == ImportBatch.TargetRegistry.EQUIPMENT:
        return _create_equipment_from_import(
            batch=batch,
            actor=actor,
            values=values,
        )
    if batch.target_registry == ImportBatch.TargetRegistry.DISPATCHING:
        return _create_dispatching_from_import(
            batch=batch,
            actor=actor,
            values=values,
        )
    raise ValidationError("Выбранный справочник не поддерживает публикацию.")


@transaction.atomic
def publish_import_batch(
    *,
    batch: ImportBatch,
    actor: Employee,
    user,
    password: str,
    expected_digest: str,
) -> ImportPublication:
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

    locked = (
        ImportBatch.objects.select_for_update()
        .select_related("organization", "created_by", "published_by")
        .get(pk=batch.pk)
    )
    list(
        locked.rows.select_for_update()
        .select_related("decided_by")
        .order_by("row_number")
    )
    preview = build_import_publication_preview(locked)
    if not expected_digest or expected_digest != preview.digest:
        raise ValidationError(
            "Состав публикации изменился. Обновите страницу и повторно проверьте итог."
        )

    result_rows: list[tuple[ImportRow, str, str, dict[str, object]]] = []
    model_counts: dict[str, int] = {}
    for row in preview.accepted_rows:
        target_model, target_object_id, result = _publish_row(
            batch=locked,
            row=row,
            actor=actor,
        )
        result_rows.append((row, target_model, target_object_id, result))
        model_counts[target_model] = model_counts.get(target_model, 0) + 1

    result_summary: dict[str, object] = {
        "accepted": len(result_rows),
        "rejected": preview.rejected_count,
        "models": model_counts,
    }
    publication = ImportPublication.objects.create(
        batch=locked,
        actor=actor,
        schema_version=PUBLICATION_SCHEMA,
        target_registry=locked.target_registry,
        mapping_revision=locked.mapping_revision,
        canonical_json=preview.canonical_json,
        digest=preview.digest,
        result_summary=result_summary,
    )
    for row, target_model, target_object_id, result in result_rows:
        row_payload = {
            "publication_digest": publication.digest,
            "row_number": row.row_number,
            "target_model": target_model,
            "target_object_id": target_object_id,
            "result": result,
        }
        _canonical, row_digest = _sha256_json(row_payload)
        ImportPublicationRow.objects.create(
            publication=publication,
            row=row,
            target_model=target_model,
            target_object_id=target_object_id,
            result=result,
            digest=row_digest,
        )

    published_at = timezone.now()
    locked.status = ImportBatch.Status.PUBLISHED
    locked.published_at = published_at
    locked.published_by = actor
    locked.publication_digest = publication.digest
    locked.publication_counts = result_summary
    locked.save(
        update_fields=(
            "status",
            "published_at",
            "published_by",
            "publication_digest",
            "publication_counts",
            "updated_at",
        )
    )
    ImportEvent.objects.create(
        batch=locked,
        event_type=ImportEvent.EventType.PUBLISHED,
        actor=actor,
        details={
            "publication_id": publication.pk,
            "publication_digest": publication.digest,
            "accepted": len(result_rows),
            "rejected": preview.rejected_count,
            "models": model_counts,
        },
    )
    return publication
