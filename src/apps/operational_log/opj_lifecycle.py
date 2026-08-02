from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.organizations.authority_models import AuthorityDecision
from apps.organizations.authority_services import evaluate_and_record_authority

from .editor import ENTRY_KIND_LABELS
from .models import (
    EntryForm,
    OperationalDraftEntry,
    OperationalJournal,
    OperationalLogEntry,
)
from .services import (
    active_shift_for_journal,
    register_entry,
    require_operational_employee,
    timeline_queryset,
    verify_entry_integrity,
)

TYPE_ENTRY = "opj-entry"
TYPE_CORRECTION = "opj-correction"
TYPE_CANCELLATION = "opj-cancellation"
TYPE_COMMUNICATION = "opj-communication"
LIFECYCLE_TYPES = frozenset({TYPE_CORRECTION, TYPE_CANCELLATION})
CHILD_EVENT_TYPES = LIFECYCLE_TYPES
COMMUNICATION_ENTRY_KINDS = frozenset({"command", "permission", "message"})

ACTION_REGISTER = "OPJ.REGISTER"
ACTION_CORRECT = "OPJ.CORRECT"
ACTION_CANCEL = "OPJ.CANCEL"
ACTION_COMMUNICATION = "OPJ.COMMUNICATION"

SCHEMA_VERSION = "eod.opj.lifecycle.v2"
DENIED_MESSAGE = "Действие не выполнено: требуемое полномочие не подтверждено."


