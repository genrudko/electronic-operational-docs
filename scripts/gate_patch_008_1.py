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
os.environ.setdefault(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,testserver",
)

import django  # noqa: E402

django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

from apps.dispatching.models import ManagementRevision  # noqa: E402
from apps.equipment.models import EquipmentAsset  # noqa: E402
from apps.imports.models import ImportBatch, ImportEvent, ImportRow  # noqa: E402
from apps.imports.services import (  # noqa: E402
    create_import_batch,
    discard_import_batch,
)
from apps.organizations.models import Employee  # noqa: E402

operator = Employee.objects.select_related("user", "organization").get(
    personnel_number="DEMO-001"
)
core_counts = (
    EquipmentAsset.objects.count(),
    ManagementRevision.objects.count(),
)

batch = create_import_batch(
    uploaded_file=SimpleUploadedFile(
        "gate-equipment.csv",
        (
            "Код;Наименование\n"
            "EQ-1; КТП  01\n"
            "EQ-1; КТП  01\n"
            ";\n"
        ).encode(),
    ),
    target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
    employee=operator,
)

if batch.status != ImportBatch.Status.READY:
    raise SystemExit(f"Import preview was not created: {batch.error_message}")
if batch.rows.filter(status=ImportRow.Status.CONFLICT).count() != 2:
    raise SystemExit("Duplicate rows were not marked as conflicts.")
if batch.rows.filter(status=ImportRow.Status.REJECTED).count() != 1:
    raise SystemExit("Empty rows were not rejected.")
if len(batch.file_sha256) != 64:
    raise SystemExit("Source SHA-256 was not recorded.")

client = Client()
client.force_login(operator.user)
list_page = client.get(reverse("imports:list"))
detail_page = client.get(reverse("imports:detail", args=[batch.public_id]))
if list_page.status_code != 200 or detail_page.status_code != 200:
    raise SystemExit("Import pages are unavailable to the personal user.")
for marker in (
    "Импорт справочников",
    "не изменяют действующие справочники",
):
    if marker not in list_page.content.decode("utf-8"):
        raise SystemExit(f"Import registry marker is missing: {marker}")
detail_html = detail_page.content.decode("utf-8")
for marker in (
    "Это только предварительный просмотр",
    "ИСХОДНЫЕ ЗНАЧЕНИЯ",
    "Нормализованные значения строки",
    "Технические реквизиты файла",
):
    if marker not in detail_html:
        raise SystemExit(f"Import preview marker is missing: {marker}")

discard_import_batch(batch=batch, employee=operator)
batch.refresh_from_db()
if batch.status != ImportBatch.Status.DISCARDED:
    raise SystemExit("Discard action did not change the batch status.")
if not batch.rows.exists():
    raise SystemExit("Discard action removed auditable rows.")
if not batch.events.filter(event_type=ImportEvent.EventType.DISCARDED).exists():
    raise SystemExit("Discard action did not create an audit event.")
if core_counts != (
    EquipmentAsset.objects.count(),
    ManagementRevision.objects.count(),
):
    raise SystemExit("Import staging changed an active registry.")

settings = (ROOT / "src/eod_config/settings.py").read_text(encoding="utf-8")
urls = (ROOT / "src/eod_config/urls.py").read_text(encoding="utf-8")
base = (ROOT / "src/templates/base.html").read_text(encoding="utf-8")
css = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
for marker in (
    "apps.imports.apps.ImportsConfig",
    'include("apps.imports.urls")',
    "imports:list",
    "Patch 008.1: import staging and preview.",
):
    if marker not in settings + urls + base + css:
        raise SystemExit(f"Import integration marker is missing: {marker}")

print("IMPORT_STAGING_MODELS=PASSED")
print("CSV_SOURCE_AND_NORMALIZATION=PASSED")
print("ROW_CLASSIFICATION=PASSED")
print("IMPORT_PREVIEW_UI=PASSED")
print("DISCARD_AUDIT_RETENTION=PASSED")
print("ACTIVE_REGISTRIES_UNCHANGED=PASSED")
print("PATCH_008_1_IMPORT_STAGING_PREVIEW_GATE_PASSED")
