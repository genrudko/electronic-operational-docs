from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Organization

from ..models import (
    AdjacentSubjectRelation,
    DispatchLevel,
    DispatchSubject,
    ManagementObject,
    ManagementRevision,
    PublicationStatus,
    SupervisionObject,
    SupervisionRevision,
)
from .helpers import DispatchingDemoMixin


class DispatchingModelTests(DispatchingDemoMixin, TestCase):
    def test_level_code_is_normalized(self):
        level = DispatchLevel.objects.create(
            organization=self.organization,
            code="  TEST-Level  ",
            name="Тестовый уровень",
            level_type=DispatchLevel.LevelType.TECHNOLOGICAL,
            rank=90,
        )
        self.assertEqual(level.code, "test-level")

    def test_external_subject_type_sets_external_flag(self):
        subject = DispatchSubject.objects.create(
            organization=self.organization,
            code="adjacent-auto",
            name="Автоматически внешний субъект",
            subject_type=DispatchSubject.SubjectType.ADJACENT,
            is_external=False,
        )
        self.assertTrue(subject.is_external)

    def test_management_object_rejects_foreign_equipment(self):
        foreign = Organization.objects.create(code="FOREIGN-DISP", name="Другая организация")
        equipment = EquipmentAsset.objects.filter(organization=self.organization).first()
        with self.assertRaises(ValidationError):
            ManagementObject.objects.create(organization=foreign, equipment=equipment)

    def test_supervision_object_rejects_foreign_equipment(self):
        foreign = Organization.objects.create(code="FOREIGN-SUP", name="Другая организация 2")
        equipment = EquipmentAsset.objects.filter(organization=self.organization).first()
        with self.assertRaises(ValidationError):
            SupervisionObject.objects.create(organization=foreign, equipment=equipment)

    def test_published_management_is_immutable(self):
        revision = ManagementRevision.objects.filter(status=PublicationStatus.PUBLISHED).first()
        revision.basis_reference = "Попытка изменения"
        with self.assertRaises(ValidationError):
            revision.save()

    def test_published_supervision_is_immutable(self):
        revision = SupervisionRevision.objects.filter(status=PublicationStatus.PUBLISHED).first()
        revision.is_information_only = not revision.is_information_only
        with self.assertRaises(ValidationError):
            revision.save()

    def test_adjacent_relation_rejects_self_reference(self):
        with self.assertRaises(ValidationError):
            AdjacentSubjectRelation.objects.create(
                organization=self.organization,
                code="self-relation",
                source_subject=self.station_subject,
                target_subject=self.station_subject,
            )

    def test_bulk_update_and_delete_are_blocked(self):
        with self.assertRaises(ValidationError):
            DispatchSubject.objects.filter(organization=self.organization).update(is_active=False)
        with self.assertRaises(ValidationError):
            ManagementRevision.objects.filter(effective_from=date(2024, 1, 1)).delete()
