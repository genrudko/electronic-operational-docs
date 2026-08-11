from __future__ import annotations

import re
from pathlib import Path

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
        theme_stylesheet = base.index("system/theme.css")
        compat_stylesheet = base.index("system/ux_platform_compat.css")
        platform_stylesheet = base.index("system/ux_platform.css")
        opj_stylesheet = base.index("operational_log/opj_ux_001.css")
        extra_head = base.index("{% block extra_head %}")

        self.assertLess(theme_resolution, first_stylesheet)
        self.assertLess(theme_stylesheet, compat_stylesheet)
        self.assertLess(compat_stylesheet, platform_stylesheet)
        self.assertLess(platform_stylesheet, opj_stylesheet)
        self.assertLess(platform_stylesheet, extra_head)
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
        self.assertIn(
            'body.ux-platform input:not([type="checkbox"])',
            platform,
        )
        self.assertNotRegex(
            platform,
            r'(?m)^body\.ux-platform input:not\(',
        )
        self.assertIn(":where(body.ux-platform textarea)", platform)
        self.assertNotIn(".ux-textarea,\nbody.ux-platform textarea", platform)

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

    def test_repair_v4_summary_grid_has_deterministic_four_two_one_geometry(self) -> None:
        compositions = read("src/static/system/ux_platform_compositions.css")

        self.assertIn("grid-template-columns:repeat(4,minmax(0,1fr))", compositions)
        self.assertIn("@media (max-width:70rem)", compositions)
        self.assertIn("repeat(2,minmax(0,1fr))", compositions)
        self.assertIn("@media (max-width:42rem)", compositions)
        self.assertIn(".ux-stat-grid { grid-template-columns:1fr; }", compositions)

    def test_repair_v4_import_and_workplace_use_semantic_compositions(self) -> None:
        imports = read("src/templates/imports/list.html")
        workplace_detail = read("src/templates/workplace_docs/detail.html")
        workplace_registry = read("src/templates/workplace_docs/registry.html")

        self.assertIn("ux-page-header-balanced", imports)
        self.assertIn("ux-profile-strip", imports)
        self.assertIn("ux-readable-value", imports)
        self.assertIn("ux-cell-stack", workplace_detail)
        self.assertIn("ux-technical-chip", workplace_detail)
        self.assertIn("ux-cell-secondary", workplace_detail)
        self.assertIn("ux-cell-stack", workplace_registry)
        self.assertNotIn("{{ entry.title }}<code", workplace_detail)

    def test_repair_v4_public_home_and_demo_credential_have_distinct_measures(self) -> None:
        home = read("src/templates/system/home.html")
        login = read("src/templates/organizations/login.html")
        public_css = read("src/static/system/ux_platform_public.css")

        self.assertIn("ux-public-home-page", home)
        self.assertIn(":has(> main.ux-public-home-page)", public_css)
        self.assertIn("width: min(100%, 82rem)", public_css)
        self.assertIn("ux-demo-credential", login)
        self.assertIn("white-space: pre-wrap", public_css)
        self.assertIn("user-select: all", public_css)

    def test_repair_v4_long_identity_and_active_relations_are_not_silent_disabled_text(self) -> None:
        sidebar = read("src/templates/shared/direction_a/_sidebar.html")
        compositions = read("src/static/system/ux_platform_compositions.css")

        self.assertIn('title="{{ user_display_name }} — {{ user_display_role', sidebar)
        self.assertIn('aria-label="Настройки интерфейса: {{ user_display_name }}', sidebar)
        self.assertIn(".da-user:is(:hover,:focus-visible) .da-user-copy strong", compositions)
        self.assertIn("body.ux-platform .equipment-relation-list li > a", compositions)
        self.assertIn("background:var(--theme-primary-soft)", compositions)
        self.assertIn(".management-function-card .authority-kind", compositions)
        self.assertIn(".supervision-function-card .authority-kind", compositions)
