from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.documents.models import (
    Document,
    DocumentLink,
    DocumentNumberSequence,
    DocumentSignature,
    DocumentType,
    SignedSnapshot,
)


@override_settings(DEBUG=True)
class DemoDocumentSeedTests(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed_demo_organization", reset_passwords=True, verbosity=0)
        call_command("seed_demo_documents", verbosity=0)
        first_counts = (
            DocumentType.objects.count(),
            Document.objects.count(),
            DocumentLink.objects.count(),
            DocumentNumberSequence.objects.count(),
            SignedSnapshot.objects.count(),
            DocumentSignature.objects.count(),
        )

        call_command("seed_demo_documents", verbosity=0)
        second_counts = (
            DocumentType.objects.count(),
            Document.objects.count(),
            DocumentLink.objects.count(),
            DocumentNumberSequence.objects.count(),
            SignedSnapshot.objects.count(),
            DocumentSignature.objects.count(),
        )

        self.assertEqual(first_counts, second_counts)
        self.assertEqual(Document.objects.filter(status=Document.Status.REGISTERED).count(), 2)
        self.assertEqual(Document.objects.filter(status=Document.Status.DRAFT).count(), 1)
        sequence = DocumentNumberSequence.objects.get()
        self.assertEqual(sequence.last_value, 2)
        self.assertEqual(SignedSnapshot.objects.count(), 2)
        self.assertEqual(
            DocumentSignature.objects.filter(
                confirmation_method=DocumentSignature.ConfirmationMethod.DEMO_SEED
            ).count(),
            2,
        )
