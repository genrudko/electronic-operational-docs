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
from django.core.exceptions import ValidationError  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

django.setup()

from apps.operational_log.models import (  # noqa: E402
    EntryForm,
    OperationalJournal,
    OperationalJournalSequence,
    OperationalLogAuditEvent,
    OperationalLogDocumentLink,
    OperationalLogEntry,
    OperationalLogEquipmentLink,
)
from apps.operational_log.services import verify_entry_integrity  # noqa: E402

call_command("seed_demo_operational_log", verbosity=0)

journal = OperationalJournal.objects.select_related("workplace", "organization").get(
    organization__code="DEMO",
    code="shift-operational-log",
)
entries = list(journal.entries.order_by("sequence_number"))
assert len(entries) == 5
assert OperationalJournalSequence.objects.get(journal=journal).last_value == 5
assert [entry.sequence_number for entry in entries] == [1, 2, 3, 4, 5]
print("TRANSACTIONAL_JOURNAL_NUMBERING=PASSED")

assert all(entry.event_at <= entry.registered_at for entry in entries)
assert all(len(entry.digest) == 64 for entry in entries)
print("EVENT_AND_REGISTRATION_TIME=PASSED")

assert {entry.entry_form for entry in entries} == {EntryForm.FREE_TEXT, EntryForm.TYPED}
assert any(
    entry.typed_payload for entry in entries if entry.entry_form == EntryForm.TYPED
)
print("TYPED_AND_FREE_ENTRIES=PASSED")

assert all(entry.author_full_name_snapshot for entry in entries)
assert all(entry.author_position_snapshot for entry in entries)
print("AUTHOR_ROLE_SNAPSHOT=PASSED")

assert OperationalLogEquipmentLink.objects.filter(entry__journal=journal).count() == 4
assert OperationalLogDocumentLink.objects.filter(entry__journal=journal).count() == 2
assert all(
    link.dispatcher_name_snapshot for link in OperationalLogEquipmentLink.objects.all()
)
assert all(
    link.registration_number_snapshot
    for link in OperationalLogDocumentLink.objects.all()
)
print("EQUIPMENT_AND_DOCUMENT_SNAPSHOTS=PASSED")

assert OperationalLogAuditEvent.objects.filter(entry__journal=journal).count() == 5
assert all(verify_entry_integrity(entry) for entry in entries)
original = entries[0].content
entries[0].content = "Недопустимая подмена"
try:
    entries[0].save()
except ValidationError:
    pass
else:
    raise AssertionError("Зарегистрированная запись допускает изменение.")
entries[0].content = original
print("IMMUTABLE_ENTRY_AND_AUDIT=PASSED")

user = get_user_model().objects.get(username="operator.demo")
client = Client()
client.force_login(user)
registry = client.get(reverse("operational_log:registry"))
assert registry.status_code == 200
registry_text = registry.content.decode("utf-8")
for marker in (
    "Оперативные журналы",
    "Зарегистрированные записи неизменяемы",
    "Оперативный журнал сменного персонала",
):
    assert marker in registry_text, marker

detail = client.get(reverse("operational_log:detail", args=(journal.pk,)))
assert detail.status_code == 200
detail_text = detail.content.decode("utf-8")
for marker in (
    "ХРОНОЛОГИЧЕСКАЯ ЛЕНТА",
    "Событие:",
    "Регистрация:",
    "Целостность подтверждена",
    "КТП-01",
    "ДЕМО-2026-000001",
):
    assert marker in detail_text, marker
for forbidden in ("Создать запись", "Редактировать запись", "Аннулировать запись"):
    assert forbidden not in detail_text, forbidden
print("READ_ONLY_CHRONOLOGICAL_UI=PASSED")

assert OperationalLogEntry.objects.count() >= 5
print("PATCH_010_1_OPERATIONAL_LOG_CORE_GATE_PASSED")
