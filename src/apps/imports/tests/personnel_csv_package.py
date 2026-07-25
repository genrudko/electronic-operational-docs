from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterable

from apps.imports.personnel import (
    ASSIGNMENTS_CSV_HEADER,
    AUTHORITIES_CSV_HEADER,
    CSV_AUTHORITY_CODE_MAP,
    ISSUES_CSV_HEADER,
    PEOPLE_CSV_HEADER,
    POSITIONS_CSV_HEADER,
)


def _csv_bytes(header: tuple[str, ...], rows: Iterable[dict[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in header})
    return buffer.getvalue().encode("utf-8")


def synthetic_personnel_csv_files() -> dict[str, bytes]:
    people = [
        {
            "source_sheet": "Приложение",
            "source_excel_row": 9,
            "source_person_no": 1,
            "full_name_raw": "Иванов Иван Иванович",
            "full_name_normalized": "Иванов Иван Иванович",
            "position_raw": "Начальник смены",
            "position_normalized_candidate": "Начальник смены",
            "organizational_unit_raw": "Оперативная служба",
            "organizational_unit_normalized_candidate": "Оперативная служба",
            "personnel_category_raw": "ОП",
            "personnel_category_normalized_candidate": "ОП",
            "electrical_safety_group_raw": "V до и выше 1000 В",
            "electrical_safety_group": "V",
            "voltage_scope": "до и выше 1000 В",
            "electrical_installation_scope_raw": "ЭУ до и выше 1000 В",
            "basis_document_title": "Синтетическое приложение",
            "basis_metadata_status": "INCOMPLETE_IN_SOURCE",
        },
        {
            "source_sheet": "Приложение",
            "source_excel_row": 10,
            "source_person_no": 2,
            "full_name_raw": "Петров Пётр Петрович",
            "full_name_normalized": "Петров Пётр Петрович",
            "position_raw": "Инженер",
            "position_normalized_candidate": "Инженер",
            "organizational_unit_raw": "Служба РЗА",
            "organizational_unit_normalized_candidate": "Служба РЗА",
            "personnel_category_raw": "АТП",
            "personnel_category_normalized_candidate": "АТП",
            "electrical_safety_group_raw": "IV до и выше 1000 В",
            "electrical_safety_group": "IV",
            "voltage_scope": "до и выше 1000 В",
            "electrical_installation_scope_raw": "ЭУ до и выше 1000 В",
            "basis_document_title": "Синтетическое приложение",
            "basis_metadata_status": "INCOMPLETE_IN_SOURCE",
        },
    ]
    positions = [
        {
            "position_key_proposed": "POS-001",
            "position_name_normalized_candidate": "Начальник смены",
            "source_variants": "Начальник смены",
            "person_count": 1,
            "normalization_status": "DIRECT",
        },
        {
            "position_key_proposed": "POS-002",
            "position_name_normalized_candidate": "Инженер",
            "source_variants": "Инженер",
            "person_count": 1,
            "normalization_status": "DIRECT",
        },
    ]
    authorities = []
    for proposed, (column, _internal) in CSV_AUTHORITY_CODE_MAP.items():
        authorities.append(
            {
                "authority_code_proposed": proposed,
                "source_excel_column": column,
                "source_label_normalized": f"Синтетическое полномочие {proposed}",
                "authority_category_proposed": "SYNTHETIC",
                "value_kind": "BOOLEAN",
                "compound_decomposition": "NO",
            }
        )
    assignments = []
    for person in people:
        person_no = person["source_person_no"]
        source_row = person["source_excel_row"]
        for proposed, (column, internal) in CSV_AUTHORITY_CODE_MAP.items():
            raw = "–"
            status = "NOT_GRANTED"
            action = "STAGING_ONLY"
            qualifier = ""
            marker = ""
            marker_text = ""
            enum_value = ""
            if internal in {"dispatch_application_submit", "team_member", "sole_inspection"}:
                raw, status, action = "+", "GRANTED", "CREATE_OR_UPDATE_ASSIGNMENT"
            if person_no == 1 and internal == "operational_application_submit":
                raw, status, action = "+2", "GRANTED_WITH_REFERENCE", "CREATE_OR_UPDATE_ASSIGNMENT"
                marker = "2.0"
                marker_text = "Синтетическая сноска 2"
            if person_no == 1 and internal == "operational_application_approve":
                raw, status, action = "+3", "AMBIGUOUS_REFERENCE", "STAGING_ONLY"
            if person_no == 1 and internal == "work_at_height":
                raw, status, action, qualifier = (
                    "+ (3 группа)",
                    "GRANTED_WITH_QUALIFIER",
                    "CREATE_OR_UPDATE_ASSIGNMENT",
                    "(3 группа)",
                )
            if person_no == 1 and internal == "rza_maintenance_category":
                raw, status, action, enum_value = "2", "ENUM_VALUE", "STAGING_ONLY", "2"
            assignments.append(
                {
                    "source_person_no": person_no,
                    "full_name_normalized": person["full_name_normalized"],
                    "authority_code_proposed": proposed,
                    "source_excel_cell": f"{column}{source_row}",
                    "source_raw_value": raw,
                    "source_status": status,
                    "qualifier_raw": qualifier,
                    "reference_marker": marker,
                    "reference_text_from_source_legend": marker_text,
                    "enum_value": enum_value,
                    "scope_raw": "ЭУ до и выше 1000 В",
                    "import_action_proposed": action,
                }
            )
    issues = [
        {
            "issue_id": "ISSUE-001",
            "source": "synthetic",
            "severity": "HIGH",
            "entity_ref": "person:1",
            "field": "basis_document_number",
            "issue_type": "MISSING_SOURCE_METADATA",
            "description": "Синтетическая проблема источника.",
            "recommended_action": "Проверить вручную.",
            "status": "OPEN",
        }
    ]
    return {
        "eod_people.csv": _csv_bytes(PEOPLE_CSV_HEADER, people),
        "eod_positions.csv": _csv_bytes(POSITIONS_CSV_HEADER, positions),
        "eod_operational_authorities.csv": _csv_bytes(AUTHORITIES_CSV_HEADER, authorities),
        "eod_person_authority_assignments.csv": _csv_bytes(ASSIGNMENTS_CSV_HEADER, assignments),
        "eod_import_issues.csv": _csv_bytes(ISSUES_CSV_HEADER, issues),
    }


def synthetic_personnel_csv_package(
    *,
    files: dict[str, bytes] | None = None,
    prefix: str = "",
    reverse_order: bool = False,
) -> bytes:
    content = files or synthetic_personnel_csv_files()
    items = list(content.items())
    if reverse_order:
        items.reverse()

    def write_deterministic(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
        info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o600 << 16
        archive.writestr(info, payload)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in items:
            write_deterministic(archive, f"{prefix}{name}", data)
    return buffer.getvalue()
