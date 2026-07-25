from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.equipment.models import EquipmentAsset
from apps.equipment.services import dispatcher_name_on
from apps.organizations.models import Employee, Organization

from .models import (
    AdjacentSubjectRelation,
    AdjacentSubjectRelationRevision,
    DispatchingAuditEvent,
    ManagementObject,
    ManagementRevision,
    PublicationStatus,
    SupervisionObject,
    SupervisionRevision,
)


def canonical_json(value: dict[str, Any]) -> str:
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


def require_dispatching_employee(user: Any) -> Employee:
    employee = employee_for_user(user)
    if employee is None:
        raise PermissionDenied("Для просмотра управления и ведения нужна персональная учётная запись.")
    return employee


def validate_actor(actor: Employee, organization_id: int) -> None:
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может публиковать редакции.")
    if actor.organization_id != organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")


def _current_revision(queryset, day: date | None = None):
    target = day or timezone.localdate()
    return (
        queryset.filter(status=PublicationStatus.PUBLISHED, effective_from__lte=target)
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gte=target))
        .order_by("-effective_from", "-revision_number")
        .first()
    )


def current_management_revisions(
    management_object: ManagementObject,
    day: date | None = None,
) -> list[ManagementRevision]:
    target = day or timezone.localdate()
    return list(
        management_object.revisions.filter(
            status=PublicationStatus.PUBLISHED,
            effective_from__lte=target,
        )
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gte=target))
        .select_related("level", "subject")
        .order_by("level__rank", "subject__name")
    )


def current_management_revision(
    management_object: ManagementObject,
    day: date | None = None,
) -> ManagementRevision | None:
    revisions = current_management_revisions(management_object, day)
    return revisions[0] if revisions else None


def current_supervision_revisions(
    supervision_object: SupervisionObject,
    day: date | None = None,
) -> list[SupervisionRevision]:
    target = day or timezone.localdate()
    return list(
        supervision_object.revisions.filter(
            status=PublicationStatus.PUBLISHED,
            effective_from__lte=target,
        )
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gte=target))
        .select_related("level", "subject")
        .order_by("level__rank", "conduct_mode", "subject__name")
    )


def current_adjacent_revision(
    relation: AdjacentSubjectRelation,
    day: date | None = None,
) -> AdjacentSubjectRelationRevision | None:
    return _current_revision(relation.revisions.all(), day)


def _audit(
    *,
    event_type: str,
    actor: Employee,
    revision: ManagementRevision | SupervisionRevision | AdjacentSubjectRelationRevision,
) -> DispatchingAuditEvent:
    values: dict[str, Any] = {
        "organization_id": actor.organization_id,
        "event_type": event_type,
        "actor_employee": actor,
        "payload": {
            "revision_number": revision.revision_number,
            "digest": revision.digest,
        },
    }
    if isinstance(revision, ManagementRevision):
        values["management_revision"] = revision
    elif isinstance(revision, SupervisionRevision):
        values["supervision_revision"] = revision
    else:
        values["adjacent_revision"] = revision
    return DispatchingAuditEvent.objects.create(**values)


@transaction.atomic
def publish_management_revision(
    *,
    revision: ManagementRevision,
    actor: Employee,
) -> ManagementRevision:
    locked = (
        ManagementRevision.objects.select_for_update(of=("self",))
        .select_related(
            "management_object__equipment",
            "management_object__organization",
            "level",
            "subject",
            "basis_document",
        )
        .get(pk=revision.pk)
    )
    organization_id = locked.management_object.organization_id
    validate_actor(actor, organization_id)
    if locked.status != PublicationStatus.DRAFT:
        raise ValidationError("Редакция управления уже опубликована.")

    ManagementObject.objects.select_for_update().get(pk=locked.management_object_id)
    conflict = (
        ManagementRevision.objects.select_for_update()
        .filter(
            management_object=locked.management_object,
            level=locked.level,
            status=PublicationStatus.PUBLISHED,
            effective_from__lte=locked.effective_until or date.max,
        )
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gte=locked.effective_from))
        .exists()
    )
    if conflict:
        raise ValidationError("На этом уровне уже действует управляющий субъект для данного объекта.")

    locked.published_at = timezone.now()
    locked.published_by = actor
    locked.digest = sha256_text(
        canonical_json(
            {
                "schema": "eod.dispatching.management.v1",
                "equipment_public_id": str(locked.management_object.equipment.public_id),
                "revision_number": locked.revision_number,
                "level_code": locked.level.code,
                "subject_code": locked.subject.code,
                "effective_from": locked.effective_from,
                "effective_until": locked.effective_until,
                "basis_document_id": locked.basis_document_id,
                "basis_reference": locked.basis_reference,
                "change_summary": locked.change_summary,
            }
        )
    )
    locked.status = PublicationStatus.PUBLISHED
    locked.save(update_fields=("status", "published_at", "published_by", "digest"))
    _audit(
        event_type=DispatchingAuditEvent.EventType.MANAGEMENT_PUBLISHED,
        actor=actor,
        revision=locked,
    )
    return locked


