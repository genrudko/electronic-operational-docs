from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command

from apps.organizations.models import RoleAssignment
from apps.workplace_docs.models import (
    RevisionStatus,
    WorkplaceDocumentAuditEvent,
    WorkplaceDocumentEntry,
    WorkplaceDocumentList,
    WorkplaceDocumentRevision,
)
from apps.workplace_docs.services import (
    add_calendar_months,
    approve_revision,
    current_revision,
    review_state,
)

from .base import WorkplaceDocumentTestBase


class WorkplaceDocumentServiceTests(WorkplaceDocumentTestBase):
    def test_approval_creates_digest_review_date_and_audit(self) -> None:
        revision = approve_revision(revision=self.create_revision(), actor=self.employee)
        self.assertEqual(revision.status, RevisionStatus.APPROVED)
        self.assertEqual(revision.next_review_date, date(2027, 1, 1))
        self.assertEqual(len(revision.digest), 64)
        event = WorkplaceDocumentAuditEvent.objects.get(revision=revision)
        self.assertEqual(event.digest, revision.digest)
        self.assertEqual(event.snapshot["entries"][0]["code"], "OP-JOURNAL")

    def test_calendar_month_addition_handles_month_end(self) -> None:
        self.assertEqual(add_calendar_months(date(2026, 1, 31), 1), date(2026, 2, 28))
        revision = self.create_revision(
            effective_from=date(2026, 1, 31),
            review_period_months=1,
        )
        approved = approve_revision(revision=revision, actor=self.employee)
        self.assertEqual(approved.next_review_date, date(2026, 2, 28))

    def test_empty_revision_cannot_be_approved(self) -> None:
        revision = self.create_revision(with_entry=False)
        with self.assertRaises(ValidationError):
            approve_revision(revision=revision, actor=self.employee)

    def test_direct_approver_role_is_required(self) -> None:
        RoleAssignment.objects.filter(pk=self.assignment.pk).update(is_active=False)
        revision = self.create_revision()
        with self.assertRaises(PermissionDenied):
            approve_revision(revision=revision, actor=self.employee)

    def test_foreign_employee_cannot_approve(self) -> None:
        revision = self.create_revision()
        with self.assertRaises(PermissionDenied):
            approve_revision(revision=revision, actor=self.foreign_employee)

    def test_current_revision_and_review_state_use_effective_window(self) -> None:
        document_list = self.create_document_list()
        revision = self.create_revision(
            document_list=document_list,
            effective_from=date(2026, 1, 1),
            effective_until=date(2026, 12, 31),
        )
        approved = approve_revision(revision=revision, actor=self.employee)
        self.assertEqual(current_revision(document_list, date(2026, 6, 1)), approved)
        self.assertIsNone(current_revision(document_list, date(2027, 1, 1)))
        self.assertEqual(review_state(approved, date(2026, 12, 15)), "DUE_SOON")
        self.assertEqual(review_state(approved, date(2027, 1, 2)), "OVERDUE")

    def test_demo_seed_is_idempotent(self) -> None:
        call_command("seed_demo_workplace_documents", verbosity=0)
        first = (
            WorkplaceDocumentList.objects.count(),
            WorkplaceDocumentRevision.objects.count(),
            WorkplaceDocumentEntry.objects.count(),
        )
        call_command("seed_demo_workplace_documents", verbosity=0)
        second = (
            WorkplaceDocumentList.objects.count(),
            WorkplaceDocumentRevision.objects.count(),
            WorkplaceDocumentEntry.objects.count(),
        )
        self.assertEqual(first, second)
        self.assertGreaterEqual(second[2], 7)
