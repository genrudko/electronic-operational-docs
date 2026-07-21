from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011343"


class ContextAwareEntityResolverRuntimeTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_longest_contextual_entity_resolution(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn("function personCompositeMatches", editor)
        self.assertIn("priority: 110", editor)
        self.assertIn("function resolveAutomaticMatches", editor)
        self.assertIn("match.start < current.end", editor)
        self.assertIn(
            "source.map((value) => normalizeSingleLine(value))",
            editor,
        )

    def test_equipment_designations_ignore_separators_and_leading_zeroes(
        self,
    ) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn("function equipmentTermPattern", editor)
        self.assertIn("0*${numeric}", editor)
        self.assertIn("№#\\-–—._/", editor)
        self.assertIn("function equipmentTermMatches", editor)

    def test_related_entries_are_refreshed_from_live_rows(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn("function refreshRelatedEntryCatalog", editor)
        self.assertIn("[data-draft-card][data-draft-id]", editor)
        self.assertIn("function relatedEntryTimeMatches", editor)
        self.assertIn("relatedEntryCueBefore", editor)
        self.assertIn("item.event_at < currentAt", editor)

    def test_simplified_time_is_user_scoped_and_safe(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        workspace = self.source("static/operational_log/draft_workspace.js")
        template = self.source("templates/operational_log/shift_workspace.html")
        model = self.source("apps/organizations/models.py")
        self.assertIn("data-simplified-time-toggle", template)
        self.assertIn("journal_simplified_time_input", model)
        self.assertIn("eod:simplified-time-setting", workspace)
        self.assertIn("function simplifiedTimeValue", editor)
        self.assertIn("numeric >= 1900 && numeric <= 2099", editor)
        self.assertIn("editableTextPositionBeforeCaret", editor)
        self.assertIn(f'const RUNTIME_REVISION = "{REVISION}";', editor)
