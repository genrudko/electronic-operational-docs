from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime, time
from typing import Any
from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import SafeString, mark_safe

from .editor import (
    ENTRY_KIND_LABELS,
    editor_document_to_text,
    normalize_editor_document,
    serialize_editor_document,
)
from .models import OperationalDraftEntry, OperationalLogEntry
from .opj_integrity import verify_registered_snapshot
from .opj_lifecycle import TYPE_CORRECTION, entry_lifecycle_context


@dataclass(frozen=True, slots=True)
class EditorPresentation:
    html: SafeString
    emergency: bool
    markers: tuple[dict[str, Any], ...]
    editor_payload: dict[str, Any]
    editor_payload_json: str
    entry_kind_label: str


@dataclass(slots=True)
class CleanJournalGroup:
    key: str
    date_label: str
    period_label: str
    start_at: datetime
    shift_public_id: str
    is_shift: bool
    rows: list[dict[str, Any]]


def _entry_editor_document(entry: OperationalLogEntry) -> dict[str, Any]:
    payload = entry.typed_payload if isinstance(entry.typed_payload, dict) else {}
    draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
    editor_payload = draft.get("editor_payload")
    if entry.type_code == TYPE_CORRECTION:
        editor_payload = payload.get("replacement_editor_payload")
    return normalize_editor_document(editor_payload, fallback_text=entry.content)


def effective_editor_document(
    entry: OperationalLogEntry,
    lifecycle_entries: Iterable[OperationalLogEntry] | None = None,
) -> dict[str, Any]:
    document = _entry_editor_document(entry)
    events = (
        tuple(lifecycle_entries)
        if lifecycle_entries is not None
        else entry_lifecycle_context(entry).lifecycle_entries
    )
    for event in events:
        if event.type_code != TYPE_CORRECTION:
            continue
        payload = event.typed_payload if isinstance(event.typed_payload, dict) else {}
        document = normalize_editor_document(
            payload.get("replacement_editor_payload"),
            fallback_text=str(payload.get("replacement_content") or event.content),
        )
    return document


def _escaped_text(value: str) -> SafeString:
    pieces = str(value or "").split("\n")
    rendered: list[str] = []
    for index, piece in enumerate(pieces):
        if index:
            rendered.append("<br>")
        rendered.append(str(conditional_escape(piece)))
    return mark_safe("".join(rendered))


def _reference_url(reference: dict[str, Any]) -> str:
    identity = str(reference.get("reference") or "").strip()
    kind = str(reference.get("kind") or "").strip()
    if ":" not in identity:
        return ""
    prefix, raw_id = identity.split(":", 1)
    if not raw_id:
        return ""
    kind = kind or prefix
    escaped = quote(raw_id, safe="")
    if kind == "equipment":
        return f"/equipment/items/{escaped}/"
    if kind == "document":
        return f"/documents/{escaped}/"
    if kind in {"person", "employee"}:
        return "/organization/"
    return ""


def _reference_html(reference: dict[str, Any], text: SafeString) -> SafeString:
    identity = str(reference.get("reference") or "").strip()
    kind = str(reference.get("kind") or "").strip()
    label = str(reference.get("label") or "").strip()
    url = _reference_url(reference)
    if not identity or not label:
        return text
    if not url:
        return format_html(
            '<span class="opj-reference-token is-unresolved" '
            'title="Связанный объект недоступен для перехода">{}</span>',
            text,
        )
    return format_html(
        '<button type="button" class="opj-reference-token" '
        'data-opj-reference-token data-reference-kind="{}" '
        'data-reference-value="{}" data-reference-label="{}" '
        'data-reference-url="{}" title="Показать связанную карточку">{}</button>',
        kind,
        identity,
        label,
        url,
        text,
    )


def _segment_html(
    segment: dict[str, Any],
    annotations: dict[str, dict[str, str]],
) -> SafeString:
    classes = ["opj-rich-segment"]
    marks = set(segment.get("marks") or [])
    mark_classes = {
        "bold": "is-bold",
        "italic": "is-italic",
        "underline": "is-underlined",
        "strike": "is-struck",
        "text_red": "is-text-red",
        "text_blue": "is-text-blue",
    }
    classes.extend(mark_classes[mark] for mark in mark_classes if mark in marks)

    annotation_rows = [
        annotations[annotation_id]
        for annotation_id in segment.get("annotations") or []
        if annotation_id in annotations
    ]
    if any(row.get("kind") in {"zn_on", "pz_install"} for row in annotation_rows):
        classes.append("is-normative-open")
    if any(row.get("kind") in {"zn_off", "pz_remove"} for row in annotation_rows):
        classes.append("is-normative-close")

    text = _escaped_text(str(segment.get("text") or ""))
    reference = segment.get("reference")
    if isinstance(reference, dict):
        text = _reference_html(reference, text)
    return format_html('<span class="{}">{}</span>', " ".join(classes), text)


