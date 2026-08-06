# ruff: noqa: E402
from __future__ import annotations

import os
import secrets
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
    DispatchLevel,
    DispatchSubject,
    ManagementRevision,
    SupervisionRevision,
)
from apps.dispatching.models import (
    PublicationStatus as DispatchPublicationStatus,
)
from apps.equipment.models import (  # noqa: E402
    EnergySite,
    EquipmentAsset,
    EquipmentNameRevision,
    EquipmentType,
)
from apps.equipment.models import (
    PublicationStatus as EquipmentPublicationStatus,
)
from apps.imports.models import (  # noqa: E402
    ImportBatch,
    ImportEvent,
    ImportPublication,
    ImportPublicationRow,
)
from apps.imports.services import (  # noqa: E402
    build_import_publication_preview,
    can_publish_import,
    create_import_batch,
    decide_import_row,
    publish_import_batch,
    save_column_mapping,
)
from apps.organizations.demo_access import (  # noqa: E402
    DemoAccessPolicyError,
    injected_demo_password,
    validate_demo_password,
)
from apps.organizations.models import (  # noqa: E402
    Division,
    Employee,
    Position,
    RoleAssignment,
)

DEMO_PASSWORD = injected_demo_password()
try:
    validate_demo_password(DEMO_PASSWORD)
except DemoAccessPolicyError as exc:
    raise SystemExit(
        "EOD_DEMO_USER_PASSWORD must be injected to run Patch 008.3 gate."
    ) from exc

publisher = Employee.objects.select_related("user", "organization").get(
    personnel_number="DEMO-002"
)
operator = Employee.objects.select_related("user", "organization").get(
    personnel_number="DEMO-001"
)
if publisher.user is None or operator.user is None:
    raise SystemExit("Demo publisher and operator require personal accounts.")
if not can_publish_import(publisher.user):
    raise SystemExit("Supervisor does not have a direct directory administrator role.")
if can_publish_import(operator.user):
    raise SystemExit("Administrative publication right was transferred through substitution.")
if (
    RoleAssignment.objects.filter(
        employee=publisher,
        role__code="organization_admin",
        is_active=True,
    ).count()
    != 1
):
    raise SystemExit("Direct directory administrator role assignment is not unique.")

organization = publisher.organization
division = Division.objects.filter(organization=organization, is_active=True).order_by("pk").first()
position = Position.objects.filter(organization=organization, is_active=True).order_by("pk").first()
site = EnergySite.objects.filter(organization=organization, is_active=True).order_by("pk").first()
equipment_type = EquipmentType.objects.filter(is_active=True).order_by("pk").first()
level = DispatchLevel.objects.filter(organization=organization, is_active=True).order_by("rank", "pk").first()
subject = DispatchSubject.objects.filter(organization=organization, is_active=True).order_by("pk").first()
if None in (division, position, site, equipment_type, level, subject):
    raise SystemExit("Demo reference data is incomplete for publication gate.")


def create_batch(*, filename: str, target: str, body: str) -> ImportBatch:
    batch = create_import_batch(
        uploaded_file=SimpleUploadedFile(filename, body.encode("utf-8")),
        target_registry=target,
        employee=publisher,
    )
    if batch.status != ImportBatch.Status.READY:
        raise SystemExit(f"Import batch was not parsed: {batch.error_message}")
    mapping = {
        column.position: column.mapped_key
        for column in batch.columns.order_by("position")
    }
    batch = save_column_mapping(batch=batch, employee=publisher, mapping=mapping)
    for row in batch.rows.order_by("row_number"):
        decide_import_row(row=row, employee=publisher, action="ACCEPT")
    batch.refresh_from_db()
    return batch


employee_number = "IMP-PUB-GATE-001"
employee_batch = create_batch(
    filename="gate-publication-employees.csv",
    target=ImportBatch.TargetRegistry.ORGANIZATION,
    body=(
        "Табельный номер;Фамилия;Имя;Отчество;Подразделение;Должность;"
        "Дата начала работы;Действующий сотрудник\n"
        f"{employee_number};Проверочный;Сотрудник;Публикации;{division.name};"
        f"{position.name};17.07.2026;Да\n"
    ),
)
first_preview = build_import_publication_preview(employee_batch)
second_preview = build_import_publication_preview(employee_batch)
if first_preview.digest != second_preview.digest or len(first_preview.digest) != 64:
    raise SystemExit("Publication preview digest is not deterministic SHA-256.")

employee_count_before = Employee.objects.filter(organization=organization).count()
invalid_credential = secrets.token_urlsafe(32)
while invalid_credential == DEMO_PASSWORD:
    invalid_credential = secrets.token_urlsafe(32)
try:
    publish_import_batch(
        batch=employee_batch,
        actor=publisher,
        user=publisher.user,
        password=invalid_credential,
        expected_digest=first_preview.digest,
    )
except ValidationError:
    pass
else:
    raise SystemExit("Wrong password was accepted for import publication.")
if Employee.objects.filter(organization=organization).count() != employee_count_before:
    raise SystemExit("Wrong password changed the organization registry.")

publication = publish_import_batch(
    batch=employee_batch,
    actor=publisher,
    user=publisher.user,
    password=DEMO_PASSWORD,
    expected_digest=first_preview.digest,
)
employee_batch.refresh_from_db()
if employee_batch.status != ImportBatch.Status.PUBLISHED:
    raise SystemExit("Organization import batch was not marked as published.")
if not Employee.objects.filter(
    organization=organization,
    personnel_number=employee_number,
).exists():
    raise SystemExit("Accepted employee row was not created.")
