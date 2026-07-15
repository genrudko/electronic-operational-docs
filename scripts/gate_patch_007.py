from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ["DJANGO_ALLOWED_HOSTS"] = "127.0.0.1,localhost,testserver"
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402
from django.db import models, transaction  # noqa: E402
from django.test import Client  # noqa: E402

django.setup()

from apps.dispatching.models import (  # noqa: E402
    AdjacentSubjectRelation,
    DispatchingAuditEvent,
    DispatchLevel,
    DispatchSubject,
    ManagementObject,
    ManagementRevision,
    PublicationStatus,
    SupervisionObject,
    SupervisionRevision,
)
from apps.dispatching.services import publish_management_revision  # noqa: E402
from apps.organizations.models import Employee, Organization  # noqa: E402

organization = Organization.objects.get(code="DEMO")
actor = Employee.objects.select_related("user").get(user__username="operator.demo")

level_count = DispatchLevel.objects.filter(organization=organization).count()
subject_count = DispatchSubject.objects.filter(organization=organization).count()
management_object_count = ManagementObject.objects.filter(organization=organization).count()
supervision_object_count = SupervisionObject.objects.filter(organization=organization).count()
management_count = ManagementRevision.objects.filter(
    management_object__organization=organization,
    status=PublicationStatus.PUBLISHED,
).count()
supervision_count = SupervisionRevision.objects.filter(
    supervision_object__organization=organization,
    status=PublicationStatus.PUBLISHED,
).count()
information_count = SupervisionRevision.objects.filter(
    supervision_object__organization=organization,
    status=PublicationStatus.PUBLISHED,
    is_information_only=True,
).count()
adjacent_count = AdjacentSubjectRelation.objects.filter(organization=organization).count()
audit_count = DispatchingAuditEvent.objects.filter(organization=organization).count()

if level_count < 2 or subject_count < 3:
    raise SystemExit("Демонстрационные уровни или субъекты не созданы.")
if management_object_count < 3 or supervision_object_count < 4:
    raise SystemExit("Объекты управления или ведения не созданы.")
if management_count < 3 or supervision_count < 4 or information_count < 1:
    raise SystemExit("Опубликованные редакции управления и ведения неполны.")
if adjacent_count < 2 or audit_count < 9:
    raise SystemExit("Смежные взаимодействия или аудит неполны.")

for revision in ManagementRevision.objects.filter(status=PublicationStatus.PUBLISHED):
    overlaps = (
        ManagementRevision.objects.filter(
            management_object=revision.management_object,
            level=revision.level,
            status=PublicationStatus.PUBLISHED,
            effective_from__lte=revision.effective_until or date.max,
        )
        .filter(
            models.Q(effective_until__isnull=True) | models.Q(effective_until__gte=revision.effective_from)
        )
        .exclude(pk=revision.pk)
    )
    if overlaps.exists():
        raise SystemExit("Обнаружены пересекающиеся опубликованные управления.")

with transaction.atomic():
    management = ManagementObject.objects.select_related("equipment").first()
    existing = ManagementRevision.objects.filter(management_object=management).first()
    draft = ManagementRevision.objects.create(
        management_object=management,
        revision_number=999,
        level=existing.level,
        subject=existing.subject,
        effective_from=existing.effective_from,
        basis_reference="Проверка конфликта Patch 007",
    )
    try:
        publish_management_revision(revision=draft, actor=actor)
    except ValidationError:
        pass
    else:
        raise SystemExit("Пересекающееся управление было ошибочно опубликовано.")
    transaction.set_rollback(True)

published = ManagementRevision.objects.filter(status=PublicationStatus.PUBLISHED).first()
published.change_summary = "Попытка изменить историю"
try:
    published.save()
except ValidationError:
    pass
else:
    raise SystemExit("Опубликованная редакция управления оказалась изменяемой.")

client = Client()
client.force_login(actor.user)
registry = client.get("/dispatching/")
subjects = client.get("/dispatching/subjects/")
if registry.status_code != 200 or "Управление и ведение" not in registry.content.decode("utf-8"):
    raise SystemExit("Русский экран управления и ведения недоступен.")
if subjects.status_code != 200 or "Смежный" not in subjects.content.decode("utf-8"):
    raise SystemExit("Экран смежных субъектов недоступен.")

print(f"DISPATCH_LEVEL_COUNT={level_count}")
print(f"DISPATCH_SUBJECT_COUNT={subject_count}")
print(f"MANAGEMENT_OBJECT_COUNT={management_object_count}")
print(f"SUPERVISION_OBJECT_COUNT={supervision_object_count}")
print(f"PUBLISHED_MANAGEMENT_COUNT={management_count}")
print(f"PUBLISHED_SUPERVISION_COUNT={supervision_count}")
print(f"INFORMATION_SUPERVISION_COUNT={information_count}")
print(f"ADJACENT_SUBJECT_RELATION_COUNT={adjacent_count}")
print(f"DISPATCHING_AUDIT_COUNT={audit_count}")
print("SINGLE_ACTIVE_MANAGEMENT_PER_LEVEL=PASSED")
print("PUBLISHED_HISTORY_IMMUTABILITY=PASSED")
print("EXPLICIT_ADJACENT_SUBJECT_INTERACTION=PASSED")
print("PATCH_007_MANAGEMENT_AND_SUPERVISION_GATE_PASSED")
