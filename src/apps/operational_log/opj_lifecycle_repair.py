from __future__ import annotations

import uuid
from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.organizations.authority_models import AuthorityDecision
from apps.organizations.models import InterfacePreference

from .editor import editor_document_to_text, normalize_editor_document
from .form_contracts import OPERATIONAL_JOURNAL_FORM
from .forms import JournalDisplayPreferenceForm
from .models import EntryForm, OperationalDraftEntry, OperationalJournal, OperationalLogEntry
from .opj_lifecycle import (
    ACTION_CORRECT,
    DENIED_MESSAGE,
    SCHEMA_VERSION,
    TYPE_CORRECTION,
    _accessible_journal,
    _authority_payload,
    _ensure_original_target,
    _entry_or_404,
    _evaluate_authority,
    _target_payload,
    cancel_entry,
    effective_state,
    register_draft,
)
from .opj_presentation import build_clean_journal_groups
from .services import (
    active_shift_for_journal,
    register_entry,
    require_operational_employee,
    timeline_queryset,
    verify_entry_integrity,
)

MAX_BATCH_SIZE = 100


class StructuredCorrectionForm(forms.Form):
    replacement_content = forms.CharField(max_length=20000)
    replacement_editor_payload = forms.JSONField(required=False)
    reason = forms.CharField(max_length=1000)
    return_shift = forms.CharField(max_length=64, required=False)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        if self.errors:
            return cleaned
        document = normalize_editor_document(
            cleaned.get("replacement_editor_payload"),
            fallback_text=cleaned.get("replacement_content", ""),
        )
        content = editor_document_to_text(document).strip()
        if not content:
            raise ValidationError("Исправленное содержание обязательно.")
        reason = str(cleaned.get("reason") or "").strip()
        if not reason:
            raise ValidationError("Причина исправления обязательна.")
        cleaned["replacement_content"] = content
        cleaned["replacement_editor_payload"] = document
        cleaned["reason"] = reason
        return cleaned


class StructuredCancellationForm(forms.Form):
    reason = forms.CharField(max_length=1000)
    return_shift = forms.CharField(max_length=64, required=False)

    def clean_reason(self) -> str:
        value = self.cleaned_data["reason"].strip()
        if not value:
            raise ValidationError("Причина отмены обязательна.")
        return value


def _clean_anchor(
    journal: OperationalJournal,
    sequence_number: int,
    shift_public_id: str = "",
) -> HttpResponse:
    location = reverse("operational_log:detail", args=(journal.pk,))
    if shift_public_id:
        location = f"{location}?shift={shift_public_id}"
    response = redirect(location)
    response["Location"] = f"{response['Location']}#entry-{sequence_number}"
    return response


def _validated_draft_ids(request: HttpRequest) -> list[uuid.UUID]:
    raw_values = request.POST.getlist("draft_ids")
    if not raw_values:
        raise ValidationError("Выберите хотя бы одну строку черновика.")
    if len(raw_values) > MAX_BATCH_SIZE:
        raise ValidationError(
            f"За один раз можно перенести не более {MAX_BATCH_SIZE} строк."
        )
    result: list[uuid.UUID] = []
    for raw in raw_values:
        try:
            value = uuid.UUID(str(raw))
        except (TypeError, ValueError, AttributeError) as error:
            raise ValidationError("Передан некорректный идентификатор строки.") from error
        if value not in result:
            result.append(value)
    return result


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
    except ValidationError as error:
        return JsonResponse(
            {"ok": False, "message": "; ".join(error.messages)},
            status=400,
        )

    drafts = {
        draft.public_id: draft
        for draft in OperationalDraftEntry.objects.filter(
            shift=shift,
            public_id__in=draft_ids,
        ).select_related("shift", "shift__journal")
    }
    results: list[dict[str, Any]] = []
    registered_count = 0
    for public_id in draft_ids:
        draft = drafts.get(public_id)
        if draft is None:
            results.append(
                {
                    "public_id": str(public_id),
                    "ok": False,
                    "message": "Строка не найдена в текущей смене.",
                }
            )
            continue
        try:
            entry = register_draft(draft=draft, actor=employee)
        except (ValidationError, PermissionDenied) as error:
            results.append(
                {
                    "public_id": str(public_id),
                    "ok": False,
                    "message": "; ".join(
                        getattr(error, "messages", [str(error)])
                    ),
                }
            )
        else:
            registered_count += 1
            results.append(
                {
                    "public_id": str(public_id),
                    "ok": True,
                    "sequence_number": entry.sequence_number,
                }
            )

    failed_count = len(results) - registered_count
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
            "Часть выбранных строк не перенесена. Проверьте сообщения у строк.",
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


