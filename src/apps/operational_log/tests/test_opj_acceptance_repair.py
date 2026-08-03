from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, SimpleTestCase
from django.urls import reverse

from apps.equipment.models import EquipmentAsset

from ..editor import EDITOR_SCHEMA_VERSION
from ..opj_integrity import verify_registered_snapshot
from ..opj_lifecycle import register_draft, registered_entry_for_draft
from ..opj_print_presentation import build_print_journal_groups
from .base import OperationalLogTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalAcceptanceRepairTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.get(username="operator.demo")
        self.client.force_login(self.user)

    def available_drafts(self):
        return list(
            self.shift.draft_entries.filter(
                is_removed=False,
            )
            .exclude(content="")
            .order_by("event_at", "position", "pk")
        )

    def test_registration_batch_uses_chronology_not_post_order(self) -> None:
        first, second = self.available_drafts()[:2]

        response = self.client.post(
            reverse(
                "operational_log:register_drafts_batch",
                args=(self.journal.pk,),
            ),
            {"draft_ids": [str(second.public_id), str(first.public_id)]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            registered_entry_for_draft(first).sequence_number,
            registered_entry_for_draft(second).sequence_number,
        )

    def test_registration_rejects_chronological_gap(self) -> None:
        first, second = self.available_drafts()[:2]

        response = self.client.post(
            reverse(
                "operational_log:register_drafts_batch",
                args=(self.journal.pk,),
            ),
            {"draft_ids": [str(second.public_id)]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("хронологический разрыв", response.json()["message"])
        self.assertIsNone(registered_entry_for_draft(first))
        self.assertIsNone(registered_entry_for_draft(second))

    def test_integrity_uses_frozen_snapshot_not_current_directory_labels(self) -> None:
        entry = register_draft(
            draft=self.available_drafts()[0],
            actor=self.actor,
        )
        self.assertTrue(verify_registered_snapshot(entry))

        self.journal.workplace.name = "Новое отображаемое наименование рабочего места"
        self.journal.workplace.save(update_fields=("name",))
        entry.refresh_from_db()

        self.assertTrue(verify_registered_snapshot(entry))

        type(entry).objects.filter(pk=entry.pk).update(content="Подмена содержания")
        entry.refresh_from_db()
        with self.assertRaises(ValidationError):
            verify_registered_snapshot(entry)

    def test_registered_reference_is_a_real_link(self) -> None:
        equipment = EquipmentAsset.objects.filter(
            organization=self.organization,
        ).first()
        self.assertIsNotNone(equipment)
        draft = self.available_drafts()[0]
        draft.content = f"Проверено {equipment.code}"
        draft.editor_payload = {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "entry_kind": "normal",
            "annotations": [],
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {"text": "Проверено ", "marks": []},
                        {
                            "text": equipment.code,
                            "marks": [],
                            "reference": {
                                "kind": "equipment",
                                "label": equipment.code,
                                "reference": f"equipment:{equipment.public_id}",
                            },
                        },
                    ],
                }
            ],
        }
        draft.save(update_fields=("content", "editor_payload"))
        register_draft(draft=draft, actor=self.actor)

        response = self.client.get(
            reverse("operational_log:detail", args=(self.journal.pk,)),
            {"shift": str(self.shift.public_id)},
        )

        self.assertContains(
            response,
            f'href="/equipment/items/{equipment.public_id}/"',
        )
        self.assertContains(response, 'class="opj-reference-token"')

    def test_print_route_is_standalone_approved_journal_form(self) -> None:
        register_draft(
            draft=self.available_drafts()[0],
            actor=self.actor,
        )

        response = self.client.get(
            reverse("operational_log:print", args=(self.journal.pk,)),
            {"shift": str(self.shift.public_id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-approved-journal-print")
        self.assertContains(response, "Дата и время записи")
        self.assertContains(
            response,
            "Содержание записей в течение смены, подписи о приемке и сдаче смены",
        )
        self.assertContains(
            response,
            "Визы и замечания административно-технического персонала",
        )
        self.assertContains(response, "border-collapse: collapse")
        self.assertContains(response, "size: A4 landscape")
        self.assertNotContains(response, "direction-a-body")
        self.assertNotContains(response, "da-sidebar")
        self.assertNotContains(response, "opj-entry-footer")
        self.assertNotContains(response, ">Действия<")

    def test_print_rows_repeat_date_only_after_calendar_transition(self) -> None:
        first, second = self.available_drafts()[:2]
        first_entry = register_draft(draft=first, actor=self.actor)
        second_entry = register_draft(draft=second, actor=self.actor)

        groups = build_print_journal_groups(
            entries=[first_entry, second_entry],
            selected_shift=str(self.shift.public_id),
        )

        self.assertEqual(len(groups), 1)
        self.assertTrue(groups[0].rows[0]["show_date"])
        self.assertFalse(groups[0].rows[1]["show_date"])


class OperationalJournalAcceptanceSourceTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_print_is_separate_from_application_shell(self) -> None:
        detail = self.source("templates/operational_log/detail.html")
        printed = self.source("templates/operational_log/print.html")
        urls = self.source("apps/operational_log/urls.py")

        self.assertIn("operational_log:print", detail)
        self.assertNotIn("data-print-journal", detail)
        self.assertNotIn("{% extends", printed)
        self.assertIn("approved-journal-print-table", printed)
        self.assertIn("border-collapse: collapse", printed)
        self.assertIn("opj_lifecycle_acceptance.print_journal_view", urls)

    def test_selection_does_not_create_time_microcolumn(self) -> None:
        rows = self.source("templates/operational_log/_shift_workspace_rows.html")
        time_block = rows.split('<div class="draft-ledger-time">', 1)[1].split(
            '<div class="draft-ledger-content">',
            1,
        )[0]

        self.assertNotIn("data-draft-selection", time_block)
        self.assertIn("opj-row-selection-control", rows)
        self.assertIn(
            "data-selection-mode-toggle",
            self.source("templates/operational_log/shift_workspace.html"),
        )

    def test_clean_actions_use_viewport_floating_menu(self) -> None:
        javascript = self.source(
            "static/operational_log/opj_registered_actions_v2.js"
        )
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("document.body.append(menu)", javascript)
        self.assertIn("position: fixed !important", css)
        self.assertIn(
            'window.addEventListener("resize", closeActionMenus)',
            javascript,
        )
        self.assertIn("window.EODOPJNavigation?.allowOnce()", javascript)
        self.assertNotIn("window.confirm", javascript)
        self.assertNotIn("window.alert", javascript)

    def test_stale_registered_fragment_is_removed(self) -> None:
        shift = self.source("templates/operational_log/shift_workspace.html")

        self.assertIn("opj_shift_clean_summary", shift)
        self.assertIn("Чистовик текущей смены", shift)
        self.assertNotIn("Загрузка зарегистрированного журнала", shift)
        self.assertNotIn("data-opj-registered-context", shift)
