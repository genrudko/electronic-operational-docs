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
