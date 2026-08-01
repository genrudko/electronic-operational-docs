from __future__ import annotations

import json
from datetime import date
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.urls import reverse

from apps.documents.services import create_document_draft, register_document_with_password
from apps.documents.tests.factories import document_context
from apps.organizations.models import Organization
from apps.organizations.tests.factories import employee_with_user

from .. import evidence_services
from ..evidence import (
    EvidenceConfirmationMethod,
    EvidenceEventType,
    LocalActStatus,
    NormativeEvidenceStatus,
    ProductTargetMode,
    ProvenLegalMode,
)
from ..evidence_models import EvidenceEvent, LegalModeDecision
from ..evidence_services import (
    EvidenceIntegrityStatus,
    record_evidence_event,
    record_legal_mode_decision,
    verify_evidence_event_integrity,
    verify_legal_mode_decision_integrity,
)
from ..models import NormativeDocument, NormativeRequirement, NormativeRevision
from ..services import publish_normative_revision
from .helpers import NormativeDemoMixin


class EvidencePersistenceTests(NormativeDemoMixin, TestCase):
    password = "EodDemo!2026"

    def _published_revision(
        self,
        *,
        code: str,
        scope: str,
        organization: Organization | None = None,
        actor=None,
    ) -> NormativeRevision:
        document = NormativeDocument.objects.create(
            organization=organization,
            code=code,
            title=f"Демонстрационное основание {code}",
            short_title=f"Основание {code}",
            scope=scope,
            issuer="Демонстрационный издатель",
        )
        revision = NormativeRevision.objects.create(
            document=document,
            revision_number=1,
            effective_from=date(2026, 1, 1),
            source_reference=f"SRC-{code.upper()}",
            change_summary="Безопасная вымышленная редакция для теста.",
        )
        NormativeRequirement.objects.create(
            revision=revision,
            code=f"REQ-{code.upper()}",
            clause="1",
            title="Демонстрационное требование",
            requirement_text="Проверить трассируемость решения.",
        )
        return publish_normative_revision(revision=revision, actor=actor or self.employee)

    def test_verify_decision_persists_without_false_legal_claim(self):
        decision = record_legal_mode_decision(
            actor=self.employee,
            organization=self.employee.organization,
            code="OPJ-ENTRY",
            module_id="OPJ",
            subject_label="Запись оперативного журнала",
            product_target_mode=ProductTargetMode.ELECTRONIC_ORIGINAL_TARGET,
            source_ids=("N-04", "SRC-DEC-STAGE2"),
        )

        self.assertEqual(decision.proven_legal_mode, ProvenLegalMode.VERIFY.value)
        self.assertEqual(
            verify_legal_mode_decision_integrity(decision).status,
            EvidenceIntegrityStatus.VALID,
        )
        self.assertIn('"proven_legal_mode":"VERIFY"', decision.canonical_json)
        self.assertFalse(decision.normative_basis_revision_id)
        self.assertFalse(decision.local_act_revision_id)

    def test_non_verify_decision_requires_published_normative_and_local_basis(self):
        before = LegalModeDecision.objects.count()
        with self.assertRaises(ValidationError):
            record_legal_mode_decision(
                actor=self.employee,
                organization=self.employee.organization,
                code="WORK-PERMIT",
                module_id="WORK-PERMIT",
                subject_label="Наряд-допуск",
                product_target_mode=ProductTargetMode.HYBRID,
                source_ids=("N-01",),
                proven_legal_mode=ProvenLegalMode.HYBRID,
                normative_evidence_status=NormativeEvidenceStatus.CONFIRMED,
                local_act_status=LocalActStatus.CONFIRMED,
                decision_basis="Тест без связанных опубликованных редакций.",
            )
        self.assertEqual(LegalModeDecision.objects.count(), before)

    def test_closed_basis_creates_append_only_non_verify_decision(self):
        normative = self._published_revision(
            code="industry-basis",
            scope=NormativeDocument.Scope.INDUSTRY,
        )
        local = self._published_revision(
            code="local-basis",
            scope=NormativeDocument.Scope.LOCAL,
            organization=self.employee.organization,
        )
        decision = record_legal_mode_decision(
            actor=self.employee,
            organization=self.employee.organization,
            code="WORK-PERMIT",
            module_id="WORK-PERMIT",
            subject_label="Наряд-допуск",
            product_target_mode=ProductTargetMode.HYBRID,
            source_ids=("N-01", "LOCAL-ACT-DEMO"),
            proven_legal_mode=ProvenLegalMode.HYBRID,
            normative_evidence_status=NormativeEvidenceStatus.CONFIRMED,
            local_act_status=LocalActStatus.CONFIRMED,
            normative_basis_revision=normative,
            local_act_revision=local,
            decision_basis=(
                "Проверенная демонстрационная нормативная редакция и локальный акт."
            ),
        )

        self.assertEqual(decision.proven_legal_mode, ProvenLegalMode.HYBRID.value)
        self.assertEqual(decision.normative_basis_revision, normative)
        self.assertEqual(decision.local_act_revision, local)
        self.assertEqual(
            verify_legal_mode_decision_integrity(decision).status,
            EvidenceIntegrityStatus.VALID,
        )
        decision.decision_basis = "Попытка изменения"
        with self.assertRaises(ValidationError):
            decision.save()
        with self.assertRaises(ValidationError):
            LegalModeDecision.objects.filter(pk=decision.pk).update(digest="0" * 64)
        with self.assertRaises(ValidationError):
            decision.delete()

    def test_local_act_of_other_organization_is_rejected(self):
        other_employee, _ = employee_with_user(
            username="other.local.publisher",
            code="OTHER-LOCAL",
        )
        other = other_employee.organization
        local = self._published_revision(
            code="other-local-basis",
            scope=NormativeDocument.Scope.LOCAL,
            organization=other,
            actor=other_employee,
        )
        with self.assertRaises(ValidationError):
            record_legal_mode_decision(
                actor=self.employee,
                organization=self.employee.organization,
                code="OPJ-ENTRY",
                module_id="OPJ",
                subject_label="Запись оперативного журнала",
                product_target_mode=ProductTargetMode.ELECTRONIC_ORIGINAL_TARGET,
                source_ids=("N-04",),
                local_act_status=LocalActStatus.CONFIRMED,
                local_act_revision=local,
            )

    def test_password_reauth_event_is_atomic_and_secret_free(self):
        before = EvidenceEvent.objects.count()
        with self.assertRaises(ValidationError):
            record_evidence_event(
                actor=self.employee,
                user=self.user,
                event_type=EvidenceEventType.ACTION_CONFIRMATION,
                subject_type="operational_action",
                subject_id="close-defect-7",
                payload={
                    "action_code": "CLOSE_DEFECT",
                    "subject_state_digest": "a" * 64,
                },
                source_ids=("SRC-DEC-STAGE2",),
                confirmation_method=EvidenceConfirmationMethod.PASSWORD_REAUTH,
                requires_reauthentication=True,
                password="wrong-password",
            )
        self.assertEqual(EvidenceEvent.objects.count(), before)

        event = record_evidence_event(
            actor=self.employee,
            user=self.user,
            event_type=EvidenceEventType.ACTION_CONFIRMATION,
            subject_type="operational_action",
            subject_id="close-defect-7",
            payload={
                "action_code": "CLOSE_DEFECT",
                "subject_state_digest": "a" * 64,
            },
            source_ids=("SRC-DEC-STAGE2",),
            confirmation_method=EvidenceConfirmationMethod.PASSWORD_REAUTH,
            requires_reauthentication=True,
            password=self.password,
        )

        corpus = event.canonical_json + json.dumps(event.payload, ensure_ascii=False)
        self.assertNotIn(self.password, corpus)
        self.assertEqual(
            verify_evidence_event_integrity(event).status,
            EvidenceIntegrityStatus.VALID,
        )
        with self.assertRaises(ValidationError):
            event.delete()
        with self.assertRaises(ValidationError):
            EvidenceEvent.objects.filter(pk=event.pk).update(payload={})

    def test_correlation_id_is_idempotent_but_not_reusable(self):
        kwargs = {
            "actor": self.employee,
            "user": self.user,
            "event_type": EvidenceEventType.ACKNOWLEDGEMENT,
            "subject_type": "workplace_document_revision",
            "subject_id": "42",
            "payload": {
                "content_digest": "b" * 64,
                "acknowledgement_scope": "FULL_REVISION",
            },
            "source_ids": ("N-09",),
            "correlation_id": "ack:42:operator-demo",
        }
        first = record_evidence_event(**kwargs)
        second = record_evidence_event(**kwargs)
        self.assertEqual(first.pk, second.pk)

        with self.assertRaises(ValidationError):
            record_evidence_event(
                **{
                    **kwargs,
                    "payload": {
                        "content_digest": "c" * 64,
                        "acknowledgement_scope": "FULL_REVISION",
                    },
                }
            )

    def test_correlation_race_recovers_only_identical_event(self):
        kwargs = {
            "actor": self.employee,
            "user": self.user,
            "event_type": EvidenceEventType.ACKNOWLEDGEMENT,
            "subject_type": "workplace_document_revision",
            "subject_id": "race-42",
            "payload": {
                "content_digest": "7" * 64,
                "acknowledgement_scope": "FULL_REVISION",
            },
            "source_ids": ("N-09",),
            "correlation_id": "ack:race-42:operator-demo",
        }
        existing = record_evidence_event(**kwargs)

        with (
            patch.object(
                evidence_services,
                "_existing_for_correlation",
                side_effect=[None, existing],
            ),
            patch.object(
                EvidenceEvent,
                "save",
                side_effect=IntegrityError("simulated unique race"),
            ),
        ):
            duplicate = record_evidence_event(**kwargs)

        self.assertEqual(duplicate.pk, existing.pk)
        self.assertEqual(EvidenceEvent.objects.filter(pk=existing.pk).count(), 1)

    def test_correction_is_new_linked_event(self):
        original = record_evidence_event(
            actor=self.employee,
            user=self.user,
            event_type=EvidenceEventType.ACKNOWLEDGEMENT,
            subject_type="workplace_document_revision",
            subject_id="51",
            payload={
                "content_digest": "d" * 64,
                "acknowledgement_scope": "FULL_REVISION",
            },
            source_ids=("N-09",),
        )
        correction = record_evidence_event(
            actor=self.employee,
            user=self.user,
            event_type=EvidenceEventType.ACKNOWLEDGEMENT,
            subject_type="workplace_document_revision",
            subject_id="51",
            payload={
                "content_digest": "e" * 64,
                "acknowledgement_scope": "FULL_REVISION",
                "correction_reason": "Исправлен digest предмета.",
            },
            source_ids=("N-09",),
            corrects_event=original,
        )
        self.assertNotEqual(original.pk, correction.pk)
        self.assertEqual(correction.corrects_event, original)

    def test_raw_database_tamper_is_detected(self):
        event = record_evidence_event(
            actor=self.employee,
            user=self.user,
            event_type=EvidenceEventType.KNOWLEDGE_CHECK,
            subject_type="qualification_assessment",
            subject_id="91",
            payload={"result": "PASSED", "assessment_reference": "TEST-91"},
            source_ids=("N-09",),
        )
        table = EvidenceEvent._meta.db_table
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    f'UPDATE "{table}" SET canonical_json = %s WHERE id = %s',
                    [event.canonical_json + " ", event.pk],
                )
            event.refresh_from_db()
            self.assertEqual(
                verify_evidence_event_integrity(event).status,
                EvidenceIntegrityStatus.INVALID,
            )
            transaction.set_rollback(True)


