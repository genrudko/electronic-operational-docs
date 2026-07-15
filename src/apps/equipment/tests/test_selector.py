from django.test import TestCase
from django.urls import reverse

from apps.organizations.models import Organization

from ..models import EnergySite, EquipmentAsset, EquipmentType
from .helpers import EquipmentDemoMixin


class EquipmentSelectorApiTests(EquipmentDemoMixin, TestCase):
    def test_selector_requires_login(self):
        response = self.client.get(reverse("equipment:selector_options"))
        self.assertEqual(response.status_code, 302)

    def test_selector_returns_russian_filter_metadata(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("equipment:selector_options"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("filters", payload)
        self.assertTrue(payload["filters"]["sites"])
        self.assertTrue(payload["filters"]["categories"])
        self.assertIn(
            "Комплектная трансформаторная подстанция",
            [row["name"] for row in payload["filters"]["categories"]],
        )

    def test_selector_searches_by_alias(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:selector_options"),
            {"q": "Блочная КТП №1"},
        )
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["code"], "DEMO-KTP-01")

    def test_selector_filters_by_site(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:selector_options"),
            {"site": "demo-grid-substation"},
        )
        payload = response.json()
        self.assertTrue(payload["items"])
        self.assertTrue(
            all(
                item["site_code"] == "demo-grid-substation"
                for item in payload["items"]
            )
        )

    def test_selector_filters_by_category(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:selector_options"),
            {"category": EquipmentType.Category.WTG},
        )
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["category"], EquipmentType.Category.WTG)

    def test_selector_filters_by_equipment_type(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:selector_options"),
            {"type": "ktp"},
        )
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["type_code"], "ktp")

    def test_selector_hides_other_organization(self):
        other = Organization.objects.create(
            code="OTHER-SELECTOR",
            name="Другая организация",
        )
        site = EnergySite.objects.create(
            organization=other,
            code="other-selector-site",
            name="Чужой объект",
            site_type=EnergySite.SiteType.OTHER,
        )
        asset = EquipmentAsset.objects.create(
            organization=other,
            site=site,
            equipment_type=EquipmentType.objects.first(),
            code="OTHER-SELECTOR-ASSET",
            technical_name="Чужое оборудование",
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:selector_options"),
            {"q": asset.code},
        )
        self.assertEqual(response.json()["total"], 0)

    def test_selector_uses_fifty_item_pages(self):
        site = EnergySite.objects.get(code="demo-wpp")
        equipment_type = EquipmentType.objects.get(code="wtg")
        EquipmentAsset.objects.bulk_create(
            [
                EquipmentAsset(
                    organization=self.employee.organization,
                    site=site,
                    equipment_type=equipment_type,
                    code=f"PAGE-{index:04d}",
                    technical_name=f"Тестовая установка {index}",
                )
                for index in range(110)
            ]
        )
        self.client.force_login(self.user)
        first = self.client.get(
            reverse("equipment:selector_options"),
            {"q": "PAGE-", "page": 1},
        ).json()
        third = self.client.get(
            reverse("equipment:selector_options"),
            {"q": "PAGE-", "page": 3},
        ).json()
        self.assertEqual(len(first["items"]), 50)
        self.assertTrue(first["has_more"])
        self.assertEqual(first["page_size"], 50)
        self.assertEqual(len(third["items"]), 10)
        self.assertFalse(third["has_more"])

    def test_invalid_page_falls_back_to_first_page(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:selector_options"),
            {"page": "не-число"},
        )
        self.assertEqual(response.json()["page"], 1)

    def test_selector_item_contains_hierarchy_and_russian_status(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("equipment:selector_options"),
            {"q": "DEMO-RZA-01"},
        )
        item = response.json()["items"][0]
        self.assertIn("РУ 35 кВ", item["hierarchy_path"])
        self.assertEqual(item["status_label"], "В работе")
