from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import (
    NormativeDocument,
    NormativeRequirement,
    NormativeRevision,
    OrganizationConfigurationRevision,
    PublicationStatus,
)
from ..services import (
    canonical_json,
    organization_name_on,
    publish_configuration_revision,
    publish_normative_revision,
)
from .helpers import NormativeDemoMixin


class NormativeRegistryServiceTests(NormativeDemoMixin, TestCase):
    def test_canonical_json_is_deterministic_and_utf8(self):
        first = canonical_json({"б": 2, "а": [3, 1]})
        second = canonical_json({"а": [3, 1], "б": 2})
        self.assertEqual(first, second)
        self.assertIn("а", first)

    def test_publish_revision_requires_requirement(self):
        document = NormativeDocument.objects.create(
            code="empty-demo",
            title="Пустой демонстрационный документ",
            scope=NormativeDocument.Scope.FEDERAL,
            issuer="Демо",
        )
        revision = NormativeRevision.objects.create(
            document=document,
            revision_number=1,
            effective_from=date(2027, 1, 1),
        )
        with self.assertRaises(ValidationError):
            publish_normative_revision(revision=revision, actor=self.employee)

    def test_publish_revision_creates_digest(self):
        document = NormativeDocument.objects.create(
            code="publish-demo",
            title="Документ для публикации",
            scope=NormativeDocument.Scope.FEDERAL,
            issuer="Демо",
        )
        revision = NormativeRevision.objects.create(
            document=document,
            revision_number=1,
            effective_from=date(2027, 1, 1),
        )
        NormativeRequirement.objects.create(
            revision=revision,
            code="REQ-1",
            clause="п. 1",
            title="Требование",
            requirement_text="Проверяемое требование.",
        )
        published = publish_normative_revision(revision=revision, actor=self.employee)
        self.assertEqual(published.status, PublicationStatus.PUBLISHED)
        self.assertEqual(len(published.digest), 64)
        self.assertIsNotNone(published.published_at)

    def test_current_organization_name_uses_effective_window(self):
        old = organization_name_on(self.employee.organization, date(2025, 6, 1))
        current = organization_name_on(self.employee.organization, date(2026, 6, 1))
        self.assertIn("НоваВетер", old.full_name)
        self.assertIn("Росатом Возобновляемая энергия", current.full_name)

    def test_publish_configuration_creates_digest(self):
        configuration = OrganizationConfigurationRevision.objects.create(
            organization=self.employee.organization,
            revision_number=2,
            effective_from=date(2027, 1, 1),
            configuration={"language": "ru", "modules": {"documents": True}},
            created_by=self.employee,
        )
        published = publish_configuration_revision(
            revision=configuration,
            actor=self.employee,
        )
        self.assertEqual(published.status, PublicationStatus.PUBLISHED)
        self.assertEqual(len(published.digest), 64)
