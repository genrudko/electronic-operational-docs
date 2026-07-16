from __future__ import annotations

import csv
import hashlib
import io
import json
import posixpath
import re
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.organizations.models import Employee

from .models import ImportBatch, ImportColumn, ImportEvent, ImportRow

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


def _xlsx_cell_value(
    cell: ElementTree.Element,
    shared_strings: list[str],
) -> tuple[str, bool]:
    formula = cell.find(f"{{{SPREADSHEET_NS}}}f")
    if formula is not None:
        return "=" + (formula.text or ""), True

    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        inline = cell.find(f"{{{SPREADSHEET_NS}}}is")
        if inline is None:
            return "", False
        return (
            "".join(
                node.text or ""
                for node in inline.iter(f"{{{SPREADSHEET_NS}}}t")
            ),
            False,
        )

    value_node = cell.find(f"{{{SPREADSHEET_NS}}}v")
    raw = "" if value_node is None else value_node.text or ""
    if cell_type == "s":
        try:
            return shared_strings[int(raw)], False
        except (ValueError, IndexError) as exc:
            raise ImportParseError(
                "XLSX содержит некорректную ссылку на общую строку."
            ) from exc
    if cell_type == "b":
        return ("ИСТИНА" if raw == "1" else "ЛОЖЬ"), False
    return raw, False


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
                    value, is_formula = _xlsx_cell_value(cell, shared_strings)
                    row_values[column_index] = value
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


def _column_payloads(parsed: ParsedTable, width: int) -> list[dict[str, object]]:
    header = list(parsed.rows[0])
    header.extend("" for _ in range(width - len(header)))
    normalized_headers = [normalize_header(value) for value in header]
    duplicate_names = {
        value
        for value in normalized_headers
        if value and normalized_headers.count(value) > 1
    }

    payloads: list[dict[str, object]] = []
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
        payloads.append(
            {
                "position": index + 1,
                "source_name": source_name,
                "normalized_name": normalized_name,
                "recognized_key": HEADER_ALIASES.get(normalized_headers[index], ""),
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
        normalized_values = [normalize_cell(value) for value in source_values]
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

        column_payloads = _column_payloads(parsed, width)
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
