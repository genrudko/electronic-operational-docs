import re
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

        theme = template.index("system/theme.css")
        compat = template.index("system/ux_platform_compat.css")
        platform = template.index("system/ux_platform.css")
        opj = template.index("operational_log/opj_ux_001.css")
        extra_head = template.index("{% block extra_head %}")
        self.assertLess(theme, compat)
        self.assertLess(compat, platform)
        self.assertLess(platform, opj)
        self.assertLess(platform, extra_head)
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
            "src/static/system/ux_platform.css",
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
        generic_selector_patterns = (
            r'^\s*\[role="button"\]\s*(?:,|\{)',
            r"^\s*th\s*,\s*td\s*(?:,|\{)",
            r"^\s*strong\s*(?:,|\{)",
            r"^\s*\.active\s*(?:,|\{)",
        )
        for pattern in generic_selector_patterns:
            self.assertNotRegex(css, re.compile(pattern, re.MULTILINE))

    def test_print_colours_are_isolated_from_screen_components(self):
        css = self.source("src/static/system/theme.css")
        screen, print_rules = css.split("@media print", 1)
        screen_without_comments = re.sub(r"/\*.*?\*/", "", screen, flags=re.S)
        self.assertNotIn("!important", screen_without_comments)
        self.assertIn("background: #fff !important", print_rules)
        self.assertIn("color: #000 !important", print_rules)

    def test_repair_two_removes_local_theme_owners(self):
        platform = self.source("src/static/system/ux_platform.css").split(
            "@media print", 1
        )[0]
        workspace = self.source("src/static/operational_log/opj_workspace_controls.css")
        self.assertNotRegex(platform, r"color-scheme\s*:\s*light")
        self.assertNotIn('html[data-theme="dark"] body.opj-workspace-page', workspace)
        self.assertIn("--theme-placeholder", self.source("src/static/system/theme.css"))

    def test_browser_matrix_contract_is_available_for_final_acceptance(self):
        runner_path = Path(settings.BASE_DIR) / "tests/browser_theme/run.py"
        if not runner_path.is_file():
            self.skipTest(
                "repository-only browser acceptance harness is not packaged in runtime images"
            )
        runner = runner_path.read_text(encoding="utf-8")
        self.assertIn("DESKTOP_VIEWPORTS = (", runner)
        self.assertIn("MOBILE_VIEWPORTS = (", runner)
        for viewport in (
            "(1280, 800)",
            "(1366, 768)",
            "(1536, 864)",
            "(1920, 1080)",
            "(390, 844)",
            "(412, 915)",
            "(430, 932)",
        ):
            self.assertIn(viewport, runner)
        self.assertIn("VIEWPORTS = DESKTOP_VIEWPORTS + MOBILE_VIEWPORTS", runner)
        self.assertIn('THEMES = ("light", "dark")', runner)
        self.assertIn("len(PUBLIC_ROUTES) + len(ROUTES)", runner)
        self.assertIn("* len(THEMES) * len(VIEWPORTS)", runner)
        self.assertIn('report["meta"]["baseline_state_count"] = expected_baselines', runner)
        self.assertIn('page.emulate_media(media="print")', runner)
        for evidence_marker in (
            "full_page=False",
            "full_page=True",
            "console_errors",
            "page_errors",
            "rendered_regions",
            "scrollWidth",
            "innerWidth",
            "window.visualViewport",
            "capture_mobile_login_focus",
            "is_mobile=True",
            "__unfocused",
            "__focused",
        ):
            self.assertIn(evidence_marker, runner)
        for route in (
            '"documents": "/documents/"',
            '"equipment": "/equipment/"',
            '"dispatching": "/dispatching/"',
            '"normatives": "/normatives/"',
            '"imports": "/imports/"',
            '"workplace_docs": "/workplace-documentation/"',
            '"operational_documents": "/operational-documents/"',
            '"defect_registration": "/operations/defects/new/"',
        ):
            self.assertIn(route, runner)
        for selector in (
            ".defect-filter-grid",
            ".defect-picker-panel",
            ".journal-settings-dialog",
            "[data-view-drawer]",
            "[data-reference-picker]",
        ):
            self.assertIn(selector, runner)

    def test_audited_components_reject_near_white_screen_colours(self):
        declaration = re.compile(r"(?:background(?:-color)?|color)\s*:\s*([^;{}]+)", re.I)
        legacy = re.compile(r"#fff(?:fff)?\b|rgba?\(\s*255\s*,\s*255\s*,\s*255", re.I)
        for path in (
            "src/static/system/ux_platform.css",
            "src/static/operational_log/opj_ux_001.css",
            "src/static/operational_log/opj_workspace_controls.css",
        ):
            screen = self.source(path).split("@media print", 1)[0]
            self.assertEqual([v for v in declaration.findall(screen) if legacy.search(v)], [], path)