def _block_html(
    block: dict[str, Any],
    annotations: dict[str, dict[str, str]],
) -> SafeString:
    block_type = block.get("type")
    if block_type == "paragraph":
        body = mark_safe(
            "".join(
                str(_segment_html(segment, annotations))
                for segment in block.get("segments") or []
            )
        )
        return format_html('<p class="opj-rich-paragraph">{}</p>', body)

    tag = "ol" if block_type == "ordered_list" else "ul"
    items = []
    for item in block.get("items") or []:
        body = mark_safe(
            "".join(
                str(_segment_html(segment, annotations))
                for segment in item.get("segments") or []
            )
        )
        items.append(str(format_html("<li>{}</li>", body)))
    return mark_safe(f'<{tag} class="opj-rich-list">{"".join(items)}</{tag}>')


def _annotation_source_text(document: dict[str, Any]) -> dict[str, str]:
    values: dict[str, list[str]] = {}
    for block in document.get("blocks") or []:
        segments = block.get("segments") or []
        if block.get("type") in {"ordered_list", "bullet_list"}:
            segments = [
                segment
                for item in block.get("items") or []
                for segment in item.get("segments") or []
            ]
        for segment in segments:
            text = " ".join(str(segment.get("text") or "").split())
            if not text:
                continue
            for annotation_id in segment.get("annotations") or []:
                bucket = values.setdefault(str(annotation_id), [])
                if text not in bucket:
                    bucket.append(text)
    return {key: "; ".join(parts) for key, parts in values.items()}


def _marker_rows(
    annotation_rows: dict[str, dict[str, str]],
    source_text: dict[str, str],
) -> tuple[dict[str, Any], ...]:
    buckets: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
    for annotation_id, row in annotation_rows.items():
        kind = str(row.get("kind") or "")
        if not kind or kind == "emergency":
            continue
        pz_number = str(row.get("pz_number") or "")
        key = (kind, pz_number)
        detail = source_text.get(annotation_id, "")
        if key not in buckets:
            buckets[key] = {
                "kind": kind,
                "label": str(row.get("label") or ""),
                "pz_number": pz_number,
                "count": 1,
                "details": [detail] if detail else [],
            }
        else:
            buckets[key]["count"] += 1
            if detail and detail not in buckets[key]["details"]:
                buckets[key]["details"].append(detail)
    for marker in buckets.values():
        marker["source_text"] = "; ".join(marker.pop("details"))
    return tuple(buckets.values())


def present_editor_document(document: dict[str, Any]) -> EditorPresentation:
    normalized = normalize_editor_document(document)
    annotation_rows = {
        str(row["id"]): row
        for row in normalized.get("annotations") or []
        if isinstance(row, dict) and row.get("id")
    }
    html = mark_safe(
        "".join(
            str(_block_html(block, annotation_rows))
            for block in normalized.get("blocks") or []
        )
    )
    entry_kind = str(normalized.get("entry_kind") or "normal")
    return EditorPresentation(
        html=html,
        emergency=any(
            row.get("kind") == "emergency" for row in annotation_rows.values()
        ),
        markers=_marker_rows(annotation_rows, _annotation_source_text(normalized)),
        editor_payload=normalized,
        editor_payload_json=serialize_editor_document(normalized),
        entry_kind_label=ENTRY_KIND_LABELS.get(entry_kind, ENTRY_KIND_LABELS["normal"]),
    )


def entry_presentation(
    entry: OperationalLogEntry,
    lifecycle_entries: Iterable[OperationalLogEntry] | None = None,
) -> EditorPresentation:
    return present_editor_document(
        effective_editor_document(entry, lifecycle_entries=lifecycle_entries)
    )


def _draft_public_id(entry: OperationalLogEntry) -> str:
    payload = entry.typed_payload if isinstance(entry.typed_payload, dict) else {}
    draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
    return str(draft.get("public_id") or "")


