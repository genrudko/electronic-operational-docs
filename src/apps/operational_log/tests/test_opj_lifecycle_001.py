from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, SimpleTestCase
from django.urls import reverse

from apps.organizations.authority_models import OperationalAuthorityGrant
from apps.organizations.models import Employee

from ..models import OperationalLogEntry
from ..opj_lifecycle import (
    TYPE_CANCELLATION,
    TYPE_COMMUNICATION,
    TYPE_CORRECTION,
    TYPE_ENTRY,
    cancel_entry,
    correct_entry,
    effective_state,
    record_communication,
    register_draft,
)
from .base import OperationalLogTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalLifecycleTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.get(username="operator.demo")

    def test_registration_correction_cancellation_and_communication_are_append_only(self) -> None:
        draft = self.shift.draft_entries.filter(is_removed=False).exclude(content="").first()
        self.assertIsNotNone(draft)

        original = register_draft(draft=draft, actor=self.actor)
        self.assertEqual(original.type_code, TYPE_ENTRY)
        self.assertIn(original.typed_payload["authority"]["decision"], {"ALLOW", "VERIFY"})
        original_content = original.content
        original_digest = original.digest

        correction = correct_entry(
            entry=original,
            actor=self.actor,
            replacement_content=f"{original_content} Уточнено после проверки.",
            reason="Уточнение диспетчерского наименования.",
        )
        self.assertEqual(correction.type_code, TYPE_CORRECTION)

        communication = record_communication(
            entry=original,
            actor=self.actor,
            direction="OUTGOING",
            channel="PHONE",
            counterpart="Диспетчер СКДУ",
            counterpart_organization="Диспетчерский центр",
            content="Передано уточнение по зарегистрированной записи.",
        )
        self.assertEqual(communication.type_code, TYPE_COMMUNICATION)

        cancellation = cancel_entry(
            entry=original,
            actor=self.actor,
            reason="Исходное событие признано недействительным.",
        )
        self.assertEqual(cancellation.type_code, TYPE_CANCELLATION)

        original.refresh_from_db()
        self.assertEqual(original.content, original_content)
        self.assertEqual(original.digest, original_digest)
        self.assertEqual(
            [
                correction.sequence_number,
                communication.sequence_number,
                cancellation.sequence_number,
            ],
            sorted(
                [
                    correction.sequence_number,
                    communication.sequence_number,
                    cancellation.sequence_number,
                ]
            ),
        )
        state = effective_state(original)
        self.assertEqual(state.status, "CANCELLED")
        self.assertEqual(state.correction_count, 1)
        self.assertIn("Уточнено после проверки", state.effective_content)

        with self.assertRaises(ValidationError):
            correct_entry(
                entry=original,
                actor=self.actor,
                replacement_content="Недопустимое исправление после отмены.",
                reason="Не должно создаваться.",
            )

    def test_deny_records_evaluation_but_does_not_create_subject_fact(self) -> None:
        denied_actor = Employee.objects.select_related(
            "organization", "position", "division", "workplace"
        ).get(organization=self.organization, personnel_number="DEMO-013")
        OperationalAuthorityGrant.objects.filter(
            employee=denied_actor,
            action_code="OPJ.COMMUNICATION",
        ).delete()
        original = (
            OperationalLogEntry.objects.filter(journal=self.journal)
            .order_by("sequence_number")
            .first()
        )
        before = self.journal.entries.count()

        with self.assertRaises(PermissionDenied):
            record_communication(
                entry=original,
                actor=denied_actor,
                direction="INCOMING",
                channel="RADIO",
                counterpart="Проверочный участник",
                counterpart_organization="",
                content="Эта запись не должна быть создана.",
            )

        self.assertEqual(self.journal.entries.count(), before)
        self.assertTrue(
            denied_actor.authority_evaluations.filter(
                action_code="OPJ.COMMUNICATION",
                decision="DENY",
            ).exists()
        )

    def test_lifecycle_page_and_draft_registration_route(self) -> None:
        self.client.force_login(self.user)
        original = (
            OperationalLogEntry.objects.filter(journal=self.journal)
            .order_by("sequence_number")
            .first()
        )

        page = self.client.get(
            reverse(
                "operational_log:entry_lifecycle",
                args=(self.journal.pk, original.sequence_number),
            )
        )
        self.assertEqual(page.status_code, 200)
        for marker in (
            "ЖИЗНЕННЫЙ ЦИКЛ",
            "НЕИЗМЕНЯЕМЫЙ ОРИГИНАЛ",
            "APPEND-ONLY ИСТОРИЯ",
            "ОПЕРАТИВНЫЕ ПЕРЕГОВОРЫ",
            "ALLOW / VERIFY / DENY",
            "opj_lifecycle_001.css",
            "system/icons.svg",
        ):
            self.assertContains(page, marker)

        draft = self.shift.draft_entries.filter(is_removed=False).exclude(content="").first()
        response = self.client.post(
            reverse(
                "operational_log:register_draft_lifecycle",
                args=(self.journal.pk, draft.public_id),
            )
        )
        self.assertEqual(response.status_code, 302)
        draft.refresh_from_db()
        self.assertTrue(draft.is_removed)
        registered = self.journal.entries.order_by("-sequence_number").first()
        self.assertEqual(registered.type_code, TYPE_ENTRY)
        self.assertIn(
            reverse(
                "operational_log:entry_lifecycle",
                args=(self.journal.pk, registered.sequence_number),
            ),
            response.url,
        )


class OperationalJournalLifecycleSourceContractTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_accepted_visual_identity_and_append_only_contract_are_used(self) -> None:
        template = self.source("templates/operational_log/entry_lifecycle.html")
        css = self.source("static/operational_log/opj_lifecycle_001.css")
        javascript = self.source("static/operational_log/opj_lifecycle_001.js")
        service = self.source("apps/operational_log/opj_lifecycle.py")

        self.assertIn("shared/direction_a/base.html", template)
        self.assertIn("system/icons.svg", template)
        self.assertIn("icon-history", template)
        self.assertIn("font-family: var(--font-interface", css)
        self.assertNotIn("font-family: Arial", css)
        self.assertIn("TYPE_CORRECTION", service)
        self.assertIn("TYPE_CANCELLATION", service)
        self.assertIn("evaluate_and_record_authority", service)
        self.assertIn("window.confirm", javascript)
        self.assertNotIn("<svg viewBox=", template)
        self.assertNotIn("window.prompt", javascript)
