from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from ..models import OperationalJournal, OperationalShift, ShiftStatus
from .base import OperationalLogTestCase


class OperationalShiftViewTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.get(
            username="operator.demo"
        )

    def test_shift_workspace_requires_authentication(self) -> None:
        response = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_detail_links_to_open_shift_workspace(self) -> None:
        self.client.force_login(self.user)
        detail = self.client.get(
            reverse(
                "operational_log:detail",
                args=(self.journal.pk,),
            )
        )
        self.assertContains(detail, "Рабочая смена")
        workspace = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        self.assertEqual(workspace.status_code, 200)
        for marker in (
            "РАБОЧИЙ ЧЕРНОВИК СМЕНЫ",
            "Автосохранение",
            "Одна страница",
            "Разворот",
            "Поиск по записям",
            "data-quick-time",
            "draft_workspace.js",
        ):
            self.assertContains(workspace, marker)
        self.assertNotContains(workspace, "Сохранить сейчас")
        self.assertNotContains(workspace, "↑ Выше")
        self.assertNotContains(workspace, "↓ Ниже")

    def test_open_shift_for_journal_without_active_shift(self) -> None:
        journal = OperationalJournal.objects.create(
            organization=self.organization,
            workplace=self.workplace,
            code="secondary-shift-log",
            title="Второй оперативный журнал",
        )
        start_at, end_at = self.planned_period()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "operational_log:open_shift",
                args=(journal.pk,),
            ),
            {
                "planned_start_at": timezone.localtime(
                    start_at
                ).strftime("%Y-%m-%dT%H:%M"),
                "planned_end_at": timezone.localtime(
                    end_at
                ).strftime("%Y-%m-%dT%H:%M"),
            },
        )
        self.assertRedirects(
            response,
            reverse(
                "operational_log:shift_workspace",
                args=(journal.pk,),
            ),
        )
        shift = OperationalShift.objects.get(
            journal=journal,
            status=ShiftStatus.OPEN,
        )
        self.assertEqual(shift.members.count(), 1)
        self.assertTrue(shift.members.get().is_shift_lead)

    def test_add_draft_creates_blank_versioned_entry(self) -> None:
        self.client.force_login(self.user)
        before = self.shift.draft_entries.count()
        response = self.client.post(
            reverse(
                "operational_log:add_draft",
                args=(self.journal.pk,),
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.shift.draft_entries.count(),
            before + 1,
        )
        entry = self.shift.draft_entries.order_by("-pk").first()
        self.assertEqual(entry.content, "")
        self.assertEqual(entry.version, 1)
        self.assertEqual(entry.revisions.count(), 1)

    def test_autosave_updates_draft_and_returns_version(self) -> None:
        self.client.force_login(self.user)
        entry = self.shift.draft_entries.filter(
            is_removed=False
        ).first()
        response = self.client.post(
            reverse(
                "operational_log:autosave_draft",
                args=(self.journal.pk, entry.public_id),
            ),
            {
                "public_id": str(entry.public_id),
                "expected_version": entry.version,
                "event_at": timezone.localtime(
                    entry.event_at
                ).strftime("%Y-%m-%dT%H:%M"),
                "content": "Текст сохранён через автосохранение",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["version"], entry.version + 1)
        entry.refresh_from_db()
        self.assertEqual(
            entry.content,
            "Текст сохранён через автосохранение",
        )

    def test_autosave_returns_conflict_for_stale_version(self) -> None:
        self.client.force_login(self.user)
        entry = self.shift.draft_entries.filter(
            is_removed=False
        ).first()
        url = reverse(
            "operational_log:autosave_draft",
            args=(self.journal.pk, entry.public_id),
        )
        data = {
            "public_id": str(entry.public_id),
            "expected_version": entry.version,
            "event_at": timezone.localtime(
                entry.event_at
            ).strftime("%Y-%m-%dT%H:%M"),
            "content": "Первая сохранённая редакция",
        }
        self.assertEqual(self.client.post(url, data).status_code, 200)
        stale = self.client.post(
            url,
            {
                **data,
                "content": "Устаревшая редакция",
            },
        )
        self.assertEqual(stale.status_code, 409)
        self.assertTrue(stale.json()["conflict"])
        entry.refresh_from_db()
        self.assertEqual(
            entry.content,
            "Первая сохранённая редакция",
        )

    def test_move_remove_and_restore_endpoints(self) -> None:
        self.client.force_login(self.user)
        entries = list(
            self.shift.draft_entries.filter(
                is_removed=False
            ).order_by("position", "pk")
        )
        first, second = entries[:2]
        response = self.client.post(
            reverse(
                "operational_log:move_draft",
                args=(self.journal.pk, second.public_id),
            ),
            {"direction": "up"},
        )
        self.assertEqual(response.status_code, 302)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertLess(second.position, first.position)

        response = self.client.post(
            reverse(
                "operational_log:remove_draft",
                args=(self.journal.pk, second.public_id),
            )
        )
        self.assertEqual(response.status_code, 302)
        second.refresh_from_db()
        self.assertTrue(second.is_removed)

        response = self.client.post(
            reverse(
                "operational_log:restore_draft",
                args=(self.journal.pk, second.public_id),
            )
        )
        self.assertEqual(response.status_code, 302)
        second.refresh_from_db()
        self.assertFalse(second.is_removed)
