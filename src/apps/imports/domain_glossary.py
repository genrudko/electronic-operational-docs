from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TechnicalEnglishTerm:
    russian_term: str
    code_name: str
    english_term: str
    domain: str
    note: str = ""


TECHNICAL_ENGLISH_GLOSSARY: tuple[TechnicalEnglishTerm, ...] = (
    TechnicalEnglishTerm(
        "энергообъект",
        "energy_facility",
        "energy facility",
        "power_system",
        "Обобщающее понятие; конкретный тип хранится отдельно.",
    ),
    TechnicalEnglishTerm(
        "ветровая электростанция",
        "wind_power_plant",
        "wind power plant",
        "power_generation",
    ),
    TechnicalEnglishTerm(
        "подстанция",
        "substation",
        "substation",
        "power_system",
    ),
    TechnicalEnglishTerm(
        "электроустановка",
        "electrical_installation",
        "electrical installation",
        "power_system",
    ),
    TechnicalEnglishTerm(
        "оборудование энергосистемы",
        "power_system_asset",
        "power system asset",
        "asset_registry",
    ),
    TechnicalEnglishTerm(
        "воздушная линия электропередачи",
        "overhead_line",
        "overhead line",
        "transmission_distribution",
    ),
    TechnicalEnglishTerm(
        "кабельная линия",
        "cable_circuit",
        "cable circuit",
        "transmission_distribution",
        "Circuit используется для отдельной электрической цепи, а не для кабеля как изделия.",
    ),
    TechnicalEnglishTerm(
        "распределительное устройство",
        "switchgear",
        "switchgear",
        "substation_equipment",
    ),
    TechnicalEnglishTerm(
        "ячейка распределительного устройства",
        "switchgear_bay",
        "switchgear bay",
        "substation_equipment",
    ),
    TechnicalEnglishTerm(
        "система шин",
        "busbar_system",
        "busbar system",
        "substation_equipment",
    ),
    TechnicalEnglishTerm(
        "секция шин",
        "busbar_section",
        "busbar section",
        "substation_equipment",
    ),
    TechnicalEnglishTerm(
        "выключатель",
        "circuit_breaker",
        "circuit breaker",
        "switching_device",
    ),
    TechnicalEnglishTerm(
        "разъединитель",
        "disconnector",
        "disconnector",
        "switching_device",
        "Не использовать generic switch.",
    ),
    TechnicalEnglishTerm(
        "заземляющий нож",
        "earthing_switch",
        "earthing switch",
        "switching_device",
    ),
    TechnicalEnglishTerm(
        "силовой трансформатор",
        "power_transformer",
        "power transformer",
        "transformer",
    ),
    TechnicalEnglishTerm(
        "трансформатор собственных нужд",
        "station_service_transformer",
        "station service transformer",
        "transformer",
    ),
    TechnicalEnglishTerm(
        "трансформатор напряжения",
        "voltage_transformer",
        "voltage transformer",
        "instrument_transformer",
    ),
    TechnicalEnglishTerm(
        "трансформатор тока",
        "current_transformer",
        "current transformer",
        "instrument_transformer",
    ),
    TechnicalEnglishTerm(
        "устройство релейной защиты и автоматики",
        "protection_and_automation_device",
        "protection and automation device",
        "protection_control",
    ),
    TechnicalEnglishTerm(
        "релейная защита",
        "relay_protection",
        "relay protection",
        "protection_control",
    ),
    TechnicalEnglishTerm(
        "диспетчерское наименование",
        "operational_designation",
        "operational designation",
        "dispatch_operation",
        "Русское опубликованное наименование хранится без перевода.",
    ),
    TechnicalEnglishTerm(
        "диспетчерское управление",
        "dispatch_control",
        "dispatch control",
        "dispatch_operation",
    ),
    TechnicalEnglishTerm(
        "оперативное управление",
        "operational_control",
        "operational control",
        "dispatch_operation",
    ),
    TechnicalEnglishTerm(
        "оперативное ведение",
        "operational_jurisdiction",
        "operational jurisdiction",
        "dispatch_operation",
        "Означает закреплённую компетенцию согласования изменения состояния или режима.",
    ),
    TechnicalEnglishTerm(
        "диспетчерский центр",
        "dispatch_center",
        "dispatch center",
        "dispatch_operation",
    ),
    TechnicalEnglishTerm(
        "оперативный журнал",
        "operational_log",
        "operational log",
        "operational_documentation",
    ),
    TechnicalEnglishTerm(
        "оперативная документация",
        "operational_documentation",
        "operational documentation",
        "operational_documentation",
    ),
    TechnicalEnglishTerm(
        "перечень документации рабочего места",
        "workplace_document_register",
        "workplace document register",
        "operational_documentation",
    ),
    TechnicalEnglishTerm(
        "оперативная запись",
        "operational_entry",
        "operational entry",
        "operational_documentation",
    ),
    TechnicalEnglishTerm(
        "подразделение",
        "organizational_unit",
        "organizational unit",
        "organization",
    ),
    TechnicalEnglishTerm(
        "должность",
        "position",
        "position",
        "organization",
    ),
    TechnicalEnglishTerm(
        "работник",
        "employee",
        "employee",
        "organization",
    ),
    TechnicalEnglishTerm(
        "группа по электробезопасности",
        "electrical_safety_group",
        "electrical safety group",
        "personnel_authorization",
    ),
    TechnicalEnglishTerm(
        "оперативное право",
        "operational_authority",
        "operational authority",
        "personnel_authorization",
    ),
    TechnicalEnglishTerm(
        "область действия права",
        "authority_scope",
        "authority scope",
        "personnel_authorization",
    ),
    TechnicalEnglishTerm(
        "профиль данных",
        "data_profile",
        "data profile",
        "data_governance",
    ),
    TechnicalEnglishTerm(
        "партия импорта",
        "import_batch",
        "import batch",
        "data_import",
    ),
    TechnicalEnglishTerm(
        "схема сопоставления колонок",
        "import_mapping_template",
        "import mapping template",
        "data_import",
    ),
    TechnicalEnglishTerm(
        "исходная запись",
        "source_record",
        "source record",
        "data_import",
    ),
    TechnicalEnglishTerm(
        "внешний идентификатор",
        "external_id",
        "external identifier",
        "data_import",
    ),
)


_CODE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def glossary_by_code_name() -> dict[str, TechnicalEnglishTerm]:
    return {term.code_name: term for term in TECHNICAL_ENGLISH_GLOSSARY}


def validate_technical_english_glossary() -> tuple[str, ...]:
    issues: list[str] = []
    seen_russian: set[str] = set()
    seen_code_names: set[str] = set()
    for term in TECHNICAL_ENGLISH_GLOSSARY:
        if term.russian_term in seen_russian:
            issues.append(f"Повторяется русский термин: {term.russian_term}")
        if term.code_name in seen_code_names:
            issues.append(f"Повторяется внутреннее имя: {term.code_name}")
        if not _CODE_NAME_RE.fullmatch(term.code_name):
            issues.append(f"Некорректное snake_case имя: {term.code_name}")
        if not term.english_term.strip():
            issues.append(f"Не задан технический английский: {term.russian_term}")
        seen_russian.add(term.russian_term)
        seen_code_names.add(term.code_name)
    return tuple(issues)