def correct_entry_structured(
    *,
    entry: OperationalLogEntry,
    actor,
    replacement_content: str,
    replacement_editor_payload: dict[str, Any],
    reason: str,
) -> OperationalLogEntry:
    _ensure_original_target(entry)
    document = normalize_editor_document(
        replacement_editor_payload,
        fallback_text=replacement_content,
    )
    normalized_content = editor_document_to_text(document).strip()
    normalized_reason = reason.strip()
    if not normalized_content:
        raise ValidationError("Исправленное содержание обязательно.")
    if not normalized_reason:
        raise ValidationError("Причина исправления обязательна.")

    denied = False
    correction: OperationalLogEntry | None = None
    with transaction.atomic():
        locked = (
            OperationalLogEntry.objects.select_for_update()
            .select_related("journal", "journal__organization", "journal__workplace")
            .get(pk=entry.pk)
        )
        _ensure_original_target(locked)
        state = effective_state(locked)
        if state.status == "CANCELLED":
            raise ValidationError("Отменённую запись нельзя исправлять.")
        evaluation = _evaluate_authority(
            actor=actor,
            journal=locked.journal,
            action_code=ACTION_CORRECT,
            subject_type="OPJ_ENTRY",
            subject_id=(
                f"{locked.journal_id}:{locked.sequence_number}:"
                f"CORRECTION:{uuid.uuid4()}"
            ),
        )
        denied = evaluation.decision == AuthorityDecision.DENY
        if not denied:
            payload = {
                "schema_version": SCHEMA_VERSION,
                "kind": "CORRECTION",
                "target": _target_payload(locked),
                "previous_effective_content": state.effective_content,
                "replacement_content": normalized_content,
                "replacement_editor_payload": document,
                "reason": normalized_reason,
                "authority": _authority_payload(evaluation),
            }
            correction = register_entry(
                journal=locked.journal,
                actor=actor,
                event_at=timezone.now(),
                content=(
                    f"Исправление к записи № {locked.sequence_number}. "
                    f"Следует читать: {normalized_content} "
                    f"Причина: {normalized_reason}"
                ),
                entry_form=EntryForm.TYPED,
                type_code=TYPE_CORRECTION,
                type_title="Исправление зарегистрированной записи",
                typed_payload=payload,
            )

    if denied:
        raise PermissionDenied(DENIED_MESSAGE)
    if correction is None:
        raise RuntimeError("Исправление записи не завершено.")
    return correction


@require_POST
@login_required
def correct_entry_view(
    request: HttpRequest,
    journal_id: int,
    sequence_number: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    entry = _entry_or_404(journal=journal, sequence_number=sequence_number)
    form = StructuredCorrectionForm(request.POST)
    if not form.is_valid():
        messages.error(
            request,
            "Исправление не зарегистрировано: проверьте содержание и причину.",
        )
    else:
        try:
            event = correct_entry_structured(
                entry=entry,
                actor=employee,
                replacement_content=form.cleaned_data["replacement_content"],
                replacement_editor_payload=form.cleaned_data[
                    "replacement_editor_payload"
                ],
                reason=form.cleaned_data["reason"],
            )
        except (ValidationError, PermissionDenied) as error:
            messages.error(
                request,
                "; ".join(getattr(error, "messages", [str(error)])),
            )
        else:
            messages.success(
                request,
                f"Исправление зарегистрировано записью № {event.sequence_number}.",
            )
    return _clean_anchor(
        journal,
        entry.sequence_number,
        form.cleaned_data.get("return_shift", "") if form.is_valid() else "",
    )


@require_POST
@login_required
def cancel_entry_view(
    request: HttpRequest,
    journal_id: int,
    sequence_number: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    entry = _entry_or_404(journal=journal, sequence_number=sequence_number)
    form = StructuredCancellationForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Отмена не зарегистрирована: укажите причину.")
    else:
        try:
            event = cancel_entry(
                entry=entry,
                actor=employee,
                reason=form.cleaned_data["reason"],
            )
        except (ValidationError, PermissionDenied) as error:
            messages.error(
                request,
                "; ".join(getattr(error, "messages", [str(error)])),
            )
        else:
            messages.success(
                request,
                f"Отмена зарегистрирована записью № {event.sequence_number}.",
            )
    return _clean_anchor(
        journal,
        entry.sequence_number,
        form.cleaned_data.get("return_shift", "") if form.is_valid() else "",
    )


@login_required
def clean_journal_view(
    request: HttpRequest,
    journal_id: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    preferences, _ = InterfacePreference.objects.get_or_create(user=request.user)
    entries = list(
        timeline_queryset(journal)
        .select_related("author")
        .prefetch_related(
            "equipment_links",
            "document_links",
            "document_links__document",
            "equipment_defect_links",
            "equipment_defect_links__record",
        )
        .order_by("sequence_number")
    )
    integrity_failures = 0
    technical_rows: list[dict[str, Any]] = []
    for entry in entries:
        try:
            integrity_ok = verify_entry_integrity(entry)
        except ValidationError:
            integrity_ok = False
            integrity_failures += 1
        technical_rows.append({"entry": entry, "integrity_ok": integrity_ok})

    selected_shift = request.GET.get("shift", "").strip()
    if selected_shift and not journal.shifts.filter(public_id=selected_shift).exists():
        selected_shift = ""
    groups = build_clean_journal_groups(
        entries=entries,
        selected_shift=selected_shift,
    )
    shift_options = list(journal.shifts.order_by("-planned_start_at"))
    return render(
        request,
        "operational_log/detail.html",
        {
            "journal": journal,
            "groups": groups,
            "rows": technical_rows,
            "form_contract": OPERATIONAL_JOURNAL_FORM,
            "display_form": JournalDisplayPreferenceForm(instance=preferences),
            "active_shift": active_shift_for_journal(journal),
            "first_entry": entries[0] if entries else None,
            "last_entry": entries[-1] if entries else None,
            "selected_shift": selected_shift,
            "shift_options": shift_options,
            "semantic_reference_catalog": {},
            "summary": {
                "total": len(entries),
                "integrity_failures": integrity_failures,
            },
        },
    )
