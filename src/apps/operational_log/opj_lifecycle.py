from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.organizations.authority_models import AuthorityDecision
from apps.organizations.authority_services import evaluate_and_record_authority

from .models import (
    EntryForm,
    OperationalDraftEntry,
    OperationalJournal,
    OperationalLogEntry,
)
from .services import (
    active_shift_for_journal,
    register_entry,
    remove_draft_entry,
    require_operational_employee,
    timeline_queryset,
    verify_entry_integrity,
)

TYPE_ENTRY = "opj-entry"
TYPE_CORRECTION = "opj-correction"
TYPE_CANCELLATION = "opj-cancellation"
TYPE_COMMUNICATION = "opj-communication"
LIFECYCLE_TYPES = frozenset({TYPE_CORRECTION, TYPE_CANCELLATION})
SYSTEM_TYPES = frozenset(
    {TYPE_ENTRY, TYPE_CORRECTION, TYPE_CANCELLATION, TYPE_COMMUNICATION}
)

ACTION_REGISTER = "OPJ.REGISTER"
ACTION_CORRECT = "OPJ.CORRECT"
ACTION_CANCEL = "OPJ.CANCEL"
ACTION_COMMUNICATION = "OPJ.COMMUNICATION"

SCHEMA_VERSION = "eod.opj.lifecycle.v1"


class CorrectionForm(forms.Form):
    replacement_content = forms.CharField(
        label="Исправленное содержание",
        max_length=20000,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Полный текст, который должен использоваться вместо исходного…",
            }
        ),
    )
    reason = forms.CharField(
        label="Основание исправления",
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "placeholder": "Почему требуется исправление и что было уточнено",
            }
        ),
    )


class CancellationForm(forms.Form):
    reason = forms.CharField(
        label="Основание отмены",
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Причина отмены записи без удаления оригинала",
            }
        ),
    )


class CommunicationForm(forms.Form):
    class Direction(models.TextChoices):
        INCOMING = "INCOMING", "Входящий разговор"
        OUTGOING = "OUTGOING", "Исходящий разговор"

    class Channel(models.TextChoices):
        PHONE = "PHONE", "Телефон"
        RADIO = "RADIO", "Радиосвязь"
        DISPATCH = "DISPATCH", "Диспетчерский канал"
        OTHER = "OTHER", "Другой канал"

    direction = forms.ChoiceField(label="Направление", choices=Direction.choices)
    channel = forms.ChoiceField(label="Канал", choices=Channel.choices)
    counterpart = forms.CharField(
        label="С кем состоялся разговор",
        max_length=500,
        widget=forms.TextInput(
            attrs={"placeholder": "Ф.И.О., должность или диспетчерское наименование"}
        ),
    )
    counterpart_organization = forms.CharField(
        label="Организация / диспетчерский центр",
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "При необходимости"}),
    )
    content = forms.CharField(
        label="Содержание разговора",
        max_length=20000,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Переданная или полученная оперативная информация…",
            }
        ),
    )


@dataclass(frozen=True, slots=True)
class EffectiveEntryState:
    status: str
    status_label: str
    effective_content: str
    correction_count: int
    cancellation_entry: OperationalLogEntry | None


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
    action_at = timezone.now()
    evaluation = evaluate_and_record_authority(
        employee=actor,
        organization=journal.organization,
        action_code=action_code,
        occurred_at=action_at,
        scope_kind="WORKPLACE",
        scope_reference=str(journal.workplace_id),
        scope_label=journal.workplace.name,
        subject_type=subject_type,
        subject_id=subject_id,
        recorded_by=actor,
    )
    if evaluation.decision == AuthorityDecision.DENY:
        raise PermissionDenied(
            "Действие не выполнено: на момент операции не подтверждено требуемое "
            "предметное полномочие."
        )
    return evaluation


