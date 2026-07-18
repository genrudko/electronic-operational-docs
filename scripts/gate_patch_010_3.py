from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

django.setup()

from apps.operational_log.models import (  # noqa: E402
    OperationalDraftEntry,
    OperationalDraftRevision,
    OperationalJournal,
    OperationalJournalSequence,
    OperationalShift,
    OperationalShiftMember,
    ShiftStatus,
)

call_command("seed_demo_operational_log", verbosity=0)

user = get_user_model().objects.get(username="operator.demo")
journal = OperationalJournal.objects.get(
    organization__code="DEMO",
    code="shift-operational-log",
)
shift = OperationalShift.objects.get(
    journal=journal,
    status=ShiftStatus.OPEN,
)

assert journal.entries.count() == 5
assert OperationalJournalSequence.objects.get(
    journal=journal
).last_value == 5
assert OperationalShift.objects.filter(journal=journal).count() == 1
assert OperationalShiftMember.objects.filter(shift=shift).count() == 1
draft_entries = OperationalDraftEntry.objects.filter(shift=shift)
assert draft_entries.count() >= 3
assert all(
    entry.revisions.exists()
    for entry in draft_entries
)
revision_count = OperationalDraftRevision.objects.filter(
    entry__shift=shift
).count()
assert revision_count >= 3
print(f"SHIFT_DRAFT_REVISION_COUNT={revision_count}")
print("SHIFT_DRAFT_SEED=PASSED")

client = Client()
client.force_login(user)

detail_url = reverse(
    "operational_log:detail",
    args=(journal.pk,),
)
workspace_url = reverse(
    "operational_log:shift_workspace",
    args=(journal.pk,),
)

detail = client.get(detail_url)
assert detail.status_code == 200
assert "Рабочая смена" in detail.content.decode("utf-8")

workspace = client.get(workspace_url)
assert workspace.status_code == 200
workspace_text = workspace.content.decode("utf-8")
for marker in (
    "РАБОЧИЙ ЧЕРНОВИК СМЕНЫ",
    "Автосохранение",
    "Одна страница",
    "Разворот",
    "Поиск по записям",
    "data-quick-time",
    "Дата и время записи",
    "Визы и замечания",
    "data-page-input",
    "data-page-buttons",
    "data-view-drawer",
    "data-column-resizer",
    "data-records-preset",
    "data-records-custom",
    "data-add-draft-form",
    "data-default-entry-date",
    "data-default-entry-date-iso",
    "data-shift-start",
    "data-shift-end",
    "screen-journal-theme",
    "data-apply-custom-records",
    "stable-page-layout-workspace",
    "draft_workspace.js",
    "draft-mini-toolbar",
):
    assert marker in workspace_text, marker
for forbidden in (
    "Подписать чистовик",
    "Закрыть смену",
):
    assert forbidden not in workspace_text, forbidden
assert "Сохранить сейчас" not in workspace_text
assert "↑ Выше" not in workspace_text
assert "↓ Ниже" not in workspace_text
assert 'data-page-size="8"' not in workspace_text
assert 'type="range"' not in workspace_text
assert "draft-workspace-layout" not in workspace_text
print("PAGED_SHIFT_DRAFT_WORKSPACE=PASSED")

before = shift.draft_entries.count()
add_response = client.post(
    reverse(
        "operational_log:add_draft",
        args=(journal.pk,),
    )
)
assert add_response.status_code == 302
assert shift.draft_entries.count() == before + 1
draft = shift.draft_entries.order_by("-pk").first()
assert draft.version == 1
assert draft.revisions.count() == 1
assert shift.planned_start_at <= draft.event_at
assert draft.event_at <= shift.planned_end_at
print("DEFAULT_DRAFT_TIME_WITHIN_SHIFT=PASSED")

