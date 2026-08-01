from __future__ import annotations

from datetime import UTC, datetime

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.normatives.evidence import (
    EvidenceConfirmationMethod,
    EvidenceEventContract,
    EvidenceEventType,
    LegalModeDecisionContract,
    LocalActStatus,
    NormativeEvidenceStatus,
    ProductTargetMode,
    ProvenLegalMode,
)


OCCURRED_AT = datetime(2026, 8, 1, 19, 15, tzinfo=UTC)


class LegalModeDecisionContractTests(SimpleTestCase):
    def test_target_and_proven_mode_remain_separate(self) -> None:
        decision = LegalModeDecisionContract(
            code="opj-entry",
            module_id="opj",
            subject_label="Зарегистрированная запись оперативного журнала",
            product_target_mode=ProductTargetMode.ELECTRONIC_ORIGINAL_TARGET,
            source_ids=("N-04",),
        )

        self.assertEqual(
            decision.product_target_mode,
            ProductTargetMode.ELECTRONIC_ORIGINAL_TARGET,
        )
        self.assertEqual(decision.proven_legal_mode, ProvenLegalMode.VERIFY)
        self.assertEqual(decision.canonical_payload()["proven_legal_mode"], "VERIFY")

    def test_non_verify_mode_requires_confirmed_evidence_and_basis(self) -> None:
        with self.assertRaises(ValidationError) as context:
            LegalModeDecisionContract(
                code="opj-entry",
                module_id="opj",
                subject_label="Зарегистрированная запись оперативного журнала",
                product_target_mode=ProductTargetMode.ELECTRONIC_ORIGINAL_TARGET,
                source_ids=("N-04",),
                proven_legal_mode=ProvenLegalMode.ELECTRONIC_ORIGINAL,
            )

        self.assertIn("normative_evidence_status", context.exception.message_dict)
        self.assertIn("local_act_status", context.exception.message_dict)
        self.assertIn("basis_revision_code", context.exception.message_dict)
        self.assertIn("decision_basis", context.exception.message_dict)

    def test_non_verify_mode_accepts_traceable_closed_basis(self) -> None:
        decision = LegalModeDecisionContract(
            code="permit",
            module_id="work-permit",
            subject_label="Наряд-допуск",
            product_target_mode=ProductTargetMode.HYBRID,
            source_ids=("N-01", "LOCAL-ACT-001"),
            proven_legal_mode=ProvenLegalMode.HYBRID,
            normative_evidence_status=NormativeEvidenceStatus.CONFIRMED,
            local_act_status=LocalActStatus.CONFIRMED,
            basis_revision_code="NORM-903N-CONSOLIDATED-R1",
            decision_basis="Проверенная нормативная редакция и применимый локальный акт.",
        )

        self.assertEqual(decision.proven_legal_mode, ProvenLegalMode.HYBRID)
        self.assertEqual(len(decision.digest), 64)

    def test_incompatible_target_and_proven_mode_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            LegalModeDecisionContract(
                code="order-journal",
                module_id="operational-orders",
                subject_label="Журнал распоряжений",
                product_target_mode=ProductTargetMode.PAPER_MIRROR,
                source_ids=("SRC-DEC-STAGE2",),
                proven_legal_mode=ProvenLegalMode.ELECTRONIC_ORIGINAL,
                normative_evidence_status=NormativeEvidenceStatus.CONFIRMED,
                local_act_status=LocalActStatus.NOT_REQUIRED,
                basis_revision_code="DECISION-R1",
                decision_basis="Тест несовместимого режима.",
            )


