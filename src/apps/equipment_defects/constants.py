from __future__ import annotations

from apps.operational_documents.models import FieldType


DOCUMENT_TYPE_CODE = "journal-equipment-defects"
DOCUMENT_TYPE_NAME = "Журнал дефектов оборудования"
DOCUMENT_TYPE_SHORT_NAME = "Журнал дефектов"
SOURCE_DOCUMENT = "И-00-007-ОР-2025 версия 2"
SOURCE_SECTION = "11"
SOURCE_APPENDIX = "8"
NUMBER_PREFIX = "ДЕФ"
NUMBER_WIDTH = 4

FIELD_DETECTED_AT = "DETECTED_AT"
FIELD_DEFECT_DESCRIPTION = "DEFECT_DESCRIPTION"
FIELD_ELIMINATION_DEADLINE = "ELIMINATION_DEADLINE"
FIELD_RESOLVED_AT = "RESOLVED_AT"
FIELD_RESOLUTION_WORK_SUMMARY = "RESOLUTION_WORK_SUMMARY"

ROLE_DISCOVERED_BY = "DISCOVERED_BY"
ROLE_OPERATIONS_RESPONSIBLE = "OPERATIONS_RESPONSIBLE"
ROLE_RESOLUTION_RESPONSIBLE = "RESOLUTION_RESPONSIBLE"
ROLE_OPERATIONAL_ACKNOWLEDGER = "OPERATIONAL_ACKNOWLEDGER"

STATUS_REGISTERED = "REGISTERED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_RESOLVED = "RESOLVED"
STATUS_CLOSED = "CLOSED"

TRANSITION_ASSIGN_DEADLINE = "ASSIGN_DEADLINE"
TRANSITION_CONFIRM_RESOLUTION = "CONFIRM_RESOLUTION"
TRANSITION_CLOSE = "CLOSE_DEFECT"

DEADLINE_EXTENSION_TEXT = "Срок устранения продлен"

FIELD_DEFINITIONS = [
    {
        "code": FIELD_DETECTED_AT,
        "label": "Дата обнаружения дефекта",
        "type": FieldType.DATETIME,
        "required": True,
        "show_in_list": False,
        "searchable": True,
        "help_text": "В утверждённой печатной форме отображается только дата.",
        "choices": [],
        "position": 1,
    },
    {
        "code": FIELD_DEFECT_DESCRIPTION,
        "label": "Содержание дефекта",
        "type": FieldType.LONG_TEXT,
        "required": True,
        "show_in_list": True,
        "searchable": True,
        "help_text": "Опишите выявленный дефект или неисправность.",
        "choices": [],
        "position": 2,
    },
    {
        "code": FIELD_ELIMINATION_DEADLINE,
        "label": "Срок устранения",
        "type": FieldType.DATETIME,
        "required": False,
        "show_in_list": True,
        "searchable": True,
        "help_text": "Устанавливается отдельным подтверждаемым действием.",
        "choices": [],
        "position": 3,
    },
    {
        "code": FIELD_RESOLVED_AT,
        "label": "Дата устранения дефекта",
        "type": FieldType.DATETIME,
        "required": False,
        "show_in_list": False,
        "searchable": True,
        "help_text": "Заполняется при подтверждении устранения.",
        "choices": [],
        "position": 4,
    },
    {
        "code": FIELD_RESOLUTION_WORK_SUMMARY,
        "label": "Содержание выполненных работ по устранению дефекта",
        "type": FieldType.LONG_TEXT,
        "required": False,
        "show_in_list": True,
        "searchable": True,
        "help_text": "Заполняется ответственным за устранение.",
        "choices": [],
        "position": 5,
    },
]

STATUS_DEFINITIONS = [
    {
        "code": STATUS_REGISTERED,
        "name": "Зарегистрирован",
        "is_initial": True,
        "is_terminal": False,
        "tone": "info",
        "position": 1,
    },
    {
        "code": STATUS_IN_PROGRESS,
        "name": "В работе",
        "is_initial": False,
        "is_terminal": False,
        "tone": "warning",
        "position": 2,
    },
    {
        "code": STATUS_RESOLVED,
        "name": "Устранён",
        "is_initial": False,
        "is_terminal": False,
        "tone": "success",
        "position": 3,
    },
    {
        "code": STATUS_CLOSED,
        "name": "Закрыт",
        "is_initial": False,
        "is_terminal": True,
        "tone": "neutral",
        "position": 4,
    },
]

TRANSITION_DEFINITIONS = [
    {
        "code": TRANSITION_ASSIGN_DEADLINE,
        "name": "Подтвердить срок",
        "from": STATUS_REGISTERED,
        "to": STATUS_IN_PROGRESS,
        "requires_comment": False,
        "position": 1,
    },
    {
        "code": TRANSITION_CONFIRM_RESOLUTION,
        "name": "Подтвердить устранение",
        "from": STATUS_IN_PROGRESS,
        "to": STATUS_RESOLVED,
        "requires_comment": False,
        "position": 2,
    },
    {
        "code": TRANSITION_CLOSE,
        "name": "Закрыть",
        "from": STATUS_RESOLVED,
        "to": STATUS_CLOSED,
        "requires_comment": False,
        "position": 3,
    },
]

PARTICIPANT_ROLE_DEFINITIONS = [
    {
        "code": ROLE_DISCOVERED_BY,
        "name": "Лицо, обнаружившее дефект",
        "required": True,
        "multiple": False,
        "position": 1,
    },
    {
        "code": ROLE_OPERATIONS_RESPONSIBLE,
        "name": "Ответственный за эксплуатацию",
        "required": False,
        "multiple": False,
        "position": 2,
    },
    {
        "code": ROLE_RESOLUTION_RESPONSIBLE,
        "name": "Ответственный за устранение",
        "required": False,
        "multiple": False,
        "position": 3,
    },
    {
        "code": ROLE_OPERATIONAL_ACKNOWLEDGER,
        "name": "Ознакомившийся оперативный персонал",
        "required": False,
        "multiple": True,
        "position": 4,
    },
]

APPROVED_PRINT_COLUMNS = (
    "Дата обнаружения дефекта",
    (
        "Наименование ЛЭП, оборудования, устройства, содержание дефекта, "
        "Ф.И.О., подпись лица, обнаружившего дефект"
    ),
    (
        "Срок устранения, Ф.И.О., подпись ответственного лица за эксплуатацию "
        "ЛЭП, оборудования, устройства, сооружения, здания"
    ),
    (
        "Дата устранения дефекта, Ф.И.О., подпись ответственного лица "
        "за его устранение"
    ),
    "Содержание выполненных работ по устранению дефекта",
    "Ф.И.О., подписи оперативного персонала",
)