autosave_url = reverse(
    "operational_log:autosave_draft",
    args=(journal.pk, draft.public_id),
)
event_value = timezone.localtime(
    draft.event_at
).strftime("%Y-%m-%dT%H:%M")
save_response = client.post(
    autosave_url,
    {
        "public_id": str(draft.public_id),
        "expected_version": 1,
        "event_at": event_value,
        "content": "Проверка автоматического сохранения черновика",
    },
)
assert save_response.status_code == 200
payload = save_response.json()
assert payload["ok"] is True
assert payload["version"] == 2
draft.refresh_from_db()
assert draft.version == 2
assert draft.revisions.count() == 2
assert (
    draft.content
    == "Проверка автоматического сохранения черновика"
)
print("DRAFT_AUTOSAVE_AND_REVISIONS=PASSED")

stale_response = client.post(
    autosave_url,
    {
        "public_id": str(draft.public_id),
        "expected_version": 1,
        "event_at": event_value,
        "content": "Устаревшая перезапись",
    },
)
assert stale_response.status_code == 409
assert stale_response.json()["conflict"] is True
draft.refresh_from_db()
assert (
    draft.content
    == "Проверка автоматического сохранения черновика"
)
print("DRAFT_OPTIMISTIC_CONCURRENCY=PASSED")

assert journal.entries.count() == 5
assert OperationalJournalSequence.objects.get(
    journal=journal
).last_value == 5
print("OFFICIAL_JOURNAL_UNCHANGED=PASSED")

css_text = (ROOT / "src/static/system/app.css").read_text(
    encoding="utf-8"
)
js_text = (
    ROOT / "src/static/operational_log/draft_workspace.js"
).read_text(encoding="utf-8")
for marker in (
    "/* Patch 010.3: рабочая смена",
    ".draft-ledger-row",
    ".draft-command-bar",
    ".draft-page-shell",
    ".draft-view-drawer",
    ".draft-column-resizer",
    ".draft-table-header",
    ".draft-save-status.is-conflict",
):
    assert marker in css_text, marker
for marker in (
    "data-draft-form",
    "response.status === 409",
    "beforeunload",
    "normalizeTime",
    "normalizeDate",
    "paginateByRecordCount",
    "buildPageNumbers",
    "updateColumnWidths",
    "startColumnResize",
    "updateOverlayOffsets",
    "openDrawer",
    "normalizeRecordSetting",
    "automaticRecordCapacity",
    "selectedRecordCapacity",
    "isDraftEditing",
    "flushDeferredPagination",
    "compositionstart",
    "compositionend",
    "createBlankRecord",
    "beginInlineCreation",
    "materializeInlineDraft",
    "defaultEntryDateIso",
    "isoDateToLabel",
    "openDateEditor",
    "validateShiftDateTime",
    "refreshInlineDateMarkers",
    'formData.set(\n            "event_at"',
    "parseCreatedDraftRow",
    "bindDraftRow",
):
    assert marker in js_text, marker
views_text = (
    ROOT / "src/apps/operational_log/views.py"
).read_text(encoding="utf-8")
assert "parse_datetime" in views_text
assert 'request.POST.get("event_at", "")' in views_text
assert "event_at=requested_event_at" in views_text
assert "Некорректная дата и время новой записи." in views_text
assert "_event_at_within_shift" in views_text
assert "_shift_event_at_error" in views_text
assert "_default_event_at_for_shift" in views_text
assert "requested_event_at = _default_event_at_for_shift(shift)" in views_text
assert "window.prompt" not in js_text

outside_event_at = shift.planned_end_at + timedelta(minutes=1)
outside_value = timezone.localtime(outside_event_at).strftime(
    "%Y-%m-%dT%H:%M"
)
before_outside = shift.draft_entries.count()
outside_add = client.post(
    reverse(
        "operational_log:add_draft",
        args=(journal.pk,),
    ),
    {"event_at": outside_value},
)
assert outside_add.status_code == 400
assert shift.draft_entries.count() == before_outside
outside_save = client.post(
    autosave_url,
    {
        "public_id": str(draft.public_id),
        "expected_version": draft.version,
        "event_at": outside_value,
        "content": draft.content,
    },
)
assert outside_save.status_code == 400
assert "event_at" in outside_save.json()["errors"]
print("INLINE_ENTRY_DATE_INHERITANCE=PASSED")
print("SHIFT_BOUND_DATE_VALIDATION=PASSED")

