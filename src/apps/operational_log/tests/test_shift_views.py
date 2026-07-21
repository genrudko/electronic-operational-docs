from datetime import timedelta

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
        for marker in (
            "id_journal_font_size",
            "id_journal_time_font_size",
            "id_journal_date_font_size",
            "id_journal_table_header_font_size",
            "id_journal_title_font_size",
            "journal-entry-size-normal",
            "journal-time-size-normal",
            "journal-date-size-normal",
            "journal-table-header-size-normal",
            "journal-title-size-normal",
        ):
            self.assertContains(detail, marker)
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
            "Дата и время записи",
            "Визы и замечания",
            "data-page-input",
            "data-page-buttons",
            "data-view-drawer",
            "data-column-resizer",
            "data-records-preset",
            "data-records-custom",
            "data-add-draft-form",
            "data-default-entry-date",
            "data-default-entry-date-iso",
            "data-shift-start",
            "data-shift-end",
            "screen-journal-theme",
            "data-apply-custom-records",
            "data-theme-choice",
            "data-page-width-choice",
            "data-initial-journal-entry-size",
            "data-initial-journal-time-size",
            "data-initial-journal-date-size",
            "data-initial-journal-table-header-size",
            "data-initial-journal-title-size",
            "data-typography-panel",
            "data-typography-preset",
            "data-typography-target",
            "data-typography-size",
            "data-quick-display-form",
            "stable-page-layout-workspace",
            "data-quick-time",
            "data-editor-fallback",
            "data-editor-payload",
            "data-rich-editor-host",
            "data-editor-ribbon",
            "data-editor-ribbon-status",
            "data-editor-floating-toolbar",
            "draft-editor-payload-field",
            "draft_editor.js",
            "draft_workspace.js",
        ):
            self.assertContains(workspace, marker)
        self.assertNotContains(workspace, "Сохранить сейчас")
        self.assertNotContains(workspace, "↑ Выше")
        self.assertNotContains(workspace, "↓ Ниже")
        self.assertNotContains(workspace, 'data-page-size="8"')
        self.assertNotContains(workspace, 'type="range"')
        self.assertNotContains(workspace, "draft-workspace-layout")
        self.assertContains(workspace, "15 записей")
        self.assertContains(workspace, "+ Запись")
        self.assertContains(
            workspace,
            "ЗАПИСЕЙ НА СТРАНИЦЕ",
        )
        self.assertNotContains(workspace, "ШИРИНА ГРАФ")
        self.assertNotContains(
            workspace,
            "data-column-time-number",
        )
        self.assertNotContains(workspace, "data-measure-page")
        self.assertNotContains(workspace, "data-view-drawer-backdrop")
        self.assertNotContains(workspace, "hybrid-paper-theme")

        quick_settings = self.client.post(
            reverse(
                "operational_log:update_display",
                args=(self.journal.pk,),
            ),
            {
                "workspace_quick_settings": "1",
                "theme": "LIGHT",
                "journal_width": "FULL",
                "journal_font_size": "LARGE",
                "journal_time_font_size": "SMALL",
                "journal_date_font_size": "EXTRA_LARGE",
                "journal_table_header_font_size": "LARGE",
                "journal_title_font_size": "EXTRA_LARGE",
                "journal_simplified_time_input": "1",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(quick_settings.status_code, 200)
        self.assertTrue(quick_settings.json()["ok"])
        preferences = self.user.interface_preference
        preferences.refresh_from_db()
        self.assertEqual(preferences.theme, "LIGHT")
        self.assertEqual(preferences.journal_width, "FULL")
        self.assertEqual(preferences.journal_font_size, "LARGE")
        self.assertEqual(preferences.journal_time_font_size, "SMALL")
        self.assertEqual(
            preferences.journal_date_font_size,
            "EXTRA_LARGE",
        )
        self.assertEqual(
            preferences.journal_table_header_font_size,
            "LARGE",
        )
        self.assertEqual(
            preferences.journal_title_font_size,
            "EXTRA_LARGE",
        )
        self.assertTrue(preferences.journal_simplified_time_input)
        self.assertTrue(
            quick_settings.json()["journal_simplified_time_input"]
        )

        detail_after = self.client.get(
            reverse(
                "operational_log:detail",
                args=(self.journal.pk,),
            )
        )
        for marker in (
            "journal-entry-size-large",
            "journal-time-size-small",
            "journal-date-size-extra_large",
            "journal-table-header-size-large",
            "journal-title-size-extra_large",
        ):
            self.assertContains(detail_after, marker)

    def test_quick_typography_rejects_unknown_size(self) -> None:
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "operational_log:update_display",
                args=(self.journal.pk,),
            ),
            {
                "workspace_quick_settings": "1",
                "journal_time_font_size": "GIANT",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertIn("времени", response.json()["message"])

        preferences = self.user.interface_preference
        preferences.refresh_from_db()
        self.assertEqual(
            preferences.journal_time_font_size,
            "NORMAL",
        )

    def test_workspace_uses_word_like_editor_controls(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        for marker in (
            "Мини-лента редактора записи",
            "РЕДАКТОР ЗАПИСИ",
            "Щёлкните по тексту записи",
            'data-editor-ribbon-status',
            'data-editor-floating-toolbar',
            "Форматирование выделенного текста",
            "Шрифт",
            "Абзац",
            "История",
            "Тип записи",
            "Связь",
        ):
            self.assertIn(marker, html)
        self.assertEqual(
            html.count('data-editor-command="bold"'),
            2,
        )
        self.assertEqual(
            html.count('data-editor-command="underline"'),
            2,
        )
        self.assertEqual(
            html.count('data-editor-command="undo"'),
            1,
        )
        self.assertNotIn(
            'aria-label="Редактор и действия с записью"',
            html,
        )
        self.assertIn(
            'aria-label="Действия с записью"',
            html,
        )

    def test_editor_payload_is_a_non_visual_form_field(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        expected = self.shift.draft_entries.filter(
            is_removed=False
        ).count()
        self.assertEqual(
            html.count('class="draft-editor-payload-field"'),
            expected,
        )
        for occurrence in html.split(
            'class="draft-editor-payload-field"'
        )[1:]:
            field_head = occurrence[:260]
            self.assertIn("data-editor-payload", field_head)
            self.assertIn("hidden", field_head)
            self.assertIn('aria-hidden="true"', field_head)
            self.assertIn('tabindex="-1"', field_head)

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
        self.assertGreaterEqual(
            entry.event_at,
            self.shift.planned_start_at,
        )
        self.assertLessEqual(
            entry.event_at,
            self.shift.planned_end_at,
        )

        target_event_at = timezone.localtime(
            self.shift.planned_start_at
        ).replace(
            hour=17,
            minute=20,
            second=0,
            microsecond=0,
        )
        response = self.client.post(
            reverse(
                "operational_log:add_draft",
                args=(self.journal.pk,),
            ),
            {
                "event_at": target_event_at.strftime(
                    "%Y-%m-%dT%H:%M"
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        dated_entry = self.shift.draft_entries.order_by(
            "-pk"
        ).first()
        self.assertEqual(
            timezone.localtime(dated_entry.event_at),
            target_event_at,
        )
        self.assertEqual(dated_entry.version, 1)
        self.assertEqual(dated_entry.revisions.count(), 1)

        response = self.client.post(
            reverse(
                "operational_log:add_draft",
                args=(self.journal.pk,),
            ),
            {"event_at": "not-a-date"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.shift.draft_entries.count(),
            before + 2,
        )

        outside_event_at = (
            self.shift.planned_end_at + timedelta(minutes=1)
        )
        response = self.client.post(
            reverse(
                "operational_log:add_draft",
                args=(self.journal.pk,),
            ),
            {
                "event_at": timezone.localtime(
                    outside_event_at
                ).strftime("%Y-%m-%dT%H:%M"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "интервал смены",
            status_code=400,
        )
        self.assertEqual(
            self.shift.draft_entries.count(),
            before + 2,
        )

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

        saved_event_at = entry.event_at
        outside_event_at = (
            self.shift.planned_end_at + timedelta(minutes=1)
        )
        outside = self.client.post(
            reverse(
                "operational_log:autosave_draft",
                args=(self.journal.pk, entry.public_id),
            ),
            {
                "public_id": str(entry.public_id),
                "expected_version": payload["version"],
                "event_at": timezone.localtime(
                    outside_event_at
                ).strftime("%Y-%m-%dT%H:%M"),
                "content": entry.content,
            },
        )
        self.assertEqual(outside.status_code, 400)
        self.assertIn("event_at", outside.json()["errors"])
        entry.refresh_from_db()
        self.assertEqual(entry.event_at, saved_event_at)
        self.assertEqual(entry.version, payload["version"])

        ordered_entries = list(
            self.shift.draft_entries.filter(is_removed=False)
            .order_by("pk")[:2]
        )
        earlier, later = ordered_entries
        earlier.event_at = self.shift.planned_start_at + timedelta(minutes=1)
        earlier.position = 99
        later.event_at = self.shift.planned_start_at + timedelta(minutes=2)
        later.position = 1
        self.shift.draft_entries.bulk_update(
            (earlier, later),
            ("event_at", "position"),
        )
        workspace = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        html = workspace.content.decode("utf-8")
        self.assertLess(
            html.index(str(earlier.public_id)),
            html.index(str(later.public_id)),
        )

    def test_autosave_rejects_unknown_editor_mark(self) -> None:
        self.client.force_login(self.user)
        entry = self.shift.draft_entries.filter(
            is_removed=False
        ).first()
        before_version = entry.version
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
                "content": entry.content,
                "editor_schema_version": (
                    "operational-draft-editor.v1"
                ),
                "editor_payload": (
                    '{"schema_version":'
                    '"operational-draft-editor.v1",'
                    '"blocks":[{"type":"paragraph",'
                    '"segments":[{"text":"x",'
                    '"marks":["html"]}]}]}'
                ),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("editor_payload", response.json()["errors"])
        entry.refresh_from_db()
        self.assertEqual(entry.version, before_version)

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
