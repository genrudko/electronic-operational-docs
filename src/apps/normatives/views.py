from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import (
    NormativeDocument,
    NormativeRevision,
    OrganizationConfigurationRevision,
    OrganizationNameRevision,
    PublicationStatus,
)
from .services import require_normative_employee


def _visible_documents(employee):
    return NormativeDocument.objects.filter(
        Q(organization__isnull=True) | Q(organization=employee.organization),
        is_active=True,
    )


@login_required
def registry(request: HttpRequest) -> HttpResponse:
    employee = require_normative_employee(request.user)
    documents = (
        _visible_documents(employee)
        .annotate(revision_count=Count("revisions", distinct=True))
        .order_by("scope", "short_title", "title")
    )
    name_revisions = OrganizationNameRevision.objects.filter(
        organization=employee.organization,
        status=PublicationStatus.PUBLISHED,
    ).order_by("-valid_from")
    configurations = OrganizationConfigurationRevision.objects.filter(
        organization=employee.organization,
        status=PublicationStatus.PUBLISHED,
    ).order_by("-revision_number")
    return render(
        request,
        "normatives/registry.html",
        {
            "documents": documents,
            "name_revisions": name_revisions,
            "configurations": configurations,
            "employee": employee,
        },
    )


@login_required
def document_detail(request: HttpRequest, code: str) -> HttpResponse:
    employee = require_normative_employee(request.user)
    document = get_object_or_404(_visible_documents(employee), code=code)
    revisions = document.revisions.prefetch_related("requirements").order_by("-revision_number")
    return render(
        request,
        "normatives/document_detail.html",
        {
            "document": document,
            "revisions": revisions,
        },
    )


@login_required
def revision_detail(
    request: HttpRequest,
    code: str,
    revision_number: int,
) -> HttpResponse:
    employee = require_normative_employee(request.user)
    document = get_object_or_404(_visible_documents(employee), code=code)
    revision = get_object_or_404(
        NormativeRevision.objects.select_related("approved_by").prefetch_related(
            "requirements__traces"
        ),
        document=document,
        revision_number=revision_number,
    )
    return render(
        request,
        "normatives/revision_detail.html",
        {
            "document": document,
            "revision": revision,
            "requirements": revision.requirements.prefetch_related("traces").all(),
        },
    )
