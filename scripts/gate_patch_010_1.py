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

from apps.operational_log.form_contracts import (  # noqa: E402
    OPERATIONAL_JOURNAL_FORM,
    OPERATIONAL_JOURNAL_FORM_CODE,
    approved_journal_form,
)
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
assert any(entry.typed_payload for entry in entries if entry.entry_form == EntryForm.TYPED)
print("TYPED_AND_FREE_ENTRIES=PASSED")

assert all(entry.author_full_name_snapshot for entry in entries)
assert all(entry.author_position_snapshot for entry in entries)
print("AUTHOR_ROLE_SNAPSHOT=PASSED")

assert OperationalLogEquipmentLink.objects.filter(entry__journal=journal).count() == 4
assert OperationalLogDocumentLink.objects.filter(entry__journal=journal).count() == 2
assert all(link.dispatcher_name_snapshot for link in OperationalLogEquipmentLink.objects.all())
assert all(link.registration_number_snapshot for link in OperationalLogDocumentLink.objects.all())
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

form_contract = approved_journal_form(OPERATIONAL_JOURNAL_FORM_CODE)
assert form_contract is OPERATIONAL_JOURNAL_FORM
form_contract.validate()
assert tuple(column.title for column in form_contract.columns) == (
    "Дата и время записи",
    "Содержание записей в течение смены, подписи о приемке и сдаче смены",
    "Визы и замечания административно-технического персонала",
)
assert tuple(column.key for column in form_contract.columns) == (
    "date_time",
    "message",
    "visas",
)
assert sum(column.width_percent for column in form_contract.columns) == 100
print("APPROVED_JOURNAL_FORM_CONTRACT=PASSED")

user = get_user_model().objects.get(username="operator.demo")
client = Client()
client.force_login(user)
registry = client.get(reverse("operational_log:registry"))
assert registry.status_code == 200
registry_text = registry.content.decode("utf-8")
for marker in (
    "Оперативные журналы",
    "Утверждённая форма является обязательным контрактом",
    "Оперативный журнал сменного персонала",
    "И-00-007-ОР-2025",
):
    assert marker in registry_text, marker

detail = client.get(reverse("operational_log:detail", args=(journal.pk,)))
assert detail.status_code == 200
detail_text = detail.content.decode("utf-8")
for marker in (
    "Дата и время записи",
    "Содержание записей в течение смены, подписи о приемке и сдаче смены",
    "Визы и замечания административно-технического персонала",
    "approved-journal-table",
    "data-approved-journal-form=",
    "КТП-01",
    "ДЕМО-2026-000001",
):
    assert marker in detail_text, marker
assert detail_text.count('<th scope="col">') == 3
assert detail_text.index("Демонстрационное дежурство начато") < detail_text.index(
    "Получена вымышленная информация"
)
for forbidden in (
    "ХРОНОЛОГИЧЕСКАЯ ЛЕНТА",
    "Целостность подтверждена",
    "operational-entry",
    "Создать запись",
    "Редактировать запись",
    "Аннулировать запись",
):
    assert forbidden not in detail_text, forbidden
print("READ_ONLY_APPROVED_FORM_UI=PASSED")

css_text = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
header_rule = css_text.split(".approved-journal-table th {", 1)[1].split("}", 1)[0]
assert "position: sticky" not in header_rule
assert "top: 62px" not in header_rule
assert "position: static" in header_rule
print("APPROVED_FORM_HEADER_FLOW=PASSED")

assert OperationalLogEntry.objects.count() >= 5
print("PATCH_010_1_OPERATIONAL_LOG_CORE_GATE_PASSED")
print("PATCH_010_1_1_APPROVED_FORM_UX_GATE_PASSED")
