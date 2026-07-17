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

from apps.organizations.models import RoleAssignment  # noqa: E402
from apps.workplace_docs.models import (  # noqa: E402
    RequirementKind,
    RevisionStatus,
    SourceKind,
    StorageForm,
    WorkplaceDocumentAuditEvent,
    WorkplaceDocumentEntry,
    WorkplaceDocumentList,
    WorkplaceDocumentRevision,
)

call_command("seed_demo_workplace_documents", verbosity=0)

document_list = WorkplaceDocumentList.objects.select_related("workplace").get(
    organization__code="DEMO",
    code="shift-workplace-documentation",
)
revision = WorkplaceDocumentRevision.objects.select_related(
    "approved_by",
    "approved_by__position",
).get(document_list=document_list, revision_number=1)
entries = list(revision.entries.select_related("normative_document"))

assert revision.status == RevisionStatus.APPROVED
assert len(revision.digest) == 64
assert revision.approved_at is not None
assert revision.next_review_date is not None
assert len(entries) == 7
print("WORKPLACE_DOCUMENT_MODELS=PASSED")

assert {entry.source_kind for entry in entries} == {SourceKind.TYPICAL, SourceKind.LOCAL}
print("TYPICAL_AND_LOCAL_POSITIONS=PASSED")

assert RequirementKind.MANDATORY in {entry.requirement_kind for entry in entries}
assert RequirementKind.CONDITIONAL in {entry.requirement_kind for entry in entries}
assert {entry.storage_form for entry in entries} == {
    StorageForm.PAPER,
    StorageForm.ELECTRONIC,
    StorageForm.MIXED,
}
assert all(entry.applicability_text for entry in entries)
print("MANDATORY_APPLICABILITY_AND_STORAGE=PASSED")

original_summary = revision.change_summary
revision.change_summary = "Недопустимое изменение"
try:
    revision.save()
except ValidationError:
    pass
else:
    raise AssertionError("Утверждённая редакция допускает изменение.")
revision.change_summary = original_summary
assert WorkplaceDocumentAuditEvent.objects.filter(revision=revision).count() == 1
print("APPROVED_REVISION_INTEGRITY=PASSED")

assert revision.review_period_months == 12
assert revision.next_review_date.isoformat() == "2027-01-01"
print("REVIEW_PERIODICITY=PASSED")

normative_entries = [entry for entry in entries if entry.normative_document_id]
assert len(normative_entries) == 1
assert normative_entries[0].normative_document.code == "demo-electronic-documentation"
print("NORMATIVE_LINK=PASSED")

assert RoleAssignment.objects.filter(
    employee=revision.approved_by,
    role__code="organization_admin",
    is_active=True,
).exists()

user_model = get_user_model()
user = user_model.objects.get(username="operator.demo")
client = Client()
client.force_login(user)
registry = client.get(reverse("workplace_docs:registry"))
assert registry.status_code == 200
registry_text = registry.content.decode("utf-8")
for marker in (
    "Перечни документации",
    "Показаны только утверждённые редакции вашей организации",
    "Перечень документации сменного персонала",
):
    assert marker in registry_text, marker

detail = client.get(reverse("workplace_docs:detail", args=(document_list.pk,)))
assert detail.status_code == 200
detail_text = detail.content.decode("utf-8")
for marker in (
    "Редакция утверждена и неизменяема",
    "Оперативный журнал",
    "Форма хранения",
    "Технические реквизиты редакции",
):
    assert marker in detail_text, marker
for forbidden in ("Создать редакцию", "Редактировать перечень", "Утвердить редакцию"):
    assert forbidden not in detail_text, forbidden
urls_text = (ROOT / "src" / "apps" / "workplace_docs" / "urls.py").read_text(encoding="utf-8")
for forbidden_route in ("create", "edit", "approve"):
    assert f'name="{forbidden_route}"' not in urls_text
print("READ_ONLY_REGISTRY_UI=PASSED")

assert WorkplaceDocumentList.objects.count() >= 1
assert WorkplaceDocumentRevision.objects.filter(status=RevisionStatus.APPROVED).count() >= 1
assert WorkplaceDocumentEntry.objects.count() >= 7
print("PATCH_009_1_WORKPLACE_DOCUMENT_REGISTRY_GATE_PASSED")
