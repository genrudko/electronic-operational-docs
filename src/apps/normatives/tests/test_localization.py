from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.documents.services import (
    IntegrityStatus,
    create_document_draft,
    register_demo_document,
)

from .helpers import NormativeDemoMixin


@override_settings(DEBUG=True)
class RussianInterfaceTests(NormativeDemoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("seed_demo_documents", verbosity=0)

    def test_integrity_statuses_have_russian_labels(self):
        self.assertEqual(IntegrityStatus.VALID.label, "Целостность подтверждена")
        self.assertEqual(IntegrityStatus.INVALID.label, "Целостность нарушена")
        self.assertEqual(IntegrityStatus.LEGACY.label, "Наследованный документ")
        self.assertEqual(IntegrityStatus.MISSING.label, "Подтверждение отсутствует")

    def test_registered_document_shows_russian_status_and_help(self):
        document_type = self.employee.organization.document_types.get(code="general")
        document = create_document_draft(
            document_type=document_type,
            actor=self.employee,
            title="Проверка русской справки",
            content={"subject": "Справка", "body": "Проверка пояснений."},
        )
        document = register_demo_document(document=document, actor=self.employee).document
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("documents:detail", args=[document.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Целостность подтверждена")
        self.assertContains(response, "Что означает этот раздел?")
        self.assertContains(response, 'class="help-tip"', html=False)
        self.assertNotContains(response, ">VALID<")
        self.assertNotContains(response, "eod.document.registration.v1")

    def test_registration_preview_contains_context_help(self):
        document_type = self.employee.organization.document_types.get(code="general")
        document = create_document_draft(
            document_type=document_type,
            actor=self.employee,
            title="Проверка справки регистрации",
            content={"subject": "Справка", "body": "Текст документа."},
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("documents:register", args=[document.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Что именно подтверждается?")
        self.assertContains(response, "Пароль нигде не сохраняется")
