from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.documents.models import Document, DocumentVersion
from apps.organizations.models import Employee, Organization

from .models import (
    DocumentEquipmentLink,
    DocumentEquipmentSnapshot,
    EnergySite,
    EquipmentAlias,
    EquipmentAsset,
    EquipmentAuditEvent,
    EquipmentNameRevision,
    EquipmentType,
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
            return moment.astimezone(UTC).isoformat(timespec="microseconds").replace(
                "+00:00",
                "Z",
            )
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


def require_equipment_employee(user: Any) -> Employee:
    employee = employee_for_user(user)
    if employee is None:
        raise PermissionDenied(
            "Для просмотра реестра оборудования нужна персональная учётная запись."
        )
    return employee


def validate_actor(actor: Employee, organization_id: int) -> None:
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может изменять реестр.")
    if actor.organization_id != organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")


def audit(
    *,
    event_type: str,
    actor: Employee,
    equipment: EquipmentAsset | None = None,
    document_version: DocumentVersion | None = None,
    payload: dict[str, Any] | None = None,
) -> EquipmentAuditEvent:
    organization_id = (
        equipment.organization_id
        if equipment is not None
        else document_version.document.organization_id
        if document_version is not None
        else actor.organization_id
    )
    validate_actor(actor, organization_id)
    return EquipmentAuditEvent.objects.create(
        organization_id=organization_id,
        event_type=event_type,
        actor_employee=actor,
        equipment=equipment,
        document_version=document_version,
        payload=payload or {},
    )


def dispatcher_name_revision_on(
    equipment: EquipmentAsset,
    day: date | None = None,
) -> EquipmentNameRevision | None:
    target = day or timezone.localdate()
    return (
        equipment.dispatcher_name_revisions.filter(
            status=PublicationStatus.PUBLISHED,
            effective_from__lte=target,
        )
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gte=target))
        .order_by("-effective_from", "-revision_number")
        .first()
    )


def dispatcher_name_on(
    equipment: EquipmentAsset,
    day: date | None = None,
) -> str:
    revision = dispatcher_name_revision_on(equipment, day)
    return revision.dispatcher_name if revision is not None else equipment.technical_name


def equipment_label(equipment: EquipmentAsset) -> str:
    return (
        f"{dispatcher_name_on(equipment)} · "
        f"{equipment.equipment_type.name} · {equipment.code}"
    )


def hierarchy_assets(equipment: EquipmentAsset) -> list[EquipmentAsset]:
    result: list[EquipmentAsset] = []
    current: EquipmentAsset | None = equipment
    visited: set[int] = set()
    while current is not None:
        if current.pk in visited:
            raise ValidationError("Иерархия оборудования содержит цикл.")
        visited.add(current.pk)
        result.append(current)
        current = current.parent
    result.reverse()
    return result


def hierarchy_path(
    equipment: EquipmentAsset,
    day: date | None = None,
) -> str:
    return " / ".join(dispatcher_name_on(item, day) for item in hierarchy_assets(equipment))


def name_history_rows(equipment: EquipmentAsset) -> list[dict[str, Any]]:
    revisions = list(
        equipment.dispatcher_name_revisions.filter(
            status=PublicationStatus.PUBLISHED
        ).order_by("effective_from", "revision_number")
    )
    rows: list[dict[str, Any]] = []
    for index, revision in enumerate(revisions):
        next_start = (
            revisions[index + 1].effective_from
            if index + 1 < len(revisions)
            else None
        )
        derived_until = (
            next_start - timedelta(days=1)
            if next_start is not None
            else None
        )
        effective_until = revision.effective_until
        if derived_until is not None and (
            effective_until is None or derived_until < effective_until
        ):
            effective_until = derived_until
        rows.append(
            {
                "revision": revision,
                "effective_until": effective_until,
                "is_current": dispatcher_name_revision_on(equipment) == revision,
            }
        )
    rows.reverse()
    return rows


@transaction.atomic
def publish_equipment_name_revision(
    *,
    revision: EquipmentNameRevision,
    actor: Employee,
) -> EquipmentNameRevision:
    locked = (
        EquipmentNameRevision.objects.select_for_update()
        .select_related("equipment__organization")
        .get(pk=revision.pk)
    )
    validate_actor(actor, locked.equipment.organization_id)
    if locked.status != PublicationStatus.DRAFT:
        raise ValidationError("Редакция диспетчерского наименования уже опубликована.")
    locked.published_at = timezone.now()
    locked.approved_by = actor
    locked.digest = sha256_text(
        canonical_json(
            {
                "schema": "eod.equipment.dispatcher-name.v1",
                "equipment_public_id": str(locked.equipment.public_id),
                "equipment_code": locked.equipment.code,
                "revision_number": locked.revision_number,
                "dispatcher_name": locked.dispatcher_name,
                "effective_from": locked.effective_from,
                "effective_until": locked.effective_until,
                "basis_reference": locked.basis_reference,
            }
        )
    )
    locked.status = PublicationStatus.PUBLISHED
    locked.save(
        update_fields=(
            "status",
            "published_at",
            "approved_by",
            "digest",
        )
    )
    audit(
        event_type=EquipmentAuditEvent.EventType.NAME_PUBLISHED,
        actor=actor,
        equipment=locked.equipment,
        payload={
            "revision_number": locked.revision_number,
            "dispatcher_name": locked.dispatcher_name,
            "digest": locked.digest,
        },
    )
    return locked


