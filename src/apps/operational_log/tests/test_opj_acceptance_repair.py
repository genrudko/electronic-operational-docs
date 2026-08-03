from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import Client, SimpleTestCase
from django.urls import reverse

from apps.equipment.models import EquipmentAsset

from ..editor import EDITOR_SCHEMA_VERSION
from ..opj_integrity import verify_registered_snapshot
from ..opj_lifecycle import register_draft, registered_entry_for_draft
from ..opj_presentation import build_clean_journal_groups
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
            self.shift.draft_entries.filter(is_removed=False)
            .exclude(content="")
            .order_by("event_at", "position", "pk")
        )

    def test_registration_batch_uses_chronology_not_post_order(self) -> None:
        first, second = self.available_drafts()[:2]

        response = self.client.post(
            reverse("operational_log:register_drafts_batch", args=(self.journal.pk,)),
            {"draft_ids": [str(second.public_id), str(first.public_id)]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            registered_entry_for_draft(first).sequence_number,
            registered_entry_for_draft(second).sequence_number,
        )

    def test_late_registration_receives_chronological_display_number(self) -> None:
        first, second = self.available_drafts()[:2]

        late_response = self.client.post(
            reverse("operational_log:register_drafts_batch", args=(self.journal.pk,)),
            {"draft_ids": [str(second.public_id)]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        early_response = self.client.post(
            reverse("operational_log:register_drafts_batch", args=(self.journal.pk,)),
            {"draft_ids": [str(first.public_id)]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(late_response.status_code, 200)
        self.assertEqual(early_response.status_code, 200)
        early_entry = registered_entry_for_draft(first)
        late_entry = registered_entry_for_draft(second)
        self.assertGreater(early_entry.sequence_number, late_entry.sequence_number)

        groups = build_clean_journal_groups(
            entries=list(self.journal.entries.order_by("sequence_number")),
            selected_shift=str(self.shift.public_id),
        )
        displayed = {
            row["entry"].pk: row["journal_number"]
            for row in groups[0].rows
        }
        self.assertLess(displayed[early_entry.pk], displayed[late_entry.pk])
        numbers = sorted(displayed.values())
        self.assertEqual(numbers, list(range(numbers[0], numbers[0] + 2)))

    def test_integrity_uses_frozen_snapshot_not_current_directory_labels(self) -> None:
        entry = register_draft(draft=self.available_drafts()[0], actor=self.actor)
        self.assertTrue(verify_registered_snapshot(entry))

        self.journal.workplace.name = "Новое отображаемое наименование рабочего места"
        self.journal.workplace.save(update_fields=("name",))
        entry.refresh_from_db()
        self.assertTrue(verify_registered_snapshot(entry))

        table = entry._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE "{table}" SET content = %s WHERE id = %s',
                ["Подмена содержания", entry.pk],
            )
        entry.refresh_from_db()
        with self.assertRaises(ValidationError):
            verify_registered_snapshot(entry)

    def test_registered_reference_opens_preview_before_target(self) -> None:
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

        self.assertContains(response, "data-opj-reference-token")
        self.assertContains(
            response,
            f'data-reference-value="equipment:{equipment.public_id}"',
        )
        self.assertContains(
            response,
            f'data-reference-url="/equipment/items/{equipment.public_id}/"',
        )
        self.assertContains(response, 'id="opj-semantic-reference-catalog"')
        self.assertNotContains(
            response,
            f'<a class="opj-reference-token" href="/equipment/items/{equipment.public_id}/"',
        )

    def test_print_route_is_standalone_coloured_approved_journal_form(self) -> None:
        register_draft(draft=self.available_drafts()[0], actor=self.actor)

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
        self.assertContains(response, "print-color-adjust: exact")
        self.assertContains(response, "border: 0.55mm solid #c7352b")
        self.assertContains(response, ".is-text-red { color: #c7352b; }")
        self.assertContains(response, ".is-text-blue { color: #1269aa; }")
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
        self.assertEqual(
            [row["journal_number"] for row in groups[0].rows],
            [1, 2],
        )


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

    def test_clean_actions_use_dedicated_viewport_controller(self) -> None:
        javascript = self.source("static/operational_log/opj_clean_journal.js")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )
        detail = self.source("templates/operational_log/detail.html")

        self.assertIn("source.cloneNode(true)", javascript)
        self.assertIn("document.body.append(actionPortal)", javascript)
        self.assertIn("position: fixed !important", css)
        self.assertIn('window.addEventListener("resize", closeTransientOverlays)', javascript)
        self.assertIn("data-opj-reference-token", javascript)
        self.assertIn("opj_clean_journal.js", detail)
        self.assertNotIn("opj_registered_actions_v2.js", detail)
        self.assertNotIn("window.confirm", javascript)
        self.assertNotIn("window.alert", javascript)

    def test_stale_registered_fragment_is_removed(self) -> None:
        shift = self.source("templates/operational_log/shift_workspace.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )
        javascript = self.source("static/operational_log/opj_clean_journal.js")

        self.assertIn("opj_shift_clean_summary", shift)
        self.assertIn("Чистовик текущей смены", shift)
        self.assertNotIn("Загрузка зарегистрированного журнала", shift)
        self.assertNotIn("data-opj-registered-context", shift)
        self.assertIn("[data-opj-registered-context]", css)
        self.assertIn("node.remove()", javascript)

    def test_marker_contract_keeps_cross_and_compact_count(self) -> None:
        marker = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("opj-normative-marker", marker)
        self.assertIn("draft-normative-marker-cross", marker)
        self.assertIn("opj-marker-count", marker)
        self.assertIn("is-pz_remove", css)
        self.assertIn("is-zn_off", css)
        self.assertIn("max-height: 96px", css)

    def test_clean_table_does_not_reuse_generic_da_table_borders(self) -> None:
        detail = self.source("templates/operational_log/detail.html")

        self.assertIn('class="approved-journal-table"', detail)
        self.assertNotIn('class="approved-journal-table da-table"', detail)
        self.assertNotIn('class="approved-journal-table-wrap da-table-wrap"', detail)
