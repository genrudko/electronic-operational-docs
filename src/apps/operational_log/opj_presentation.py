from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

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
from .opj_lifecycle import TYPE_CORRECTION, entry_lifecycle_context


@dataclass(frozen=True, slots=True)
class EditorPresentation:
    html: SafeString
    emergency: bool
    markers: tuple[dict[str, str], ...]
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
    if isinstance(reference, dict) and reference.get("label"):
        text = format_html(
            '<span class="opj-reference-token" title="{}">{}</span>',
            reference.get("label"),
            text,
        )
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
    markers: list[dict[str, str]] = []
    for row in annotation_rows.values():
        kind = str(row.get("kind") or "")
        if kind == "emergency":
            continue
        markers.append(
            {
                "kind": kind,
                "label": str(row.get("label") or ""),
                "pz_number": str(row.get("pz_number") or ""),
            }
        )
    entry_kind = str(normalized.get("entry_kind") or "normal")
    return EditorPresentation(
        html=html,
        emergency=any(
            row.get("kind") == "emergency" for row in annotation_rows.values()
        ),
        markers=tuple(markers),
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

    groups: OrderedDict[str, CleanJournalGroup] = OrderedDict()
    for entry in entries:
        lifecycle = entry_lifecycle_context(entry)
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
        group.rows.append(
            {
                "entry": entry,
                "lifecycle": lifecycle,
                "presentation": presentation,
                "effective_content": editor_document_to_text(
                    presentation.editor_payload
                ),
                "defect_links": list(entry.equipment_defect_links.all()),
            }
        )

    result = sorted(groups.values(), key=lambda item: item.start_at)
    for group in result:
        group.rows.sort(
            key=lambda row: (
                row["entry"].event_at,
                row["entry"].sequence_number,
            )
        )
    return result