class EvidenceEventContractTests(SimpleTestCase):
    def test_taxonomy_contains_five_distinct_event_types(self) -> None:
        self.assertEqual(
            {item.value for item in EvidenceEventType},
            {
                "SIGNATURE",
                "ACKNOWLEDGEMENT",
                "INSTRUCTION",
                "KNOWLEDGE_CHECK",
                "ACTION_CONFIRMATION",
            },
        )

    def test_acknowledgement_cannot_be_substituted_with_instruction_payload(self) -> None:
        with self.assertRaises(ValidationError) as context:
            EvidenceEventContract(
                event_type=EvidenceEventType.ACKNOWLEDGEMENT,
                subject_type="workplace_document_revision",
                subject_id="42",
                actor_employee_id=7,
                occurred_at=OCCURRED_AT,
                confirmation_method=EvidenceConfirmationMethod.SESSION_AUTH,
                payload={
                    "content_digest": "a" * 64,
                    "instruction_kind": "TARGETED",
                    "instructor_employee_id": 8,
                },
                source_ids=("N-09",),
            )

        self.assertIn("acknowledgement_scope", str(context.exception))

    def test_signature_requires_explicit_password_reauthentication(self) -> None:
        with self.assertRaises(ValidationError):
            EvidenceEventContract(
                event_type=EvidenceEventType.SIGNATURE,
                subject_type="document_version",
                subject_id="12",
                actor_employee_id=7,
                occurred_at=OCCURRED_AT,
                confirmation_method=EvidenceConfirmationMethod.SESSION_AUTH,
                payload={"snapshot_digest": "b" * 64, "purpose": "REGISTRATION"},
                source_ids=("N-04",),
            )

        event = EvidenceEventContract(
            event_type=EvidenceEventType.SIGNATURE,
            subject_type="document_version",
            subject_id="12",
            actor_employee_id=7,
            occurred_at=OCCURRED_AT,
            confirmation_method=EvidenceConfirmationMethod.PASSWORD_REAUTH,
            requires_reauthentication=True,
            payload={"snapshot_digest": "b" * 64, "purpose": "REGISTRATION"},
            source_ids=("N-04",),
        )

        self.assertTrue(event.requires_reauthentication)
        self.assertEqual(event.confirmation_method, EvidenceConfirmationMethod.PASSWORD_REAUTH)

    def test_action_confirmation_can_require_reauthentication(self) -> None:
        with self.assertRaises(ValidationError):
            EvidenceEventContract(
                event_type=EvidenceEventType.ACTION_CONFIRMATION,
                subject_type="operational_action",
                subject_id="open-shift-17",
                actor_employee_id=7,
                occurred_at=OCCURRED_AT,
                confirmation_method=EvidenceConfirmationMethod.SESSION_AUTH,
                requires_reauthentication=True,
                payload={
                    "action_code": "OPEN_SHIFT",
                    "subject_state_digest": "c" * 64,
                },
                source_ids=("SRC-DEC-STAGE2",),
            )

    def test_digest_is_stable_for_equivalent_payload_order(self) -> None:
        first = EvidenceEventContract(
            event_type=EvidenceEventType.KNOWLEDGE_CHECK,
            subject_type="qualification_assessment",
            subject_id="91",
            actor_employee_id=7,
            occurred_at=OCCURRED_AT,
            confirmation_method=EvidenceConfirmationMethod.SESSION_AUTH,
            payload={"result": "PASSED", "assessment_reference": "TEST-2026-91"},
            source_ids=("N-09",),
        )
        second = EvidenceEventContract(
            event_type=EvidenceEventType.KNOWLEDGE_CHECK,
            subject_type="qualification_assessment",
            subject_id="91",
            actor_employee_id=7,
            occurred_at=OCCURRED_AT,
            confirmation_method=EvidenceConfirmationMethod.SESSION_AUTH,
            payload={"assessment_reference": "TEST-2026-91", "result": "PASSED"},
            source_ids=("N-09",),
        )

        self.assertEqual(first.digest, second.digest)
        self.assertEqual(len(first.digest), 64)

    def test_secret_like_fields_are_rejected_recursively(self) -> None:
        with self.assertRaises(ValidationError) as context:
            EvidenceEventContract(
                event_type=EvidenceEventType.ACTION_CONFIRMATION,
                subject_type="operational_action",
                subject_id="close-defect-4",
                actor_employee_id=7,
                occurred_at=OCCURRED_AT,
                confirmation_method=EvidenceConfirmationMethod.SESSION_AUTH,
                payload={
                    "action_code": "CLOSE_DEFECT",
                    "subject_state_digest": "d" * 64,
                    "authentication": {"password": "must-not-be-persisted"},
                },
                source_ids=("SRC-DEC-STAGE2",),
            )

        self.assertIn("Секретное поле запрещено", str(context.exception))

    def test_naive_server_time_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            EvidenceEventContract(
                event_type=EvidenceEventType.ACKNOWLEDGEMENT,
                subject_type="workplace_document_revision",
                subject_id="42",
                actor_employee_id=7,
                occurred_at=datetime(2026, 8, 1, 19, 15),
                confirmation_method=EvidenceConfirmationMethod.SESSION_AUTH,
                payload={
                    "content_digest": "e" * 64,
                    "acknowledgement_scope": "FULL_REVISION",
                },
                source_ids=("N-09",),
            )
