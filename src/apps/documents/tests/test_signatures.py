
from __future__ import annotations

import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.test import TestCase, override_settings

from apps.documents.models import (
    AuditEvent,
    Document,
    DocumentNumberSequence,
    DocumentSignature,
    DocumentVersion,
    SignedSnapshot,
)
from apps.documents.services import (
    IntegrityStatus,
    canonical_json,
    create_document_draft,
    register_document_with_password,
    sha256_text,
    verify_document_integrity,
)

from .factories import document_context


class DocumentSignatureTests(TestCase):
    def setUp(self) -> None:
        self.employee, self.user, self.document_type = document_context(code="SIGN")
        self.password = "TestPass!2026"

    def _draft(self, title: str = "Подписываемый документ") -> Document:
        return create_document_draft(
            document_type=self.document_type,
            actor=self.employee,
            title=title,
            content={"subject": "Тема", "body": "Содержимое для подписи"},
        )

    def _register(self, document: Document | None = None):
        return register_document_with_password(
            document=document or self._draft(),
            actor=self.employee,
            user=self.user,
            password=self.password,
        )

    def test_wrong_password_does_not_allocate_number_or_signature(self):
        document = self._draft()
        before = DocumentNumberSequence.objects.count()
        with self.assertRaises(ValidationError):
            register_document_with_password(
                document=document,
                actor=self.employee,
                user=self.user,
                password="wrong-password",
            )
        document.refresh_from_db()
        self.assertEqual(document.status, Document.Status.DRAFT)
        self.assertEqual(DocumentNumberSequence.objects.count(), before)
        self.assertFalse(SignedSnapshot.objects.filter(document=document).exists())
        self.assertFalse(DocumentSignature.objects.exists())

    def test_other_user_cannot_confirm_for_employee(self):
        _, other_user, _ = document_context(code="OTHER-SIGN")
        with self.assertRaises(PermissionDenied):
            register_document_with_password(
                document=self._draft(),
                actor=self.employee,
                user=other_user,
                password="TestPass!2026",
            )

    def test_success_creates_exactly_one_snapshot_and_signature(self):
        result = self._register()
        self.assertEqual(result.document.status, Document.Status.REGISTERED)
        self.assertEqual(result.snapshot.document, result.document)
        self.assertEqual(result.signature.snapshot, result.snapshot)
        self.assertEqual(
            result.signature.confirmation_method,
            DocumentSignature.ConfirmationMethod.PASSWORD_REAUTH,
        )
        self.assertEqual(SignedSnapshot.objects.filter(document=result.document).count(), 1)
        self.assertEqual(DocumentSignature.objects.filter(snapshot=result.snapshot).count(), 1)
        self.assertEqual(verify_document_integrity(result.document).status, IntegrityStatus.VALID)

    def test_password_is_not_persisted_in_snapshot_signature_or_audit(self):
        result = self._register()
        corpus = [
            result.snapshot.canonical_json,
            json.dumps(result.signature.roles_snapshot, ensure_ascii=False),
            result.signature.checksum,
            *[
                json.dumps(item.payload, ensure_ascii=False)
                for item in AuditEvent.objects.filter(document=result.document)
            ],
        ]
        self.assertNotIn(self.password, "\n".join(corpus))

    def test_content_tamper_is_invalid(self):
        result = self._register()
        table = DocumentVersion._meta.db_table
        with transaction.atomic():
            with connection.cursor() as cursor:
                payload = {"subject": "Тема", "body": "Подмена"}
                if connection.vendor == "postgresql":
                    cursor.execute(
                        f'UPDATE "{table}" SET content = %s::jsonb WHERE id = %s',
                        [json.dumps(payload), result.version.pk],
                    )
                else:
                    cursor.execute(
                        f'UPDATE "{table}" SET content = %s WHERE id = %s',
                        [json.dumps(payload), result.version.pk],
                    )
            result.document.refresh_from_db()
            self.assertEqual(verify_document_integrity(result.document).status, IntegrityStatus.INVALID)
            transaction.set_rollback(True)

    def test_title_tamper_is_invalid(self):
        result = self._register()
        table = Document._meta.db_table
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    f'UPDATE "{table}" SET title = %s WHERE id = %s',
                    ["Подменённый заголовок", result.document.pk],
                )
            result.document.refresh_from_db()
            self.assertEqual(verify_document_integrity(result.document).status, IntegrityStatus.INVALID)
            transaction.set_rollback(True)

    def test_snapshot_tamper_is_invalid(self):
        result = self._register()
        table = SignedSnapshot._meta.db_table
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    f'UPDATE "{table}" SET canonical_json = %s WHERE id = %s',
                    [result.snapshot.canonical_json + " ", result.snapshot.pk],
                )
            result.document.refresh_from_db()
            self.assertEqual(verify_document_integrity(result.document).status, IntegrityStatus.INVALID)
            transaction.set_rollback(True)

    def test_signature_tamper_is_invalid(self):
        result = self._register()
        table = DocumentSignature._meta.db_table
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    f'UPDATE "{table}" SET full_name_snapshot = %s WHERE id = %s',
                    ["Подменённый Подписант", result.signature.pk],
                )
            result.document.refresh_from_db()
            self.assertEqual(verify_document_integrity(result.document).status, IntegrityStatus.INVALID)
            transaction.set_rollback(True)

    def test_historical_name_and_position_do_not_change(self):
        result = self._register()
        old_name = result.signature.full_name_snapshot
        old_position = result.signature.position_snapshot
        self.employee.last_name = "НоваяФамилия"
        self.employee.save(update_fields=("last_name",))
        position = self.employee.position
        position.name = "Новая должность"
        position.save(update_fields=("name",))
        result.signature.refresh_from_db()
        self.assertEqual(result.signature.full_name_snapshot, old_name)
        self.assertEqual(result.signature.position_snapshot, old_position)
        result.document.refresh_from_db()
        self.assertEqual(verify_document_integrity(result.document).status, IntegrityStatus.VALID)

    def test_snapshot_and_signature_are_immutable(self):
        result = self._register()
        result.snapshot.digest = "0" * 64
        with self.assertRaises(ValidationError):
            result.snapshot.save()
        result.signature.checksum = "0" * 64
        with self.assertRaises(ValidationError):
            result.signature.save()
        with self.assertRaises(ValidationError):
            result.snapshot.delete()
        with self.assertRaises(ValidationError):
            result.signature.delete()
        with self.assertRaises(ValidationError):
            SignedSnapshot.objects.filter(pk=result.snapshot.pk).update(digest="0" * 64)
        with self.assertRaises(ValidationError):
            DocumentSignature.objects.filter(pk=result.signature.pk).delete()

    def test_missing_signature_returns_missing(self):
        result = self._register()
        table = DocumentSignature._meta.db_table
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{table}" WHERE id = %s', [result.signature.pk])
            result.document.refresh_from_db()
            self.assertEqual(verify_document_integrity(result.document).status, IntegrityStatus.MISSING)
            transaction.set_rollback(True)

    def test_canonical_json_is_deterministic_and_utf8(self):
        first = canonical_json({"b": 2, "a": "Энергия"})
        second = canonical_json({"a": "Энергия", "b": 2})
        self.assertEqual(first, second)
        self.assertEqual(first, '{"a":"Энергия","b":2}')
        self.assertEqual(sha256_text(first), sha256_text(second))

    def test_registration_audit_contains_digests_without_secret(self):
        result = self._register()
        event = AuditEvent.objects.get(
            document=result.document,
            event_type=AuditEvent.EventType.DOCUMENT_REGISTERED,
        )
        self.assertEqual(event.payload["snapshot_digest"], result.snapshot.digest)
        self.assertEqual(event.payload["signature_checksum"], result.signature.checksum)
        self.assertEqual(event.payload["confirmation_method"], "PASSWORD_REAUTH")
        self.assertNotIn(self.password, json.dumps(event.payload, ensure_ascii=False))

    def test_second_registration_attempt_creates_no_duplicate_confirmation(self):
        result = self._register()
        with self.assertRaises(ValidationError):
            register_document_with_password(
                document=result.document,
                actor=self.employee,
                user=self.user,
                password=self.password,
            )
        self.assertEqual(SignedSnapshot.objects.filter(document=result.document).count(), 1)
        self.assertEqual(DocumentSignature.objects.filter(snapshot=result.snapshot).count(), 1)

    @override_settings(DEBUG=False)
    def test_demo_registration_is_not_available_outside_debug(self):
        from apps.documents.services import register_demo_document

        with self.assertRaises(PermissionDenied):
            register_demo_document(document=self._draft(), actor=self.employee)
