from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.organizations.models import Organization

from ..models import (
    NormativeDocument,
    NormativeRequirement,
    NormativeRevision,
    OrganizationConfigurationRevision,
    OrganizationNameRevision,
    RequirementTrace,
)
from .helpers import NormativeDemoMixin


class NormativeRegistryModelTests(NormativeDemoMixin, TestCase):
    def test_local_document_requires_organization(self):
        document = NormativeDocument(
            code="local-without-org",
            title="Локальный документ",
            scope=NormativeDocument.Scope.LOCAL,
            issuer="Демо",
        )
        with self.assertRaises(ValidationError):
            document.full_clean()

    def test_global_document_rejects_organization(self):
        document = NormativeDocument(
            organization=self.employee.organization,
            code="global-with-org",
            title="Федеральный документ",
            scope=NormativeDocument.Scope.FEDERAL,
            issuer="Демо",
        )
        with self.assertRaises(ValidationError):
            document.full_clean()

    def test_published_revision_is_immutable(self):
        revision = NormativeRevision.objects.get(document__code="demo-electronic-documentation")
        revision.change_summary = "Попытка изменения"
        with self.assertRaises(ValidationError):
            revision.save()

    def test_published_revision_bulk_update_is_blocked(self):
        revision = NormativeRevision.objects.get(document__code="demo-electronic-documentation")
        with self.assertRaises(ValidationError):
            NormativeRevision.objects.filter(pk=revision.pk).update(revision_number=2)

    def test_published_requirement_is_immutable(self):
        requirement = NormativeRequirement.objects.get(code="EOD-IDENTITY")
        requirement.title = "Попытка изменения"
        with self.assertRaises(ValidationError):
            requirement.save()

    def test_trace_is_append_only(self):
        trace = RequirementTrace.objects.first()
        trace.notes = "Попытка изменения"
        with self.assertRaises(ValidationError):
            trace.save()

    def test_name_revision_rejects_overlapping_period(self):
        overlap = OrganizationNameRevision(
            organization=self.employee.organization,
            full_name="Пересекающееся наименование",
            valid_from=date(2025, 1, 1),
            valid_until=date(2026, 6, 1),
            created_by=self.employee,
        )
        with self.assertRaises(ValidationError):
            overlap.full_clean()

    def test_configuration_requires_json_object(self):
        configuration = OrganizationConfigurationRevision(
            organization=self.employee.organization,
            revision_number=99,
            effective_from=date(2027, 1, 1),
            configuration=["не", "объект"],
            created_by=self.employee,
        )
        with self.assertRaises(ValidationError):
            configuration.full_clean()

    def test_foreign_employee_cannot_create_local_name_revision(self):
        other = Organization.objects.create(code="OTHER", name="Другая организация")
        foreign = OrganizationNameRevision(
            organization=other,
            full_name="Другая организация",
            valid_from=date(2028, 1, 1),
            created_by=self.employee,
        )
        with self.assertRaises(ValidationError):
            foreign.full_clean()

    def test_published_configuration_is_immutable(self):
        configuration = OrganizationConfigurationRevision.objects.get(revision_number=1)
        configuration.change_summary = "Попытка изменения"
        with self.assertRaises(ValidationError):
            configuration.save()
