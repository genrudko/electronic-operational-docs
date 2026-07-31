from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class GlobalThemeContractTests(SimpleTestCase):
    @staticmethod
    def source(relative_path: str) -> str:
        return (Path(settings.BASE_DIR) / relative_path).read_text(encoding="utf-8")

    def test_first_paint_bootstrap_precedes_theme_dependent_css(self):
        template = self.source("src/templates/base.html")
        bootstrap = template.index("const preference =")
        first_stylesheet = template.index('rel="stylesheet"')

        self.assertLess(bootstrap, first_stylesheet)
        self.assertIn('data-theme-preference="{{ ui_preferences.theme|lower }}"', template)
        self.assertIn('root.dataset.theme = dark ? "dark" : "light"', template)
        self.assertIn("root.style.colorScheme = dark ?", template)

    def test_single_global_controller_owns_runtime_resolution(self):
        controller = self.source("src/static/system/theme.js")
        workspace = self.source("src/static/operational_log/draft_workspace.js")

        self.assertIn("window.EODTheme = Object.freeze", controller)
        self.assertIn('new CustomEvent("eod:themechange"', controller)
        self.assertIn('systemTheme.addEventListener?.("change"', controller)
        self.assertIn('window.EODTheme?.apply(themePreference, "opj-workspace")', workspace)
        self.assertNotIn("function resolvedTheme", workspace)
        self.assertNotIn("localStorage", controller)

    def test_semantic_tokens_cover_light_dark_and_print(self):
        css = self.source("src/static/system/theme.css")

        for token in (
            "--theme-canvas",
            "--theme-surface",
            "--theme-border",
            "--theme-text",
            "--theme-control",
            "--theme-success",
            "--theme-focus",
            "--theme-overlay",
            "--theme-shadow",
            "--theme-surface-document",
            "--theme-table-header",
            "--theme-table-hover",
            "--theme-table-selected",
            "--theme-control-readonly",
            "--theme-control-disabled",
            "--theme-info-soft",
            "--theme-lifecycle-inactive",
            "--theme-lifecycle-current",
            "--theme-lifecycle-completed",
        ):
            self.assertIn(token, css)
        self.assertIn(':root[data-theme="dark"]', css)
        self.assertIn("@media print", css)
        self.assertIn("color-scheme: light !important", css)

    def test_shared_asset_is_loaded_after_feature_layers(self):
        template = self.source("src/templates/base.html")

        self.assertGreater(
            template.index("system/theme.css"),
            template.index("system/direction_a_shell_final.css"),
        )
        self.assertEqual(template.count("system/theme.css"), 1)
        self.assertEqual(template.count("system/theme.js"), 1)

    def test_feature_components_consume_shared_theme_tokens(self):
        for relative_path in (
            "src/static/equipment_defects/ux_foundation.css",
            "src/static/equipment_defects/ux_foundation_repair3.css",
            "src/static/equipment_defects/ux_foundation_repair3_picker.css",
            "src/static/equipment_defects/ux_foundation_repair5.css",
            "src/static/operational_log/opj_ux_001.css",
            "src/static/operational_log/opj_workspace_controls.css",
            "src/static/system/direction_a.css",
        ):
            css = self.source(relative_path)
            screen_css = css.split("@media print", maxsplit=1)[0]
            self.assertNotIn("background: #fff;", screen_css, relative_path)
            self.assertNotIn("background: #ffffff;", screen_css, relative_path)
        defect = self.source("src/static/equipment_defects/ux_foundation.css")
        opj = self.source("src/static/operational_log/opj_ux_001.css")
        self.assertNotIn("color-scheme: light", defect.split("@media print", 1)[0])
        self.assertIn("--ux-surface: var(--theme-surface)", defect)
        self.assertIn("--opj-editor-surface: var(--theme-surface-document)", opj)
        self.assertIn("--opj-header-surface: var(--theme-table-header)", opj)

    def test_theme_layer_does_not_recolour_generic_feature_elements(self):
        css = self.source("src/static/system/theme.css").split("@media print", 1)[0]
        for selector in ("[role=\"button\"]", "th, td", "strong {", ".active {"):
            self.assertNotIn(selector, css)

    def test_print_colours_are_isolated_from_screen_components(self):
        css = self.source("src/static/system/theme.css")
        screen, print_rules = css.split("@media print", 1)
        self.assertNotIn("!important", screen)
        self.assertIn("background: #fff !important", print_rules)
        self.assertIn("color: #000 !important", print_rules)