repair_css = css_text.split(
    "/* Patch 010.3.1 Repair 7.2 Repair 1:",
    1,
)[-1]
assert "aspect-ratio: 210 / 297" not in repair_css
assert "max-width: 1650px" in repair_css
assert "--draft-page-body-height" not in repair_css
assert ".draft-view-drawer" in repair_css
assert ".draft-column-resizer" in repair_css
assert ".draft-empty-record" in repair_css
assert ".draft-empty-record-time" in repair_css
assert ".draft-inline-create-content" in repair_css
assert ".draft-record-presets" in repair_css
assert "overflow: hidden" not in repair_css.split(
    ".draft-page-shell",
    1,
)[1].split("}", 1)[0]
assert "height: auto" in repair_css.split(
    ".draft-page-shell",
    1,
)[1].split("}", 1)[0]
assert "contain: layout paint" not in repair_css
assert "draft-workspace-layout" not in repair_css
assert "type=\"range\"" not in workspace_text
assert "data-view-drawer-backdrop" not in workspace_text
assert "data-column-time-number" not in workspace_text
assert "data-measure-page" not in workspace_text
assert "ШИРИНА ГРАФ" not in workspace_text
assert "ЗАПИСЕЙ НА СТРАНИЦЕ" in workspace_text
assert 'data-autosave-delay="1000"' in workspace_text
assert "data-add-draft-form" in workspace_text
assert "data-default-entry-date" in workspace_text
assert "+ Запись" in workspace_text
assert "eod-draft-records-per-page" in js_text
assert "paginateByRecordCount" in js_text
assert "visibleRows.slice" in js_text
assert "start += capacity" in js_text
assert "capacity - pageData.rows.length" in js_text
assert "beginInlineCreation" in js_text
assert "materializeInlineDraft" in js_text
assert "parseCreatedDraftRow" in js_text
assert "bindDraftRow" in js_text
assert "new DOMParser()" in js_text
assert "new FormData(addDraftForm)" in js_text
assert "updateOverlayOffsets" in js_text
assert 'handle.addEventListener("dblclick"' in js_text
assert 'textarea.addEventListener("input"' in js_text
input_contract = js_text.split(
    'textarea.addEventListener("input"',
    1,
)[1].split("});", 1)[0]
assert "schedulePagination" not in input_contract
assert "markPaginationPending" in input_contract
print("LARGE_BOOK_WORKSPACE=PASSED")
print("WORD_COLUMN_RESIZE_CONTRACT=PASSED")
print("STABLE_CONTINUOUS_INPUT=PASSED")
print("RECORD_COUNT_PAGINATION=PASSED")
print("UNCUT_PAGE_BOTTOM=PASSED")
print("DOCKED_DRAWER_LAYERING=PASSED")
print("REDUNDANT_COLUMN_PANEL_REMOVED=PASSED")
assert ".screen-journal-theme" in repair_css
assert '[data-theme="dark"]' in repair_css
assert ".draft-date-editor" in repair_css
assert "@media print" in repair_css
assert "color-scheme: dark" in repair_css
assert "hybrid-paper-theme" not in workspace_text
assert "window.prompt" not in js_text
assert "openDateEditor" in js_text
assert "validateShiftDateTime" in js_text
print("INLINE_BLANK_RECORD_CREATION=PASSED")
print("ADD_RECORD_BUTTON_PRESERVED=PASSED")
print("FULL_DARK_JOURNAL_THEME=PASSED")
print("INLINE_DATE_EDITOR=PASSED")

print("PATCH_010_3_1_REPAIR7_2_REPAIR1_DARK_DATE_EDITOR_GATE_PASSED")
