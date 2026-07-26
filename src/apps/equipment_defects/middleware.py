from __future__ import annotations

from collections.abc import Callable

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from apps.operational_documents.models import (
    OperationalDocumentRecord,
    OperationalDocumentType,
)

from .constants import DOCUMENT_TYPE_CODE


GENERIC_RECORD_ROUTES = {
    "record_detail",
    "record_edit",
    "record_transition",
}


class EquipmentDefectRouteGuardMiddleware:
    """Keep source-bound defect work out of the generic schema-driven UI."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self._specialized_redirect(request)
        if response is not None:
            return response
        return self.get_response(request)

    def _specialized_redirect(self, request: HttpRequest) -> HttpResponse | None:
        match = request.resolver_match
        if match is None or match.namespace != "operational_documents":
            return None
        if not request.user.is_authenticated:
            return None
        try:
            employee = request.user.employee_profile
        except (AttributeError, ObjectDoesNotExist):
            return None

        if match.url_name in GENERIC_RECORD_ROUTES:
            record = (
                OperationalDocumentRecord.objects.filter(
                    public_id=match.kwargs.get("public_id"),
                    organization=employee.organization,
                    document_type__code=DOCUMENT_TYPE_CODE,
                )
                .only("public_id")
                .first()
            )
            if record is not None:
                return redirect("equipment_defects:detail", public_id=record.public_id)

        if match.url_name == "record_create":
            document_type = (
                OperationalDocumentType.objects.filter(
                    public_id=match.kwargs.get("type_public_id"),
                    organization=employee.organization,
                    code=DOCUMENT_TYPE_CODE,
                )
                .only("pk")
                .first()
            )
            if document_type is not None:
                return redirect("equipment_defects:create")
        return None
