from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .evidence_models import LegalModeDecision
from .evidence_services import (
    verify_evidence_event_integrity,
    verify_legal_mode_decision_integrity,
    visible_evidence_events,
    visible_legal_mode_decisions,
)
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


def _latest_decisions(employee) -> list[LegalModeDecision]:
    result: list[LegalModeDecision] = []
    seen: set[tuple[int | None, str]] = set()
    for decision in visible_legal_mode_decisions(employee).order_by(
        "organization_id", "code", "-decided_at", "-pk"
    ):
        key = (decision.organization_id, decision.code)
        if key in seen:
            continue
        seen.add(key)
        result.append(decision)
    return sorted(result, key=lambda item: (item.module_id, item.code))


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
def evidence_registry(request: HttpRequest) -> HttpResponse:
    employee = require_normative_employee(request.user)
    events = visible_evidence_events(employee).order_by("-occurred_at", "-pk")[:50]
    return render(
        request,
        "normatives/evidence_registry.html",
        {
            "employee": employee,
            "decisions": _latest_decisions(employee),
            "events": events,
        },
    )


@login_required
def legal_mode_decision_detail(
    request: HttpRequest,
    public_id,
) -> HttpResponse:
    employee = require_normative_employee(request.user)
    decision = get_object_or_404(
        visible_legal_mode_decisions(employee),
        public_id=public_id,
    )
    return render(
        request,
        "normatives/legal_mode_decision_detail.html",
        {
            "decision": decision,
            "integrity": verify_legal_mode_decision_integrity(decision),
        },
    )


@login_required
def evidence_event_detail(
    request: HttpRequest,
    public_id,
) -> HttpResponse:
    employee = require_normative_employee(request.user)
    event = get_object_or_404(
        visible_evidence_events(employee),
        public_id=public_id,
    )
    return render(
        request,
        "normatives/evidence_event_detail.html",
        {
            "event": event,
            "integrity": verify_evidence_event_integrity(event),
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
