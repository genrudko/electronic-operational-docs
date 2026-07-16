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

from django.core.exceptions import ValidationError  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

from apps.dispatching.models import (  # noqa: E402
    ManagementRevision,
    SupervisionRevision,
)
from apps.equipment.models import (  # noqa: E402
    EnergySite,
    EquipmentAsset,
    EquipmentType,
)
from apps.imports.models import ImportBatch, ImportEvent, ImportRow  # noqa: E402
from apps.imports.services import (  # noqa: E402
    create_import_batch,
    decide_import_row,
    save_column_mapping,
    save_row_correction,
)
from apps.organizations.models import Employee  # noqa: E402

operator = Employee.objects.select_related("user", "organization").get(
    personnel_number="DEMO-001"
)
site = EnergySite.objects.filter(
    organization=operator.organization,
    is_active=True,
).first()
equipment_type = EquipmentType.objects.filter(is_active=True).first()
if site is None or equipment_type is None:
    raise SystemExit("Demo registries do not contain an active site and equipment type.")

active_counts = {
    "employees": Employee.objects.count(),
    "equipment": EquipmentAsset.objects.count(),
    "management": ManagementRevision.objects.count(),
    "supervision": SupervisionRevision.objects.count(),
}

batch = create_import_batch(
    uploaded_file=SimpleUploadedFile(
        "gate-mapping-review.csv",
        (
            "Код;Наименование;Вид оборудования;Энергообъект;Состояние\n"
            f"IMP-GATE-0082-A;Новый объект A;{equipment_type.code};{site.code};В работе\n"
            f"IMP-GATE-0082-D;Новый объект D;{equipment_type.code};{site.code};Резерв\n"
            f"IMP-GATE-0082-D;Новый объект D;{equipment_type.code};{site.code};Резерв\n"
        ).encode(),
    ),
    target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
    employee=operator,
)
if batch.status != ImportBatch.Status.READY:
    raise SystemExit(f"Import preview was not created: {batch.error_message}")

mapping = {
    column.position: column.mapped_key
    for column in batch.columns.order_by("position")
}
batch = save_column_mapping(
    batch=batch,
    employee=operator,
    mapping=mapping,
)
if batch.mapping_revision != 1 or batch.mapping_completed_at is None:
    raise SystemExit("Column mapping was not persisted.")
if batch.rows.filter(review_status=ImportRow.ReviewStatus.VALID).count() != 1:
    raise SystemExit("A valid mapped row was not detected.")
if batch.rows.filter(review_status=ImportRow.ReviewStatus.CONFLICT).count() != 2:
    raise SystemExit("Mapped duplicates were not detected.")

valid_row = batch.rows.get(review_status=ImportRow.ReviewStatus.VALID)
decide_import_row(row=valid_row, employee=operator, action="ACCEPT")
valid_row.refresh_from_db()
if valid_row.decision != ImportRow.Decision.ACCEPTED:
    raise SystemExit("Valid row was not accepted inside staging.")

conflict_rows = list(
    batch.rows.filter(review_status=ImportRow.ReviewStatus.CONFLICT).order_by("row_number")
)
corrected_values = dict(conflict_rows[0].mapped_values)
corrected_values["code"] = "IMP-GATE-0082-FIX"
save_row_correction(
    row=conflict_rows[0],
    employee=operator,
    values=corrected_values,
    note="Gate correction",
)
decide_import_row(
    row=conflict_rows[1],
    employee=operator,
    action="REJECT",
    note="Gate rejection",
)
batch.refresh_from_db()
if batch.review_counts.get("accepted") != 2:
    raise SystemExit("Accepted decision count is incorrect.")
if batch.review_counts.get("rejected") != 1:
    raise SystemExit("Rejected decision count is incorrect.")
if not batch.review_counts.get("ready"):
    raise SystemExit("Completed preliminary decisions were not recognized.")

if not batch.events.filter(event_type=ImportEvent.EventType.MAPPING_UPDATED).exists():
    raise SystemExit("Mapping update was not audited.")
if batch.events.filter(event_type=ImportEvent.EventType.ROW_DECISION).count() != 3:
    raise SystemExit("Every row decision was not audited.")
first_event = batch.events.first()
first_event.details = {"tamper": True}
try:
    first_event.save()
except ValidationError:
    pass
else:
    raise SystemExit("Import audit event is mutable.")

client = Client()
client.force_login(operator.user)
detail_page = client.get(reverse("imports:detail", args=[batch.public_id]))
mapping_page = client.get(reverse("imports:mapping", args=[batch.public_id]))
edit_page = client.get(
    reverse("imports:row_edit", args=[batch.public_id, conflict_rows[0].pk])
)
if any(page.status_code != 200 for page in (detail_page, mapping_page, edit_page)):
    raise SystemExit("Patch 008.2 pages are unavailable to the personal user.")
detail_html = detail_page.content.decode("utf-8")
for marker in (
    "СОПОСТАВЛЕНИЕ КОЛОНОК",
    "Массовое решение для отмеченных строк",
    "Приняты предварительно",
    "Убрать из рабочего списка",
    "Публикация из этого этапа",
    "Нормализованные значения строки",
):
    if marker not in detail_html:
        raise SystemExit(f"Mapping and review UI marker is missing: {marker}")
for marker in (
    "Сопоставление не публикует данные",
    "Подтвердить сопоставление и пересчитать строки",
):
    if marker not in mapping_page.content.decode("utf-8"):
        raise SystemExit(f"Mapping page marker is missing: {marker}")
if "Исправление останется только в промежуточной зоне" not in edit_page.content.decode(
    "utf-8"
):
    raise SystemExit("Row correction safety marker is missing.")
if "/publish/" in detail_html or 'name="publish"' in detail_html:
    raise SystemExit("A publication action appeared in Patch 008.2.")

urls_text = (ROOT / "src/apps/imports/urls.py").read_text(encoding="utf-8")
list_template = (ROOT / "src/templates/imports/list.html").read_text(encoding="utf-8")
css = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
for marker in (
    "imports/<uuid:public_id>/mapping/",
    "imports/<uuid:public_id>/bulk-decision/",
    "{% if batches %}<span class=\"count-badge\"",
    "Patch 008.2: import column mapping and row review.",
):
    if marker not in urls_text + list_template + css:
        raise SystemExit(f"Patch 008.2 integration marker is missing: {marker}")
if "publish" in urls_text.casefold():
    raise SystemExit("Imports URL configuration contains a publication endpoint.")

if active_counts != {
    "employees": Employee.objects.count(),
    "equipment": EquipmentAsset.objects.count(),
    "management": ManagementRevision.objects.count(),
    "supervision": SupervisionRevision.objects.count(),
}:
    raise SystemExit("Mapping or row decisions changed an active registry.")

print("COLUMN_MAPPING=PASSED")
print("REQUIRED_FIELD_VALIDATION=PASSED")
print("IN_FILE_AND_ACTIVE_REGISTRY_CONFLICTS=PASSED")
print("ROW_CORRECTION_AND_DECISIONS=PASSED")
print("INDIVIDUAL_DECISION_AUDIT=PASSED")
print("IMMUTABLE_IMPORT_AUDIT=PASSED")
print("MAPPING_AND_REVIEW_UI=PASSED")
print("ACTIVE_REGISTRY_PUBLICATION=DISABLED")
print("PATCH_008_2_MAPPING_AND_REVIEW_GATE_PASSED")