class DocumentSignatureEvidenceIntegrationTests(TestCase):
    def test_document_signature_automatically_creates_one_signature_event(self):
        employee, user, document_type = document_context(code="EVID-SIGN")
        document = create_document_draft(
            document_type=document_type,
            actor=employee,
            title="Документ для evidence-события",
            content={"subject": "Тема", "body": "Содержимое"},
        )
        result = register_document_with_password(
            document=document,
            actor=employee,
            user=user,
            password="TestPass!2026",
        )

        event = EvidenceEvent.objects.get(document_signature_id=result.signature.pk)
        self.assertEqual(event.event_type, EvidenceEventType.SIGNATURE.value)
        self.assertEqual(event.payload["snapshot_digest"], result.snapshot.digest)
        self.assertEqual(event.payload["signature_checksum"], result.signature.checksum)
        self.assertTrue(event.requires_reauthentication)
        self.assertEqual(
            verify_evidence_event_integrity(event).status,
            EvidenceIntegrityStatus.VALID,
        )
        self.assertEqual(
            EvidenceEvent.objects.filter(
                document_signature_id=result.signature.pk
            ).count(),
            1,
        )


class EvidenceViewTests(NormativeDemoMixin, TestCase):
    def test_registry_requires_login(self):
        response = self.client.get(reverse("normatives:evidence_registry"))
        self.assertEqual(response.status_code, 302)

    def test_registry_has_honest_verify_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("normatives:evidence_registry"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Правовые режимы и подтверждения")
        self.assertContains(
            response,
            "Отсутствие записи не означает автоматически разрешённый режим",
        )
        self.assertContains(response, "ознакомление не доказывает инструктаж")

    def test_decision_and_event_details_are_read_only_and_russian(self):
        decision = record_legal_mode_decision(
            actor=self.employee,
            organization=self.employee.organization,
            code="OPJ-ENTRY",
            module_id="OPJ",
            subject_label="Запись оперативного журнала",
            product_target_mode=ProductTargetMode.ELECTRONIC_ORIGINAL_TARGET,
            source_ids=("N-04",),
        )
        event = record_evidence_event(
            actor=self.employee,
            user=self.user,
            event_type=EvidenceEventType.ACKNOWLEDGEMENT,
            subject_type="workplace_document_revision",
            subject_id="42",
            payload={
                "content_digest": "f" * 64,
                "acknowledgement_scope": "FULL_REVISION",
            },
            source_ids=("N-09",),
        )
        self.client.force_login(self.user)

        decision_response = self.client.get(
            reverse(
                "normatives:legal_mode_decision_detail",
                args=[decision.public_id],
            )
        )
        self.assertEqual(decision_response.status_code, 200)
        self.assertContains(decision_response, "Требует проверки")
        self.assertContains(decision_response, "Режим оставлен на проверке")
        self.assertNotContains(decision_response, ">VERIFY<")

        event_response = self.client.get(
            reverse("normatives:evidence_event_detail", args=[event.public_id])
        )
        self.assertEqual(event_response.status_code, 200)
        self.assertContains(event_response, "Ознакомление")
        self.assertContains(event_response, "Целостность подтверждена")
        self.assertNotContains(event_response, ">ACKNOWLEDGEMENT<")

    def test_other_organization_event_is_hidden(self):
        other_employee, other_user = employee_with_user(
            username="other.evidence",
            code="OTHER-EVIDENCE",
        )
        event = record_evidence_event(
            actor=other_employee,
            user=other_user,
            event_type=EvidenceEventType.ACTION_CONFIRMATION,
            subject_type="operational_action",
            subject_id="other-1",
            payload={
                "action_code": "OTHER_ACTION",
                "subject_state_digest": "9" * 64,
            },
            source_ids=("SRC-DEC-STAGE2",),
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("normatives:evidence_event_detail", args=[event.public_id])
        )
        self.assertEqual(response.status_code, 404)

    def test_legacy_migration_cannot_be_created_through_user_service(self):
        with self.assertRaises(PermissionDenied):
            record_evidence_event(
                actor=self.employee,
                user=self.user,
                event_type=EvidenceEventType.ACTION_CONFIRMATION,
                subject_type="operational_action",
                subject_id="legacy-attempt",
                payload={
                    "action_code": "ATTEMPT",
                    "subject_state_digest": "8" * 64,
                },
                source_ids=("SRC-AUDIT-STAGE1",),
                confirmation_method=EvidenceConfirmationMethod.LEGACY_MIGRATION,
            )
