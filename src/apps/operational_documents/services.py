from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.equipment.services import dispatcher_name_on
from apps.organizations.models import Employee, Workplace
from apps.organizations.services import user_has_role

from .models import (
    DocumentLinkType,
    FieldType,
    OperationalDocumentAuditEvent,
    OperationalDocumentEquipmentLink,
    OperationalDocumentExternalDocumentLink,
    OperationalDocumentNumberSequence,
    OperationalDocumentParticipant,
    OperationalDocumentRecord,
    OperationalDocumentRecordRevision,
    OperationalDocumentRelation,
    OperationalDocumentType,
    OperationalDocumentTypeRevision,
    RecordRelationType,
    RecordRevisionAction,
    SchemaPublicationStatus,
)

CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")

DEFAULT_STATUS_DEFINITIONS = [
    {
        "code": "OPEN",
        "name": "Открыта",
        "is_initial": True,
        "is_terminal": False,
        "tone": "info",
    },
    {
        "code": "IN_PROGRESS",
        "name": "В работе",
        "is_initial": False,
        "is_terminal": False,
        "tone": "warning",
    },
    {
        "code": "CLOSED",
        "name": "Закрыта",
        "is_initial": False,
        "is_terminal": True,
        "tone": "success",
    },
]

DEFAULT_TRANSITION_DEFINITIONS = [
    {
        "code": "START",
        "name": "Принять в работу",
        "from": "OPEN",
        "to": "IN_PROGRESS",
        "requires_comment": False,
    },
    {
        "code": "CLOSE_OPEN",
        "name": "Закрыть",
        "from": "OPEN",
        "to": "CLOSED",
        "requires_comment": True,
    },
    {
        "code": "CLOSE",
        "name": "Закрыть",
        "from": "IN_PROGRESS",
        "to": "CLOSED",
        "requires_comment": True,
    },
]

DEFAULT_PARTICIPANT_ROLE_DEFINITIONS = [
    {
        "code": "RESPONSIBLE",
        "name": "Ответственный",
        "required": False,
        "multiple": False,
    },
    {
        "code": "PERFORMER",
        "name": "Исполнитель",
        "required": False,
        "multiple": True,
    },
]


