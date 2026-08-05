from __future__ import annotations

import uuid
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.organizations.models import InterfacePreference

from .form_contracts import OPERATIONAL_JOURNAL_FORM
from .forms import JournalDisplayPreferenceForm
from .models import OperationalDraftEntry, OperationalJournal
from .opj_integrity import verify_registered_snapshot
from .opj_lifecycle import _accessible_journal, register_draft
from .opj_presentation import build_clean_journal_groups
from .opj_print_presentation import build_print_journal_groups
from .opj_registration_order import ordered_registration_drafts
from .services import (
    active_shift_for_journal,
    require_operational_employee,
    timeline_queryset,
)
from .views import _semantic_reference_catalog

MAX_BATCH_SIZE = 100


def _selected_shift_public_id(
    request: HttpRequest,
    journal: OperationalJournal,
) -> str:
    raw_value = request.GET.get("shift", "").strip()
    if not raw_value:
        return ""
    try:
        public_id = uuid.UUID(raw_value)
    except (ValueError, AttributeError):
        return ""
    if not journal.shifts.filter(public_id=public_id).exists():
        return ""
    return str(public_id)


def _validated_draft_ids(request: HttpRequest) -> list[uuid.UUID]:
    raw_values = request.POST.getlist("draft_ids")
    if not raw_values:
        raise ValidationError("Выберите хотя бы одну строку черновика.")
    if len(raw_values) > MAX_BATCH_SIZE:
        raise ValidationError(
            f"За один раз можно перенести не более {MAX_BATCH_SIZE} строк."
        )
    values: list[uuid.UUID] = []
    for raw in raw_values:
        try:
            value = uuid.UUID(str(raw))
        except (TypeError, ValueError, AttributeError) as error:
            raise ValidationError(
                "Передан некорректный идентификатор строки."
            ) from error
        if value not in values:
            values.append(value)
    return values


def _journal_entries(journal: OperationalJournal):
    return list(
        timeline_queryset(journal)
        .select_related("author")
        .prefetch_related(
            "equipment_links",
            "equipment_links__equipment",
            "document_links",
            "document_links__document",
            "equipment_defect_links",
            "equipment_defect_links__record",
            "audit_events",
        )
        .order_by("sequence_number")
    )


def _register_ordered_rows(
    *,
    shift,
    draft_ids: list[uuid.UUID],
    actor,
) -> tuple[list[dict[str, Any]], int, int]:
    with transaction.atomic():
        ordered = ordered_registration_drafts(
            shift=shift,
            requested_ids=draft_ids,
        )
        results: list[dict[str, Any]] = []
        registered_count = 0
        for draft in ordered:
            try:
                entry = register_draft(draft=draft, actor=actor)
            except (ValidationError, PermissionDenied) as error:
                results.append(
                    {
                        "public_id": str(draft.public_id),
                        "ok": False,
                        "message": "; ".join(
                            getattr(error, "messages", [str(error)])
                        ),
                    }
                )
                break
            else:
                registered_count += 1
                results.append(
                    {
                        "public_id": str(draft.public_id),
                        "ok": True,
                        "sequence_number": entry.sequence_number,
                    }
                )
        failed_count = len(ordered) - registered_count
        if failed_count > len(results) - registered_count:
            completed_ids = {row["public_id"] for row in results}
            for draft in ordered:
                if str(draft.public_id) in completed_ids:
                    continue
                results.append(
                    {
                        "public_id": str(draft.public_id),
                        "ok": False,
                        "message": (
                            "Строка не перенесена после ошибки предыдущей записи."
                        ),
                    }
                )
        return results, registered_count, failed_count


@require_POST
@login_required
def register_drafts_batch_view(
    request: HttpRequest,
    journal_id: int,
) -> JsonResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = active_shift_for_journal(journal)
    if shift is None:
        return JsonResponse(
            {"ok": False, "message": "Открытая смена не найдена."},
            status=409,
        )
    try:
        draft_ids = _validated_draft_ids(request)
        results, registered_count, failed_count = _register_ordered_rows(
            shift=shift,
            draft_ids=draft_ids,
            actor=employee,
        )
    except ValidationError as error:
        return JsonResponse(
            {"ok": False, "message": "; ".join(error.messages)},
            status=409,
        )

    if registered_count:
        messages.success(
            request,
            (
                f"В чистовик перенесено строк: {registered_count}."
                if failed_count == 0
                else (
                    f"В чистовик перенесено строк: {registered_count}; "
                    f"не перенесено: {failed_count}."
                )
            ),
        )
    if failed_count:
        messages.error(
            request,
            "Регистрация остановлена на первой ошибке.",
        )
    return JsonResponse(
        {
            "ok": failed_count == 0,
            "registered_count": registered_count,
            "failed_count": failed_count,
            "results": results,
            "shift_public_id": str(shift.public_id),
        },
        status=200 if registered_count else 400,
    )


