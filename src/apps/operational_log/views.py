from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from apps.organizations.models import InterfacePreference

from .form_contracts import OPERATIONAL_JOURNAL_FORM
from .forms import (
    DraftEntryAutoSaveForm,
    JournalDisplayPreferenceForm,
    ShiftOpenForm,
)
from .models import (
    OperationalDraftEntry,
    OperationalJournal,
    OperationalShift,
)
from .services import (
    DraftConflictError,
    active_shift_for_journal,
    create_draft_entry,
    draft_entries_queryset,
    move_draft_entry,
    open_shift,
    remove_draft_entry,
    require_operational_employee,
    restore_draft_entry,
    timeline_queryset,
    update_draft_entry,
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


def _active_shift_or_404(
    *,
    journal: OperationalJournal,
) -> OperationalShift:
    shift = active_shift_for_journal(journal)
    return get_object_or_404(
        OperationalShift.objects.select_related(
            "journal",
            "journal__workplace",
            "opened_by",
            "opened_by__position",
        ),
        pk=shift.pk if shift else None,
    )


def _draft_or_404(
    *,
    shift: OperationalShift,
    public_id,
) -> OperationalDraftEntry:
    return get_object_or_404(
        OperationalDraftEntry.objects.select_related(
            "shift",
            "shift__journal",
            "created_by",
            "updated_by",
        ),
        shift=shift,
        public_id=public_id,
    )


def _validation_payload(error: ValidationError) -> Any:
    if hasattr(error, "message_dict"):
        return error.message_dict
    return error.messages


def _event_at_within_shift(
    *,
    shift: OperationalShift,
    event_at: datetime,
) -> bool:
    return (
        shift.planned_start_at
        <= event_at
        <= shift.planned_end_at
    )


def _shift_event_at_error(shift: OperationalShift) -> str:
    start = timezone.localtime(shift.planned_start_at)
    end = timezone.localtime(shift.planned_end_at)
    return (
        "Дата и время записи должны входить в интервал смены: "
        f"{start:%d.%m.%Y %H:%M} — {end:%d.%m.%Y %H:%M}."
    )


def _default_event_at_for_shift(shift: OperationalShift) -> datetime:
    now = timezone.now()
    if now < shift.planned_start_at:
        return shift.planned_start_at
    if now > shift.planned_end_at:
        return shift.planned_end_at
    return now


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
                "last_entry": entries.order_by(
                    "-sequence_number"
                ).first(),
                "form_contract": OPERATIONAL_JOURNAL_FORM,
                "active_shift": active_shift_for_journal(journal),
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
    preferences, _ = InterfacePreference.objects.get_or_create(
        user=request.user
    )
    entries = list(
        timeline_queryset(journal).order_by("sequence_number")
    )
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
            "display_form": JournalDisplayPreferenceForm(
                instance=preferences
            ),
            "active_shift": active_shift_for_journal(journal),
            "first_entry": entries[0] if entries else None,
            "last_entry": entries[-1] if entries else None,
            "summary": {
                "total": len(entries),
                "integrity_failures": integrity_failures,
            },
        },
    )


