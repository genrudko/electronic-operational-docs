from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.organizations.models import Employee

from .models import (
    RequirementKind,
    RevisionStatus,
    SourceKind,
    WorkplaceDocumentList,
)
from .services import current_revision, review_state


def _employee_for_request(request: HttpRequest) -> Employee:
    employee = (
        Employee.objects.select_related("organization", "division", "position", "workplace")
        .filter(user=request.user, is_active=True)
        .first()
    )
    if employee is None:
        raise PermissionDenied("Для просмотра перечней требуется действующий профиль сотрудника.")
    return employee


@login_required
def registry(request: HttpRequest) -> HttpResponse:
    employee = _employee_for_request(request)
    lists = list(
        WorkplaceDocumentList.objects.filter(
            organization=employee.organization,
            is_active=True,
        ).select_related("workplace", "workplace__division")
    )
    rows: list[dict[str, object]] = []
    storage_forms: set[str] = set()
    due_count = 0
    entry_count = 0
    for item in lists:
        revision = current_revision(item)
        state = review_state(revision) if revision else "MISSING"
        if state in {"OVERDUE", "DUE_SOON"}:
            due_count += 1
        if revision:
            entries = list(revision.entries.all())
            entry_count += len(entries)
            storage_forms.update(entry.get_storage_form_display() for entry in entries)
        rows.append({"document_list": item, "revision": revision, "review_state": state})

    context = {
        "rows": rows,
        "summary": {
            "lists": len(lists),
            "approved": sum(1 for row in rows if row["revision"] is not None),
            "entries": entry_count,
            "due": due_count,
        },
        "storage_forms": sorted(storage_forms),
    }
    return render(request, "workplace_docs/registry.html", context)


@login_required
def detail(
    request: HttpRequest,
    list_id: int,
    revision_number: int | None = None,
) -> HttpResponse:
    employee = _employee_for_request(request)
    document_list = get_object_or_404(
        WorkplaceDocumentList.objects.select_related(
            "organization",
            "workplace",
            "workplace__division",
        ),
        pk=list_id,
        organization=employee.organization,
    )
    revisions = document_list.revisions.filter(status=RevisionStatus.APPROVED).select_related(
        "approved_by",
        "approved_by__position",
    )
    if revision_number is None:
        revision = current_revision(document_list)
    else:
        revision = revisions.filter(revision_number=revision_number).first()
    if revision is None:
        raise Http404("Утверждённая редакция перечня не найдена.")

    entries = list(
        revision.entries.select_related("normative_document").order_by("display_order", "code")
    )
    history = list(revisions.order_by("-revision_number"))
    context = {
        "document_list": document_list,
        "revision": revision,
        "entries": entries,
        "history": history,
        "review_state": review_state(revision),
        "today": timezone.localdate(),
        "summary": {
            "total": len(entries),
            "mandatory": sum(
                1 for entry in entries if entry.requirement_kind == RequirementKind.MANDATORY
            ),
            "typical": sum(1 for entry in entries if entry.source_kind == SourceKind.TYPICAL),
            "local": sum(1 for entry in entries if entry.source_kind == SourceKind.LOCAL),
        },
    }
    return render(request, "workplace_docs/detail.html", context)
