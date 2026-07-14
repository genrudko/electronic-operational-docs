from django.test import TestCase, override_settings
from django.urls import reverse

from apps.documents.models import DocumentType
from apps.documents.services import create_document_draft, register_demo_document
from apps.organizations.models import Organization

from ..models import EnergySite, EquipmentAsset, EquipmentType
from .helpers import EquipmentDemoMixin


@override_settings(DEBUG=True)
class EquipmentRegistryViewTests(EquipmentDemoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.document_type, _ = DocumentType.objects.get_or_create(
            organization=cls.employee.organization,
            code="equipment-view-note",
            defaults={
                "name": "Документ по оборудованию для представлений",
                "number_prefix": "ОВИД",
                "number_width": 6,
                "is_active": True,
            },
        )

    def test_registry_requires_login(self):
        response = self.client.get(reverse("equipment:registry"))
        self.assertEqual(response.status_code, 302)

    def test_registry_is_russian_and_contains_demo_assets(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("equipment:registry"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Реестр оборудования")
        self.assertContains(response, "КТП-01 Демо-ВЭС")
        self.assertContains(response, "Исторические редакции", count=0)

    def test_registry_searches_by_alias(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:registry"),
            {"q": "Блочная КТП №1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "КТП-01 Демо-ВЭС")
        self.assertNotContains(response, "ВЭУ-01 Демо-ВЭС")

    def test_site_detail_shows_hierarchy(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:site_detail", args=["demo-wpp"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Иерархия оборудования")
        self.assertContains(response, "DEMO-RU35")
        self.assertContains(response, "DEMO-CELL-01")

    def test_equipment_detail_shows_history_and_aliases(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:detail", args=[self.ktp.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "История диспетчерских наименований")
        self.assertContains(response, "КТП-1 Демо-ВЭС")
        self.assertContains(response, "КТП-01 Демо-ВЭС")
        self.assertContains(response, "Блочная КТП №1")

    def test_other_organization_equipment_is_hidden(self):
        other = Organization.objects.create(
            code="OTHER-VIEW",
            name="Другая организация",
        )
        site = EnergySite.objects.create(
            organization=other,
            code="other-view-site",
            name="Другой объект",
            site_type=EnergySite.SiteType.OTHER,
        )
        asset = EquipmentAsset.objects.create(
            organization=other,
            site=site,
            equipment_type=EquipmentType.objects.first(),
            code="OTHER-VIEW-ASSET",
            technical_name="Чужое оборудование",
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:detail", args=[asset.public_id])
        )
        self.assertEqual(response.status_code, 404)

    def test_document_detail_shows_frozen_equipment_name(self):
        document = create_document_draft(
            document_type=self.document_type,
            actor=self.employee,
            title="Документ со снимком оборудования",
            content={
                "subject": "Оборудование",
                "body": "Проверка пользовательского отображения.",
            },
            equipment_assets=[self.ktp],
        )
        document = register_demo_document(
            document=document,
            actor=self.employee,
        ).document
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("documents:detail", args=[document.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Оборудование документа")
        self.assertContains(response, "КТП-01 Демо-ВЭС")
        self.assertContains(response, "Снимок на момент регистрации")
