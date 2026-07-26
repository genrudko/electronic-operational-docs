from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from apps.operational_documents.models import (
    OperationalDocumentType,
    OperationalDocumentTypeRevision,
    SchemaPublicationStatus,
)
from apps.operational_documents.services import (
    current_published_revision,
    normalize_field_definitions,
    normalize_participant_role_definitions,
    normalize_status_definitions,
    normalize_transition_definitions,
    publish_type_revision,
)
from apps.organizations.models import Employee

from ..constants import (
    DOCUMENT_TYPE_CODE,
    DOCUMENT_TYPE_NAME,
    DOCUMENT_TYPE_SHORT_NAME,
    FIELD_DEFINITIONS,
    NUMBER_PREFIX,
    NUMBER_WIDTH,
    PARTICIPANT_ROLE_DEFINITIONS,
    SOURCE_APPENDIX,
    SOURCE_DOCUMENT,
    SOURCE_SECTION,
    STATUS_DEFINITIONS,
    TRANSITION_DEFINITIONS,
)


SOURCE_DESCRIPTION = (
    "Source-bound форма по "
    f"{SOURCE_DOCUMENT}, раздел {SOURCE_SECTION}, приложение № {SOURCE_APPENDIX}. "
    "Электронный справочно-контрольный и демонстрационный контур с печатным "
    "представлением утверждённой бумажной формы."
)


def expected_contract() -> dict[str, Any]:
    statuses = normalize_status_definitions(STATUS_DEFINITIONS)
    return {
        "fields": normalize_field_definitions(FIELD_DEFINITIONS),
        "roles": normalize_participant_role_definitions(PARTICIPANT_ROLE_DEFINITIONS),
        "statuses": statuses,
        "transitions": normalize_transition_definitions(TRANSITION_DEFINITIONS, statuses),
    }


def validate_installed_revision(revision: OperationalDocumentTypeRevision) -> None:
    expected = expected_contract()
    mismatches: list[str] = []
    if revision.number_prefix != NUMBER_PREFIX:
        mismatches.append("префикс номера")
    if revision.number_width != NUMBER_WIDTH:
        mismatches.append("разрядность номера")
    if not revision.requires_workplace:
        mismatches.append("обязательность рабочего места")
    if revision.field_definitions != expected["fields"]:
        mismatches.append("поля")
    if revision.participant_role_definitions != expected["roles"]:
        mismatches.append("роли участников")
    if revision.status_definitions != expected["statuses"]:
        mismatches.append("состояния")
    if revision.transition_definitions != expected["transitions"]:
        mismatches.append("переходы")
    if mismatches:
        raise ValidationError(
            "Опубликованная форма журнала дефектов не соответствует приложению № 8: "
            + ", ".join(mismatches)
            + ". Опубликованная редакция не изменена автоматически."
        )


@transaction.atomic
def ensure_defect_document_type(actor: Employee) -> OperationalDocumentTypeRevision:
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может установить форму журнала.")

    try:
        document_type = OperationalDocumentType.objects.select_for_update().get(
            organization=actor.organization,
            code=DOCUMENT_TYPE_CODE,
        )
    except OperationalDocumentType.DoesNotExist:
        document_type = OperationalDocumentType.objects.create(
            organization=actor.organization,
            code=DOCUMENT_TYPE_CODE,
            name=DOCUMENT_TYPE_NAME,
            short_name=DOCUMENT_TYPE_SHORT_NAME,
            description=SOURCE_DESCRIPTION,
            created_by=actor,
        )
    else:
        if document_type.name != DOCUMENT_TYPE_NAME:
            raise ValidationError(
                "Системный код журнала дефектов уже занят типом с другим наименованием."
            )

    published = current_published_revision(document_type)
    if published is not None:
        validate_installed_revision(published)
        return published

    revision_number = (
        document_type.revisions.aggregate(maximum=Max("revision_number"))["maximum"] or 0
    ) + 1
    revision = OperationalDocumentTypeRevision.objects.create(
        document_type=document_type,
        revision_number=revision_number,
        number_prefix=NUMBER_PREFIX,
        number_width=NUMBER_WIDTH,
        requires_workplace=True,
        field_definitions=FIELD_DEFINITIONS,
        participant_role_definitions=PARTICIPANT_ROLE_DEFINITIONS,
        status_definitions=STATUS_DEFINITIONS,
        transition_definitions=TRANSITION_DEFINITIONS,
        created_by=actor,
    )
    published = publish_type_revision(revision=revision, actor=actor)
    validate_installed_revision(published)
    return published


def installed_defect_revision_for(actor: Employee) -> OperationalDocumentTypeRevision:
    revision = ensure_defect_document_type(actor)
    if revision.status != SchemaPublicationStatus.PUBLISHED:
        raise ValidationError("Форма журнала дефектов не опубликована.")
    return revision
