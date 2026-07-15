from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402
from django.db import connection, transaction  # noqa: E402

django.setup()

from apps.documents.models import Document  # noqa: E402
from apps.documents.services import (  # noqa: E402
    IntegrityStatus,
    create_document_draft,
    register_demo_document,
    verify_document_integrity,
)
from apps.equipment.models import (  # noqa: E402
    DocumentEquipmentSnapshot,
    EnergySite,
    EquipmentAlias,
    EquipmentAsset,
    EquipmentNameRevision,
    EquipmentRelation,
    EquipmentType,
)
from apps.equipment.services import (  # noqa: E402
    dispatcher_name_on,
    hierarchy_path,
    resolve_equipment_alias,
)
from apps.organizations.models import Employee, Organization  # noqa: E402

GATE_ID = UUID("00000000-0000-4000-8000-000000000306")

organization = Organization.objects.get(code="DEMO")
actor = Employee.objects.select_related("user").get(
    user__username="operator.demo"
)
ktp = EquipmentAsset.objects.get(code="DEMO-KTP-01")
wtg = EquipmentAsset.objects.get(code="DEMO-WTG-01")

if EnergySite.objects.filter(organization=organization).count() < 2:
    raise SystemExit("Expected at least two demonstration energy sites.")
if EquipmentType.objects.count() < 8:
    raise SystemExit("Expected equipment types for KTP, WTG, RU, lines, RPA and SDTU.")
if EquipmentAsset.objects.filter(organization=organization).count() < 9:
    raise SystemExit("Expected at least nine demonstration equipment assets.")
if EquipmentRelation.objects.count() < 6:
    raise SystemExit("Expected demonstration equipment relations.")
if EquipmentAlias.objects.count() < 4:
    raise SystemExit("Expected demonstration equipment aliases.")
if EquipmentNameRevision.objects.filter(status="PUBLISHED").count() < 10:
    raise SystemExit("Expected published dispatcher name revisions.")

if dispatcher_name_on(ktp, date(2025, 6, 1)) != "КТП-1 Демо-ВЭС":
    raise SystemExit("Historical dispatcher name resolution failed.")
if dispatcher_name_on(ktp) != "КТП-01 Кочубеевской ВЭС":
    raise SystemExit("Current dispatcher name resolution failed.")
if resolve_equipment_alias(organization, "КТП 1") != ktp:
    raise SystemExit("Equipment alias resolution failed.")
if "РУ 35 кВ" not in hierarchy_path(
    EquipmentAsset.objects.get(code="DEMO-RZA-01")
):
    raise SystemExit("Equipment hierarchy path is incomplete.")

published_name = EquipmentNameRevision.objects.filter(
    equipment=ktp,
    status="PUBLISHED",
).order_by("-revision_number").first()
try:
    published_name.dispatcher_name = "Недопустимое изменение"
    published_name.save()
except ValidationError:
    pass
else:
    raise SystemExit("Published dispatcher name is mutable.")

document = Document.objects.filter(public_id=GATE_ID).first()
document_type = organization.document_types.get(code="general")
if document is None:
    document = create_document_draft(
        document_type=document_type,
        actor=actor,
        title="Контрольная запись оборудования Patch 006",
        content={
            "subject": "Оборудование",
            "body": "Проверка снимка диспетчерских наименований.",
        },
        equipment_assets=[ktp, wtg],
        public_id=GATE_ID,
    )
if document.status == Document.Status.DRAFT:
    document = register_demo_document(
        document=document,
        actor=actor,
    ).document

integrity = verify_document_integrity(document)
if integrity.status != IntegrityStatus.VALID:
    raise SystemExit(f"Equipment document integrity is {integrity.status}.")
if integrity.snapshot is None:
    raise SystemExit("Signed snapshot is missing.")
payload = json.loads(integrity.snapshot.canonical_json)
if payload.get("schema") != "eod.document.registration.v2":
    raise SystemExit("Equipment document does not use registration snapshot v2.")
if len(payload.get("equipment", [])) != 2:
    raise SystemExit("Equipment snapshot does not contain two equipment items.")
snapshots = DocumentEquipmentSnapshot.objects.filter(document=document)
if snapshots.count() != 2:
    raise SystemExit("Document equipment snapshots are missing.")

tampered = snapshots.first()
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute(
            f'UPDATE "{DocumentEquipmentSnapshot._meta.db_table}" '
            "SET dispatcher_name_snapshot = %s WHERE id = %s",
            ["Подменённое имя", tampered.pk],
        )
    document.refresh_from_db()
    if verify_document_integrity(document).status != IntegrityStatus.INVALID:
        raise SystemExit("Equipment snapshot tampering was not detected.")
    transaction.set_rollback(True)

base_template = (ROOT / "src/templates/base.html").read_text(encoding="utf-8")
javascript = (ROOT / "src/static/system/app.js").read_text(encoding="utf-8")
css = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
for marker in (
    "system/app.js",
    "Оборудование",
):
    if marker not in base_template:
        raise SystemExit(f"Base template marker is missing: {marker}")
for marker in (
    "closeOtherTips",
    'event.key === "Escape"',
    'document.addEventListener("pointerdown"',
    "positionTip",
):
    if marker not in javascript:
        raise SystemExit(f"Context help JavaScript marker is missing: {marker}")
for marker in (
    "Patch 005.1",
    'data-placement="bottom-sheet"',
):
    if marker not in css:
        raise SystemExit(f"Context help CSS marker is missing: {marker}")

print(f"ENERGY_SITE_COUNT={EnergySite.objects.count()}")
print(f"EQUIPMENT_TYPE_COUNT={EquipmentType.objects.count()}")
print(f"EQUIPMENT_ASSET_COUNT={EquipmentAsset.objects.count()}")
print(f"DISPATCHER_NAME_REVISION_COUNT={EquipmentNameRevision.objects.count()}")
print(f"EQUIPMENT_ALIAS_COUNT={EquipmentAlias.objects.count()}")
print(f"EQUIPMENT_RELATION_COUNT={EquipmentRelation.objects.count()}")
print(f"DOCUMENT_EQUIPMENT_SNAPSHOT_COUNT={snapshots.count()}")
print("HISTORICAL_DISPATCHER_NAME=PASSED")
print("EQUIPMENT_ALIAS_RESOLUTION=PASSED")
print("EQUIPMENT_SNAPSHOT_TAMPER_DETECTION=PASSED")
print("SINGLE_CONTEXT_HELP_POPOVER=PASSED")
print("PATCH_005_1_006_TOOLTIP_AND_EQUIPMENT_REGISTRY_GATE_PASSED")
