from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402

django.setup()

from apps.documents.services import IntegrityStatus  # noqa: E402
from apps.normatives.models import (  # noqa: E402
    NormativeDocument,
    NormativeRequirement,
    NormativeRevision,
    OrganizationConfigurationRevision,
    OrganizationNameRevision,
    PublicationStatus,
    RequirementTrace,
)
from apps.normatives.services import organization_name_on  # noqa: E402
from apps.organizations.models import Organization  # noqa: E402

document = NormativeDocument.objects.get(code="demo-electronic-documentation")
revision = NormativeRevision.objects.get(document=document, revision_number=1)
if revision.status != PublicationStatus.PUBLISHED or len(revision.digest) != 64:
    raise SystemExit("Published normative revision or its SHA-256 is missing.")
if revision.requirements.count() < 3:
    raise SystemExit("Expected at least three normative requirements.")
if RequirementTrace.objects.count() < 3:
    raise SystemExit("Expected requirement-to-function traces.")

try:
    revision.change_summary = "Недопустимое изменение"
    revision.save()
except ValidationError:
    pass
else:
    raise SystemExit("Published normative revision is mutable.")

try:
    NormativeRevision.objects.filter(pk=revision.pk).update(revision_number=99)
except ValidationError:
    pass
else:
    raise SystemExit("Published normative revision bulk update is not blocked.")

organization = Organization.objects.get(code="DEMO")
current_name = organization_name_on(organization)
if current_name is None or "Демонстрационная энергия" not in current_name.full_name:
    raise SystemExit("Current historical organization name was not resolved.")
if OrganizationNameRevision.objects.filter(
    organization=organization,
    status=PublicationStatus.PUBLISHED,
).count() < 2:
    raise SystemExit("Organization name history is incomplete.")
if not OrganizationConfigurationRevision.objects.filter(
    organization=organization,
    status=PublicationStatus.PUBLISHED,
).exists():
    raise SystemExit("Published organization configuration is missing.")

for status in IntegrityStatus:
    if not status.label or status.label == status.value:
        raise SystemExit(f"Russian integrity label is missing for {status.value}.")

detail_template = (ROOT / "src/templates/documents/detail.html").read_text(encoding="utf-8")
confirmation_template = (
    ROOT / "src/templates/documents/register_confirm.html"
).read_text(encoding="utf-8")
for marker in (
    "Что означает этот раздел?",
    'class="help-tip"',
    "Целостность подтверждена",
):
    if marker not in detail_template:
        raise SystemExit(f"Document detail help marker is missing: {marker}")
for marker in (
    "Что именно подтверждается?",
    "Пароль нигде не сохраняется",
    'class="help-tip"',
):
    if marker not in confirmation_template:
        raise SystemExit(f"Registration confirmation help marker is missing: {marker}")
if "{{ integrity.status.value }}" in detail_template:
    raise SystemExit("Raw English integrity status is still displayed.")

print(f"NORMATIVE_DOCUMENT_COUNT={NormativeDocument.objects.count()}")
print(f"PUBLISHED_REVISION_COUNT={NormativeRevision.objects.filter(status='PUBLISHED').count()}")
print(f"REQUIREMENT_COUNT={NormativeRequirement.objects.count()}")
print(f"TRACE_COUNT={RequirementTrace.objects.count()}")
print(f"NAME_REVISION_COUNT={OrganizationNameRevision.objects.count()}")
print(f"CONFIGURATION_REVISION_COUNT={OrganizationConfigurationRevision.objects.count()}")
print("RUSSIAN_STATUS_LABELS=PASSED")
print("CONTEXT_HELP=PASSED")
print("PATCH_005_NORMATIVE_REGISTRY_GATE_PASSED")
