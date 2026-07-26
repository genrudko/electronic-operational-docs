from __future__ import annotations

from typing import Any


def source_bound_form_runtime_inventory() -> list[dict[str, Any]]:
    """Inventory approved journal forms separately from installed runtime types.

    Catalog presence, an installed type, a published type and runtime records are
    intentionally separate facts. A catalog declaration alone is never treated
    as an implemented journal.
    """

    from apps.operational_documents.journal_forms import APPROVED_JOURNAL_FORMS
    from apps.operational_documents.models import (
        OperationalDocumentRecord,
        OperationalDocumentType,
        OperationalDocumentTypeRevision,
        SchemaPublicationStatus,
    )

    rows: list[dict[str, Any]] = []
    for form in APPROVED_JOURNAL_FORMS:
        types = OperationalDocumentType.objects.filter(code=form.code)
        type_ids = list(types.values_list("pk", flat=True))
        published_revision_count = (
            OperationalDocumentTypeRevision.objects.filter(
                document_type_id__in=type_ids,
                status=SchemaPublicationStatus.PUBLISHED,
            ).count()
            if type_ids
            else 0
        )
        published_type_count = (
            OperationalDocumentType.objects.filter(
                pk__in=type_ids,
                revisions__status=SchemaPublicationStatus.PUBLISHED,
            )
            .distinct()
            .count()
            if type_ids
            else 0
        )
        record_count = (
            OperationalDocumentRecord.objects.filter(
                document_type_id__in=type_ids,
            ).count()
            if type_ids
            else 0
        )
        rows.append(
            {
                "code": form.code,
                "name": form.name,
                "purpose": form.purpose,
                "source_document": form.source_document,
                "source_section": form.source_section,
                "source_appendix": form.source_appendix,
                "catalog_present": True,
                "installed_type_count": len(type_ids),
                "published_revision_count": published_revision_count,
                "published_type_count": published_type_count,
                "record_count": record_count,
            }
        )
    return rows
