from __future__ import annotations

from collections.abc import Callable
from typing import Any

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
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponse],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponse | None:
        del view_func, view_args
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
                    public_id=view_kwargs.get("public_id"),
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
                    public_id=view_kwargs.get("type_public_id"),
                    organization=employee.organization,
                    code=DOCUMENT_TYPE_CODE,
                )
                .only("pk")
                .first()
            )
            if document_type is not None:
                return redirect("equipment_defects:create")
        return None
