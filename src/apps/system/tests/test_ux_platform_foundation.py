from __future__ import annotations

from pathlib import Path
import re

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[4]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UxPlatformFoundationSourceContractTests(SimpleTestCase):
    def test_base_owns_one_application_shell(self) -> None:
        base = read("src/templates/base.html")
        wrapper = read("src/templates/shared/direction_a/base.html")

        self.assertEqual(base.count('class="da-shell"'), 1)
        self.assertNotIn('class="da-shell"', wrapper)
        self.assertIn('{% include "shared/direction_a/_sidebar.html" %}', base)
        self.assertIn('{% include "shared/direction_a/_topbar.html" %}', base)
        self.assertNotIn("equipment_defect_tags", base)
        self.assertNotIn("direction_a_shell_final.css", base)
        self.assertFalse(
            (ROOT / "src/static/system/direction_a_shell_final.css").exists()
        )

    def test_specialised_opj_assets_are_scoped_to_opj_namespace(self) -> None:
        base = read("src/templates/base.html")
        marker = "request.resolver_match.namespace == 'operational_log'"

        self.assertGreaterEqual(base.count(marker), 2)
        self.assertEqual(base.count("operational_log/opj_ux_001.css"), 1)
        self.assertEqual(base.count("operational_log/opj_ux_001.js"), 1)
        self.assertTrue(
            (
                ROOT
                / "src/static/operational_log/opj_workspace_controls.css"
            ).exists()
        )
        self.assertTrue(
            (
                ROOT
                / "src/static/operational_log/opj_workspace_controls.js"
            ).exists()
        )

    def test_defect_forms_consume_shared_shell(self) -> None:
        for path in (
            "src/templates/equipment_defects/registration_form.html",
            "src/templates/equipment_defects/action_form.html",
        ):
            template = read(path)
            self.assertIn('{% extends "shared/direction_a/base.html" %}', template)
            self.assertNotIn("defect-da-shell", template)
            self.assertNotIn("_direction_a_sidebar.html", template)
            self.assertNotIn("_direction_a_topbar.html", template)

        self.assertFalse(
            (ROOT / "src/templates/equipment_defects/_direction_a_sidebar.html").exists()
        )
        self.assertFalse(
            (ROOT / "src/templates/equipment_defects/_direction_a_topbar.html").exists()
        )

    def test_theme_resolves_before_first_theme_dependent_stylesheet(self) -> None:
        base = read("src/templates/base.html")
        theme_resolution = base.index("root.dataset.theme = dark ? \"dark\" : \"light\"")
        first_stylesheet = base.index('rel="stylesheet"')

        self.assertLess(theme_resolution, first_stylesheet)
        self.assertIn(
            'data-theme-preference="{{ ui_preferences.theme|lower }}"',
            base,
        )
        self.assertIn('<meta name="color-scheme" content="light dark">', base)

    def test_theme_is_single_semantic_token_owner(self) -> None:
        theme = read("src/static/system/theme.css")
        platform = read("src/static/system/ux_platform.css")

        required_tokens = (
            "--theme-canvas",
            "--theme-surface",
            "--theme-text",
            "--theme-border",
            "--theme-primary",
            "--theme-focus",
            "--theme-font-ui",
            "--theme-font-mono",
            "--theme-space-4",
            "--theme-radius-md",
            "--theme-control-height-md",
            "--theme-z-modal",
        )
        for token in required_tokens:
            self.assertIn(token, theme)
            self.assertIn("--theme-", platform)

        self.assertIn("sole semantic token owner", theme)
        self.assertNotIn(":root {", platform)

    def test_platform_css_has_no_responsive_scale_hacks_or_feature_palette(self) -> None:
        platform = read("src/static/system/ux_platform.css")
        compact = re.sub(r"\s+", " ", platform.lower())

        self.assertNotIn("zoom:", compact)
        self.assertNotIn("transform: scale(", compact)
        colors = set(re.findall(r"#[0-9a-fA-F]{3,8}\b", platform))
        self.assertLessEqual(colors, {"#fff", "#000"})
        self.assertIn("@media (max-width: 980px)", platform)
        self.assertIn("@media (max-width: 700px)", platform)
        self.assertIn("prefers-reduced-motion", platform)

    def test_shared_interaction_owner_covers_keyboard_and_focus_return(self) -> None:
        script = read("src/static/system/direction_a.js")

        self.assertIn('event.key === "Escape"', script)
        self.assertIn('"ArrowLeft"', script)
        self.assertIn('"ArrowRight"', script)
        self.assertIn("focusOrigins", script)
        self.assertIn("showModal()", script)
        self.assertIn("data-ux-drawer", script)

    def test_navigation_projects_central_module_access_contract(self) -> None:
        tag = read("src/apps/system/templatetags/module_navigation.py")
        sidebar = read("src/templates/shared/direction_a/_sidebar.html")

        self.assertIn("decide_module_access", tag)
        self.assertIn("ModuleOperation.READ", tag)
        self.assertIn("EntryPointClass.NAVIGATION_UI", tag)
        self.assertIn("module_navigation_allowed", sidebar)
        self.assertIn('"OPJ" "CAP-OPJ-DEMO"', sidebar)
        self.assertIn('"DEFECT" "CAP-DEFECT-DEMO"', sidebar)
        self.assertIn('"WORKPLACE-DOCS" "CAP-WORKPLACE-DOCS-DEMO"', sidebar)
