from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.operational_documents.services import require_operational_document_employee
from apps.operational_log.models import OperationalLogEntry
from apps.system.module_registry import EntryPointClass

from . import views
from .services import require_defect_opj_link_access


@login_required
@require_http_methods(["GET", "POST"])
def create_from_operational_log(
    request: HttpRequest,
    entry_id: int,
) -> HttpResponse:
    """Fail closed before exposing the OPJ -> DEFECT creation surface."""

    employee = require_operational_document_employee(request.user)
    source_entry = get_object_or_404(
        OperationalLogEntry.objects.select_related(
            "journal",
            "journal__workplace",
        ),
        pk=entry_id,
        journal__organization=employee.organization,
    )
    require_defect_opj_link_access(
        organization_id=employee.organization_id,
        workplace_id=source_entry.journal.workplace_id,
        entry_point_class=EntryPointClass.HTTP_ROUTE,
    )
    return views.create_from_operational_log(request, entry_id)
