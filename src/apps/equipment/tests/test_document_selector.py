from django import forms
from django.test import TestCase
from django.urls import reverse

from apps.documents.forms import DocumentDraftForm
from apps.documents.models import DocumentType
from apps.documents.services import create_document_draft
from apps.organizations.models import Organization

from ..models import EnergySite, EquipmentAsset, EquipmentType
from .helpers import EquipmentDemoMixin


class DocumentEquipmentSelectorTests(EquipmentDemoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.document_type, _ = DocumentType.objects.get_or_create(
            organization=cls.employee.organization,
            code="selector-document",
            defaults={
                "name": "Документ с серверным селектором",
                "number_prefix": "СЕЛ",
                "number_width": 6,
                "is_active": True,
            },
        )

    def form_data(self, equipment_ids):
        return {
            "document_type": self.document_type.pk,
            "title": "Проверка селектора",
            "subject": "Оборудование",
            "body": "Проверка выбора оборудования.",
            "equipment_assets": equipment_ids,
        }

    def test_form_uses_hidden_multiple_widget(self):
        form = DocumentDraftForm(employee=self.employee)
        self.assertIsInstance(
            form.fields["equipment_assets"].widget,
            forms.MultipleHiddenInput,
        )

    def test_bound_form_accepts_selected_equipment(self):
        form = DocumentDraftForm(
            data=self.form_data([self.ktp.pk, self.wtg.pk]),
            employee=self.employee,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            set(form.cleaned_data["equipment_assets"]),
            {self.ktp, self.wtg},
        )

    def test_bound_form_rejects_foreign_equipment(self):
        other = Organization.objects.create(
            code="OTHER-FORM-SELECTOR",
            name="Другая организация",
        )
        site = EnergySite.objects.create(
            organization=other,
            code="other-form-site",
            name="Другой объект",
            site_type=EnergySite.SiteType.OTHER,
        )
        asset = EquipmentAsset.objects.create(
            organization=other,
            site=site,
            equipment_type=EquipmentType.objects.first(),
            code="OTHER-FORM-ASSET",
            technical_name="Чужое оборудование",
        )
        form = DocumentDraftForm(
            data=self.form_data([asset.pk]),
            employee=self.employee,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("equipment_assets", form.errors)

    def test_create_page_contains_dialog_and_no_multiple_select(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Выбрать оборудование")
        self.assertContains(response, "СЕРВЕРНЫЙ СЕЛЕКТОР")
        self.assertContains(response, 'data-equipment-selector', html=False)
        self.assertNotContains(response, "<select multiple", html=False)

    def test_edit_form_preserves_existing_selection(self):
        document = create_document_draft(
            document_type=self.document_type,
            actor=self.employee,
            title="Черновик с оборудованием",
            content={"subject": "Оборудование", "body": "Текст."},
            equipment_assets=[self.ktp, self.wtg],
        )
        form = DocumentDraftForm(
            employee=self.employee,
            document=document,
        )
        selected_codes = {
            row["code"]
            for row in form.selected_equipment_rows
        }
        self.assertEqual(
            selected_codes,
            {"DEMO-KTP-01", "DEMO-WTG-01"},
        )

    def test_selector_javascript_has_pagination_and_selected_map(self):
        from pathlib import Path

        from django.conf import settings

        source = (
            Path(settings.BASE_DIR) / "src/static/system/app.js"
        ).read_text(encoding="utf-8")
        self.assertIn("const selected = new Map()", source)
        self.assertIn("data-equipment-load-more", source)
        self.assertIn("URLSearchParams", source)
        self.assertIn("page: String(currentPage)", source)
