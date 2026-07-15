from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase

from apps.organizations.models import Employee

from ..models import (
    AdjacentSubjectRelationRevision,
    ManagementObject,
    ManagementRevision,
    PublicationStatus,
    SupervisionObject,
    SupervisionRevision,
)
from ..services import (
    current_adjacent_revision,
    current_management_revision,
    current_management_revisions,
    current_supervision_revisions,
    publish_adjacent_relation_revision,
    publish_management_revision,
    publish_supervision_revision,
)
from .helpers import DispatchingDemoMixin


class DispatchingServiceTests(DispatchingDemoMixin, TestCase):
    def test_current_management_is_resolved_by_date(self):
        management = ManagementObject.objects.get(equipment=self.wtg)
        revision = current_management_revision(management, date(2025, 1, 1))
        self.assertEqual(revision.subject, self.station_subject)

    def test_current_supervision_preserves_information_characteristic(self):
        information = SupervisionRevision.objects.get(is_information_only=True)
        revisions = current_supervision_revisions(information.supervision_object)
        self.assertTrue(any(item.is_information_only for item in revisions))

    def test_overlapping_management_is_rejected(self):
        management = ManagementObject.objects.get(equipment=self.wtg)
        draft = ManagementRevision.objects.create(
            management_object=management,
            revision_number=2,
            level=self.station_level,
            subject=self.regional_subject,
            effective_from=date(2025, 1, 1),
            basis_reference="Конфликтующая демонстрационная редакция",
        )
        with self.assertRaises(ValidationError):
            publish_management_revision(revision=draft, actor=self.employee)

    def test_different_management_levels_can_be_active_together(self):
        management = ManagementObject.objects.get(equipment=self.wtg)
        revision = ManagementRevision.objects.create(
            management_object=management,
            revision_number=2,
            level=self.regional_level,
            subject=self.regional_subject,
            effective_from=date(2024, 1, 1),
            basis_reference="Дополнительный вышестоящий уровень управления",
        )
        publish_management_revision(revision=revision, actor=self.employee)
        current = current_management_revisions(management)
        self.assertEqual(len(current), 2)
        self.assertEqual({item.level_id for item in current}, {self.station_level.pk, self.regional_level.pk})

    def test_management_publication_creates_sha256(self):
        existing_asset_ids = ManagementObject.objects.values_list("equipment_id", flat=True)
        asset = self.organization.equipment_assets.exclude(pk__in=existing_asset_ids).first()
        management = ManagementObject.objects.create(
            organization=self.organization,
            equipment=asset,
        )
        revision = ManagementRevision.objects.create(
            management_object=management,
            revision_number=1,
            level=self.regional_level,
            subject=self.regional_subject,
            effective_from=date.today() + timedelta(days=1),
            basis_reference="Новая демонстрационная редакция",
        )
        published = publish_management_revision(revision=revision, actor=self.employee)
        self.assertEqual(len(published.digest), 64)

    def test_multiple_supervision_subjects_are_allowed(self):
        supervision = SupervisionObject.objects.get(equipment=self.wtg)
        revision = SupervisionRevision.objects.create(
            supervision_object=supervision,
            revision_number=2,
            level=self.station_level,
            subject=self.regional_subject,
            is_information_only=True,
            effective_from=date(2024, 1, 1),
            basis_reference="Дополнительное информационное ведение",
        )
        published = publish_supervision_revision(revision=revision, actor=self.employee)
        self.assertEqual(published.status, PublicationStatus.PUBLISHED)

    def test_adjacent_relation_publication_has_digest(self):
        current = AdjacentSubjectRelationRevision.objects.first()
        self.assertEqual(len(current.digest), 64)
        self.assertEqual(current_adjacent_revision(current.relation), current)

    def test_foreign_actor_cannot_publish(self):
        foreign_actor = Employee.objects.get(pk=self.employee.pk)
        foreign_actor.is_active = False
        foreign_actor.save(update_fields=("is_active",))
        relation = AdjacentSubjectRelationRevision.objects.first().relation
        with transaction.atomic():
            draft = AdjacentSubjectRelationRevision.objects.create(
                relation=relation,
                revision_number=99,
                effective_from=date(2030, 1, 1),
                interaction_scope="Тест",
                communication_rules="Тест",
                basis_reference="Тест",
            )
            with self.assertRaises(ValidationError):
                publish_adjacent_relation_revision(revision=draft, actor=foreign_actor)
