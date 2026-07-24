from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovedJournalForm:
    code: str
    name: str
    purpose: str
    source_document: str
    source_section: str
    source_appendix: str


SOURCE_DOCUMENT_TITLE = "И-00-007-ОР-2025 версия 2"

APPROVED_JOURNAL_FORMS = (
    ApprovedJournalForm(
        code="journal-orders",
        name="Журнал распоряжений",
        purpose="Распоряжения оперативному персоналу и контроль ознакомления с ними.",
        source_document=SOURCE_DOCUMENT_TITLE,
        source_section="7",
        source_appendix="4",
    ),
    ApprovedJournalForm(
        code="journal-outage-requests",
        name="Журнал заявок на вывод из работы ЛЭП, оборудования и устройств",
        purpose="Регистрация содержания и сроков оперативных заявок.",
        source_document=SOURCE_DOCUMENT_TITLE,
        source_section="8",
        source_appendix="5",
    ),
    ApprovedJournalForm(
        code="journal-equipment-commissioning",
        name="Журнал ввода оборудования в работу",
        purpose="Записи о результатах работ и возможности ввода оборудования в работу.",
        source_document=SOURCE_DOCUMENT_TITLE,
        source_section="9",
        source_appendix="6",
    ),
    ApprovedJournalForm(
        code="journal-rza-telemechanics",
        name="Журнал РЗА и телемеханики",
        purpose="Записи о вторичных системах, их обслуживании и возможности ввода в работу.",
        source_document=SOURCE_DOCUMENT_TITLE,
        source_section="10",
        source_appendix="7",
    ),
    ApprovedJournalForm(
        code="journal-equipment-defects",
        name="Журнал дефектов оборудования",
        purpose="Регистрация обнаружения, срока и результата устранения дефектов оборудования.",
        source_document=SOURCE_DOCUMENT_TITLE,
        source_section="11",
        source_appendix="8",
    ),
)

APPROVED_JOURNAL_FORM_CODES = frozenset(item.code for item in APPROVED_JOURNAL_FORMS)


def approved_journal_form(code: str) -> ApprovedJournalForm | None:
    normalized = code.strip().lower()
    return next((item for item in APPROVED_JOURNAL_FORMS if item.code == normalized), None)


def is_approved_journal_form_code(code: str) -> bool:
    return code.strip().lower() in APPROVED_JOURNAL_FORM_CODES
