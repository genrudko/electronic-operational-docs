from django.test import TestCase
from django.urls import reverse

from apps.organizations.models import Organization

from ..models import NormativeDocument, NormativeRevision
from .helpers import NormativeDemoMixin


class NormativeRegistryViewTests(NormativeDemoMixin, TestCase):
    def test_registry_requires_login(self):
        response = self.client.get(reverse("normatives:registry"))
        self.assertEqual(response.status_code, 302)

    def test_registry_is_available_to_personal_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("normatives:registry"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Нормативный реестр")
        self.assertContains(response, "История наименований организации")

    def test_document_detail_is_russian(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "normatives:document_detail",
                args=["demo-electronic-documentation"],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Редакции")
        self.assertNotContains(response, ">PUBLISHED<")

    def test_revision_detail_shows_requirement_trace(self):
        revision = NormativeRevision.objects.get(document__code="demo-electronic-documentation")
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "normatives:revision_detail",
                args=[revision.document.code, revision.revision_number],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Техническая трассируемость")
        self.assertContains(response, "Автоматический тест")
        self.assertContains(response, 'class="help-tip"', html=False)

    def test_local_document_of_other_organization_is_hidden(self):
        other = Organization.objects.create(code="OTHER", name="Другая организация")
        NormativeDocument.objects.create(
            organization=other,
            code="other-local",
            title="Чужой локальный документ",
            scope=NormativeDocument.Scope.LOCAL,
            issuer="Другая организация",
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("normatives:document_detail", args=["other-local"])
        )
        self.assertEqual(response.status_code, 404)