def _target_payload(entry: OperationalLogEntry) -> dict[str, Any]:
    return {
        "journal_id": entry.journal_id,
        "sequence_number": entry.sequence_number,
        "digest": entry.digest,
        "event_at": entry.event_at.isoformat(),
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


def _communication_entries(entry: OperationalLogEntry) -> list[OperationalLogEntry]:
    candidates = (
        entry.journal.entries.filter(type_code=TYPE_COMMUNICATION)
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


def _ensure_original_target(entry: OperationalLogEntry) -> None:
    if entry.type_code in LIFECYCLE_TYPES:
        raise ValidationError(
            "Исправление или отмену нужно создавать для исходной записи, "
            "а не для уже зарегистрированного события жизненного цикла."
        )


def register_draft(
    *,
    draft: OperationalDraftEntry,
    actor,
) -> OperationalLogEntry:
    draft_context = OperationalDraftEntry.objects.select_related(
        "shift",
        "shift__journal",
        "shift__journal__organization",
        "shift__journal__workplace",
    ).get(pk=draft.pk)
    evaluation = _evaluate_authority(
        actor=actor,
        journal=draft_context.shift.journal,
        action_code=ACTION_REGISTER,
        subject_type="OPJ_DRAFT",
        subject_id=str(draft_context.public_id),
    )
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
        if locked_draft.is_removed:
            raise ValidationError("Убранную черновую запись нельзя зарегистрировать.")
        if not locked_draft.content.strip():
            raise ValidationError("Перед регистрацией заполните содержание записи.")
        payload = {
            "schema_version": SCHEMA_VERSION,
            "kind": "ORIGINAL",
            "draft": {
                "public_id": str(locked_draft.public_id),
                "version": locked_draft.version,
                "editor_schema_version": locked_draft.editor_schema_version,
                "editor_payload": locked_draft.editor_payload,
            },
            "authority": _authority_payload(evaluation),
        }
        entry = register_entry(
            journal=locked_draft.shift.journal,
            actor=actor,
            event_at=locked_draft.event_at,
            content=locked_draft.content,
            entry_form=EntryForm.TYPED,
            type_code=TYPE_ENTRY,
            type_title="Оперативная запись",
            typed_payload=payload,
        )
        remove_draft_entry(entry=locked_draft, actor=actor)
        return entry


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
        raise ValidationError({"replacement_content": "Исправленное содержание обязательно."})
    if not normalized_reason:
        raise ValidationError({"reason": "Основание исправления обязательно."})
    evaluation = _evaluate_authority(
        actor=actor,
        journal=entry.journal,
        action_code=ACTION_CORRECT,
        subject_type="OPJ_ENTRY",
        subject_id=f"{entry.journal_id}:{entry.sequence_number}:CORRECTION:{uuid.uuid4()}",
    )
    with transaction.atomic():
        locked = (
            OperationalLogEntry.objects.select_for_update()
            .select_related("journal", "journal__organization", "journal__workplace")
            .get(pk=entry.pk)
        )
        _ensure_original_target(locked)
        lifecycle = _lifecycle_entries(locked)
        state = effective_state(locked, lifecycle)
        if state.status == "CANCELLED":
            raise ValidationError("Отменённую запись нельзя исправлять.")
        payload = {
            "schema_version": SCHEMA_VERSION,
            "kind": "CORRECTION",
            "target": _target_payload(locked),
            "previous_effective_content": state.effective_content,
            "replacement_content": normalized_content,
            "reason": normalized_reason,
            "authority": _authority_payload(evaluation),
        }
        return register_entry(
            journal=locked.journal,
            actor=actor,
            event_at=timezone.now(),
            content=(
                f"Исправление записи № {locked.sequence_number}. "
                f"{normalized_content} Основание: {normalized_reason}"
            ),
            entry_form=EntryForm.TYPED,
            type_code=TYPE_CORRECTION,
            type_title="Исправление зарегистрированной записи",
            typed_payload=payload,
        )


def cancel_entry(
    *,
    entry: OperationalLogEntry,
    actor,
    reason: str,
) -> OperationalLogEntry:
    _ensure_original_target(entry)
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise ValidationError({"reason": "Основание отмены обязательно."})
    evaluation = _evaluate_authority(
        actor=actor,
        journal=entry.journal,
        action_code=ACTION_CANCEL,
        subject_type="OPJ_ENTRY",
        subject_id=f"{entry.journal_id}:{entry.sequence_number}:CANCELLATION:{uuid.uuid4()}",
    )
    with transaction.atomic():
        locked = (
            OperationalLogEntry.objects.select_for_update()
            .select_related("journal", "journal__organization", "journal__workplace")
            .get(pk=entry.pk)
        )
        _ensure_original_target(locked)
        lifecycle = _lifecycle_entries(locked)
        state = effective_state(locked, lifecycle)
        if state.status == "CANCELLED":
            raise ValidationError("Запись уже отменена.")
        payload = {
            "schema_version": SCHEMA_VERSION,
            "kind": "CANCELLATION",
            "target": _target_payload(locked),
            "effective_content_at_cancellation": state.effective_content,
            "reason": normalized_reason,
            "authority": _authority_payload(evaluation),
        }
        return register_entry(
            journal=locked.journal,
            actor=actor,
            event_at=timezone.now(),
            content=(
                f"Отмена записи № {locked.sequence_number}. "
                f"Основание: {normalized_reason}"
            ),
            entry_form=EntryForm.TYPED,
            type_code=TYPE_CANCELLATION,
            type_title="Отмена зарегистрированной записи",
            typed_payload=payload,
        )


def record_communication(
    *,
    entry: OperationalLogEntry,
    actor,
    direction: str,
    channel: str,
    counterpart: str,
    counterpart_organization: str,
    content: str,
) -> OperationalLogEntry:
    _ensure_original_target(entry)
    normalized_counterpart = " ".join(counterpart.split())
    normalized_organization = " ".join(counterpart_organization.split())
    normalized_content = content.strip()
    if direction not in dict(CommunicationForm.Direction.choices):
        raise ValidationError({"direction": "Неизвестное направление разговора."})
    if channel not in dict(CommunicationForm.Channel.choices):
        raise ValidationError({"channel": "Неизвестный канал разговора."})
    if not normalized_counterpart:
        raise ValidationError({"counterpart": "Укажите участника разговора."})
    if not normalized_content:
        raise ValidationError({"content": "Содержание разговора обязательно."})
    evaluation = _evaluate_authority(
        actor=actor,
        journal=entry.journal,
        action_code=ACTION_COMMUNICATION,
        subject_type="OPJ_COMMUNICATION",
        subject_id=f"{entry.journal_id}:{entry.sequence_number}:{uuid.uuid4()}",
    )
    with transaction.atomic():
        locked = (
            OperationalLogEntry.objects.select_for_update()
            .select_related("journal", "journal__organization", "journal__workplace")
            .get(pk=entry.pk)
        )
        _ensure_original_target(locked)
        direction_label = dict(CommunicationForm.Direction.choices)[direction]
        channel_label = dict(CommunicationForm.Channel.choices)[channel]
        payload = {
            "schema_version": SCHEMA_VERSION,
            "kind": "COMMUNICATION",
            "target": _target_payload(locked),
            "direction": direction,
            "direction_label": direction_label,
            "channel": channel,
            "channel_label": channel_label,
            "counterpart": normalized_counterpart,
            "counterpart_organization": normalized_organization,
            "content": normalized_content,
            "authority": _authority_payload(evaluation),
        }
        organization_part = (
            f", {normalized_organization}" if normalized_organization else ""
        )
        return register_entry(
            journal=locked.journal,
            actor=actor,
            event_at=timezone.now(),
            content=(
                f"{direction_label}, {channel_label}: {normalized_counterpart}"
                f"{organization_part}. {normalized_content}"
            ),
            entry_form=EntryForm.TYPED,
            type_code=TYPE_COMMUNICATION,
            type_title="Оперативный разговор",
            typed_payload=payload,
        )


@login_required
def entry_lifecycle_view(
    request: HttpRequest,
    journal_id: int,
    sequence_number: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    entry = _entry_or_404(journal=journal, sequence_number=sequence_number)

    linked_original = None
    if entry.type_code in SYSTEM_TYPES - {TYPE_ENTRY}:
        target_sequence = entry.typed_payload.get("target", {}).get("sequence_number")
        if target_sequence:
            linked_original = journal.entries.filter(
                sequence_number=target_sequence
            ).first()

    lifecycle = _lifecycle_entries(entry) if entry.type_code not in LIFECYCLE_TYPES else []
    communications = (
        _communication_entries(entry) if entry.type_code not in LIFECYCLE_TYPES else []
    )
    state = effective_state(entry, lifecycle)
    integrity_ok = True
    try:
        verify_entry_integrity(entry)
        for event in (*lifecycle, *communications):
            verify_entry_integrity(event)
    except ValidationError:
        integrity_ok = False

    return render(
        request,
        "operational_log/entry_lifecycle.html",
        {
            "journal": journal,
            "entry": entry,
            "linked_original": linked_original,
            "lifecycle_entries": lifecycle,
            "communications": communications,
            "state": state,
            "integrity_ok": integrity_ok,
            "correction_form": CorrectionForm(
                initial={"replacement_content": state.effective_content}
            ),
            "cancellation_form": CancellationForm(),
            "communication_form": CommunicationForm(),
            "can_act": entry.type_code not in LIFECYCLE_TYPES,
        },
    )


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
        text = "; ".join(getattr(error, "messages", [str(error)]))
        messages.error(request, text)
        return redirect("operational_log:shift_workspace", journal_id=journal.pk)
    messages.success(
        request,
        f"Запись № {entry.sequence_number} зарегистрирована и стала неизменяемой.",
    )
    return redirect(
        "operational_log:entry_lifecycle",
        journal_id=journal.pk,
        sequence_number=entry.sequence_number,
    )


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
        messages.error(request, "Исправление не зарегистрировано: проверьте поля формы.")
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
            decision = event.typed_payload["authority"]["decision"]
            messages.success(
                request,
                f"Исправление зарегистрировано отдельной записью № "
                f"{event.sequence_number}. Решение полномочия: {decision}.",
            )
    return redirect(
        "operational_log:entry_lifecycle",
        journal_id=journal.pk,
        sequence_number=entry.sequence_number,
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
    form = CancellationForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Отмена не зарегистрирована: укажите основание.")
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
            decision = event.typed_payload["authority"]["decision"]
            messages.success(
                request,
                f"Отмена зарегистрирована отдельной записью № "
                f"{event.sequence_number}. Решение полномочия: {decision}.",
            )
    return redirect(
        "operational_log:entry_lifecycle",
        journal_id=journal.pk,
        sequence_number=entry.sequence_number,
    )


@require_POST
@login_required
def communication_view(
    request: HttpRequest,
    journal_id: int,
    sequence_number: int,
) -> HttpResponse:
    employee = require_operational_employee(request.user)
    journal = _accessible_journal(employee, journal_id)
    entry = _entry_or_404(journal=journal, sequence_number=sequence_number)
    form = CommunicationForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Разговор не зарегистрирован: проверьте поля формы.")
    else:
        try:
            event = record_communication(
                entry=entry,
                actor=employee,
                direction=form.cleaned_data["direction"],
                channel=form.cleaned_data["channel"],
                counterpart=form.cleaned_data["counterpart"],
                counterpart_organization=form.cleaned_data[
                    "counterpart_organization"
                ],
                content=form.cleaned_data["content"],
            )
        except (ValidationError, PermissionDenied) as error:
            messages.error(
                request,
                "; ".join(getattr(error, "messages", [str(error)])),
            )
        else:
            decision = event.typed_payload["authority"]["decision"]
            messages.success(
                request,
                f"Оперативный разговор зарегистрирован записью № "
                f"{event.sequence_number}. Решение полномочия: {decision}.",
            )
    return redirect(
        "operational_log:entry_lifecycle",
        journal_id=journal.pk,
        sequence_number=entry.sequence_number,
    )