def canonical_json(value: Any) -> str:
    def normalize(item: Any) -> Any:
        if isinstance(item, dict):
            return {str(key): normalize(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [normalize(child) for child in item]
        if isinstance(item, datetime):
            moment = item
            if timezone.is_naive(moment):
                moment = timezone.make_aware(moment, timezone.get_current_timezone())
            return moment.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        if isinstance(item, date):
            return item.isoformat()
        if isinstance(item, Decimal):
            return format(item, "f")
        if item is None or isinstance(item, (str, int, float, bool)):
            return item
        return str(item)

    return json.dumps(
        normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def employee_for_user(user: Any) -> Employee | None:
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    try:
        employee = user.employee_profile
    except (AttributeError, Employee.DoesNotExist):
        return None
    return employee if employee.is_active else None


def require_operational_document_employee(user: Any) -> Employee:
    employee = employee_for_user(user)
    if employee is None:
        raise PermissionDenied(
            "Для работы с оперативной документацией нужен действующий профиль сотрудника."
        )
    return employee


def can_administer_operational_document_types(user: Any) -> bool:
    return bool(
        getattr(user, "is_superuser", False)
        or user_has_role(user, "shift_supervisor")
    )


def require_operational_document_type_administrator(user: Any) -> Employee:
    employee = require_operational_document_employee(user)
    if not can_administer_operational_document_types(user):
        raise PermissionDenied("Нет полномочий для публикации типов оперативных документов.")
    return employee


def _normalized_code(value: Any, label: str) -> str:
    code = str(value or "").strip().upper()
    if not CODE_RE.fullmatch(code):
        raise ValidationError(
            f"{label}: код должен начинаться с латинской буквы и содержать только A–Z, 0–9 и _."
        )
    return code


def normalize_field_definitions(definitions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(definitions, Sequence) or isinstance(definitions, (str, bytes)):
        raise ValidationError("Описание полей должно быть списком.")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    allowed_types = {choice for choice, _label in FieldType.choices}
    for position, raw in enumerate(definitions, start=1):
        if not isinstance(raw, Mapping):
            raise ValidationError(f"Поле № {position}: описание должно быть объектом.")
        code = _normalized_code(raw.get("code"), f"Поле № {position}")
        if code in seen:
            raise ValidationError(f"Код поля {code} указан более одного раза.")
        seen.add(code)
        label = str(raw.get("label") or "").strip()
        if not label:
            raise ValidationError(f"Поле {code}: наименование обязательно.")
        field_type = str(raw.get("type") or FieldType.TEXT).strip().upper()
        if field_type not in allowed_types:
            raise ValidationError(f"Поле {code}: неизвестный тип {field_type}.")
        choices: list[dict[str, str]] = []
        raw_choices = raw.get("choices") or []
        if field_type == FieldType.CHOICE:
            if not isinstance(raw_choices, Sequence) or isinstance(raw_choices, (str, bytes)):
                raise ValidationError(f"Поле {code}: варианты должны быть списком.")
            choice_values: set[str] = set()
            for choice_position, raw_choice in enumerate(raw_choices, start=1):
                if isinstance(raw_choice, Mapping):
                    choice_value = str(raw_choice.get("value") or "").strip()
                    choice_label = str(raw_choice.get("label") or choice_value).strip()
                else:
                    choice_value = str(raw_choice).strip()
                    choice_label = choice_value
                if not choice_value or not choice_label:
                    raise ValidationError(
                        f"Поле {code}: вариант № {choice_position} не заполнен."
                    )
                if choice_value in choice_values:
                    raise ValidationError(f"Поле {code}: вариант {choice_value} повторяется.")
                choice_values.add(choice_value)
                choices.append({"value": choice_value, "label": choice_label})
            if not choices:
                raise ValidationError(f"Поле {code}: для выбора нужен хотя бы один вариант.")
        elif raw_choices:
            raise ValidationError(f"Поле {code}: варианты допустимы только для типа «Выбор». ")
        result.append(
            {
                "code": code,
                "label": label,
                "type": field_type,
                "required": bool(raw.get("required", False)),
                "show_in_list": bool(raw.get("show_in_list", False)),
                "searchable": bool(raw.get("searchable", True)),
                "help_text": str(raw.get("help_text") or "").strip(),
                "choices": choices,
                "position": position,
            }
        )
    if not result:
        raise ValidationError("Тип документа должен содержать хотя бы одно предметное поле.")
    if sum(1 for item in result if item["show_in_list"]) > 4:
        raise ValidationError("В общем реестре можно показывать не более четырёх предметных полей.")
    return result


def normalize_status_definitions(definitions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not definitions:
        raise ValidationError("Требуется хотя бы одно состояние.")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    initial_count = 0
    terminal_count = 0
    for position, raw in enumerate(definitions, start=1):
        if not isinstance(raw, Mapping):
            raise ValidationError(f"Состояние № {position}: описание должно быть объектом.")
        code = _normalized_code(raw.get("code"), f"Состояние № {position}")
        if code in seen:
            raise ValidationError(f"Код состояния {code} повторяется.")
        seen.add(code)
        name = str(raw.get("name") or "").strip()
        if not name:
            raise ValidationError(f"Состояние {code}: наименование обязательно.")
        is_initial = bool(raw.get("is_initial", False))
        is_terminal = bool(raw.get("is_terminal", False))
        initial_count += int(is_initial)
        terminal_count += int(is_terminal)
        result.append(
            {
                "code": code,
                "name": name,
                "is_initial": is_initial,
                "is_terminal": is_terminal,
                "tone": str(raw.get("tone") or "neutral").strip().lower(),
                "position": position,
            }
        )
    if initial_count != 1:
        raise ValidationError("В редакции типа должно быть ровно одно начальное состояние.")
    if terminal_count < 1:
        raise ValidationError("В редакции типа требуется хотя бы одно конечное состояние.")
    return result


def normalize_transition_definitions(
    definitions: Sequence[Mapping[str, Any]],
    statuses: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    status_codes = {str(item["code"]) for item in statuses}
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    seen_edges: set[tuple[str, str]] = set()
    for position, raw in enumerate(definitions, start=1):
        if not isinstance(raw, Mapping):
            raise ValidationError(f"Переход № {position}: описание должно быть объектом.")
        code = _normalized_code(raw.get("code"), f"Переход № {position}")
        if code in seen:
            raise ValidationError(f"Код перехода {code} повторяется.")
        seen.add(code)
        name = str(raw.get("name") or "").strip()
        from_code = _normalized_code(raw.get("from"), f"Переход {code}")
        to_code = _normalized_code(raw.get("to"), f"Переход {code}")
        if not name:
            raise ValidationError(f"Переход {code}: наименование обязательно.")
        if from_code not in status_codes or to_code not in status_codes:
            raise ValidationError(f"Переход {code}: указано неизвестное состояние.")
        if from_code == to_code:
            raise ValidationError(f"Переход {code}: начальное и конечное состояния совпадают.")
        edge = (from_code, to_code)
        if edge in seen_edges:
            raise ValidationError(
                f"Переход {from_code} → {to_code} указан более одного раза."
            )
        seen_edges.add(edge)
        result.append(
            {
                "code": code,
                "name": name,
                "from": from_code,
                "to": to_code,
                "requires_comment": bool(raw.get("requires_comment", False)),
                "position": position,
            }
        )
    return result


def normalize_participant_role_definitions(
    definitions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, raw in enumerate(definitions, start=1):
        if not isinstance(raw, Mapping):
            raise ValidationError(f"Роль № {position}: описание должно быть объектом.")
        code = _normalized_code(raw.get("code"), f"Роль № {position}")
        if code in seen:
            raise ValidationError(f"Код роли {code} повторяется.")
        seen.add(code)
        name = str(raw.get("name") or "").strip()
        if not name:
            raise ValidationError(f"Роль {code}: наименование обязательно.")
        result.append(
            {
                "code": code,
                "name": name,
                "required": bool(raw.get("required", False)),
                "multiple": bool(raw.get("multiple", False)),
                "position": position,
            }
        )
    return result


def _audit(
    *,
    organization_id: int,
    actor: Employee,
    event_type: str,
    entity_type: str,
    entity_id: str,
    document_type: OperationalDocumentType | None = None,
    record: OperationalDocumentRecord | None = None,
    payload: dict[str, Any] | None = None,
) -> OperationalDocumentAuditEvent:
    return OperationalDocumentAuditEvent.objects.create(
        organization_id=organization_id,
        document_type=document_type,
        record=record,
        event_type=event_type,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload or {},
    )


@transaction.atomic
def publish_type_revision(
    *,
    revision: OperationalDocumentTypeRevision,
    actor: Employee,
) -> OperationalDocumentTypeRevision:
    locked = (
        OperationalDocumentTypeRevision.objects.select_for_update()
        .select_related("document_type", "document_type__organization")
        .get(pk=revision.pk)
    )
    if actor.organization_id != locked.document_type.organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")
    if locked.status != SchemaPublicationStatus.DRAFT:
        raise ValidationError("Опубликовать можно только черновик редакции.")
    fields = normalize_field_definitions(locked.field_definitions)
    statuses = normalize_status_definitions(locked.status_definitions)
    transitions = normalize_transition_definitions(locked.transition_definitions, statuses)
    roles = normalize_participant_role_definitions(locked.participant_role_definitions)
    published_at = timezone.now()
    snapshot = {
        "schema": "eod.operational-document-type.v1",
        "type": {
            "public_id": str(locked.document_type.public_id),
            "code": locked.document_type.code,
            "name": locked.document_type.name,
            "short_name": locked.document_type.short_name,
            "description": locked.document_type.description,
        },
        "revision_number": locked.revision_number,
        "number_prefix": locked.number_prefix,
        "number_width": locked.number_width,
        "requires_workplace": locked.requires_workplace,
        "field_definitions": fields,
        "status_definitions": statuses,
        "transition_definitions": transitions,
        "participant_role_definitions": roles,
        "published_at": published_at,
        "published_by": {
            "employee_public_id": str(actor.public_id),
            "full_name": actor.full_name,
            "position": actor.position.name,
            "division": actor.division.name,
        },
    }
    snapshot = json.loads(canonical_json(snapshot))
    digest = sha256_text(canonical_json(snapshot))
    locked.field_definitions = fields
    locked.status_definitions = statuses
    locked.transition_definitions = transitions
    locked.participant_role_definitions = roles
    locked.canonical_snapshot = snapshot
    locked.sha256 = digest
    locked.status = SchemaPublicationStatus.PUBLISHED
    locked.published_by = actor
    locked.published_at = published_at
    locked.save()
    _audit(
        organization_id=actor.organization_id,
        actor=actor,
        event_type="TYPE_REVISION_PUBLISHED",
        entity_type="operational_document_type_revision",
        entity_id=str(locked.public_id),
        document_type=locked.document_type,
        payload={
            "revision_number": locked.revision_number,
            "sha256": digest,
            "field_count": len(fields),
            "status_count": len(statuses),
        },
    )
    return locked


@transaction.atomic
def create_and_publish_type(
    *,
    actor: Employee,
    code: str,
    name: str,
    short_name: str,
    description: str,
    number_prefix: str,
    number_width: int,
    requires_workplace: bool,
    field_definitions: Sequence[Mapping[str, Any]],
    status_definitions: Sequence[Mapping[str, Any]] | None = None,
    transition_definitions: Sequence[Mapping[str, Any]] | None = None,
    participant_role_definitions: Sequence[Mapping[str, Any]] | None = None,
) -> OperationalDocumentType:
    normalized_code = str(code or "").strip().lower()
    if not normalized_code:
        raise ValidationError({"code": "Код типа обязателен."})
    document_type = OperationalDocumentType.objects.create(
        organization=actor.organization,
        code=normalized_code,
        name=name,
        short_name=short_name,
        description=description,
        created_by=actor,
    )
    revision = OperationalDocumentTypeRevision.objects.create(
        document_type=document_type,
        revision_number=1,
        number_prefix=str(number_prefix or "").strip().upper(),
        number_width=number_width,
        requires_workplace=requires_workplace,
        field_definitions=list(field_definitions),
        status_definitions=list(status_definitions or DEFAULT_STATUS_DEFINITIONS),
        transition_definitions=list(transition_definitions or DEFAULT_TRANSITION_DEFINITIONS),
        participant_role_definitions=list(
            participant_role_definitions or DEFAULT_PARTICIPANT_ROLE_DEFINITIONS
        ),
        created_by=actor,
    )
    publish_type_revision(revision=revision, actor=actor)
    return document_type


def current_published_revision(
    document_type: OperationalDocumentType,
) -> OperationalDocumentTypeRevision | None:
    return (
        document_type.revisions.filter(status=SchemaPublicationStatus.PUBLISHED)
        .order_by("-revision_number", "-pk")
        .first()
    )


def _aware(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


def _status_map(revision: OperationalDocumentTypeRevision) -> dict[str, dict[str, Any]]:
    return {str(item["code"]): dict(item) for item in revision.status_definitions}


def _initial_status(revision: OperationalDocumentTypeRevision) -> dict[str, Any]:
    matches = [item for item in revision.status_definitions if item.get("is_initial")]
    if len(matches) != 1:
        raise ValidationError("Редакция типа не содержит единственного начального состояния.")
    return dict(matches[0])


def available_transitions(record: OperationalDocumentRecord) -> list[dict[str, Any]]:
    statuses = _status_map(record.schema_revision)
    result: list[dict[str, Any]] = []
    for transition in record.schema_revision.transition_definitions:
        if transition.get("from") != record.status_code:
            continue
        target = statuses.get(str(transition.get("to")))
        if target is None:
            continue
        result.append({**dict(transition), "target": target})
    return result


def _json_value_and_display(
    definition: Mapping[str, Any],
    value: Any,
) -> tuple[Any, str]:
    field_type = str(definition["type"])
    if value in (None, ""):
        return None, ""
    if field_type in {FieldType.TEXT, FieldType.LONG_TEXT}:
        normalized = str(value).strip()
        return normalized, normalized
    if field_type == FieldType.INTEGER:
        try:
            normalized = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"Поле «{definition['label']}» должно быть целым числом.") from exc
        return normalized, str(normalized)
    if field_type == FieldType.DECIMAL:
        try:
            normalized_decimal = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValidationError(f"Поле «{definition['label']}» должно быть числом.") from exc
        normalized = format(normalized_decimal, "f")
        return normalized, normalized.replace(".", ",")
    if field_type == FieldType.BOOLEAN:
        normalized_bool = bool(value)
        return normalized_bool, "Да" if normalized_bool else "Нет"
    if field_type == FieldType.DATE:
        if isinstance(value, datetime):
            value = value.date()
        if not isinstance(value, date):
            raise ValidationError(f"Поле «{definition['label']}» должно быть датой.")
        return value.isoformat(), value.strftime("%d.%m.%Y")
    if field_type == FieldType.DATETIME:
        if not isinstance(value, datetime):
            raise ValidationError(f"Поле «{definition['label']}» должно содержать дату и время.")
        moment = _aware(value)
        return canonical_json(moment).strip('"'), timezone.localtime(moment).strftime("%d.%m.%Y %H:%M")
    if field_type == FieldType.CHOICE:
        normalized_choice = str(value).strip()
        options = {str(item["value"]): str(item["label"]) for item in definition.get("choices", [])}
        if normalized_choice not in options:
            raise ValidationError(f"Поле «{definition['label']}»: выбран неизвестный вариант.")
        return normalized_choice, options[normalized_choice]
    raise ValidationError(f"Поле «{definition['label']}»: неизвестный тип.")


def normalize_field_values(
    revision: OperationalDocumentTypeRevision,
    values: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    known_codes = {str(item["code"]) for item in revision.field_definitions}
    unknown = sorted(set(values) - known_codes)
    if unknown:
        raise ValidationError("Неизвестные поля: " + ", ".join(unknown))
    for definition in revision.field_definitions:
        code = str(definition["code"])
        raw_value = values.get(code)
        normalized, display = _json_value_and_display(definition, raw_value)
        missing = normalized in (None, "")
        if definition.get("required") and missing:
            raise ValidationError(f"Поле «{definition['label']}» обязательно.")
        result[code] = {
            "label": str(definition["label"]),
            "type": str(definition["type"]),
            "value": normalized,
            "display": display,
            "show_in_list": bool(definition.get("show_in_list")),
            "searchable": bool(definition.get("searchable", True)),
        }
    return result


def _unique_objects(items: Iterable[Any], label: str) -> list[Any]:
    result: list[Any] = []
    seen: set[int] = set()
    for item in items:
        if item.pk is None:
            raise ValidationError(f"{label}: несохранённый объект нельзя связать с записью.")
        if item.pk in seen:
            raise ValidationError(f"{label}: один объект указан более одного раза.")
        seen.add(item.pk)
        result.append(item)
    return result


def _validate_participants(
    revision: OperationalDocumentTypeRevision,
    organization_id: int,
    participant_map: Mapping[str, Iterable[Employee]],
) -> dict[str, list[Employee]]:
    role_map = {str(item["code"]): dict(item) for item in revision.participant_role_definitions}
    unknown = sorted(set(participant_map) - set(role_map))
    if unknown:
        raise ValidationError("Неизвестные роли участников: " + ", ".join(unknown))
    result: dict[str, list[Employee]] = {}
    for code, role in role_map.items():
        employees = _unique_objects(participant_map.get(code, []), f"Роль «{role['name']}»")
        if any(employee.organization_id != organization_id for employee in employees):
            raise ValidationError(f"Роль «{role['name']}»: сотрудник относится к другой организации.")
        if role.get("required") and not employees:
            raise ValidationError(f"Роль «{role['name']}» обязательна.")
        if not role.get("multiple") and len(employees) > 1:
            raise ValidationError(f"Для роли «{role['name']}» допускается только один сотрудник.")
        result[code] = employees
    return result


def _employee_snapshot(employee: Employee) -> dict[str, str]:
    return {
        "full_name": employee.full_name,
        "position": employee.position.name,
        "division": employee.division.name,
        "workplace": employee.workplace.name if employee.workplace_id else "",
    }


def _equipment_snapshot(equipment: EquipmentAsset, day: date) -> dict[str, str]:
    return {
        "code": equipment.code,
        "dispatcher_name": dispatcher_name_on(equipment, day),
        "site": equipment.site.short_name or equipment.site.name,
        "equipment_type": equipment.equipment_type.name,
    }


def _sync_participants(
    record: OperationalDocumentRecord,
    participants: Mapping[str, Sequence[Employee]],
) -> None:
    role_map = {str(item["code"]): dict(item) for item in record.schema_revision.participant_role_definitions}
    record.participants.all().delete()
    rows: list[OperationalDocumentParticipant] = []
    for role_code, employees in participants.items():
        role = role_map[role_code]
        for employee in employees:
            snapshot = _employee_snapshot(employee)
            rows.append(
                OperationalDocumentParticipant(
                    record=record,
                    role_code=role_code,
                    role_name_snapshot=str(role["name"]),
                    employee=employee,
                    employee_full_name_snapshot=snapshot["full_name"],
                    employee_position_snapshot=snapshot["position"],
                    employee_division_snapshot=snapshot["division"],
                    employee_workplace_snapshot=snapshot["workplace"],
                )
            )
    OperationalDocumentParticipant.objects.bulk_create(rows)


def _sync_equipment(
    record: OperationalDocumentRecord,
    equipment_assets: Sequence[EquipmentAsset],
) -> None:
    record.equipment_links.all().delete()
    day = timezone.localtime(record.event_at).date()
    rows: list[OperationalDocumentEquipmentLink] = []
    for equipment in equipment_assets:
        snapshot = _equipment_snapshot(equipment, day)
        rows.append(
            OperationalDocumentEquipmentLink(
                record=record,
                equipment=equipment,
                equipment_code_snapshot=snapshot["code"],
                dispatcher_name_snapshot=snapshot["dispatcher_name"],
                site_name_snapshot=snapshot["site"],
                equipment_type_snapshot=snapshot["equipment_type"],
            )
        )
    OperationalDocumentEquipmentLink.objects.bulk_create(rows)


def _sync_documents(
    record: OperationalDocumentRecord,
    documents: Sequence[Document],
) -> None:
    record.document_links.all().delete()
    rows = [
        OperationalDocumentExternalDocumentLink(
            record=record,
            document=document,
            link_type=DocumentLinkType.BASIS,
            registration_number_snapshot=document.registration_number,
            title_snapshot=document.title,
        )
        for document in documents
    ]
    OperationalDocumentExternalDocumentLink.objects.bulk_create(rows)


def _sync_relations(
    record: OperationalDocumentRecord,
    related_records: Sequence[OperationalDocumentRecord],
    actor: Employee,
) -> None:
    record.outgoing_relations.all().delete()
    rows = [
        OperationalDocumentRelation(
            source_record=record,
            target_record=target,
            relation_type=RecordRelationType.RELATED,
            relation_name_snapshot=RecordRelationType.RELATED.label,
            created_by=actor,
        )
        for target in related_records
    ]
    OperationalDocumentRelation.objects.bulk_create(rows)


def normalize_search_text(value: object) -> str:
    """Normalize text for database-independent Unicode substring search."""

    if value is None:
        return ""
    return unicodedata.normalize("NFKC", str(value)).casefold()


def _search_text(record: OperationalDocumentRecord) -> str:
    chunks = [
        record.registration_number,
        record.document_type.name,
        record.title,
        record.summary,
        record.workplace_name_snapshot,
        record.status_name_snapshot,
    ]
    chunks.extend(
        str(value.get("display") or "")
        for value in record.field_values.values()
        if value.get("searchable")
    )
    chunks.extend(record.participants.values_list("employee_full_name_snapshot", flat=True))
    chunks.extend(record.equipment_links.values_list("dispatcher_name_snapshot", flat=True))
    chunks.extend(record.document_links.values_list("title_snapshot", flat=True))
    rendered = "\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip())
    return normalize_search_text(rendered)


def build_record_snapshot(record: OperationalDocumentRecord) -> dict[str, Any]:
    snapshot = {
        "schema": "eod.operational-document-record.v1",
        "record": {
            "public_id": str(record.public_id),
            "registration_number": record.registration_number,
            "type": {
                "public_id": str(record.document_type.public_id),
                "code": record.document_type.code,
                "name": record.document_type.name,
                "schema_revision": record.schema_revision.revision_number,
                "schema_sha256": record.schema_revision.sha256,
            },
            "title": record.title,
            "summary": record.summary,
            "event_at": record.event_at,
            "workplace": {
                "code": record.workplace.code if record.workplace_id else "",
                "name": record.workplace_name_snapshot,
            },
            "status": {
                "code": record.status_code,
                "name": record.status_name_snapshot,
                "is_terminal": record.status_is_terminal,
            },
            "field_values": record.field_values,
            "version": record.version,
            "created_by": {
                "employee_public_id": str(record.created_by.public_id),
                "full_name": record.created_by_full_name_snapshot,
                "position": record.created_by_position_snapshot,
                "division": record.created_by_division_snapshot,
            },
        },
        "participants": [
            {
                "role_code": item.role_code,
                "role_name": item.role_name_snapshot,
                "employee_public_id": str(item.employee.public_id),
                "full_name": item.employee_full_name_snapshot,
                "position": item.employee_position_snapshot,
                "division": item.employee_division_snapshot,
                "workplace": item.employee_workplace_snapshot,
            }
            for item in record.participants.select_related("employee").order_by("role_code", "employee_id")
        ],
        "equipment": [
            {
                "equipment_public_id": str(item.equipment.public_id),
                "code": item.equipment_code_snapshot,
                "dispatcher_name": item.dispatcher_name_snapshot,
                "site": item.site_name_snapshot,
                "equipment_type": item.equipment_type_snapshot,
            }
            for item in record.equipment_links.select_related("equipment").order_by("equipment_id")
        ],
        "documents": [
            {
                "document_public_id": str(item.document.public_id),
                "link_type": item.link_type,
                "registration_number": item.registration_number_snapshot,
                "title": item.title_snapshot,
            }
            for item in record.document_links.select_related("document").order_by("document_id")
        ],
        "relations": [
            {
                "target_public_id": str(item.target_record.public_id),
                "target_registration_number": item.target_record.registration_number,
                "relation_type": item.relation_type,
                "relation_name": item.relation_name_snapshot,
            }
            for item in record.outgoing_relations.select_related("target_record").order_by("target_record_id")
        ],
    }
    return json.loads(canonical_json(snapshot))


def _append_record_revision(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    action: str,
    comment: str = "",
) -> OperationalDocumentRecordRevision:
    snapshot = build_record_snapshot(record)
    digest = sha256_text(canonical_json(snapshot))
    return OperationalDocumentRecordRevision.objects.create(
        record=record,
        revision_number=record.version,
        action=action,
        status_code_snapshot=record.status_code,
        status_name_snapshot=record.status_name_snapshot,
        snapshot=snapshot,
        sha256=digest,
        actor=actor,
        comment=comment.strip(),
    )


def _allocate_number(document_type: OperationalDocumentType, year: int) -> int:
    sequence, _created = OperationalDocumentNumberSequence.objects.select_for_update().get_or_create(
        document_type=document_type,
        year=year,
        defaults={"last_value": 0},
    )
    sequence.last_value += 1
    sequence.save(update_fields=("last_value", "updated_at"))
    return sequence.last_value


def _registration_number(
    revision: OperationalDocumentTypeRevision,
    year: int,
    value: int,
) -> str:
    return f"{revision.number_prefix}-{year}-{value:0{revision.number_width}d}"


def _validate_related_collections(
    *,
    organization_id: int,
    equipment_assets: Iterable[EquipmentAsset],
    documents: Iterable[Document],
    related_records: Iterable[OperationalDocumentRecord],
    current_record: OperationalDocumentRecord | None = None,
) -> tuple[list[EquipmentAsset], list[Document], list[OperationalDocumentRecord]]:
    equipment = _unique_objects(equipment_assets, "Оборудование")
    linked_documents = _unique_objects(documents, "Документы")
    linked_records = _unique_objects(related_records, "Связанные записи")
    if any(item.organization_id != organization_id for item in equipment):
        raise ValidationError("Оборудование относится к другой организации.")
    if any(item.organization_id != organization_id for item in linked_documents):
        raise ValidationError("Документ относится к другой организации.")
    if any(item.organization_id != organization_id for item in linked_records):
        raise ValidationError("Связанная запись относится к другой организации.")
    if current_record and any(item.pk == current_record.pk for item in linked_records):
        raise ValidationError("Запись нельзя связать саму с собой.")
    return equipment, linked_documents, linked_records


@transaction.atomic
def create_record(
    *,
    revision: OperationalDocumentTypeRevision,
    actor: Employee,
    title: str,
    summary: str,
    event_at: datetime,
    workplace: Workplace | None,
    field_values: Mapping[str, Any],
    participant_map: Mapping[str, Iterable[Employee]],
    equipment_assets: Iterable[EquipmentAsset] = (),
    documents: Iterable[Document] = (),
    related_records: Iterable[OperationalDocumentRecord] = (),
) -> OperationalDocumentRecord:
    revision = (
        OperationalDocumentTypeRevision.objects.select_for_update()
        .select_related("document_type", "document_type__organization")
        .get(pk=revision.pk)
    )
    if revision.status != SchemaPublicationStatus.PUBLISHED:
        raise ValidationError("Запись можно создать только по опубликованной редакции типа.")
    if actor.organization_id != revision.document_type.organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")
    if workplace and workplace.organization_id != actor.organization_id:
        raise ValidationError("Рабочее место относится к другой организации.")
    if revision.requires_workplace and workplace is None:
        raise ValidationError({"workplace": "Для этого типа документа требуется рабочее место."})
    normalized_values = normalize_field_values(revision, field_values)
    participants = _validate_participants(revision, actor.organization_id, participant_map)
    equipment, linked_documents, linked_records = _validate_related_collections(
        organization_id=actor.organization_id,
        equipment_assets=equipment_assets,
        documents=documents,
        related_records=related_records,
    )
    initial_status = _initial_status(revision)
    moment = _aware(event_at)
    year = timezone.localtime(moment).year
    sequence_value = _allocate_number(revision.document_type, year)
    creator_snapshot = _employee_snapshot(actor)
    record = OperationalDocumentRecord.objects.create(
        organization=actor.organization,
        document_type=revision.document_type,
        schema_revision=revision,
        sequence_year=year,
        sequence_value=sequence_value,
        registration_number=_registration_number(revision, year, sequence_value),
        title=title,
        summary=summary,
        workplace=workplace,
        workplace_name_snapshot=workplace.name if workplace else "",
        event_at=moment,
        status_code=str(initial_status["code"]),
        status_name_snapshot=str(initial_status["name"]),
        status_is_terminal=bool(initial_status.get("is_terminal")),
        field_values=normalized_values,
        created_by=actor,
        created_by_full_name_snapshot=creator_snapshot["full_name"],
        created_by_position_snapshot=creator_snapshot["position"],
        created_by_division_snapshot=creator_snapshot["division"],
        updated_by=actor,
        closed_at=timezone.now() if initial_status.get("is_terminal") else None,
    )
    _sync_participants(record, participants)
    _sync_equipment(record, equipment)
    _sync_documents(record, linked_documents)
    _sync_relations(record, linked_records, actor)
    record.search_text = _search_text(record)
    record.save(update_fields=("search_text", "updated_at"))
    revision_row = _append_record_revision(
        record=record,
        actor=actor,
        action=RecordRevisionAction.CREATED,
    )
    _audit(
        organization_id=actor.organization_id,
        actor=actor,
        event_type="RECORD_CREATED",
        entity_type="operational_document_record",
        entity_id=str(record.public_id),
        document_type=record.document_type,
        record=record,
        payload={
            "registration_number": record.registration_number,
            "revision_sha256": revision_row.sha256,
        },
    )
    return record


@transaction.atomic
def update_record(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    title: str,
    summary: str,
    event_at: datetime,
    workplace: Workplace | None,
    field_values: Mapping[str, Any],
    participant_map: Mapping[str, Iterable[Employee]],
    equipment_assets: Iterable[EquipmentAsset] = (),
    documents: Iterable[Document] = (),
    related_records: Iterable[OperationalDocumentRecord] = (),
    comment: str = "",
) -> OperationalDocumentRecord:
    locked = (
        OperationalDocumentRecord.objects.select_for_update()
        .select_related("schema_revision", "document_type", "organization")
        .get(pk=record.pk)
    )
    if actor.organization_id != locked.organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")
    if locked.status_is_terminal:
        raise ValidationError("Запись в конечном состоянии нельзя редактировать.")
    if workplace and workplace.organization_id != locked.organization_id:
        raise ValidationError("Рабочее место относится к другой организации.")
    if locked.schema_revision.requires_workplace and workplace is None:
        raise ValidationError({"workplace": "Для этого типа документа требуется рабочее место."})
    normalized_values = normalize_field_values(locked.schema_revision, field_values)
    participants = _validate_participants(
        locked.schema_revision,
        locked.organization_id,
        participant_map,
    )
    equipment, linked_documents, linked_records = _validate_related_collections(
        organization_id=locked.organization_id,
        equipment_assets=equipment_assets,
        documents=documents,
        related_records=related_records,
        current_record=locked,
    )
    locked.title = title
    locked.summary = summary
    locked.event_at = _aware(event_at)
    locked.workplace = workplace
    locked.workplace_name_snapshot = workplace.name if workplace else ""
    locked.field_values = normalized_values
    locked.updated_by = actor
    locked.version += 1
    locked.save()
    _sync_participants(locked, participants)
    _sync_equipment(locked, equipment)
    _sync_documents(locked, linked_documents)
    _sync_relations(locked, linked_records, actor)
    locked.search_text = _search_text(locked)
    locked.save(update_fields=("search_text", "updated_at"))
    revision_row = _append_record_revision(
        record=locked,
        actor=actor,
        action=RecordRevisionAction.UPDATED,
        comment=comment,
    )
    _audit(
        organization_id=locked.organization_id,
        actor=actor,
        event_type="RECORD_UPDATED",
        entity_type="operational_document_record",
        entity_id=str(locked.public_id),
        document_type=locked.document_type,
        record=locked,
        payload={"version": locked.version, "revision_sha256": revision_row.sha256},
    )
    return locked


@transaction.atomic
def transition_record(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    transition_code: str,
    comment: str = "",
) -> OperationalDocumentRecord:
    locked = (
        OperationalDocumentRecord.objects.select_for_update()
        .select_related("schema_revision", "document_type", "organization")
        .get(pk=record.pk)
    )
    if actor.organization_id != locked.organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")
    normalized_code = _normalized_code(transition_code, "Переход")
    transition = next(
        (
            dict(item)
            for item in locked.schema_revision.transition_definitions
            if item.get("code") == normalized_code and item.get("from") == locked.status_code
        ),
        None,
    )
    if transition is None:
        raise ValidationError("Переход из текущего состояния не разрешён.")
    normalized_comment = comment.strip()
    if transition.get("requires_comment") and not normalized_comment:
        raise ValidationError("Для этого перехода требуется комментарий.")
    target = _status_map(locked.schema_revision).get(str(transition["to"]))
    if target is None:
        raise ValidationError("Целевое состояние отсутствует в опубликованной редакции типа.")
    from_code = locked.status_code
    from_name = locked.status_name_snapshot
    locked.status_code = str(target["code"])
    locked.status_name_snapshot = str(target["name"])
    locked.status_is_terminal = bool(target.get("is_terminal"))
    locked.closed_at = timezone.now() if locked.status_is_terminal else None
    locked.updated_by = actor
    locked.version += 1
    locked.save()
    locked.search_text = _search_text(locked)
    locked.save(update_fields=("search_text", "updated_at"))
    revision_row = _append_record_revision(
        record=locked,
        actor=actor,
        action=RecordRevisionAction.TRANSITION,
        comment=normalized_comment,
    )
    _audit(
        organization_id=locked.organization_id,
        actor=actor,
        event_type="STATUS_CHANGED",
        entity_type="operational_document_record",
        entity_id=str(locked.public_id),
        document_type=locked.document_type,
        record=locked,
        payload={
            "transition_code": normalized_code,
            "from": {"code": from_code, "name": from_name},
            "to": {"code": locked.status_code, "name": locked.status_name_snapshot},
            "comment": normalized_comment,
            "revision_sha256": revision_row.sha256,
        },
    )
    return locked


def list_field_columns(revision: OperationalDocumentTypeRevision) -> list[dict[str, Any]]:
    return [dict(item) for item in revision.field_definitions if item.get("show_in_list")]


def field_display_rows(record: OperationalDocumentRecord) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for definition in record.schema_revision.field_definitions:
        value = record.field_values.get(str(definition["code"]), {})
        rows.append(
            {
                "code": definition["code"],
                "label": definition["label"],
                "display": value.get("display", ""),
                "is_empty": value.get("display", "") == "",
            }
        )
    return rows
