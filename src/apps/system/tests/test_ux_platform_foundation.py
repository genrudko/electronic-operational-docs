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
            (ROOT / "src/static/operational_log/opj_workspace_controls.css").exists()
        )
        self.assertTrue(
            (ROOT / "src/static/operational_log/opj_workspace_controls.js").exists()
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

    def test_repair_v5_metric_grid_is_content_responsive_not_magic_four_columns(self) -> None:
        compositions = read("src/static/system/ux_platform_compositions.css")

        self.assertIn(
            "grid-template-columns:repeat(auto-fit,minmax(min(13.5rem,100%),1fr))",
            compositions,
        )
        self.assertNotIn(
            ".ux-stat-grid { min-width:0; display:grid; grid-template-columns:repeat(4",
            compositions,
        )
        self.assertIn("--theme-space-3", compositions)

    def test_repair_v5_geometry_contracts_are_shared(self) -> None:
        compositions = read("src/static/system/ux_platform_compositions.css")

        for selector in (
            ".ux-section-inset",
            ".ux-form-grid",
            ".ux-filter-actions",
            ".ux-table-actions",
            ".ux-value-stack",
            ".ux-value-primary",
            ".ux-value-secondary",
            ".ux-technical",
            ".ux-tree-row",
        ):
            self.assertIn(selector, compositions)
        self.assertIn("repeat(12,minmax(0,1fr))", compositions)
        self.assertIn("--theme-control-height-sm", compositions)
        self.assertIn("main.authority-main", compositions)

    def test_repair_v5_import_and_workplace_use_semantic_compositions(self) -> None:
        imports = read("src/templates/imports/list.html")
        workplace_detail = read("src/templates/workplace_docs/detail.html")
        workplace_registry = read("src/templates/workplace_docs/registry.html")

        self.assertIn("ux-page-header-balanced", imports)
        self.assertIn("ux-profile-strip", imports)
        self.assertIn("ux-readable-value", imports)
        self.assertIn("ux-stat-grid", imports)
        self.assertIn("ux-cell-stack", workplace_detail)
        self.assertIn("ux-technical-chip", workplace_detail)
        self.assertIn("ux-cell-secondary", workplace_detail)
        self.assertIn("ux-cell-stack", workplace_registry)
        self.assertNotIn("{{ entry.title }}<code", workplace_detail)

    def test_repair_v5_home_section_has_platform_inset(self) -> None:
        home = read("src/templates/system/home.html")

        self.assertIn("da-panel-flat ux-stack ux-section-inset", home)
        self.assertIn("Ключевые правила системы", home)

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

    def test_repair_v5_long_identity_is_readable_without_hover_only_contract(self) -> None:
        sidebar = read("src/templates/shared/direction_a/_sidebar.html")
        compositions = read("src/static/system/ux_platform_compositions.css")

        self.assertIn('title="{{ user_display_name }} — {{ user_display_role', sidebar)
        self.assertIn(
            'aria-label="Настройки интерфейса: {{ user_display_name }}',
            sidebar,
        )
        self.assertIn("-webkit-line-clamp:2", compositions)
        self.assertIn(".da-user { min-height:5rem; }", compositions)
        self.assertNotIn(
            ".da-user:is(:hover,:focus-visible) .da-user-copy strong",
            compositions,
        )

    def test_repair_v5_equipment_uses_human_label_and_technical_code_stack(self) -> None:
        template = read("src/templates/equipment/detail.html")
        compositions = read("src/static/system/ux_platform_compositions.css")

        self.assertIn('class="ux-value-stack"', template)
        self.assertIn('class="ux-value-primary"', template)
        self.assertIn('class="ux-technical technical-only"', template)
        self.assertNotIn("{{ relation.target_equipment.code }} · ", template)
        self.assertIn("body.ux-platform .equipment-relation-list li > a", compositions)

    def test_repair_v5_dispatching_filter_actions_and_semantics_are_explicit(self) -> None:
        template = read("src/templates/dispatching/registry.html")

        self.assertIn('class="ux-filter-actions ux-field-full"', template)
        self.assertIn("management-function-card", template)
        self.assertIn("supervision-function-card", template)

    def test_repair_v5_defect_detail_uses_canonical_header_and_visible_actions(self) -> None:
        header = read("src/templates/equipment_defects/_detail_repair2_header.html")
        aside = read("src/templates/equipment_defects/_detail_repair2_aside.html")

        self.assertIn('class="defect-da-record-header da-page-header"', header)
        self.assertNotIn("defect-da-record-heading-row", header)
        self.assertIn('class="da-button is-secondary"', header)
        self.assertIn('class="da-button"', aside)
        self.assertNotIn('class="defect-button"', aside)
        self.assertIn("is-terminal-reached", aside)
        self.assertIn(
            "{% if record.status_code == 'CLOSED' %}✓{% else %}4{% endif %}",
            aside,
        )

    def test_repair_v6_personnel_tree_is_adaptive_and_forms_stay_normalized(self) -> None:
        directory_css = read("src/static/organizations/personnel_directory.css")
        management_css = read("src/static/organizations/personnel_management.css")
        compact = re.sub(r"\s+", "", directory_css)

        self.assertIn(
            "grid-template-columns:clamp(20rem,24%,30rem)minmax(0,1fr)",
            compact,
        )
        self.assertIn(".personnel-division-row > strong > small", directory_css)
        self.assertIn("overflow-wrap:normal", compact)
        self.assertIn("word-break:normal", compact)
        self.assertIn("min-width:64rem", compact)
        self.assertIn("repeat(12,minmax(0,1fr))", management_css.replace(" ", ""))
        self.assertIn("grid-column:1 / -1", management_css)

    def test_repair_v5_opj_full_width_and_controls_consume_platform_geometry(self) -> None:
        compositions = read("src/static/system/ux_platform_compositions.css")
        rows = read("src/templates/operational_log/_shift_workspace_rows.html")

        self.assertIn("body.ux-platform.opj-workspace-page .da-page", compositions)
        self.assertIn('data-page-width="full"', compositions)
        self.assertIn("button.draft-editor-ribbon-button", compositions)
        self.assertIn('class="da-icon-button draft-row-action"', rows)
        self.assertIn('class="da-icon-button draft-row-action is-danger"', rows)
        self.assertIn("--theme-control-height-sm", compositions)

    def test_repair_v6_authority_layout_css_is_not_runtime_injected(self) -> None:
        script = read("src/static/organizations/personnel_authority_followup.js")

        self.assertNotIn('createElement("link")', script)
        self.assertNotIn("document.head.append", script)
        self.assertNotIn("personnel_authority_followup.css", script)
        self.assertIn("Progressive enhancement only", script)

    def test_repair_v6_authority_has_one_synchronous_geometry_owner(self) -> None:
        matrix = read("src/static/organizations/personnel_authority_matrix.css")
        repair = read("src/static/organizations/personnel_authority_repair.css")
        followup = read("src/static/organizations/personnel_authority_followup.css")

        self.assertIn("canonical matrix/hierarchy presentation", matrix)
        self.assertIn("--authority-tree-width:clamp", matrix)
        self.assertIn("grid-template-columns:var(--authority-tree-width)", matrix)
        self.assertNotIn(".authority-workspace", repair)
        self.assertNotIn(".authority-workspace", followup)

    def test_repair_v6_platform_has_explicit_width_profiles(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")

        for token in (
            "--ux-page-normal-max",
            "--ux-page-wide-max",
            "--ux-page-gutter",
            "main.ux-page-wide",
            "main.ux-page-specialist",
        ):
            self.assertIn(token, css)
        self.assertIn("main.authority-main", css)
        self.assertIn("main.opj-shift-main", css)

    def test_repair_v6_opj_full_spread_use_specialist_stage(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        compact = re.sub(r"\s+", " ", css)

        self.assertIn(
            'opj-workspace[data-page-width="full"] { width:100%; max-width:none; }',
            compact,
        )
        self.assertIn(
            'opj-workspace[data-view-mode="spread"] .opj-editor-container '
            "{ min-width:0; grid-template-columns:repeat(2,minmax(0,1fr))",
            compact,
        )
        self.assertIn("font-size:clamp(1.3rem,1.25vw,1.65rem)", compact)

    def test_repair_v6_opj_bridge_has_no_meaningful_micro_typography(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        opj_bridge = css.split("Specialist OPJ", 1)[1]

        for literal in ("0.52rem", "0.53rem", "0.58rem", "0.61rem", "0.64rem"):
            self.assertNotIn(literal, opj_bridge)
