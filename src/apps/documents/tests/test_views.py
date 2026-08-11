from __future__ import annotations

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.documents.models import Document
from apps.documents.services import create_document_draft, register_demo_document
from tests.credential_fixtures import ephemeral_credential

from .factories import document_context


@override_settings(DEBUG=True)
class DocumentViewTests(TestCase):
    def setUp(self) -> None:
        self.credential = ephemeral_credential("DocumentView")
        self.employee, self.user, self.document_type = document_context(
            code="VIEW",
            credential=self.credential,
        )

    def _draft(self) -> Document:
        return create_document_draft(
            document_type=self.document_type,
            actor=self.employee,
            title="Тестовый черновик",
            content={"subject": "Тема", "body": "Содержимое"},
        )

    def test_document_list_requires_login(self):
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("organizations:login"), response.url)

    def test_employee_without_document_role_is_forbidden(self):
        _, user, _ = document_context(code="NOACCESS", role_code="viewer")
        self.client.force_login(user)
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 403)

    def test_operator_can_open_document_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Документарное ядро")
        self.assertContains(response, "Новый черновик")
        self.assertContains(response, "ux-stat-grid")

    def test_create_edit_and_register_flow(self):
        self.client.force_login(self.user)
        create_response = self.client.post(
            reverse("documents:create"),
            {
                "document_type": self.document_type.pk,
                "title": "Созданный документ",
                "subject": "Тема",
                "body": "Первоначальный текст",
            },
        )
        document = Document.objects.get(title="Созданный документ")
        self.assertRedirects(
            create_response,
            reverse("documents:detail", kwargs={"public_id": document.public_id}),
        )

        edit_response = self.client.post(
            reverse("documents:edit", kwargs={"public_id": document.public_id}),
            {
                "document_type": self.document_type.pk,
                "title": "Обновлённый документ",
                "subject": "Новая тема",
                "body": "Обновлённый текст",
            },
        )
        self.assertRedirects(
            edit_response,
            reverse("documents:detail", kwargs={"public_id": document.public_id}),
        )
        document.refresh_from_db()
        self.assertEqual(document.title, "Обновлённый документ")

        preview_response = self.client.get(
            reverse("documents:register", kwargs={"public_id": document.public_id})
        )
        self.assertEqual(preview_response.status_code, 200)
        self.assertContains(preview_response, "Подтверждение регистрации")

        register_response = self.client.post(
            reverse("documents:register", kwargs={"public_id": document.public_id}),
            {"password": self.credential, "confirm": "on"},
        )
        self.assertRedirects(
            register_response,
            reverse("documents:detail", kwargs={"public_id": document.public_id}),
        )
        document.refresh_from_db()
        self.assertEqual(document.status, Document.Status.REGISTERED)
        self.assertTrue(document.registration_number)

        detail_response = self.client.get(
            reverse("documents:detail", kwargs={"public_id": document.public_id})
        )
        self.assertContains(detail_response, document.registration_number)
        self.assertContains(detail_response, "Зарегистрирован")

    def test_registered_document_edit_is_rejected(self):
        document = register_demo_document(document=self._draft(), actor=self.employee).document
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("documents:edit", kwargs={"public_id": document.public_id})
        )
        self.assertRedirects(
            response,
            reverse("documents:detail", kwargs={"public_id": document.public_id}),
        )

    def test_document_from_other_organization_is_not_visible(self):
        other_employee, _, other_type = document_context(code="HIDDEN")
        other_document = create_document_draft(
            document_type=other_type,
            actor=other_employee,
            title="Чужой документ",
            content={"body": "Содержимое"},
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("documents:detail", kwargs={"public_id": other_document.public_id})
        )
        self.assertEqual(response.status_code, 404)

    def test_link_can_be_created_from_detail_action(self):
        source = register_demo_document(document=self._draft(), actor=self.employee).document
        target = create_document_draft(
            document_type=self.document_type,
            actor=self.employee,
            title="Связанный документ",
            content={"body": "Содержимое"},
        )
        target = register_demo_document(document=target, actor=self.employee).document
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("documents:link_create", kwargs={"public_id": source.public_id}),
            {
                "target_document": target.pk,
                "link_type": "RELATED",
            },
        )
        self.assertRedirects(
            response,
            reverse("documents:detail", kwargs={"public_id": source.public_id}),
        )
        self.assertTrue(source.outgoing_links.filter(target_document=target).exists())
