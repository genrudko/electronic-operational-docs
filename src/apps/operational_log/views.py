from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.organizations.models import InterfacePreference

from .form_contracts import OPERATIONAL_JOURNAL_FORM
from .models import OperationalJournal
from .services import (
    require_operational_employee,
    timeline_queryset,
    verify_entry_integrity,
)


def _accessible_journal(employee, journal_id: int) -> OperationalJournal:
    return get_object_or_404(
        OperationalJournal.objects.select_related(
            "organization",
            "workplace",
            "workplace__division",
        ),
        pk=journal_id,
        organization=employee.organization,
        is_active=True,
    )


@login_required
def registry(request: HttpRequest) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journals = list(
        OperationalJournal.objects.filter(
            organization=employee.organization,
            is_active=True,
        ).select_related("workplace", "workplace__division")
    )
    rows: list[dict[str, object]] = []
    total_entries = 0
    for journal in journals:
        entries = journal.entries.all()
        count = entries.count()
        total_entries += count
        rows.append(
            {
                "journal": journal,
                "entry_count": count,
                "last_entry": entries.order_by("-sequence_number").first(),
                "form_contract": OPERATIONAL_JOURNAL_FORM,
            }
        )
    return render(
        request,
        "operational_log/registry.html",
        {
            "rows": rows,
            "form_contract": OPERATIONAL_JOURNAL_FORM,
            "summary": {
                "journals": len(journals),
                "entries": total_entries,
            },
        },
    )


@login_required
def detail(request: HttpRequest, journal_id: int) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    entries = list(timeline_queryset(journal).order_by("sequence_number"))
    rows: list[dict[str, object]] = []
    integrity_failures = 0
    for entry in entries:
        try:
            integrity_ok = verify_entry_integrity(entry)
        except ValidationError:
            integrity_ok = False
            integrity_failures += 1
        rows.append({"entry": entry, "integrity_ok": integrity_ok})
    return render(
        request,
        "operational_log/detail.html",
        {
            "journal": journal,
            "rows": rows,
            "form_contract": OPERATIONAL_JOURNAL_FORM,
            "first_entry": entries[0] if entries else None,
            "last_entry": entries[-1] if entries else None,
            "summary": {
                "total": len(entries),
                "integrity_failures": integrity_failures,
            },
        },
    )


@require_POST
@login_required
def update_display(request: HttpRequest, journal_id: int) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    mode = request.POST.get("journal_heading_mode", "").strip().upper()
    allowed_modes = {
        value for value, _label in InterfacePreference.JournalHeadingMode.choices
    }
    if mode not in allowed_modes:
        return HttpResponseBadRequest("Неизвестный режим шапки оперативного журнала.")

    preferences, _ = InterfacePreference.objects.get_or_create(user=request.user)
    if preferences.journal_heading_mode != mode:
        preferences.journal_heading_mode = mode
        preferences.save(update_fields=("journal_heading_mode", "updated_at"))
    return redirect("operational_log:detail", journal_id=journal.pk)
