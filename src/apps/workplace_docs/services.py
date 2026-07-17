from __future__ import annotations

import calendar
import hashlib
import json
from datetime import date, timedelta
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.organizations.models import Employee, RoleAssignment

from .models import (
    RevisionStatus,
    WorkplaceDocumentAuditEvent,
    WorkplaceDocumentList,
    WorkplaceDocumentRevision,
)

DIRECT_APPROVER_ROLE = "organization_admin"


def canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def add_calendar_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def has_direct_approver_role(actor: Employee, day: date | None = None) -> bool:
    current = day or timezone.localdate()
    return (
        RoleAssignment.objects.filter(
            employee=actor,
            role__code=DIRECT_APPROVER_ROLE,
            is_active=True,
            valid_from__lte=current,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=current))
        .exists()
    )


def build_revision_snapshot(revision: WorkplaceDocumentRevision) -> dict[str, Any]:
    entries = revision.entries.select_related("normative_document").order_by(
        "display_order", "code"
    )
    return {
        "schema_version": "workplace-document-list.v1",
        "list": {
            "id": revision.document_list_id,
            "code": revision.document_list.code,
            "title": revision.document_list.title,
            "organization_id": revision.document_list.organization_id,
            "workplace_id": revision.document_list.workplace_id,
            "workplace": revision.document_list.workplace.name,
        },
        "revision": {
            "number": revision.revision_number,
            "status": revision.status,
            "effective_from": revision.effective_from.isoformat(),
            "effective_until": (
                revision.effective_until.isoformat() if revision.effective_until else None
            ),
            "review_period_months": revision.review_period_months,
            "next_review_date": (
                revision.next_review_date.isoformat() if revision.next_review_date else None
            ),
            "change_summary": revision.change_summary,
            "approved_by": {
                "employee_id": revision.approved_by_id,
                "full_name": revision.approved_by.full_name if revision.approved_by_id else "",
                "position": (
                    revision.approved_by.position.name if revision.approved_by_id else ""
                ),
            },
            "approved_at": revision.approved_at.isoformat() if revision.approved_at else None,
        },
        "entries": [
            {
                "code": entry.code,
                "title": entry.title,
                "source_kind": entry.source_kind,
                "requirement_kind": entry.requirement_kind,
                "applicability_text": entry.applicability_text,
                "storage_form": entry.storage_form,
                "normative_document": (
                    {
                        "id": entry.normative_document_id,
                        "code": entry.normative_document.code,
                        "title": str(entry.normative_document),
                    }
                    if entry.normative_document_id
                    else None
                ),
                "normative_clause": entry.normative_clause,
                "basis_text": entry.basis_text,
                "notes": entry.notes,
                "display_order": entry.display_order,
            }
            for entry in entries
        ],
    }


@transaction.atomic
def approve_revision(
    *,
    revision: WorkplaceDocumentRevision,
    actor: Employee,
) -> WorkplaceDocumentRevision:
    locked = (
        WorkplaceDocumentRevision.objects.select_for_update()
        .select_related(
            "document_list",
            "document_list__workplace",
            "approved_by",
            "approved_by__position",
        )
        .get(pk=revision.pk)
    )
    if locked.status != RevisionStatus.DRAFT:
        raise ValidationError("Утвердить можно только черновик редакции.")
    if locked.document_list.organization_id != actor.organization_id:
        raise PermissionDenied("Нельзя утверждать перечень другой организации.")
    if not has_direct_approver_role(actor):
        raise PermissionDenied(
            "Для утверждения требуется прямое назначение роли администратора справочников."
        )
    if not locked.document_list.is_active:
        raise ValidationError("Неактивный перечень нельзя утверждать.")

    entries = list(locked.entries.select_related("normative_document"))
    if not entries:
        raise ValidationError("Нельзя утвердить пустой перечень документации.")
    for entry in entries:
        entry.full_clean()

    overlaps = (
        WorkplaceDocumentRevision.objects.filter(
            document_list=locked.document_list,
            status=RevisionStatus.APPROVED,
        )
        .exclude(pk=locked.pk)
        .filter(effective_from__lte=locked.effective_until or date.max)
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gte=locked.effective_from))
    )
    if overlaps.exists():
        raise ValidationError("Период действия пересекается с другой утверждённой редакцией.")

    locked.status = RevisionStatus.APPROVED
    locked.approved_by = actor
    locked.approved_at = timezone.now()
    locked.next_review_date = add_calendar_months(
        locked.effective_from,
        locked.review_period_months,
    )
    snapshot = build_revision_snapshot(locked)
    locked.digest = sha256_text(canonical_json(snapshot))
    locked.save()

    WorkplaceDocumentAuditEvent.objects.create(
        document_list=locked.document_list,
        revision=locked,
        event_type=WorkplaceDocumentAuditEvent.EventType.REVISION_APPROVED,
        actor=actor,
        event_at=locked.approved_at,
        snapshot=snapshot,
        digest=locked.digest,
    )
    return locked


def current_revision(
    document_list: WorkplaceDocumentList,
    day: date | None = None,
) -> WorkplaceDocumentRevision | None:
    current = day or timezone.localdate()
    return (
        document_list.revisions.filter(
            status=RevisionStatus.APPROVED,
            effective_from__lte=current,
        )
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gte=current))
        .select_related("approved_by", "approved_by__position")
        .order_by("-effective_from", "-revision_number")
        .first()
    )


def review_state(
    revision: WorkplaceDocumentRevision,
    day: date | None = None,
) -> str:
    current = day or timezone.localdate()
    if revision.next_review_date is None:
        return "UNKNOWN"
    if revision.next_review_date < current:
        return "OVERDUE"
    if revision.next_review_date <= current + timedelta(days=30):
        return "DUE_SOON"
    return "CURRENT"