if publication.digest != employee_batch.publication_digest:
    raise SystemExit("Batch and immutable publication digests differ.")
if publication.published_rows.count() != 1:
    raise SystemExit("Per-row publication result was not created.")

try:
    publish_import_batch(
        batch=employee_batch,
        actor=publisher,
        user=publisher.user,
        password=DEMO_PASSWORD,
        expected_digest=publication.digest,
    )
except ValidationError:
    pass
else:
    raise SystemExit("The same staging batch was published twice.")

stored_publication = ImportPublication.objects.get(pk=publication.pk)
stored_publication.result_summary = {"tamper": True}
try:
    stored_publication.save()
except ValidationError:
    pass
else:
    raise SystemExit("Import publication snapshot is mutable.")
stored_row = ImportPublicationRow.objects.get(publication=publication)
stored_row.result = {"tamper": True}
try:
    stored_row.save()
except ValidationError:
    pass
else:
    raise SystemExit("Per-row publication result is mutable.")

code = "IMP-PUB-GATE-EQ"
equipment_batch = create_batch(
    filename="gate-publication-equipment.csv",
    target=ImportBatch.TargetRegistry.EQUIPMENT,
    body=(
        "Стабильный код;Техническое наименование;Диспетчерское наименование;"
        "Вид оборудования;Энергообъект;Состояние;Класс напряжения;Дата ввода\n"
        f"{code};Проверочное оборудование;Проверочное диспетчерское наименование;"
        f"{equipment_type.code};{site.code};В работе;35 кВ;17.07.2026\n"
    ),
)
equipment_preview = build_import_publication_preview(equipment_batch)
publish_import_batch(
    batch=equipment_batch,
    actor=publisher,
    user=publisher.user,
    password=DEMO_PASSWORD,
    expected_digest=equipment_preview.digest,
)
equipment = EquipmentAsset.objects.get(organization=organization, code=code)
name_revision = EquipmentNameRevision.objects.get(equipment=equipment)
if name_revision.status != EquipmentPublicationStatus.PUBLISHED or len(name_revision.digest) != 64:
    raise SystemExit("Dispatcher name revision was not published with the equipment.")


def publish_dispatching(relation: str, information_only: str) -> None:
    batch = create_batch(
        filename=f"gate-{relation.casefold().replace(' ', '-')}.csv",
        target=ImportBatch.TargetRegistry.DISPATCHING,
        body=(
            "Код оборудования;Управление или ведение;Субъект;Уровень;"
            "Действует с;Действует по;Информационное ведение;Основание\n"
            f"{code};{relation};{subject.code};{level.code};17.07.2026;;"
            f"{information_only};Gate Patch 008.3\n"
        ),
    )
    preview = build_import_publication_preview(batch)
    publish_import_batch(
        batch=batch,
        actor=publisher,
        user=publisher.user,
        password=DEMO_PASSWORD,
        expected_digest=preview.digest,
    )


publish_dispatching("Оперативное управление", "Нет")
publish_dispatching("Оперативное ведение", "Да")
management = ManagementRevision.objects.get(management_object__equipment=equipment)
supervision = SupervisionRevision.objects.get(supervision_object__equipment=equipment)
if management.status != DispatchPublicationStatus.PUBLISHED or len(management.digest) != 64:
    raise SystemExit("Management revision was not published.")
if supervision.status != DispatchPublicationStatus.PUBLISHED or len(supervision.digest) != 64:
    raise SystemExit("Supervision revision was not published.")
if not supervision.is_information_only:
    raise SystemExit("Information-only supervision flag was lost.")

other_batch = create_batch(
    filename="gate-other.csv",
    target=ImportBatch.TargetRegistry.OTHER,
    body="Ключ;Наименование\nIMP-OTHER;Проверочная запись\n",
)
try:
    build_import_publication_preview(other_batch)
except ValidationError:
    pass
else:
    raise SystemExit("The undefined OTHER registry became publishable.")

client = Client()
client.force_login(publisher.user)
preview_page = client.get(reverse("imports:publication", args=[equipment_batch.public_id]))
result_page = client.get(reverse("imports:publication_result", args=[equipment_batch.public_id]))
if preview_page.status_code != 302 or result_page.status_code != 200:
    raise SystemExit("Controlled publication pages are unavailable after publication.")
result_html = result_page.content.decode("utf-8")
for marker in (
    "НЕИЗМЕНЯЕМЫЙ ИТОГ ПУБЛИКАЦИИ",
    "Публикация завершена одной транзакцией",
    "SHA-256",
):
    if marker not in result_html:
        raise SystemExit(f"Publication result UI marker is missing: {marker}")

if not employee_batch.events.filter(event_type=ImportEvent.EventType.PUBLISHED).exists():
    raise SystemExit("Successful publication was not recorded in import audit.")

print("DIRECT_DIRECTORY_ADMIN_ROLE=PASSED")
print("PUBLICATION_PREVIEW_DIGEST=PASSED")
print("PASSWORD_REAUTHENTICATION=PASSED")
print("ATOMIC_ORGANIZATION_PUBLICATION=PASSED")
print("EQUIPMENT_AND_NAME_PUBLICATION=PASSED")
print("DISPATCHING_REVISION_PUBLICATION=PASSED")
print("IMMUTABLE_PUBLICATION_AUDIT=PASSED")
print("OTHER_REGISTRY_PUBLICATION=DISABLED")
print("PATCH_008_3_CONTROLLED_IMPORT_PUBLICATION_GATE_PASSED")