def active_aliases(
    equipment: EquipmentAsset,
    day: date | None = None,
) -> list[EquipmentAlias]:
    target = day or timezone.localdate()
    return list(
        equipment.aliases.filter(valid_from__lte=target)
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=target))
        .order_by("alias")
    )


def resolve_equipment_alias(
    organization: Organization,
    value: str,
    day: date | None = None,
) -> EquipmentAsset | None:
    target = day or timezone.localdate()
    normalized = " ".join(value.split()).casefold()
    alias = (
        EquipmentAlias.objects.filter(
            organization=organization,
            normalized_alias=normalized,
            valid_from__lte=target,
        )
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=target))
        .select_related("equipment")
        .order_by("-valid_from")
        .first()
    )
    if alias is not None:
        return alias.equipment
    return (
        EquipmentAsset.objects.filter(
            organization=organization,
            code__iexact=value.strip(),
        )
        .order_by("pk")
        .first()
    )


def equipment_registry_rows(
    assets: Iterable[EquipmentAsset],
    day: date | None = None,
) -> list[dict[str, Any]]:
    target = day or timezone.localdate()
    rows: list[dict[str, Any]] = []
    for equipment in assets:
        revision = dispatcher_name_revision_on(equipment, target)
        rows.append(
            {
                "equipment": equipment,
                "display_name": (
                    revision.dispatcher_name
                    if revision is not None
                    else equipment.technical_name
                ),
                "name_revision": revision,
                "hierarchy_path": hierarchy_path(equipment, target),
            }
        )
    return rows


def build_site_tree(
    site: EnergySite,
    day: date | None = None,
) -> list[dict[str, Any]]:
    target = day or timezone.localdate()
    assets = list(
        EquipmentAsset.objects.filter(site=site)
        .select_related("parent", "equipment_type", "site")
        .order_by("code")
    )
    children: dict[int | None, list[EquipmentAsset]] = {}
    for equipment in assets:
        children.setdefault(equipment.parent_id, []).append(equipment)

    rows: list[dict[str, Any]] = []
    visited: set[int] = set()

    def visit(equipment: EquipmentAsset, level: int) -> None:
        if equipment.pk in visited:
            return
        visited.add(equipment.pk)
        rows.append(
            {
                "equipment": equipment,
                "level": level,
                "display_name": dispatcher_name_on(equipment, target),
            }
        )
        for child in children.get(equipment.pk, []):
            visit(child, level + 1)

    for root in children.get(None, []):
        visit(root, 0)
    for equipment in assets:
        if equipment.pk not in visited:
            visit(equipment, 0)
    return rows


def search_equipment(
    *,
    organization: Organization,
    query: str = "",
    site_code: str = "",
    type_code: str = "",
):
    queryset = EquipmentAsset.objects.filter(organization=organization).select_related(
        "site",
        "equipment_type",
        "parent",
    )
    if query.strip():
        value = query.strip()
        queryset = queryset.filter(
            Q(code__icontains=value)
            | Q(technical_name__icontains=value)
            | Q(dispatcher_name_revisions__dispatcher_name__icontains=value)
            | Q(aliases__alias__icontains=value)
        ).distinct()
    if site_code:
        queryset = queryset.filter(site__code=site_code)
    if type_code:
        queryset = queryset.filter(equipment_type__code=type_code)
    return queryset.order_by("site__name", "code")


