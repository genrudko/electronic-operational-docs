from django.urls import reverse

from apps.workplace_docs.services import approve_revision

from .base import WorkplaceDocumentTestBase


class WorkplaceDocumentViewTests(WorkplaceDocumentTestBase):
    def test_registry_requires_authentication(self) -> None:
        response = self.client.get(reverse("workplace_docs:registry"))
        self.assertEqual(response.status_code, 302)

    def test_registry_and_detail_show_approved_content(self) -> None:
        revision = approve_revision(revision=self.create_revision(), actor=self.employee)
        self.client.force_login(self.user)
        registry = self.client.get(reverse("workplace_docs:registry"))
        self.assertContains(registry, "Перечни документации")
        self.assertContains(registry, "Рабочее место смены")
        self.assertContains(registry, "Действует")

        detail = self.client.get(
            reverse("workplace_docs:detail", args=(revision.document_list_id,))
        )
        self.assertContains(detail, "Редакция утверждена и неизменяема")
        self.assertContains(detail, "Оперативный журнал")
        self.assertContains(detail, "Электронная")
        self.assertContains(detail, "Технические реквизиты редакции")
        self.assertContains(detail, revision.digest)

    def test_other_organization_list_is_hidden(self) -> None:
        revision = approve_revision(revision=self.create_revision(), actor=self.employee)
        self.client.force_login(self.foreign_user)
        response = self.client.get(
            reverse("workplace_docs:detail", args=(revision.document_list_id,))
        )
        self.assertEqual(response.status_code, 404)
