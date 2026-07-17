from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import EntryForm, OperationalJournal
from .services import (
    require_operational_employee,
    timeline_queryset,
    verify_entry_integrity,
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
    typed_entries = 0
    free_entries = 0
    for journal in journals:
        entries = journal.entries.all()
        count = entries.count()
        typed = entries.filter(entry_form=EntryForm.TYPED).count()
        total_entries += count
        typed_entries += typed
        free_entries += count - typed
        rows.append(
            {
                "journal": journal,
                "entry_count": count,
                "last_entry": entries.order_by("-sequence_number").first(),
            }
        )
    return render(
        request,
        "operational_log/registry.html",
        {
            "rows": rows,
            "summary": {
                "journals": len(journals),
                "entries": total_entries,
                "typed": typed_entries,
                "free": free_entries,
            },
        },
    )


@login_required
def detail(request: HttpRequest, journal_id: int) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = get_object_or_404(
        OperationalJournal.objects.select_related(
            "organization",
            "workplace",
            "workplace__division",
        ),
        pk=journal_id,
        organization=employee.organization,
        is_active=True,
    )
    entries = list(timeline_queryset(journal))
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
            "summary": {
                "total": len(entries),
                "typed": sum(
                    1 for entry in entries if entry.entry_form == EntryForm.TYPED
                ),
                "free": sum(
                    1 for entry in entries if entry.entry_form == EntryForm.FREE_TEXT
                ),
                "integrity_failures": integrity_failures,
            },
        },
    )