@transaction.atomic
def set_document_equipment_links(
    *,
    document_version: DocumentVersion,
    actor: Employee,
    equipment_assets: Iterable[EquipmentAsset],
) -> list[DocumentEquipmentLink]:
    version = (
        DocumentVersion.objects.select_for_update()
        .select_related("document__organization")
        .get(pk=document_version.pk)
    )
    validate_actor(actor, version.document.organization_id)
    if version.status != DocumentVersion.Status.DRAFT:
        raise ValidationError(
            "Состав оборудования можно изменять только у черновой версии."
        )

    unique_assets: dict[int, EquipmentAsset] = {}
    for equipment in equipment_assets:
        if equipment.organization_id != version.document.organization_id:
            raise ValidationError(
                "Оборудование документа относится к другой организации."
            )
        unique_assets[equipment.pk] = equipment

    existing = {
        link.equipment_id: link
        for link in DocumentEquipmentLink.objects.filter(
            document_version=version
        ).select_related("document_version")
    }
    for equipment_id, link in existing.items():
        if equipment_id not in unique_assets:
            link.delete()

    for equipment_id, equipment in unique_assets.items():
        if equipment_id not in existing:
            DocumentEquipmentLink.objects.create(
                document=version.document,
                document_version=version,
                equipment=equipment,
                created_by=actor,
            )
    return list(
        DocumentEquipmentLink.objects.filter(document_version=version)
        .select_related(
            "equipment__site",
            "equipment__equipment_type",
            "equipment__parent",
        )
        .order_by("equipment__code")
    )


def document_equipment_preview(
    document: Document,
    day: date | None = None,
) -> list[dict[str, Any]]:
    if document.current_version_id is None:
        return []
    target = day or timezone.localdate()
    links = (
        DocumentEquipmentLink.objects.filter(
            document_version_id=document.current_version_id
        )
        .select_related(
            "equipment__site",
            "equipment__equipment_type",
            "equipment__parent",
        )
        .order_by("equipment__code")
    )
    rows: list[dict[str, Any]] = []
    for link in links:
        revision = dispatcher_name_revision_on(link.equipment, target)
        rows.append(
            {
                "public_id": link.equipment.public_id,
                "equipment": link.equipment,
                "code": link.equipment.code,
                "display_name": (
                    revision.dispatcher_name
                    if revision is not None
                    else link.equipment.technical_name
                ),
                "technical_name": link.equipment.technical_name,
                "type_name": link.equipment.equipment_type.name,
                "site_name": str(link.equipment.site),
                "hierarchy_path": hierarchy_path(link.equipment, target),
                "name_revision_number": (
                    revision.revision_number if revision is not None else None
                ),
                "frozen": False,
            }
        )
    return rows


@transaction.atomic
def freeze_document_equipment_links(
    *,
    document_version: DocumentVersion,
    actor: Employee,
    captured_at: datetime,
) -> list[DocumentEquipmentSnapshot]:
    version = (
        DocumentVersion.objects.select_for_update()
        .select_related("document__organization")
        .get(pk=document_version.pk)
    )
    validate_actor(actor, version.document.organization_id)
    if version.status != DocumentVersion.Status.REGISTERED:
        raise ValidationError(
            "Снимок оборудования создаётся только для зарегистрированной версии."
        )
    day = timezone.localtime(captured_at).date()
    links = list(
        DocumentEquipmentLink.objects.filter(document_version=version)
        .select_related(
            "equipment__site",
            "equipment__equipment_type",
            "equipment__parent",
        )
        .order_by("equipment__code")
    )
    snapshots: list[DocumentEquipmentSnapshot] = []
    for link in links:
        if hasattr(link, "snapshot"):
            raise ValidationError(
                "Снимок оборудования для этой связи уже существует."
            )
        equipment = link.equipment
        revision = dispatcher_name_revision_on(equipment, day)
        snapshot = DocumentEquipmentSnapshot.objects.create(
            link=link,
            document=version.document,
            document_version=version,
            equipment=equipment,
            equipment_public_id_snapshot=equipment.public_id,
            equipment_code_snapshot=equipment.code,
            dispatcher_name_snapshot=(
                revision.dispatcher_name
                if revision is not None
                else equipment.technical_name
            ),
            technical_name_snapshot=equipment.technical_name,
            equipment_type_code_snapshot=equipment.equipment_type.code,
            equipment_type_name_snapshot=equipment.equipment_type.name,
            site_code_snapshot=equipment.site.code,
            site_name_snapshot=str(equipment.site),
            hierarchy_path_snapshot=hierarchy_path(equipment, day),
            name_revision_number_snapshot=(
                revision.revision_number if revision is not None else None
            ),
            captured_at=captured_at,
        )
        snapshots.append(snapshot)
        audit(
            event_type=EquipmentAuditEvent.EventType.DOCUMENT_SNAPSHOT_CREATED,
            actor=actor,
            equipment=equipment,
            document_version=version,
            payload={
                "dispatcher_name_snapshot": snapshot.dispatcher_name_snapshot,
                "equipment_code_snapshot": snapshot.equipment_code_snapshot,
                "name_revision_number_snapshot": (
                    snapshot.name_revision_number_snapshot
                ),
            },
        )
    return snapshots