@require_POST
@login_required
def register_single_draft_view(
    request: HttpRequest,
    journal_id: int,
    public_id: uuid.UUID,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = active_shift_for_journal(journal)
    if shift is None:
        messages.error(request, "Открытая смена не найдена.")
        return _shift_redirect(journal, public_id)
    try:
        results, registered_count, _ = _register_ordered_rows(
            shift=shift,
            draft_ids=[public_id],
            actor=employee,
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        if registered_count:
            messages.success(
                request,
                "Запись перенесена в чистовик и поставлена в журнальную хронологию.",
            )
        elif results:
            messages.error(request, results[0]["message"])
    return _shift_redirect(journal, public_id)


def _shift_redirect(
    journal: OperationalJournal,
    public_id: uuid.UUID | None = None,
) -> HttpResponse:
    response = redirect(
        reverse("operational_log:shift_workspace", args=(journal.pk,))
    )
    if public_id is not None:
        response["Location"] = f"{response['Location']}#draft-{public_id}"
    return response


def _clean_reference_catalog(
    journal: OperationalJournal,
    selected_shift: str,
) -> dict[str, list[dict[str, Any]]]:
    selected = (
        journal.shifts.filter(public_id=selected_shift).first()
        if selected_shift
        else None
    )
    shift = selected or active_shift_for_journal(journal)
    drafts = list(
        OperationalDraftEntry.objects.filter(
            shift__journal=journal,
            is_removed=False,
        )
        .select_related(
            "shift",
            "updated_by",
            "updated_by__position",
        )
        .order_by("event_at", "position", "pk")[:500]
    )
    return _semantic_reference_catalog(journal, shift, drafts)


@login_required
def clean_journal_view(
    request: HttpRequest,
    journal_id: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    preferences, _ = InterfacePreference.objects.get_or_create(user=request.user)
    entries = _journal_entries(journal)
    selected_shift = _selected_shift_public_id(request, journal)
    groups = build_clean_journal_groups(
        entries=entries,
        selected_shift=selected_shift,
    )
    integrity_failures = 0
    for entry in entries:
        try:
            verify_registered_snapshot(entry)
        except ValidationError:
            integrity_failures += 1
    active_shift = active_shift_for_journal(journal)
    return render(
        request,
        "operational_log/detail.html",
        {
            "journal": journal,
            "groups": groups,
            "form_contract": OPERATIONAL_JOURNAL_FORM,
            "display_form": JournalDisplayPreferenceForm(instance=preferences),
            "ui_preferences": preferences,
            "active_shift": active_shift,
            "first_entry": entries[0] if entries else None,
            "last_entry": entries[-1] if entries else None,
            "selected_shift": selected_shift,
            "shift_options": list(journal.shifts.order_by("-planned_start_at")),
            "semantic_reference_catalog": _clean_reference_catalog(
                journal,
                selected_shift,
            ),
            "summary": {
                "total": len(entries),
                "integrity_failures": integrity_failures,
            },
        },
    )


@login_required
def print_journal_view(
    request: HttpRequest,
    journal_id: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    entries = _journal_entries(journal)
    selected_shift = _selected_shift_public_id(request, journal)
    groups = build_print_journal_groups(
        entries=entries,
        selected_shift=selected_shift,
    )
    back_url = reverse("operational_log:detail", args=(journal.pk,))
    if selected_shift:
        back_url = f"{back_url}?shift={selected_shift}"
    return render(
        request,
        "operational_log/print.html",
        {
            "journal": journal,
            "groups": groups,
            "form_contract": OPERATIONAL_JOURNAL_FORM,
            "selected_shift": selected_shift,
            "back_url": back_url,
        },
    )
