from __future__ import annotations

import csv
import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.imports.power_system import (
    ALIAS_FILE,
    ALIAS_HEADERS,
    ANALYSIS_PREFIX,
    ASSET_FILE,
    ASSET_HEADERS,
    AUTHORITY_FILE,
    AUTHORITY_HEADERS,
    ISSUE_FILE,
    ISSUE_HEADERS,
    TYPE_FILE,
    TYPE_HEADERS,
)


def _csv_bytes(headers: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: row.get(header, "") for header in headers})
    return stream.getvalue().encode("utf-8")


def synthetic_power_system_package(
    *,
    filename: str = "synthetic-power-system.zip",
    include_repair6_cases: bool = False,
):
    facility = "Синтетическая ВЭС"
    base = {
        "source_sheet": "Синтетический перечень",
        "source_item_number": "",
        "domain": "HIERARCHY",
        "source_category_raw": "",
        "voltage_context_raw": "35 кВ",
        "nominal_voltage_kv": "35",
        "voltage_basis": "SOURCE_CONTEXT",
        "management_raw": "",
        "conduct_raw": "",
        "note_raw": "",
        "is_primary_equipment_proposed": "FALSE",
        "is_secondary_device_proposed": "FALSE",
        "is_operational_control_object_candidate": "TRUE",
        "is_independent_dispatching_object_candidate": "FALSE",
        "classification_confidence": "HIGH",
        "hierarchy_confidence": "HIGH",
        "import_disposition": "AUTO_IMPORT",
        "duplicate_group": "",
        "related_primary_asset_raw": "",
        "relation_basis": "",
        "source_fact_notes": "Синтетическая строка автоматизированного теста.",
        "energy_facility_raw": facility,
    }
    asset_rows = [
        {
            **base,
            "occurrence_id": "SYN-SITE",
            "source_row": "1",
            "record_role": "HIERARCHY_NODE",
            "asset_type_proposed": "energy_facility",
            "asset_type_ru_proposed": "Энергообъект",
            "dispatcher_name_raw": facility,
            "display_name_normalized_proposed": facility,
            "comparison_key": "синтетическая вэс",
            "parent_raw": "",
            "hierarchy_path_raw": facility,
        },
        {
            **base,
            "occurrence_id": "SYN-35KV",
            "source_row": "2",
            "record_role": "HIERARCHY_NODE",
            "asset_type_proposed": "voltage_level",
            "asset_type_ru_proposed": "Класс напряжения",
            "dispatcher_name_raw": "35 кВ",
            "display_name_normalized_proposed": "35 кВ",
            "comparison_key": "35 кв",
            "parent_raw": facility,
            "hierarchy_path_raw": f"{facility} / 35 кВ",
        },
        {
            **base,
            "occurrence_id": "SYN-KTP-1",
            "source_row": "3",
            "record_role": "HIERARCHY_NODE",
            "asset_type_proposed": "unit_substation",
            "asset_type_ru_proposed": "Комплектная трансформаторная подстанция",
            "dispatcher_name_raw": "КТП-1",
            "display_name_normalized_proposed": "КТП-1",
            "comparison_key": "ктп-1",
            # Намеренно повторяем дефект реального пакета: родителем указан объект,
            # хотя контекст напряжения однозначно задаёт промежуточный узел 35 кВ.
            "parent_raw": facility,
            "hierarchy_path_raw": f"{facility} / {facility}",
        },
        {
            **base,
            "occurrence_id": "SYN-OPU",
            "source_row": "4",
            "record_role": "HIERARCHY_NODE",
            "asset_type_proposed": "control_building",
            "asset_type_ru_proposed": "Общеподстанционный пункт управления",
            "dispatcher_name_raw": "ОПУ ВЭС",
            "display_name_normalized_proposed": "ОПУ ВЭС",
            "comparison_key": "опу вэс",
            "parent_raw": facility,
            "hierarchy_path_raw": f"{facility} / {facility}",
        },
        {
            **base,
            "occurrence_id": "SYN-WTG-GROUP",
            "source_row": "5",
            "record_role": "HIERARCHY_NODE",
            "asset_type_proposed": "asset_group",
            "asset_type_ru_proposed": "Группа оборудования",
            "dispatcher_name_raw": "ВЭУ",
            "display_name_normalized_proposed": "ВЭУ",
            "comparison_key": "вэу",
            "parent_raw": facility,
            "hierarchy_path_raw": f"{facility} / ВЭУ",
            "voltage_context_raw": "",
            "nominal_voltage_kv": "",
        },
        {
            **base,
            "occurrence_id": "SYN-WTG-1",
            "source_row": "6",
            "record_role": "HIERARCHY_NODE",
            "asset_type_proposed": "wind_turbine",
            "asset_type_ru_proposed": "Ветроэнергетическая установка",
            "dispatcher_name_raw": "ВЭУ-1",
            "display_name_normalized_proposed": "ВЭУ-1",
            "comparison_key": "вэу-1",
            "parent_raw": facility,
            "hierarchy_path_raw": f"{facility} / {facility}",
            "voltage_context_raw": "",
            "nominal_voltage_kv": "",
        },
        {
            **base,
            "occurrence_id": "SYN-LINE-35",
            "source_row": "7",
            "record_role": "DISPATCHING_OBJECT_OCCURRENCE",
            "domain": "LINE",
            "asset_type_proposed": "cable_line",
            "asset_type_ru_proposed": "Кабельная линия",
            "dispatcher_name_raw": "КЛ 35 кВ КТП-1 – КТП-2",
            "display_name_normalized_proposed": "КЛ 35 кВ КТП-1 – КТП-2",
            "comparison_key": "кл 35 кв ктп-1 ктп-2",
            "parent_raw": facility,
            "hierarchy_path_raw": f"{facility} / {facility}",
            "is_primary_equipment_proposed": "TRUE",
        },
        {
            **base,
            "occurrence_id": "SYN-Q-1",
            "source_row": "8",
            "record_role": "DISPATCHING_OBJECT_OCCURRENCE",
            "domain": "PRIMARY_EQUIPMENT",
            "asset_type_proposed": "circuit_breaker",
            "asset_type_ru_proposed": "Выключатель",
            "dispatcher_name_raw": "В-35 КТП-1",
            "display_name_normalized_proposed": "В-35 КТП-1",
            "comparison_key": "в-35 ктп-1",
            "parent_raw": "КТП-1",
            "hierarchy_path_raw": f"{facility} / 35 кВ / КТП-1 / В-35 КТП-1",
            "is_primary_equipment_proposed": "TRUE",
            "management_raw": facility,
            "conduct_raw": facility,
        },
        {
            **base,
            "occurrence_id": "SYN-BLOCKED",
            "source_row": "9",
            "record_role": "DISPATCHING_OBJECT_OCCURRENCE",
            "domain": "PRIMARY_EQUIPMENT",
            "asset_type_proposed": "circuit_breaker",
            "asset_type_ru_proposed": "Выключатель",
            "dispatcher_name_raw": "В-35 спорный",
            "display_name_normalized_proposed": "В-35 спорный",
            "comparison_key": "в-35 спорный",
            "parent_raw": "КТП-1",
            "hierarchy_path_raw": f"{facility} / 35 кВ / КТП-1 / В-35 спорный",
            "import_disposition": "REVIEW_CONFLICT",
            "is_primary_equipment_proposed": "TRUE",
        },
    ]
    if include_repair6_cases:
        asset_rows.extend(
            [
                {
                    **base,
                    "occurrence_id": "SYN-SHOT-1",
                    "source_row": "10",
                    "record_role": "DISPATCHING_OBJECT_OCCURRENCE",
                    "domain": "PRIMARY_EQUIPMENT",
                    "asset_type_proposed": "other_equipment",
                    "asset_type_ru_proposed": "Прочее оборудование",
                    "source_category_raw": "Прочее",
                    "dispatcher_name_raw": "ШОТ",
                    "display_name_normalized_proposed": "ШОТ",
                    "comparison_key": "шот",
                    "parent_raw": "КТП-1",
                    "hierarchy_path_raw": f"{facility} / 35 кВ / КТП-1 / Прочее",
                    "classification_confidence": "LOW",
                    "import_disposition": "CREATE",
                    "is_primary_equipment_proposed": "TRUE",
                },
                {
                    **base,
                    "occurrence_id": "SYN-DUP-A",
                    "source_row": "11",
                    "record_role": "DISPATCHING_OBJECT_OCCURRENCE",
                    "domain": "POWER_LINE",
                    "asset_type_proposed": "cable_line",
                    "asset_type_ru_proposed": "Кабельная линия",
                    "dispatcher_name_raw": "КЛ 35 кВ Синтетическая 1 цепь",
                    "display_name_normalized_proposed": "КЛ 35 кВ Синтетическая 1 цепь",
                    "comparison_key": "кл 35 кв синтетическая 1 цепь",
                    "parent_raw": facility,
                    "hierarchy_path_raw": f"{facility} / 35 кВ",
                    "import_disposition": "MERGE_CANDIDATE",
                    "duplicate_group": "SYN_DUP_1",
                    "is_primary_equipment_proposed": "TRUE",
                },
                {
                    **base,
                    "occurrence_id": "SYN-DUP-B",
                    "source_row": "12",
                    "record_role": "DISPATCHING_OBJECT_OCCURRENCE",
                    "domain": "POWER_LINE",
                    "asset_type_proposed": "cable_line",
                    "asset_type_ru_proposed": "Кабельная линия",
                    "dispatcher_name_raw": "КЛ 35 кВ Синтетическая 1 цепь",
                    "display_name_normalized_proposed": "КЛ 35 кВ Синтетическая 1 цепь",
                    "comparison_key": "кл 35 кв синтетическая 1 цепь",
                    "parent_raw": facility,
                    "hierarchy_path_raw": f"{facility} / 35 кВ",
                    "import_disposition": "MERGE_CANDIDATE",
                    "duplicate_group": "SYN_DUP_1",
                    "is_primary_equipment_proposed": "TRUE",
                },
            ]
        )
    authority_rows = [
        {
            "occurrence_id": "SYN-Q-1",
            "source_sheet": "Синтетический перечень",
            "source_row": "8",
            "dispatcher_name_raw": "В-35 КТП-1",
            "authority_kind": "OPERATIONAL_MANAGEMENT",
            "assignment_status": "ASSIGNED",
            "authority_subject_raw": facility,
            "authority_subject_normalized_proposed": facility,
            "normalization_status": "AS_IS",
            "source_cell_raw": facility,
            "is_informational": "",
            "informational_basis": "",
        },
        {
            "occurrence_id": "SYN-Q-1",
            "source_sheet": "Синтетический перечень",
            "source_row": "8",
            "dispatcher_name_raw": "В-35 КТП-1",
            "authority_kind": "OPERATIONAL_CONDUCT",
            "assignment_status": "ASSIGNED",
            "authority_subject_raw": facility,
            "authority_subject_normalized_proposed": facility,
            "normalization_status": "AS_IS",
            "source_cell_raw": facility,
            "is_informational": "FALSE",
            "informational_basis": "Прямое синтетическое значение.",
        },
    ]
    alias_rows = [
        {
            "alias_scope": "ASSET",
            "occurrence_id": "SYN-Q-1",
            "parent_context_raw": "КТП-1",
            "alias_raw": "В 35 КТП 1",
            "target_name_raw": "В-35 КТП-1",
            "alias_kind": "SPACING_VARIANT",
            "normalization_rule": "Пробелы и дефисы",
            "confidence": "HIGH",
            "status": "PROPOSED",
            "note": "Синтетический поисковый вариант.",
        }
    ]
    type_rows = [
        {
            "type_code_proposed": "energy_facility",
            "russian_label_proposed": "Энергообъект",
            "domain": "HIERARCHY",
            "source_evidence": facility,
            "status": "PROPOSED",
        },
        {
            "type_code_proposed": "voltage_level",
            "russian_label_proposed": "Класс напряжения",
            "domain": "HIERARCHY",
            "source_evidence": "35 кВ",
            "status": "PROPOSED",
        },
        {
            "type_code_proposed": "unit_substation",
            "russian_label_proposed": "Комплектная трансформаторная подстанция",
            "domain": "HIERARCHY",
            "source_evidence": "КТП-1",
            "status": "PROPOSED",
        },
        {
            "type_code_proposed": "control_building",
            "russian_label_proposed": "Общеподстанционный пункт управления",
            "domain": "HIERARCHY",
            "source_evidence": "ОПУ ВЭС",
            "status": "PROPOSED",
        },
        {
            "type_code_proposed": "asset_group",
            "russian_label_proposed": "Группа оборудования",
            "domain": "HIERARCHY",
            "source_evidence": "ВЭУ",
            "status": "PROPOSED",
        },
        {
            "type_code_proposed": "wind_turbine",
            "russian_label_proposed": "Ветроэнергетическая установка",
            "domain": "HIERARCHY",
            "source_evidence": "ВЭУ-1",
            "status": "PROPOSED",
        },
        {
            "type_code_proposed": "cable_line",
            "russian_label_proposed": "Кабельная линия",
            "domain": "LINE",
            "source_evidence": "КЛ 35 кВ",
            "is_primary_equipment_default": "TRUE",
            "is_operational_control_object_default": "TRUE",
            "status": "PROPOSED",
        },
        {
            "type_code_proposed": "circuit_breaker",
            "russian_label_proposed": "Выключатель",
            "domain": "PRIMARY_EQUIPMENT",
            "source_evidence": "В-35",
            "is_primary_equipment_default": "TRUE",
            "is_operational_control_object_default": "TRUE",
            "status": "PROPOSED",
        },
    ]
    issue_rows = [
        {
            "issue_code": "LEP_CROSS_LISTED_35KV_CABLES",
            "severity": "MEDIUM",
            "category": "DUPLICATE",
            "source_sheet": "Синтетический перечень",
            "source_rows": "7, 9",
            "evidence": "Merge candidate после review двух source-occurrence.",
            "import_risk": "Ложный дубль в staging external authority references.",
            "recommended_handling": "Оставить merge candidate в построчном карантине до review.",
            "blocks_automatic_import": "TRUE",
            "status": "OPEN",
        }
    ]
    analysis_name = f"{ANALYSIS_PREFIX}synthetic.md"
    analysis = (
        "# Синтетический аналитический пакет\n\n"
        "**Источник:** `synthetic-source.xlsx`\n"
        f"**SHA-256 источника:** `{'1' * 64}`\n"
    ).encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(analysis_name, analysis)
        archive.writestr(ASSET_FILE, _csv_bytes(ASSET_HEADERS, asset_rows))
        archive.writestr(AUTHORITY_FILE, _csv_bytes(AUTHORITY_HEADERS, authority_rows))
        archive.writestr(ALIAS_FILE, _csv_bytes(ALIAS_HEADERS, alias_rows))
        archive.writestr(TYPE_FILE, _csv_bytes(TYPE_HEADERS, type_rows))
        archive.writestr(ISSUE_FILE, _csv_bytes(ISSUE_HEADERS, issue_rows))
    return SimpleUploadedFile(filename, output.getvalue(), content_type="application/zip")