def equipment_snapshot_payload(
    document_version: DocumentVersion,
) -> list[dict[str, Any]]:
    snapshots = (
        DocumentEquipmentSnapshot.objects.filter(document_version=document_version)
        .order_by("equipment_code_snapshot", "pk")
    )
    return [
        {
            "equipment_public_id": str(item.equipment_public_id_snapshot),
            "equipment_code": item.equipment_code_snapshot,
            "dispatcher_name": item.dispatcher_name_snapshot,
            "technical_name": item.technical_name_snapshot,
            "equipment_type_code": item.equipment_type_code_snapshot,
            "equipment_type_name": item.equipment_type_name_snapshot,
            "site_code": item.site_code_snapshot,
            "site_name": item.site_name_snapshot,
            "hierarchy_path": item.hierarchy_path_snapshot,
            "name_revision_number": item.name_revision_number_snapshot,
            "captured_at": item.captured_at,
        }
        for item in snapshots
    ]


def document_equipment_rows(document: Document) -> list[dict[str, Any]]:
    if document.current_version_id is None:
        return []
    if document.status == Document.Status.REGISTERED:
        snapshots = (
            DocumentEquipmentSnapshot.objects.filter(
                document_version_id=document.current_version_id
            )
            .select_related("equipment")
            .order_by("equipment_code_snapshot")
        )
        return [
            {
                "public_id": item.equipment.public_id,
                "equipment": item.equipment,
                "code": item.equipment_code_snapshot,
                "display_name": item.dispatcher_name_snapshot,
                "technical_name": item.technical_name_snapshot,
                "type_name": item.equipment_type_name_snapshot,
                "site_name": item.site_name_snapshot,
                "hierarchy_path": item.hierarchy_path_snapshot,
                "name_revision_number": item.name_revision_number_snapshot,
                "frozen": True,
                "captured_at": item.captured_at,
            }
            for item in snapshots
        ]
    return document_equipment_preview(document)

SELECTOR_PAGE_SIZE = 50


def equipment_selector_item(
    equipment: EquipmentAsset,
    day: date | None = None,
) -> dict[str, Any]:
    revision = dispatcher_name_revision_on(equipment, day)
    return {
        "id": equipment.pk,
        "public_id": str(equipment.public_id),
        "code": equipment.code,
        "display_name": (
            revision.dispatcher_name
            if revision is not None
            else equipment.technical_name
        ),
        "technical_name": equipment.technical_name,
        "type_code": equipment.equipment_type.code,
        "type_name": equipment.equipment_type.name,
        "category": equipment.equipment_type.category,
        "category_label": equipment.equipment_type.get_category_display(),
        "site_code": equipment.site.code,
        "site_name": str(equipment.site),
        "status": equipment.status,
        "status_label": equipment.get_status_display(),
        "hierarchy_path": hierarchy_path(equipment, day),
    }


def equipment_selection_rows(assets: Iterable[EquipmentAsset]) -> list[dict[str, Any]]:
    return [
        equipment_selector_item(equipment)
        for equipment in assets
    ]


def equipment_selector_page(
    *,
    organization: Organization,
    query: str = "",
    site_code: str = "",
    category: str = "",
    type_code: str = "",
    page: int = 1,
) -> dict[str, Any]:
    queryset = search_equipment(
        organization=organization,
        query=query,
        site_code=site_code,
        type_code=type_code,
    )
    if category:
        queryset = queryset.filter(equipment_type__category=category)

    page_number = max(1, page)
    total = queryset.count()
    start = (page_number - 1) * SELECTOR_PAGE_SIZE
    end = start + SELECTOR_PAGE_SIZE
    assets = list(queryset[start:end])

    site_rows = EnergySite.objects.filter(
        organization=organization,
        is_active=True,
    ).order_by("name")
    type_rows = (
        EquipmentType.objects.filter(
            equipment_assets__organization=organization,
            is_active=True,
        )
        .distinct()
        .order_by("category", "name")
    )
    used_categories = set(type_rows.values_list("category", flat=True))
    category_labels = dict(EquipmentType.Category.choices)

    return {
        "items": equipment_selection_rows(assets),
        "page": page_number,
        "page_size": SELECTOR_PAGE_SIZE,
        "total": total,
        "has_more": end < total,
        "filters": {
            "sites": [
                {
                    "code": site.code,
                    "name": str(site),
                }
                for site in site_rows
            ],
            "categories": [
                {
                    "code": code,
                    "name": category_labels[code],
                }
                for code in category_labels
                if code in used_categories
            ],
            "types": [
                {
                    "code": equipment_type.code,
                    "name": equipment_type.name,
                    "category": equipment_type.category,
                }
                for equipment_type in type_rows
            ],
        },
    }
