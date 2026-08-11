from __future__ import annotations

import re

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.documents.models import DocumentType
from apps.documents.services import create_document_draft
from apps.organizations.models import Employee


class Patch0076VisualAcceptanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_dispatching", verbosity=0)
        cls.operator = Employee.objects.select_related("user").get(
            personnel_number="DEMO-001"
        )
        cls.user = cls.operator.user
        document_type, _ = DocumentType.objects.update_or_create(
            organization=cls.operator.organization,
            code="patch-007-6-draft",
            defaults={
                "name": "Тестовый тип документа Patch 007.6",
                "number_prefix": "P76",
                "number_width": 6,
                "is_active": True,
            },
        )
        cls.draft = create_document_draft(
            document_type=document_type,
            actor=cls.operator,
            title="Тестовый черновик Patch 007.6",
            content={
                "subject": "Визуальная приёмка",
                "body": "Черновик для проверки пользовательской подписи номера.",
            },
        )

    def test_document_list_uses_registration_placeholder(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:list"))
        self.assertContains(response, "Без регистрационного номера")
        self.assertNotIn(
            '<code>черновик</code>',
            response.content.decode("utf-8"),
        )

    def test_document_actions_use_single_toolbar(self):
        template = (
            settings.BASE_DIR / "src/templates/documents/detail.html"
        ).read_text(encoding="utf-8")
        css = (
            settings.BASE_DIR / "src/static/system/app.css"
        ).read_text(encoding="utf-8")
        self.assertIn('class="da-actions document-actions"', template)
        self.assertIn(".document-actions {", css)
        self.assertIn("flex-wrap: nowrap;", css)
        self.assertIn("min-width: max-content;", css)

    def test_role_cards_show_assignment_mode_and_scope(self):
        template = (
            settings.BASE_DIR / "src/templates/organizations/account.html"
        ).read_text(encoding="utf-8")
        for marker in (
            "role-assignment",
            "role-assignment-heading",
            "role-assignment-scope-label",
            "role-assignment-scope",
            "Прямое назначение",
            "По замещению",
            "Область действия",
        ):
            self.assertIn(marker, template)
        self.assertNotIn("role-assignment-basis", template)

    def test_revision_digest_is_grouped_as_technical_details(self):
        template = (
            settings.BASE_DIR / "src/templates/normatives/revision_detail.html"
        ).read_text(encoding="utf-8")
        self.assertEqual(template.count("SHA-256 редакции"), 1)
        self.assertIn("Технические реквизиты редакции", template)
        self.assertIn("revision-technical-details technical-only", template)
        self.assertIn('data-default-collapsed="true"', template)
        technical_start = template.index("Технические реквизиты редакции")
        digest_position = template.index("SHA-256 редакции")
        requirements_start = template.index(
            '<section class="requirements-stack">'
        )
        self.assertLess(technical_start, digest_position)
        self.assertLess(digest_position, requirements_start)

    def test_traceability_disclosures_start_closed(self):
        template = (
            settings.BASE_DIR / "src/templates/normatives/revision_detail.html"
        ).read_text(encoding="utf-8")
        script = (
            settings.BASE_DIR / "src/static/system/app.js"
        ).read_text(encoding="utf-8")
        self.assertIn("technical-traceability technical-only", template)
        self.assertGreaterEqual(
            template.count('data-default-collapsed="true"'),
            2,
        )
        self.assertIsNone(
            re.search(
                r"<details[^>]*technical-traceability[^>]*\sopen(?:\s|=|>)",
                template,
                flags=re.DOTALL,
            )
        )
        self.assertIn("closeDefaultCollapsedDisclosures", script)

    def test_equipment_cards_have_interactive_surface_styles(self):
        css = (
            settings.BASE_DIR / "src/static/system/app.css"
        ).read_text(encoding="utf-8")
        for marker in (
            ".site-card:hover",
            ".equipment-tree-row:hover",
            "background: var(--panel);",
            "transform: translateY(-1px);",
        ):
            self.assertIn(marker, css)