def _date_group(entry: OperationalLogEntry) -> CleanJournalGroup:
    local_event = timezone.localtime(entry.event_at)
    start = timezone.make_aware(
        datetime.combine(local_event.date(), time.min),
        timezone.get_current_timezone(),
    )
    return CleanJournalGroup(
        key=f"date:{local_event:%Y-%m-%d}",
        date_label=local_event.strftime("%d.%m.%Y"),
        period_label="Записи вне сменного черновика",
        start_at=start,
        shift_public_id="",
        is_shift=False,
        rows=[],
    )


def _stable_lifecycle(entry: OperationalLogEntry):
    lifecycle = entry_lifecycle_context(entry)
    try:
        verify_registered_snapshot(entry)
        for event in lifecycle.lifecycle_entries:
            verify_registered_snapshot(event)
    except ValidationError:
        integrity_ok = False
    else:
        integrity_ok = True
    return replace(lifecycle, integrity_ok=integrity_ok)


def journal_number_map(
    entries: Iterable[OperationalLogEntry],
    drafts: dict[str, OperationalDraftEntry] | None = None,
) -> dict[int, int]:
    draft_rows = drafts or {}

    def order_key(entry: OperationalLogEntry):
        draft = draft_rows.get(_draft_public_id(entry))
        source_position = draft.position if draft is not None else 1_000_000_000
        return (
            entry.event_at,
            source_position,
            entry.sequence_number,
            entry.pk,
        )

    ordered = sorted(entries, key=order_key)
    return {entry.pk: index for index, entry in enumerate(ordered, start=1)}


def build_clean_journal_groups(
    *,
    entries: list[OperationalLogEntry],
    selected_shift: str = "",
) -> list[CleanJournalGroup]:
    draft_ids = {
        draft_id for entry in entries if (draft_id := _draft_public_id(entry))
    }
    drafts = {
        str(draft.public_id): draft
        for draft in OperationalDraftEntry.objects.filter(
            public_id__in=draft_ids
        ).select_related("shift")
    }
    numbers = journal_number_map(entries, drafts)

    groups: OrderedDict[str, CleanJournalGroup] = OrderedDict()
    for entry in entries:
        lifecycle = _stable_lifecycle(entry)
        if lifecycle.is_child:
            continue
        draft = drafts.get(_draft_public_id(entry))
        if draft is not None:
            shift = draft.shift
            shift_public_id = str(shift.public_id)
            if selected_shift and selected_shift != shift_public_id:
                continue
            local_start = timezone.localtime(shift.planned_start_at)
            local_end = timezone.localtime(shift.planned_end_at)
            key = f"shift:{shift_public_id}"
            group = groups.get(key)
            if group is None:
                group = CleanJournalGroup(
                    key=key,
                    date_label=local_start.strftime("%d.%m.%Y"),
                    period_label=f"Смена {local_start:%H:%M}–{local_end:%H:%M}",
                    start_at=shift.planned_start_at,
                    shift_public_id=shift_public_id,
                    is_shift=True,
                    rows=[],
                )
                groups[key] = group
        else:
            if selected_shift:
                continue
            candidate = _date_group(entry)
            group = groups.setdefault(candidate.key, candidate)

        presentation = entry_presentation(
            entry,
            lifecycle_entries=lifecycle.lifecycle_entries,
        )
        lifecycle_rows = [
            {
                "entry": event,
                "journal_number": numbers.get(event.pk, event.sequence_number),
                "presentation": entry_presentation(event),
            }
            for event in lifecycle.lifecycle_entries
        ]
        group.rows.append(
            {
                "entry": entry,
                "journal_number": numbers.get(entry.pk, entry.sequence_number),
                "lifecycle": lifecycle,
                "lifecycle_rows": lifecycle_rows,
                "presentation": presentation,
                "effective_content": editor_document_to_text(
                    presentation.editor_payload
                ),
                "defect_links": list(entry.equipment_defect_links.all()),
                "show_date": False,
            }
        )

    result = sorted(groups.values(), key=lambda item: item.start_at)
    for group in result:
        group.rows.sort(key=lambda row: row["journal_number"])
        previous_date = None
        for row in group.rows:
            current_date = timezone.localtime(row["entry"].event_at).date()
            row["show_date"] = current_date != previous_date
            previous_date = current_date
    return result