class CorrectionForm(forms.Form):
    replacement_content = forms.CharField(
        label="Исправленное содержание",
        max_length=20000,
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    reason = forms.CharField(
        label="Причина исправления",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class CancellationForm(forms.Form):
    reason = forms.CharField(
        label="Причина отмены",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


@dataclass(frozen=True, slots=True)
class EffectiveEntryState:
    status: str
    status_label: str
    effective_content: str
    correction_count: int
    cancellation_entry: OperationalLogEntry | None


@dataclass(frozen=True, slots=True)
class EntryLifecycleContext:
    is_child: bool
    child_label: str
    linked_original: OperationalLogEntry | None
    lifecycle_entries: tuple[OperationalLogEntry, ...]
    state: EffectiveEntryState
    integrity_ok: bool


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


def _entry_or_404(
    *,
    journal: OperationalJournal,
    sequence_number: int,
) -> OperationalLogEntry:
    return get_object_or_404(
        timeline_queryset(journal),
        sequence_number=sequence_number,
    )


def _authority_payload(record) -> dict[str, Any]:
    return {
        "evaluation_public_id": str(record.public_id),
        "decision": record.decision,
        "reasons": list(record.reasons),
        "digest": record.digest,
        "snapshot": record.snapshot,
    }


def _evaluate_authority(
    *,
    actor,
    journal: OperationalJournal,
    action_code: str,
    subject_type: str,
    subject_id: str,
):
    return evaluate_and_record_authority(
        employee=actor,
        organization=journal.organization,
        action_code=action_code,
        occurred_at=timezone.now(),
        scope_kind="WORKPLACE",
        scope_reference=str(journal.workplace_id),
        scope_label=journal.workplace.name,
        subject_type=subject_type,
        subject_id=subject_id,
        recorded_by=actor,
    )


def _target_payload(entry: OperationalLogEntry) -> dict[str, Any]:
    return {
        "journal_id": entry.journal_id,
        "sequence_number": entry.sequence_number,
        "digest": entry.digest,
        "event_at": entry.event_at.isoformat(),
    }


def _draft_entry_kind(draft: OperationalDraftEntry) -> str:
    payload = draft.editor_payload if isinstance(draft.editor_payload, dict) else {}
    entry_kind = str(payload.get("entry_kind", "normal"))
    return entry_kind if entry_kind in ENTRY_KIND_LABELS else "normal"


def registered_entry_for_draft(
    draft: OperationalDraftEntry,
) -> OperationalLogEntry | None:
    return (
        draft.shift.journal.entries.filter(
            type_code__in=(TYPE_ENTRY, TYPE_COMMUNICATION),
            typed_payload__draft__public_id=str(draft.public_id),
        )
        .select_related("author")
        .order_by("-sequence_number")
        .first()
    )


def draft_registration_context(draft: OperationalDraftEntry) -> dict[str, Any]:
    entry = registered_entry_for_draft(draft)
    return {
        "is_registered": entry is not None,
        "entry": entry,
    }


def _lifecycle_entries(entry: OperationalLogEntry) -> list[OperationalLogEntry]:
    candidates = (
        entry.journal.entries.filter(type_code__in=LIFECYCLE_TYPES)
        .select_related("author")
        .order_by("sequence_number")
    )
    return [
        candidate
        for candidate in candidates
        if candidate.typed_payload.get("target", {}).get("sequence_number")
        == entry.sequence_number
    ]


def effective_state(
    entry: OperationalLogEntry,
    lifecycle_entries: list[OperationalLogEntry] | None = None,
) -> EffectiveEntryState:
    events = lifecycle_entries if lifecycle_entries is not None else _lifecycle_entries(entry)
    effective_content = entry.content
    correction_count = 0
    cancellation_entry = None
    for event in events:
        if event.type_code == TYPE_CORRECTION:
            replacement = str(event.typed_payload.get("replacement_content", "")).strip()
            if replacement:
                effective_content = replacement
                correction_count += 1
        elif event.type_code == TYPE_CANCELLATION:
            cancellation_entry = event
    if cancellation_entry is not None:
        return EffectiveEntryState(
            status="CANCELLED",
            status_label="Отменена",
            effective_content=effective_content,
            correction_count=correction_count,
            cancellation_entry=cancellation_entry,
        )
    if correction_count:
        return EffectiveEntryState(
            status="CORRECTED",
            status_label="Исправлена",
            effective_content=effective_content,
            correction_count=correction_count,
            cancellation_entry=None,
        )
    return EffectiveEntryState(
        status="REGISTERED",
        status_label="Зарегистрирована",
        effective_content=effective_content,
        correction_count=0,
        cancellation_entry=None,
    )


def _linked_original(entry: OperationalLogEntry) -> OperationalLogEntry | None:
    if entry.type_code not in CHILD_EVENT_TYPES:
        return None
    target_sequence = entry.typed_payload.get("target", {}).get("sequence_number")
    if not target_sequence:
        return None
    return entry.journal.entries.filter(sequence_number=target_sequence).first()


def entry_lifecycle_context(entry: OperationalLogEntry) -> EntryLifecycleContext:
    linked_original = _linked_original(entry)
    is_child = linked_original is not None
    lifecycle = [] if is_child else _lifecycle_entries(entry)
    state = effective_state(entry, lifecycle)
    integrity_ok = True
    try:
        verify_entry_integrity(entry)
        for event in lifecycle:
            verify_entry_integrity(event)
    except ValidationError:
        integrity_ok = False
    labels = {
        TYPE_CORRECTION: "Исправление",
        TYPE_CANCELLATION: "Отмена",
    }
    return EntryLifecycleContext(
        is_child=is_child,
        child_label=labels.get(entry.type_code, ""),
        linked_original=linked_original,
        lifecycle_entries=tuple(lifecycle),
        state=state,
        integrity_ok=integrity_ok,
    )


def _ensure_original_target(entry: OperationalLogEntry) -> None:
    if entry.type_code in CHILD_EVENT_TYPES:
        raise ValidationError(
            "Действие выполняется для исходной зарегистрированной записи."
        )


def register_draft(
    *,
    draft: OperationalDraftEntry,
    actor,
) -> OperationalLogEntry:
    denied = False
    registered: OperationalLogEntry | None = None
    with transaction.atomic():
        locked_draft = (
            OperationalDraftEntry.objects.select_for_update()
            .select_related(
                "shift",
                "shift__journal",
                "shift__journal__organization",
                "shift__journal__workplace",
            )
            .get(pk=draft.pk)
        )
        existing = registered_entry_for_draft(locked_draft)
        if existing is not None:
            raise ValidationError(
                "Эта строка уже зарегистрирована в чистовике "
                f"под № {existing.sequence_number}."
            )
        if locked_draft.is_removed:
            raise ValidationError("Убранную черновую строку нельзя зарегистрировать.")
        if not locked_draft.content.strip():
            raise ValidationError("Перед регистрацией заполните содержание строки.")

        entry_kind = _draft_entry_kind(locked_draft)
        is_communication = entry_kind in COMMUNICATION_ENTRY_KINDS
        action_code = ACTION_COMMUNICATION if is_communication else ACTION_REGISTER
        subject_type = (
            "OPJ_COMMUNICATION_DRAFT" if is_communication else "OPJ_DRAFT"
        )
        evaluation = _evaluate_authority(
            actor=actor,
            journal=locked_draft.shift.journal,
            action_code=action_code,
            subject_type=subject_type,
            subject_id=str(locked_draft.public_id),
        )
        denied = evaluation.decision == AuthorityDecision.DENY
        if not denied:
            entry_kind_label = ENTRY_KIND_LABELS[entry_kind]
            payload = {
                "schema_version": SCHEMA_VERSION,
                "kind": "COMMUNICATION_OUTCOME" if is_communication else "ORIGINAL",
                "draft": {
                    "public_id": str(locked_draft.public_id),
                    "version": locked_draft.version,
                    "editor_schema_version": locked_draft.editor_schema_version,
                    "editor_payload": locked_draft.editor_payload,
                },
                "authority": _authority_payload(evaluation),
            }
            if is_communication:
                payload["communication"] = {
                    "entry_kind": entry_kind,
                    "entry_kind_label": entry_kind_label,
                }
            registered = register_entry(
                journal=locked_draft.shift.journal,
                actor=actor,
                event_at=locked_draft.event_at,
                content=locked_draft.content,
                entry_form=EntryForm.TYPED,
                type_code=TYPE_COMMUNICATION if is_communication else TYPE_ENTRY,
                type_title=(
                    f"Оперативные переговоры · {entry_kind_label}"
                    if is_communication
                    else "Оперативная запись"
                ),
                typed_payload=payload,
            )

    if denied:
        raise PermissionDenied(DENIED_MESSAGE)
    if registered is None:
        raise RuntimeError("Регистрация записи не завершена.")
    return registered


def correct_entry(
    *,
    entry: OperationalLogEntry,
    actor,
    replacement_content: str,
    reason: str,
) -> OperationalLogEntry:
    _ensure_original_target(entry)
    normalized_content = replacement_content.strip()
    normalized_reason = reason.strip()
    if not normalized_content:
        raise ValidationError(
            {"replacement_content": "Исправленное содержание обязательно."}
        )
    if not normalized_reason:
        raise ValidationError({"reason": "Причина исправления обязательна."})

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


def cancel_entry(
    *,
    entry: OperationalLogEntry,
    actor,
    reason: str,
) -> OperationalLogEntry:
    _ensure_original_target(entry)
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise ValidationError({"reason": "Причина отмены обязательна."})

    denied = False
    cancellation: OperationalLogEntry | None = None
    with transaction.atomic():
        locked = (
            OperationalLogEntry.objects.select_for_update()
            .select_related("journal", "journal__organization", "journal__workplace")
            .get(pk=entry.pk)
        )
        _ensure_original_target(locked)
        state = effective_state(locked)
        if state.status == "CANCELLED":
            raise ValidationError("Запись уже отменена.")
        evaluation = _evaluate_authority(
            actor=actor,
            journal=locked.journal,
            action_code=ACTION_CANCEL,
            subject_type="OPJ_ENTRY",
            subject_id=(
                f"{locked.journal_id}:{locked.sequence_number}:"
                f"CANCELLATION:{uuid.uuid4()}"
            ),
        )
        denied = evaluation.decision == AuthorityDecision.DENY
        if not denied:
            payload = {
                "schema_version": SCHEMA_VERSION,
                "kind": "CANCELLATION",
                "target": _target_payload(locked),
                "effective_content_at_cancellation": state.effective_content,
                "reason": normalized_reason,
                "authority": _authority_payload(evaluation),
            }
            cancellation = register_entry(
                journal=locked.journal,
                actor=actor,
                event_at=timezone.now(),
                content=(
                    f"Запись № {locked.sequence_number} отменена. "
                    f"Причина: {normalized_reason}"
                ),
                entry_form=EntryForm.TYPED,
                type_code=TYPE_CANCELLATION,
                type_title="Отмена зарегистрированной записи",
                typed_payload=payload,
            )

    if denied:
        raise PermissionDenied(DENIED_MESSAGE)
    if cancellation is None:
        raise RuntimeError("Отмена записи не завершена.")
    return cancellation


def _detail_anchor(journal: OperationalJournal, sequence_number: int) -> HttpResponse:
    response = redirect("operational_log:detail", journal_id=journal.pk)
    response["Location"] = f"{response['Location']}#entry-{sequence_number}"
    return response


def _shift_anchor(journal: OperationalJournal, public_id) -> HttpResponse:
    response = redirect("operational_log:shift_workspace", journal_id=journal.pk)
    response["Location"] = f"{response['Location']}#draft-{public_id}"
    return response


@login_required
def entry_lifecycle_view(
    request: HttpRequest,
    journal_id: int,
    sequence_number: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    _entry_or_404(journal=journal, sequence_number=sequence_number)
    return _detail_anchor(journal, sequence_number)


@require_POST
@login_required
def register_draft_view(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = active_shift_for_journal(journal)
    draft = get_object_or_404(
        OperationalDraftEntry.objects.select_related("shift", "shift__journal"),
        public_id=public_id,
        shift=shift,
    )
    try:
        entry = register_draft(draft=draft, actor=employee)
    except (ValidationError, PermissionDenied) as error:
        messages.error(
            request,
            "; ".join(getattr(error, "messages", [str(error)])),
        )
    else:
        messages.success(
            request,
            f"Строка перенесена в чистовик как запись № {entry.sequence_number}.",
        )
    return _shift_anchor(journal, draft.public_id)


def _registered_draft_guard(
    request: HttpRequest,
    *,
    journal: OperationalJournal,
    draft: OperationalDraftEntry,
) -> HttpResponse | None:
    entry = registered_entry_for_draft(draft)
    if entry is None:
        return None
    message = (
        f"Строка уже находится в чистовике под № {entry.sequence_number} "
        "и больше не редактируется как черновик."
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": False,
                "registered": True,
                "message": message,
                "errors": [message],
            },
            status=409,
        )
    messages.error(request, message)
    return _shift_anchor(journal, draft.public_id)


def _guarded_draft(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> tuple[OperationalJournal, OperationalDraftEntry, HttpResponse | None]:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    shift = active_shift_for_journal(journal)
    draft = get_object_or_404(
        OperationalDraftEntry.objects.select_related("shift", "shift__journal"),
        public_id=public_id,
        shift=shift,
    )
    return journal, draft, _registered_draft_guard(
        request,
        journal=journal,
        draft=draft,
    )


@require_POST
@login_required
def autosave_draft_guard_view(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> HttpResponse:
    _, _, blocked = _guarded_draft(request, journal_id, public_id)
    if blocked is not None:
        return blocked
    from . import views as standard_views

    return standard_views.autosave_draft_entry(request, journal_id, public_id)


@require_POST
@login_required
def move_draft_guard_view(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> HttpResponse:
    _, _, blocked = _guarded_draft(request, journal_id, public_id)
    if blocked is not None:
        return blocked
    from . import views as standard_views

    return standard_views.move_draft_entry_view(request, journal_id, public_id)


@require_POST
@login_required
def remove_draft_guard_view(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> HttpResponse:
    _, _, blocked = _guarded_draft(request, journal_id, public_id)
    if blocked is not None:
        return blocked
    from . import views as standard_views

    return standard_views.remove_draft_entry_view(request, journal_id, public_id)


@require_POST
@login_required
def restore_draft_guard_view(
    request: HttpRequest,
    journal_id: int,
    public_id,
) -> HttpResponse:
    _, _, blocked = _guarded_draft(request, journal_id, public_id)
    if blocked is not None:
        return blocked
    from . import views as standard_views

    return standard_views.restore_draft_entry_view(request, journal_id, public_id)


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
    form = CorrectionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Исправление не зарегистрировано: проверьте поля.")
    else:
        try:
            event = correct_entry(
                entry=entry,
                actor=employee,
                replacement_content=form.cleaned_data["replacement_content"],
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
                f"Исправление добавлено в чистовик записью № {event.sequence_number}.",
            )
    return _detail_anchor(journal, entry.sequence_number)


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
    form = CancellationForm(request.POST)
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
                f"Отмена добавлена в чистовик записью № {event.sequence_number}.",
            )
    return _detail_anchor(journal, entry.sequence_number)
