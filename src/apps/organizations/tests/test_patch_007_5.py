from __future__ import annotations

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.documents.models import DocumentType
from apps.documents.services import create_document_draft
from apps.organizations.models import Division, Employee, InterfacePreference


class Patch0075PresentationValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_dispatching", verbosity=0)
        cls.operator = Employee.objects.select_related("user").get(
            personnel_number="DEMO-001"
        )
        cls.user = cls.operator.user
        document_type, _ = DocumentType.objects.update_or_create(
            organization=cls.operator.organization,
            code="patch-007-5-draft",
            defaults={
                "name": "Тестовый тип документа Patch 007.5",
                "number_prefix": "P75",
                "number_width": 6,
                "is_active": True,
            },
        )
        cls.draft = create_document_draft(
            document_type=document_type,
            actor=cls.operator,
            title="Тестовый черновик Patch 007.5",
            content={
                "subject": "Проверка пользовательской подписи",
                "body": "Минимальный черновик без демонстрационной регистрации.",
            },
        )

    def test_presentation_preferences_start_without_technical_details(self):
        preferences = InterfacePreference.objects.get(user=self.user)
        self.assertEqual(preferences.theme, InterfacePreference.Theme.LIGHT)
        self.assertFalse(preferences.show_technical_details)

    def test_header_uses_employee_name_instead_of_login(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("system:home"))
        self.assertContains(response, self.operator.full_name)
        self.assertNotContains(response, "operator.demo")
        self.assertContains(response, 'data-technical="false"')

    def test_reference_navigation_is_active_for_directory(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:directory"))
        self.assertContains(response, 'class="nav-menu active"')

    def test_draft_uses_friendly_label(self):
        self.client.force_login(self.user)
        draft = self.draft
        response = self.client.get(
            reverse("documents:detail", args=[draft.public_id])
        )
        self.assertContains(response, "Черновик без регистрационного номера")
        self.assertNotContains(response, f"Черновик <code>{draft.public_id}</code>")

    def test_energy_site_system_code_is_technical_only(self):
        template = (
            settings.BASE_DIR / "src/templates/equipment/site_detail.html"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '<dt class="technical-only">Системный код</dt>',
            template,
        )
        self.assertRegex(
            template,
            (
                r'<code class="[^"]*\btechnical-only\b[^"]*">'
                r"\{\{ row\.equipment\.code \}\}</code>"
            ),
        )

    def test_dispatching_summary_uses_operational_labels(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dispatching:registry"))
        self.assertContains(response, "Оборудование с назначенным управлением")
        self.assertContains(response, "Оборудование с назначенным ведением")
        self.assertContains(response, "В том числе информационное ведение")

    def test_official_chief_engineer_block_name_is_used(self):
        block = Division.objects.get(code="CHIEF_ENGINEER_BLOCK")
        self.assertEqual(block.name, "Блок ЗГД — главного инженера")

    def test_normative_traceability_is_collapsed(self):
        templates = []
        for path in sorted(
            (settings.BASE_DIR / "src/templates/normatives").glob("*.html")
        ):
            source = path.read_text(encoding="utf-8")
            if "Техническая трассируемость" in source:
                templates.append(source)
        self.assertEqual(len(templates), 1)
        self.assertIn(
            "technical-traceability technical-only",
            templates[0],
        )
