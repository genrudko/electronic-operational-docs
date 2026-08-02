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
    ACTION_CANCEL,
    ACTION_COMMUNICATION,
    ACTION_CORRECT,
    ACTION_REGISTER,
    TYPE_CANCELLATION,
    TYPE_COMMUNICATION,
    TYPE_CORRECTION,
    TYPE_ENTRY,
    cancel_entry,
    correct_entry,
    effective_state,
    entry_lifecycle_context,
    record_communication,
    register_draft,
    registered_entry_for_draft,
)
from .base import OperationalLogTestCase

ROOT = Path(__file__).resolve().parents[3]
ACTION_CODES = (
    ACTION_REGISTER,
    ACTION_CORRECT,
    ACTION_CANCEL,
    ACTION_COMMUNICATION,
)


class OperationalJournalLifecycleTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.get(username="operator.demo")
        self.assertEqual(
            OperationalAuthorityGrant.objects.filter(
                employee=self.actor,
                action_code__in=ACTION_CODES,
                scope_kind="WORKPLACE",
                scope_reference=str(self.journal.workplace_id),
                is_active=True,
            ).count(),
            len(ACTION_CODES),
        )

    def nonempty_draft(self):
        draft = (
            self.shift.draft_entries.filter(is_removed=False)
            .exclude(content="")
            .first()
        )
        self.assertIsNotNone(draft)
        return draft

    def test_registration_keeps_traceable_row_and_prevents_duplicate(self) -> None:
        draft = self.nonempty_draft()
        original_content = draft.content

        registered = register_draft(draft=draft, actor=self.actor)

        draft.refresh_from_db()
        self.assertFalse(draft.is_removed)
        self.assertEqual(draft.content, original_content)
        self.assertEqual(registered.type_code, TYPE_ENTRY)
        self.assertEqual(
            registered.typed_payload["draft"]["public_id"],
            str(draft.public_id),
        )
        self.assertEqual(
            registered_entry_for_draft(draft).pk,
            registered.pk,
        )
        with self.assertRaisesMessage(
            ValidationError,
            "уже зарегистрирована в чистовике",
        ):
            register_draft(draft=draft, actor=self.actor)

    def test_correction_cancellation_and_communication_are_clean_journal_entries(
        self,
    ) -> None:
        original = register_draft(
            draft=self.nonempty_draft(),
            actor=self.actor,
        )
        original_content = original.content
        original_digest = original.digest

        correction = correct_entry(
            entry=original,
            actor=self.actor,
            replacement_content=f"{original_content} Уточнено после проверки.",
            reason="Уточнено диспетчерское наименование.",
        )
        self.assertEqual(correction.type_code, TYPE_CORRECTION)
        self.assertIn("Следует читать", correction.content)

        communication = record_communication(
            entry=original,
            actor=self.actor,
            outcome_kind="RECEIVED_CONFIRMATION",
            counterpart="Диспетчер СКДУ",
            channel="PHONE",
            content="Подтверждено уточнение зарегистрированной записи.",
        )
        self.assertEqual(communication.type_code, TYPE_COMMUNICATION)
        self.assertEqual(
            communication.typed_payload["kind"],
            "COMMUNICATION_OUTCOME",
        )
        self.assertNotIn("counterpart_organization", communication.typed_payload)

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

        context = entry_lifecycle_context(original)
        self.assertFalse(context.is_child)
        self.assertEqual(len(context.lifecycle_entries), 2)
        self.assertEqual(len(context.communications), 1)
        child_context = entry_lifecycle_context(correction)
        self.assertTrue(child_context.is_child)
        self.assertEqual(child_context.linked_original.pk, original.pk)

        with self.assertRaises(ValidationError):
            correct_entry(
                entry=original,
                actor=self.actor,
                replacement_content="Недопустимое исправление после отмены.",
                reason="Не должно создаваться.",
            )
        with self.assertRaises(ValidationError):
            record_communication(
                entry=communication,
                actor=self.actor,
                outcome_kind="SENT_MESSAGE",
                counterpart="Вложенный участник",
                channel="",
                content="Дочерняя запись не может стать корнем истории.",
            )

    def test_deny_records_evaluation_but_does_not_create_subject_fact(self) -> None:
        denied_actor = Employee.objects.select_related(
            "organization", "position", "division", "workplace"
        ).get(organization=self.organization, personnel_number="DEMO-013")
        OperationalAuthorityGrant.objects.filter(
            employee=denied_actor,
            action_code=ACTION_COMMUNICATION,
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
                outcome_kind="RECEIVED_COMMAND",
                counterpart="Проверочный участник",
                channel="RADIO",
                content="Эта запись не должна быть создана.",
            )

        self.assertEqual(self.journal.entries.count(), before)
        self.assertTrue(
            denied_actor.authority_evaluations.filter(
                action_code=ACTION_COMMUNICATION,
                decision="DENY",
            ).exists()
        )

    def test_real_routes_keep_actions_inside_draft_and_clean_journal(self) -> None:
        self.client.force_login(self.user)
        draft = self.nonempty_draft()

        registration = self.client.post(
            reverse(
                "operational_log:register_draft_lifecycle",
                args=(self.journal.pk, draft.public_id),
            )
        )
        self.assertEqual(registration.status_code, 302)
        self.assertIn(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            ),
            registration.url,
        )
        self.assertIn(f"#draft-{draft.public_id}", registration.url)
        draft.refresh_from_db()
        self.assertFalse(draft.is_removed)
        registered = registered_entry_for_draft(draft)
        self.assertIsNotNone(registered)

        workspace = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        self.assertContains(workspace, "Чистовик · №")
        self.assertContains(workspace, "Открыть в чистовике")
        self.assertContains(workspace, "data-registered-draft")
        self.assertNotContains(workspace, "ЖИЗНЕННЫЙ ЦИКЛ")

        blocked_save = self.client.post(
            reverse(
                "operational_log:autosave_draft",
                args=(self.journal.pk, draft.public_id),
            ),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(blocked_save.status_code, 409)
        self.assertTrue(blocked_save.json()["registered"])
        blocked_remove = self.client.post(
            reverse(
                "operational_log:remove_draft",
                args=(self.journal.pk, draft.public_id),
            )
        )
        self.assertEqual(blocked_remove.status_code, 302)
        draft.refresh_from_db()
        self.assertFalse(draft.is_removed)

        clean_journal = self.client.get(
            reverse(
                "operational_log:detail",
                args=(self.journal.pk,),
            )
        )
        self.assertContains(clean_journal, "Действия с записью")
        self.assertContains(clean_journal, "Исправить запись")
        self.assertContains(clean_journal, "Результат переговоров")
        self.assertContains(clean_journal, "opj_registered_actions.css")
        self.assertNotContains(clean_journal, "ALLOW / VERIFY / DENY")
        self.assertNotContains(clean_journal, "APPEND-ONLY ИСТОРИЯ")

        legacy = self.client.get(
            reverse(
                "operational_log:entry_lifecycle",
                args=(self.journal.pk, registered.sequence_number),
            )
        )
        self.assertEqual(legacy.status_code, 302)
        self.assertIn(
            f"#entry-{registered.sequence_number}",
            legacy.url,
        )

    def test_clean_journal_forms_append_entries_and_return_to_source_row(self) -> None:
        self.client.force_login(self.user)
        original = register_draft(
            draft=self.nonempty_draft(),
            actor=self.actor,
        )

        correction = self.client.post(
            reverse(
                "operational_log:entry_correct",
                args=(self.journal.pk, original.sequence_number),
            ),
            {
                "replacement_content": "Исправленная редакция записи.",
                "reason": "Обнаружена описка.",
            },
        )
        self.assertEqual(correction.status_code, 302)
        self.assertIn(f"#entry-{original.sequence_number}", correction.url)
        correction_entry = self.journal.entries.order_by("-sequence_number").first()
        self.assertEqual(correction_entry.type_code, TYPE_CORRECTION)

        communication = self.client.post(
            reverse(
                "operational_log:entry_communication",
                args=(self.journal.pk, original.sequence_number),
            ),
            {
                "outcome_kind": "REPORTED_EXECUTION",
                "counterpart": "Диспетчер СКДУ",
                "channel": "DISPATCH",
                "content": "Сообщено об исполнении команды.",
            },
        )
        self.assertEqual(communication.status_code, 302)
        communication_entry = self.journal.entries.order_by("-sequence_number").first()
        self.assertEqual(communication_entry.type_code, TYPE_COMMUNICATION)

        page = self.client.get(
            reverse(
                "operational_log:detail",
                args=(self.journal.pk,),
            )
        )
        self.assertContains(page, "Показать действующую редакцию")
        self.assertContains(page, "Первоначальный текст сохранён")
        self.assertContains(page, f'href="#entry-{original.sequence_number}"')


class OperationalJournalLifecycleSourceContractTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_rejected_technical_page_and_global_layer_are_absent(self) -> None:
        self.assertFalse(
            (ROOT / "templates/operational_log/entry_lifecycle.html").exists()
        )
        self.assertFalse(
            (ROOT / "static/operational_log/opj_lifecycle_001.css").exists()
        )
        self.assertFalse(
            (ROOT / "static/operational_log/opj_lifecycle_001.js").exists()
        )
        shared_base = self.source("templates/shared/direction_a/base.html")
        self.assertNotIn("opj_lifecycle_001", shared_base)

    def test_accepted_opj_screens_own_the_lifecycle_controls(self) -> None:
        detail = self.source("templates/operational_log/detail.html")
        rows = self.source("templates/operational_log/_shift_workspace_rows.html")
        registered_row = self.source(
            "templates/operational_log/_shift_workspace_registered_row.html"
        )
        css = self.source("static/operational_log/opj_registered_actions.css")
        javascript = self.source(
            "static/operational_log/opj_registered_actions.js"
        )
        service = self.source("apps/operational_log/opj_lifecycle.py")

        for marker in (
            "Исправить запись",
            "Отменить запись",
            "Результат переговоров",
            "Первоначальный текст сохранён",
        ):
            self.assertIn(marker, detail)
        self.assertIn("В чистовик", rows)
        self.assertIn("data-register-draft", rows)
        self.assertIn("Чистовик · №", registered_row)
        self.assertIn("data-registered-draft", registered_row)
        self.assertIn("font-family: var(--font-interface", css)
        self.assertNotIn("font-family: Arial", css)
        self.assertNotIn("#", css)
        self.assertIn("persistDraft(form)", javascript)
        self.assertIn("window.confirm", javascript)
        self.assertNotIn("remove_draft_entry", service)
        self.assertIn("COMMUNICATION_OUTCOME", service)
        self.assertNotIn("counterpart_organization", service)