@transaction.atomic
def publish_supervision_revision(
    *,
    revision: SupervisionRevision,
    actor: Employee,
) -> SupervisionRevision:
    locked = (
        SupervisionRevision.objects.select_for_update(of=("self",))
        .select_related(
            "supervision_object__equipment",
            "supervision_object__organization",
            "level",
            "subject",
            "basis_document",
        )
        .get(pk=revision.pk)
    )
    organization_id = locked.supervision_object.organization_id
    validate_actor(actor, organization_id)
    if locked.status != PublicationStatus.DRAFT:
        raise ValidationError("Редакция ведения уже опубликована.")

    locked.published_at = timezone.now()
    locked.published_by = actor
    locked.digest = sha256_text(
        canonical_json(
            {
                "schema": "eod.dispatching.supervision.v2",
                "equipment_public_id": str(locked.supervision_object.equipment.public_id),
                "revision_number": locked.revision_number,
                "level_code": locked.level.code,
                "subject_code": locked.subject.code,
                "conduct_mode": locked.conduct_mode,
                "information_only": locked.is_information_only,
                "effective_from": locked.effective_from,
                "effective_until": locked.effective_until,
                "basis_document_id": locked.basis_document_id,
                "basis_reference": locked.basis_reference,
                "change_summary": locked.change_summary,
            }
        )
    )
    locked.status = PublicationStatus.PUBLISHED
    locked.save(update_fields=("status", "published_at", "published_by", "digest"))
    _audit(
        event_type=DispatchingAuditEvent.EventType.SUPERVISION_PUBLISHED,
        actor=actor,
        revision=locked,
    )
    return locked


@transaction.atomic
def publish_adjacent_relation_revision(
    *,
    revision: AdjacentSubjectRelationRevision,
    actor: Employee,
) -> AdjacentSubjectRelationRevision:
    locked = (
        AdjacentSubjectRelationRevision.objects.select_for_update(of=("self",))
        .select_related(
            "relation__organization",
            "relation__source_subject",
            "relation__target_subject",
            "basis_document",
        )
        .get(pk=revision.pk)
    )
    validate_actor(actor, locked.relation.organization_id)
    if locked.status != PublicationStatus.DRAFT:
        raise ValidationError("Редакция взаимодействия уже опубликована.")

    locked.published_at = timezone.now()
    locked.published_by = actor
    locked.digest = sha256_text(
        canonical_json(
            {
                "schema": "eod.dispatching.adjacent-subjects.v1",
                "relation_code": locked.relation.code,
                "source_subject_code": locked.relation.source_subject.code,
                "target_subject_code": locked.relation.target_subject.code,
                "revision_number": locked.revision_number,
                "effective_from": locked.effective_from,
                "effective_until": locked.effective_until,
                "interaction_scope": locked.interaction_scope,
                "communication_rules": locked.communication_rules,
                "basis_document_id": locked.basis_document_id,
                "basis_reference": locked.basis_reference,
                "change_summary": locked.change_summary,
            }
        )
    )
    locked.status = PublicationStatus.PUBLISHED
    locked.save(update_fields=("status", "published_at", "published_by", "digest"))
    _audit(
        event_type=DispatchingAuditEvent.EventType.ADJACENCY_PUBLISHED,
        actor=actor,
        revision=locked,
    )
    return locked


def dispatching_registry_rows(
    *,
    organization: Organization,
    query: str = "",
    level_type: str = "",
    day: date | None = None,
) -> list[dict[str, Any]]:
    assets = (
        EquipmentAsset.objects.filter(organization=organization)
        .filter(Q(management_object__isnull=False) | Q(supervision_object__isnull=False))
        .select_related(
            "site",
            "equipment_type",
            "management_object",
            "supervision_object",
        )
        .distinct()
        .order_by("site__name", "code")
    )
    if query.strip():
        value = query.strip()
        assets = assets.filter(
            Q(code__icontains=value)
            | Q(technical_name__icontains=value)
            | Q(dispatcher_name_revisions__dispatcher_name__icontains=value)
            | Q(management_object__revisions__subject__name__icontains=value)
            | Q(supervision_object__revisions__subject__name__icontains=value)
        ).distinct()

    rows: list[dict[str, Any]] = []
    for equipment in assets:
        management = (
            current_management_revisions(equipment.management_object, day)
            if hasattr(equipment, "management_object")
            else []
        )
        supervision = (
            current_supervision_revisions(equipment.supervision_object, day)
            if hasattr(equipment, "supervision_object")
            else []
        )
        if level_type:
            management_matches = any(item.level.level_type == level_type for item in management)
            supervision_matches = any(item.level.level_type == level_type for item in supervision)
            if not management_matches and not supervision_matches:
                continue
        rows.append(
            {
                "equipment": equipment,
                "display_name": dispatcher_name_on(equipment, day),
                "management": management,
                "supervision": supervision,
            }
        )
    return rows
