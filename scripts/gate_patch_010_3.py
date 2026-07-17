from __future__ import annotations

import os
import sys
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
assert OperationalDraftEntry.objects.filter(shift=shift).count() == 3
assert OperationalDraftRevision.objects.filter(
    entry__shift=shift
).count() == 3
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
    "Черновик текущей смены",
    "Автосохранение включено",
    "Рабочая хронология",
    "Состав смены",
    "draft_workspace.js",
    "Убрать из черновика",
):
    assert marker in workspace_text, marker
for forbidden in (
    "Подписать чистовик",
    "Закрыть смену",
):
    assert forbidden not in workspace_text, forbidden
print("SHIFT_DRAFT_WORKSPACE=PASSED")

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
    ".draft-entry-card",
    ".draft-save-status.is-conflict",
):
    assert marker in css_text, marker
for marker in (
    "data-draft-form",
    "response.status === 409",
    "beforeunload",
):
    assert marker in js_text, marker
print("SHIFT_DRAFT_FRONTEND_CONTRACT=PASSED")

print("PATCH_010_3_OPERATIONAL_SHIFT_DRAFT_GATE_PASSED")
