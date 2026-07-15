import json
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.documents.forms import DocumentDraftForm
from apps.documents.models import DocumentType
from apps.documents.services import (
    IntegrityStatus,
    create_document_draft,
    register_demo_document,
    update_document_draft,
    verify_document_integrity,
)
from apps.organizations.models import Organization

from ..models import (
    DocumentEquipmentLink,
    DocumentEquipmentSnapshot,
    EnergySite,
    EquipmentAsset,
    EquipmentNameRevision,
    EquipmentType,
)
from ..services import publish_equipment_name_revision
from .helpers import EquipmentDemoMixin


@override_settings(DEBUG=True)
class DocumentEquipmentIntegrationTests(EquipmentDemoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.document_type, _ = DocumentType.objects.get_or_create(
            organization=cls.employee.organization,
            code="equipment-note",
            defaults={
                "name": "Документ по оборудованию",
                "number_prefix": "ОБОР",
                "number_width": 6,
                "is_active": True,
            },
        )

    def create_draft(self, assets):
        return create_document_draft(
            document_type=self.document_type,
            actor=self.employee,
            title="Документ по оборудованию",
            content={
                "subject": "Оборудование",
                "body": "Проверка снимка диспетчерских наименований.",
            },
            equipment_assets=assets,
        )

    def test_create_draft_adds_equipment_links(self):
        document = self.create_draft([self.ktp, self.wtg])
        codes = list(
            document.current_version.equipment_links.order_by(
                "equipment__code"
            ).values_list("equipment__code", flat=True)
        )
        self.assertEqual(codes, ["DEMO-KTP-01", "DEMO-WTG-01"])

    def test_update_draft_replaces_equipment_links(self):
        document = self.create_draft([self.ktp])
        update_document_draft(
            document=document,
            actor=self.employee,
            title=document.title,
            content=document.current_version.content,
            equipment_assets=[self.wtg],
        )
        codes = list(
            document.current_version.equipment_links.values_list(
                "equipment__code",
                flat=True,
            )
        )
        self.assertEqual(codes, ["DEMO-WTG-01"])

    def test_registration_creates_v2_equipment_snapshot(self):
        document = self.create_draft([self.ktp, self.wtg])
        result = register_demo_document(
            document=document,
            actor=self.employee,
        )
        payload = json.loads(result.snapshot.canonical_json)
        self.assertEqual(
            result.snapshot.schema_version,
            "eod.document.registration.v2",
        )
        self.assertEqual(payload["schema"], "eod.document.registration.v2")
        self.assertEqual(len(payload["equipment"]), 2)
        self.assertEqual(
            DocumentEquipmentSnapshot.objects.filter(
                document=result.document
            ).count(),
            2,
        )
        self.assertEqual(
            verify_document_integrity(result.document).status,
            IntegrityStatus.VALID,
        )

    def test_future_rename_does_not_change_registered_snapshot(self):
        document = self.create_draft([self.ktp])
        result = register_demo_document(
            document=document,
            actor=self.employee,
        )
        frozen = DocumentEquipmentSnapshot.objects.get(
            document=result.document
        )
        frozen_name = frozen.dispatcher_name_snapshot
        next_revision_number = (
            EquipmentNameRevision.objects.filter(equipment=self.ktp)
            .order_by("-revision_number")
            .values_list("revision_number", flat=True)
            .first()
            or 0
        ) + 1
        future_revision = EquipmentNameRevision.objects.create(
            equipment=self.ktp,
            revision_number=next_revision_number,
            dispatcher_name="КТП-01 новое будущее имя",
            effective_from=timezone.localdate() + timedelta(days=1),
        )
        publish_equipment_name_revision(
            revision=future_revision,
            actor=self.employee,
        )
        frozen.refresh_from_db()
        self.assertEqual(frozen.dispatcher_name_snapshot, frozen_name)
        self.assertEqual(
            verify_document_integrity(result.document).status,
            IntegrityStatus.VALID,
        )

    def test_equipment_snapshot_tamper_is_detected(self):
        document = self.create_draft([self.ktp])
        result = register_demo_document(
            document=document,
            actor=self.employee,
        )
        frozen = DocumentEquipmentSnapshot.objects.get(
            document=result.document
        )
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    f'UPDATE "{DocumentEquipmentSnapshot._meta.db_table}" '
                    "SET dispatcher_name_snapshot = %s WHERE id = %s",
                    ["Подменённое имя", frozen.pk],
                )
            result.document.refresh_from_db()
            self.assertEqual(
                verify_document_integrity(result.document).status,
                IntegrityStatus.INVALID,
            )
            transaction.set_rollback(True)

    def test_registered_equipment_link_cannot_be_deleted(self):
        document = self.create_draft([self.ktp])
        result = register_demo_document(
            document=document,
            actor=self.employee,
        )
        link = DocumentEquipmentLink.objects.get(document=result.document)
        with self.assertRaises(ValidationError):
            link.delete()

    def test_equipment_snapshot_is_immutable(self):
        document = self.create_draft([self.ktp])
        result = register_demo_document(
            document=document,
            actor=self.employee,
        )
        frozen = DocumentEquipmentSnapshot.objects.get(
            document=result.document
        )
        frozen.dispatcher_name_snapshot = "Попытка изменения"
        with self.assertRaises(ValidationError):
            frozen.save()

    def test_document_form_lists_only_organization_equipment(self):
        other = Organization.objects.create(
            code="OTHER-DOC",
            name="Другая организация",
        )
        other_site = EnergySite.objects.create(
            organization=other,
            code="other-site-doc",
            name="Другой объект",
            site_type=EnergySite.SiteType.OTHER,
        )
        other_asset = EquipmentAsset.objects.create(
            organization=other,
            site=other_site,
            equipment_type=EquipmentType.objects.first(),
            code="OTHER-ASSET",
            technical_name="Чужое оборудование",
        )
        form = DocumentDraftForm(employee=self.employee)
        queryset = form.fields["equipment_assets"].queryset
        self.assertIn(self.ktp, queryset)
        self.assertNotIn(other_asset, queryset)

    def test_cross_organization_equipment_link_is_rejected(self):
        other = Organization.objects.create(
            code="OTHER-LINK",
            name="Другая организация",
        )
        other_site = EnergySite.objects.create(
            organization=other,
            code="other-site-link",
            name="Другой объект",
            site_type=EnergySite.SiteType.OTHER,
        )
        other_asset = EquipmentAsset.objects.create(
            organization=other,
            site=other_site,
            equipment_type=EquipmentType.objects.first(),
            code="OTHER-LINK-ASSET",
            technical_name="Чужое оборудование",
        )
        with self.assertRaises(ValidationError):
            self.create_draft([other_asset])
