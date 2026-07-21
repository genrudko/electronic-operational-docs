from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011344"


class ReferenceNavigationRuntimeContractTests(SimpleTestCase):
    def test_picker_owns_wheel_and_prevents_scroll_chaining(self) -> None:
        editor = (
            ROOT / "static" / "operational_log" / "draft_editor.js"
        ).read_text(encoding="utf-8")

        self.assertIn("function handleReferencePickerWheel(event)", editor)
        self.assertIn("surface.scrollTop = Math.max(", editor)
        self.assertIn("event.preventDefault();", editor)
        self.assertIn("event.stopPropagation();", editor)
        self.assertIn("{passive: false},", editor)
        self.assertIn(
            "if (referencePicker && !referencePicker.hidden)",
            editor,
        )

    def test_entry_kind_preserves_viewport(self) -> None:
        editor = (
            ROOT / "static" / "operational_log" / "draft_editor.js"
        ).read_text(encoding="utf-8")

        self.assertIn("function captureEntryKindViewport", editor)
        self.assertIn("function restoreEntryKindViewport", editor)
        self.assertIn("restoreEntryKindViewport(controller);", editor)
        self.assertIn(
            "controller.editor.focus({preventScroll: true});",
            editor,
        )

    def test_reference_identity_uses_serialized_token_attribute(self) -> None:
        navigation = (
            ROOT
            / "static"
            / "operational_log"
            / "draft_reference_navigation.js"
        ).read_text(encoding="utf-8")

        self.assertIn("token.dataset.referenceValue", navigation)
        self.assertIn(
            'token.getAttribute("data-reference-value")',
            navigation,
        )
        self.assertNotIn("innerHTML", navigation)

    def test_runtime_assets_are_cache_versioned(self) -> None:
        template = (
            ROOT
            / "templates"
            / "operational_log"
            / "shift_workspace.html"
        ).read_text(encoding="utf-8")
        base_template = (ROOT / "templates" / "base.html").read_text(
            encoding="utf-8"
        )

        for asset in (
            "draft_editor.js",
            "draft_workspace.js",
            "draft_reference_navigation.js",
        ):
            self.assertIn(
                f"operational_log/{asset}' %}}?v={REVISION}",
                template,
            )
        self.assertIn(
            f"system/app.css' %}}?v={REVISION}",
            base_template,
        )
