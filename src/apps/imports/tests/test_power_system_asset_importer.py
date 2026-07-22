from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.dispatching.models import ManagementRevision, SupervisionRevision
from apps.equipment.models import EnergySite, EquipmentAlias, EquipmentAsset
from apps.imports.models import (
    DataProfile,
    PowerSystemAssetOccurrence,
    PowerSystemSourceRevision,
)
from apps.imports.power_system import (
    build_power_system_publication_preview,
    decide_power_system_occurrence,
    publish_power_system_revision,
    stage_power_system_package,
)
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Role,
    RoleAssignment,
)

from .power_system_package import synthetic_power_system_package


class PowerSystemAssetImporterTests(TestCase):
    password = "Power-System-2026!"

    def setUp(self):
        self.organization = Organization.objects.create(
            code="PS-ORG",
            name="Синтетическая организация",
        )
        division = Division.objects.create(
            organization=self.organization,
            code="PS-DIV",
            name="Оперативная служба",
        )
        position = Position.objects.create(
            organization=self.organization,
            code="PS-POS",
            name="Администратор справочников",
        )
        self.user = get_user_model().objects.create_user(
            username="power-system-publisher",
            password=self.password,
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=division,
            position=position,
            user=self.user,
            personnel_number="PS-001",
            last_name="Тестов",
            first_name="Импорт",
            employment_start=date(2026, 1, 1),
        )
        role, _created = Role.objects.get_or_create(
            code="organization_admin",
            defaults={
                "name": "Администратор справочников",
                "description": "Контролируемая публикация справочников.",
                "is_system": True,
            },
        )
        RoleAssignment.objects.create(
            employee=self.employee,
            role=role,
            valid_from=date(2026, 1, 1),
        )
        self.profile = DataProfile.default_for_organization(self.organization)

    def stage(self):
        return stage_power_system_package(
            uploaded_file=synthetic_power_system_package(),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Синтетический перечень объектов диспетчеризации",
            source_approval_status=PowerSystemSourceRevision.SourceApprovalStatus.DRAFT,
        )

    def test_stage_is_idempotent_and_keeps_conflict_in_row_quarantine(self):
        revision, created = self.stage()
        self.assertTrue(created)
        self.assertEqual(revision.total_occurrences, 5)
        self.assertEqual(revision.ready_count, 4)
        self.assertEqual(revision.blocked_count, 1)
        blocked = revision.asset_occurrences.get(occurrence_id="SYN-BLOCKED")
        self.assertEqual(blocked.review_status, PowerSystemAssetOccurrence.ReviewStatus.BLOCKED)
        self.assertEqual(EquipmentAsset.objects.count(), 0)

        duplicate, duplicate_created = self.stage()
        self.assertFalse(duplicate_created)
        self.assertEqual(duplicate.pk, revision.pk)
        self.assertEqual(PowerSystemSourceRevision.objects.count(), 1)

    def test_manual_decision_is_audited_and_resettable(self):
        revision, _created = self.stage()
        blocked = revision.asset_occurrences.get(occurrence_id="SYN-BLOCKED")
        accepted = decide_power_system_occurrence(
            occurrence=blocked,
            employee=self.employee,
            action="ACCEPT_AS_NEW",
            note="Проверено на синтетическом источнике.",
        )
        self.assertEqual(accepted.review_status, PowerSystemAssetOccurrence.ReviewStatus.READY)
        self.assertEqual(accepted.reviewed_by, self.employee)
        self.assertIsNotNone(accepted.reviewed_at)
        reset = decide_power_system_occurrence(
            occurrence=accepted,
            employee=self.employee,
            action="RESET",
        )
        self.assertEqual(reset.review_status, PowerSystemAssetOccurrence.ReviewStatus.BLOCKED)
        self.assertIsNone(reset.reviewed_by)

    def test_publication_rebuilds_hierarchy_and_separates_management_from_conduct(self):
        revision, _created = self.stage()
        preview = build_power_system_publication_preview(
            revision=revision,
            effective_from=date(2026, 7, 22),
        )
        with self.assertRaises(ValidationError):
            publish_power_system_revision(
                revision=revision,
                actor=self.employee,
                user=self.user,
                password="wrong-password",
                effective_from=date(2026, 7, 22),
                expected_digest=preview.digest,
            )
        publication = publish_power_system_revision(
            revision=revision,
            actor=self.employee,
            user=self.user,
            password=self.password,
            effective_from=date(2026, 7, 22),
            expected_digest=preview.digest,
        )
        revision.refresh_from_db()
        self.assertEqual(revision.status, PowerSystemSourceRevision.Status.PARTIALLY_PUBLISHED)
        self.assertEqual(revision.published_count, 4)
        self.assertEqual(revision.blocked_count, 1)
        self.assertEqual(EnergySite.objects.filter(organization=self.organization).count(), 1)

        voltage = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="35 кВ",
        )
        ktp = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="КТП-1",
        )
        breaker = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="В-35 КТП-1",
        )
        self.assertIsNone(voltage.parent)
        self.assertEqual(ktp.parent, voltage)
        self.assertEqual(breaker.parent, ktp)
        self.assertEqual(breaker.attributes["source_occurrence_ids"], ["SYN-Q-1"])
        self.assertEqual(EquipmentAlias.objects.get().scope_parent, ktp)
        self.assertEqual(ManagementRevision.objects.count(), 1)
        supervision = SupervisionRevision.objects.get()
        self.assertEqual(supervision.conduct_mode, SupervisionRevision.ConductMode.OPERATIONAL)
        self.assertFalse(supervision.is_information_only)
        self.assertEqual(len(publication.digest), 64)

    def test_views_expose_staging_without_publishing(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("imports:power_system_upload"),
            {
                "data_profile": self.profile.pk,
                "source_reference": "Синтетический перечень",
                "source_approval_status": PowerSystemSourceRevision.SourceApprovalStatus.DRAFT,
                "source_file": synthetic_power_system_package(),
            },
        )
        self.assertEqual(response.status_code, 302)
        revision = PowerSystemSourceRevision.objects.get()
        self.assertEqual(EquipmentAsset.objects.count(), 0)
        detail = self.client.get(
            reverse("imports:power_system_detail", args=[revision.public_id])
        )
        self.assertContains(detail, "Строки источника")
        self.assertContains(detail, "SYN-BLOCKED")
        self.assertContains(detail, "Требует проверки")
