from __future__ import annotations

import re
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]

OLD_UNCONDITIONAL_SCROLL_HANDLER = re.compile(
    r'window\.addEventListener\(\s*"scroll",\s*\(\)\s*=>\s*\{\s*'
    r'hideFloatingToolbar\(\);\s*'
    r'hideEntryKindMenu\(\);\s*'
    r'hideReferencePicker\(\);\s*'
    r'\},\s*true\s*\);',
    re.DOTALL,
)
GUARDED_REFERENCE_SCROLL_HANDLER = re.compile(
    r'window\.addEventListener\(\s*"scroll",\s*\(event\)\s*=>\s*\{\s*'
    r'hideFloatingToolbar\(\);\s*'
    r'const target = event\.target;\s*'
    r'if\s*\(\s*'
    r'target instanceof Element\s*'
    r'&&\s*target\.closest\("\[data-reference-picker\]"\)\s*'
    r'\)\s*\{\s*return;\s*\}\s*'
    r'hideEntryKindMenu\(\);\s*'
    r'hideReferencePicker\(\);\s*'
    r'\},\s*true\s*\);',
    re.DOTALL,
)


class ReferenceNavigationStaticContractTests(SimpleTestCase):
    def test_reference_picker_scroll_does_not_close_itself(self) -> None:
        editor = (
            ROOT / "static" / "operational_log" / "draft_editor.js"
        ).read_text(encoding="utf-8")
        self.assertIsNotNone(
            GUARDED_REFERENCE_SCROLL_HANDLER.search(editor),
        )
        self.assertIsNone(
            OLD_UNCONDITIONAL_SCROLL_HANDLER.search(editor),
        )

    def test_reference_navigation_extension_is_safe_and_loaded_last(
        self,
    ) -> None:
        navigation = (
            ROOT
            / "static"
            / "operational_log"
            / "draft_reference_navigation.js"
        ).read_text(encoding="utf-8")
        template = (
            ROOT
            / "templates"
            / "operational_log"
            / "shift_workspace.html"
        ).read_text(encoding="utf-8")
        workspace = (
            ROOT / "static" / "operational_log" / "draft_workspace.js"
        ).read_text(encoding="utf-8")

        self.assertNotIn("innerHTML", navigation)
        self.assertIn("draft-reference-preview", navigation)
        self.assertIn("/equipment/items/", navigation)
        self.assertIn("/documents/", navigation)
        self.assertIn('value: "/organization/"', navigation)
        self.assertIn('"eod:reveal-draft-reference"', navigation)
        self.assertIn('"eod:editor-overlay-state"', workspace)
        self.assertLess(
            template.index("operational_log/draft_workspace.js"),
            template.index("operational_log/draft_reference_navigation.js"),
        )