@login_required
def shift_workspace(
    request: HttpRequest,
    journal_id: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = active_shift_for_journal(journal)
    now = timezone.localtime().replace(second=0, microsecond=0)
    open_form = ShiftOpenForm(
        initial={
            "planned_start_at": now,
            "planned_end_at": now + timedelta(hours=12, minutes=15),
        }
    )
    drafts = []
    removed_drafts = []
    members = []
    if shift is not None:
        drafts = list(draft_entries_queryset(shift))
        removed_drafts = list(
            draft_entries_queryset(
                shift,
                include_removed=True,
            ).filter(is_removed=True)
        )
        members = list(
            shift.members.select_related(
                "employee",
                "employee__position",
            ).all()
        )
    return render(
        request,
        "operational_log/shift_workspace.html",
        {
            "journal": journal,
            "shift": shift,
            "open_form": open_form,
            "drafts": drafts,
            "removed_drafts": removed_drafts,
            "members": members,
        },
    )


@require_POST
@login_required
def open_shift_view(
    request: HttpRequest,
    journal_id: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    form = ShiftOpenForm(request.POST)
    if not form.is_valid():
        messages.error(
            request,
            "Не удалось открыть смену: проверь плановое время.",
        )
        return redirect(
            "operational_log:shift_workspace",
            journal_id=journal.pk,
        )
    try:
        open_shift(
            journal=journal,
            actor=employee,
            planned_start_at=form.cleaned_data["planned_start_at"],
            planned_end_at=form.cleaned_data["planned_end_at"],
        )
    except ValidationError as error:
        messages.error(
            request,
            "; ".join(error.messages),
        )
    else:
        messages.success(
            request,
            "Рабочая смена открыта. Черновик сохраняется автоматически.",
        )
    return redirect(
        "operational_log:shift_workspace",
        journal_id=journal.pk,
    )


@require_POST
@login_required
def add_draft_entry(
    request: HttpRequest,
    journal_id: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = _active_shift_or_404(journal=journal)

    requested_event_at = _default_event_at_for_shift(shift)
    event_at_raw = request.POST.get("event_at", "").strip()
    if event_at_raw:
        requested_event_at = parse_datetime(event_at_raw)
        if requested_event_at is None:
            return HttpResponseBadRequest(
                "Некорректная дата и время новой записи."
            )
        if timezone.is_naive(requested_event_at):
            requested_event_at = timezone.make_aware(
                requested_event_at,
                timezone.get_current_timezone(),
            )
        if not _event_at_within_shift(
            shift=shift,
            event_at=requested_event_at,
        ):
            return HttpResponseBadRequest(
                _shift_event_at_error(shift)
            )

    entry = create_draft_entry(
        shift=shift,
        actor=employee,
        event_at=requested_event_at,
    )
    response = redirect(
        "operational_log:shift_workspace",
        journal_id=journal.pk,
    )
    response["Location"] = (
        f"{response['Location']}#draft-{entry.public_id}"
    )
    return response


@require_POST
@login_required
def autosave_draft_entry(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> JsonResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = _active_shift_or_404(journal=journal)
    entry = _draft_or_404(
        shift=shift,
        public_id=public_id,
    )
    form = DraftEntryAutoSaveForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "errors": form.errors.get_json_data(),
            },
            status=400,
        )
    if form.cleaned_data["public_id"] != entry.public_id:
        return JsonResponse(
            {
                "ok": False,
                "errors": {
                    "public_id": ["Идентификатор записи не совпадает."]
                },
            },
            status=400,
        )
    if not _event_at_within_shift(
        shift=shift,
        event_at=form.cleaned_data["event_at"],
    ):
        return JsonResponse(
            {
                "ok": False,
                "errors": {
                    "event_at": [_shift_event_at_error(shift)],
                },
            },
            status=400,
        )
    try:
        saved = update_draft_entry(
            entry=entry,
            actor=employee,
            expected_version=form.cleaned_data["expected_version"],
            event_at=form.cleaned_data["event_at"],
            content=form.cleaned_data["content"],
        )
    except DraftConflictError as error:
        current = error.current_entry
        return JsonResponse(
            {
                "ok": False,
                "conflict": True,
                "message": error.messages[0],
                "current": {
                    "version": current.version,
                    "event_at": timezone.localtime(
                        current.event_at
                    ).strftime("%Y-%m-%dT%H:%M"),
                    "content": current.content,
                },
            },
            status=409,
        )
    except ValidationError as error:
        return JsonResponse(
            {
                "ok": False,
                "errors": _validation_payload(error),
            },
            status=400,
        )
    return JsonResponse(
        {
            "ok": True,
            "public_id": str(saved.public_id),
            "version": saved.version,
            "saved_at": timezone.localtime(
                saved.updated_at
            ).strftime("%H:%M:%S"),
            "revision_count": saved.revisions.count(),
        }
    )


@require_POST
@login_required
def move_draft_entry_view(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = _active_shift_or_404(journal=journal)
    entry = _draft_or_404(
        shift=shift,
        public_id=public_id,
    )
    try:
        move_draft_entry(
            entry=entry,
            actor=employee,
            direction=request.POST.get("direction", ""),
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    return redirect(
        "operational_log:shift_workspace",
        journal_id=journal.pk,
    )


@require_POST
@login_required
def remove_draft_entry_view(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = _active_shift_or_404(journal=journal)
    entry = _draft_or_404(
        shift=shift,
        public_id=public_id,
    )
    try:
        remove_draft_entry(
            entry=entry,
            actor=employee,
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    return redirect(
        "operational_log:shift_workspace",
        journal_id=journal.pk,
    )


@require_POST
@login_required
def restore_draft_entry_view(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = _active_shift_or_404(journal=journal)
    entry = _draft_or_404(
        shift=shift,
        public_id=public_id,
    )
    try:
        restore_draft_entry(
            entry=entry,
            actor=employee,
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    return redirect(
        "operational_log:shift_workspace",
        journal_id=journal.pk,
    )


@require_POST
@login_required
def update_display(
    request: HttpRequest,
    journal_id: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    preferences, _ = InterfacePreference.objects.get_or_create(
        user=request.user
    )
    form = JournalDisplayPreferenceForm(
        request.POST,
        instance=preferences,
    )
    if not form.is_valid():
        return HttpResponseBadRequest(
            "Настройки отображения оперативного журнала некорректны."
        )
    form.save()
    return redirect(
        "operational_log:detail",
        journal_id=journal.pk,
    )
