from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.documents.services import employee_for_user
from apps.organizations.models import Employee, Organization

from .models import (
    NormativeRevision,
    OrganizationConfigurationRevision,
    OrganizationNameRevision,
    PublicationStatus,
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


def require_normative_employee(user: Any) -> Employee:
    employee = employee_for_user(user)
    if employee is None:
        raise PermissionDenied("Для просмотра нормативного реестра нужна персональная учётная запись.")
    return employee


def _validate_actor_for_organization(
    actor: Employee,
    organization: Organization | None,
) -> None:
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может публиковать редакции.")
    if organization is not None and actor.organization_id != organization.pk:
        raise ValidationError("Сотрудник относится к другой организации.")


def _normative_payload(revision: NormativeRevision) -> dict[str, Any]:
    requirements = [
        {
            "code": requirement.code,
            "clause": requirement.clause,
            "title": requirement.title,
            "requirement_text": requirement.requirement_text,
            "applicability_text": requirement.applicability_text,
            "is_mandatory": requirement.is_mandatory,
            "display_order": requirement.display_order,
        }
        for requirement in revision.requirements.order_by("display_order", "code")
    ]
    return {
        "schema": "eod.normative.revision.v1",
        "document": {
            "code": revision.document.code,
            "title": revision.document.title,
            "short_title": revision.document.short_title,
            "scope": revision.document.scope,
            "issuer": revision.document.issuer,
            "document_number": revision.document.document_number,
            "document_date": revision.document.document_date,
            "organization_id": revision.document.organization_id,
        },
        "revision": {
            "revision_number": revision.revision_number,
            "effective_from": revision.effective_from,
            "effective_until": revision.effective_until,
            "source_reference": revision.source_reference,
            "change_summary": revision.change_summary,
        },
        "requirements": requirements,
    }


@transaction.atomic
def publish_normative_revision(
    *,
    revision: NormativeRevision,
    actor: Employee,
) -> NormativeRevision:
    locked = (
        NormativeRevision.objects.select_for_update()
        .select_related("document")
        .get(pk=revision.pk)
    )
    _validate_actor_for_organization(actor, locked.document.organization)
    if locked.status != PublicationStatus.DRAFT:
        raise ValidationError("Редакция уже опубликована.")
    if not locked.requirements.exists():
        raise ValidationError("Нельзя опубликовать редакцию без нормативных требований.")

    locked.published_at = timezone.now()
    locked.approved_by = actor
    locked.digest = sha256_text(canonical_json(_normative_payload(locked)))
    locked.status = PublicationStatus.PUBLISHED
    locked.save(
        update_fields=(
            "status",
            "approved_by",
            "published_at",
            "digest",
        )
    )
    return locked


@transaction.atomic
def publish_organization_name_revision(
    *,
    revision: OrganizationNameRevision,
    actor: Employee,
) -> OrganizationNameRevision:
    locked = (
        OrganizationNameRevision.objects.select_for_update()
        .select_related("organization")
        .get(pk=revision.pk)
    )
    _validate_actor_for_organization(actor, locked.organization)
    if locked.status != PublicationStatus.DRAFT:
        raise ValidationError("Редакция наименования уже опубликована.")
    locked.status = PublicationStatus.PUBLISHED
    locked.published_at = timezone.now()
    locked.save(update_fields=("status", "published_at"))
    return locked


@transaction.atomic
def publish_configuration_revision(
    *,
    revision: OrganizationConfigurationRevision,
    actor: Employee,
) -> OrganizationConfigurationRevision:
    locked = (
        OrganizationConfigurationRevision.objects.select_for_update()
        .select_related("organization")
        .get(pk=revision.pk)
    )
    _validate_actor_for_organization(actor, locked.organization)
    if locked.status != PublicationStatus.DRAFT:
        raise ValidationError("Редакция конфигурации уже опубликована.")
    locked.published_at = timezone.now()
    locked.digest = sha256_text(
        canonical_json(
            {
                "schema": "eod.organization.configuration.v1",
                "organization_id": locked.organization_id,
                "revision_number": locked.revision_number,
                "effective_from": locked.effective_from,
                "effective_until": locked.effective_until,
                "configuration": locked.configuration,
                "change_summary": locked.change_summary,
            }
        )
    )
    locked.status = PublicationStatus.PUBLISHED
    locked.save(update_fields=("status", "published_at", "digest"))
    return locked


def organization_name_on(
    organization: Organization,
    day: date | None = None,
) -> OrganizationNameRevision | None:
    target = day or timezone.localdate()
    return (
        OrganizationNameRevision.objects.filter(
            organization=organization,
            status=PublicationStatus.PUBLISHED,
            valid_from__lte=target,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=target))
        .order_by("-valid_from")
        .first()
    )
