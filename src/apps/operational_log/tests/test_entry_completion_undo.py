from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from .base import OperationalLogTestCase


class DraftEntryCompletionUndoTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.get(
            username="operator.demo"
        )
        self.client.force_login(self.user)

    def test_ajax_remove_and_restore_preserve_position(self) -> None:
        entry = (
            self.shift.draft_entries.filter(is_removed=False)
            .order_by("position", "pk")
            .first()
        )
        original_position = entry.position

        remove_response = self.client.post(
            reverse(
                "operational_log:remove_draft",
                args=(self.journal.pk, entry.public_id),
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(remove_response.status_code, 200)
        self.assertTrue(remove_response.json()["ok"])
        self.assertTrue(remove_response.json()["is_removed"])
        entry.refresh_from_db()
        self.assertTrue(entry.is_removed)
        self.assertEqual(entry.position, original_position)

        restore_response = self.client.post(
            reverse(
                "operational_log:restore_draft",
                args=(self.journal.pk, entry.public_id),
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(restore_response.status_code, 200)
        self.assertTrue(restore_response.json()["ok"])
        self.assertFalse(restore_response.json()["is_removed"])
        entry.refresh_from_db()
        self.assertFalse(entry.is_removed)
        self.assertEqual(entry.position, original_position)

    def test_workspace_exposes_completion_undo_and_clear_actions(self) -> None:
        response = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        self.assertEqual(response.status_code, 200)
        for marker in (
            "Ctrl+Enter — сохранить и завершить",
            "data-inline-undo",
            "data-remove-draft",
            "data-restore-url",
            "draft-floating-kind-trigger",
            "Сохранено ·",
            "Запись №",
            "Версия&nbsp;",
            "?v=01134",
        ):
            self.assertContains(response, marker)
