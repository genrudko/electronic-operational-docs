from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EquipmentDefectUXFoundationRepairFiveTests(SimpleTestCase):
    def setUp(self) -> None:
        self.template_root = (
            Path(settings.BASE_DIR)
            / "src"
            / "templates"
            / "equipment_defects"
        )
        self.static_root = (
            Path(settings.BASE_DIR)
            / "src"
            / "static"
            / "equipment_defects"
        )
        self.project_template_root = (
            Path(settings.BASE_DIR) / "src" / "templates"
        )

    def test_repair_five_asset_is_loaded_after_repair_four(self) -> None:
        for filename in (
            "registry.html",
            "detail.html",
            "registration_form.html",
            "action_form.html",
        ):
            with self.subTest(template=filename):
                template = (self.template_root / filename).read_text(encoding="utf-8")
                repair_four = "equipment_defects/ux_foundation_repair4.css"
                repair_five = "equipment_defects/ux_foundation_repair5.css"
                self.assertIn(repair_four, template)
                self.assertIn(repair_five, template)
                self.assertIn("?v=uxf001r5", template)
                self.assertLess(template.index(repair_four), template.index(repair_five))

    def test_defect_status_mapping_consumes_platform_semantic_tokens(self) -> None:
        stylesheet = (self.static_root / "ux_foundation_repair5.css").read_text(
            encoding="utf-8"
        )
        required = (
            "--da-status-registered: var(--theme-primary)",
            "--da-status-progress: var(--theme-warning)",
            "--da-status-resolved: var(--theme-success)",
            "--da-status-closed: var(--theme-text-muted)",
            ".defect-da-status::before",
            "background: currentColor",
            "white-space: nowrap !important",
            "word-break: keep-all !important",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)

        for obsolete in (
            "--da-status-registered-soft: #e7f2fb",
            "--da-status-progress-soft: #fff0df",
            "--da-status-resolved-soft: #e5f4ea",
            "--da-status-closed-soft: #edf1f4",
        ):
            self.assertNotIn(obsolete, stylesheet)

    def test_future_lifecycle_is_secondary_without_component_opacity(self) -> None:
        stylesheet = (self.static_root / "ux_foundation_repair5.css").read_text(
            encoding="utf-8"
        )
        required = (
            "border-color: var(--theme-border)",
            "background: var(--theme-surface-soft)",
            "color: var(--theme-text-muted)",
            "opacity: 1",
            'data-current-status="REGISTERED"',
            'data-current-status="IN_PROGRESS"',
            'data-current-status="RESOLVED"',
            'data-current-status="CLOSED"',
            'content: "✓"',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)

        self.assertNotIn("opacity: .25", stylesheet)
        self.assertNotIn("opacity: .38", stylesheet)

    def test_defect_detail_links_use_generic_platform_link_semantics(self) -> None:
        stylesheet = (self.static_root / "ux_foundation_repair5.css").read_text(
            encoding="utf-8"
        )
        self.assertIn(".defect-da-back-link", stylesheet)
        self.assertIn(".defect-da-aside-card summary", stylesheet)
        self.assertIn("color: var(--theme-primary)", stylesheet)
        self.assertIn("color: var(--theme-primary-hover)", stylesheet)
        self.assertIn("outline: var(--theme-focus-width) solid var(--theme-focus)", stylesheet)

    def test_operational_documents_uses_defect_domain_status_code_mapping_only(self) -> None:
        template = (
            self.project_template_root / "operational_documents" / "registry.html"
        ).read_text(encoding="utf-8")

        self.assertIn("record.document_type.code == 'DEFECTS'", template)
        self.assertIn("record.status_code == 'REGISTERED'", template)
        self.assertIn("record.status_code == 'IN_PROGRESS'", template)
        self.assertIn("record.status_code == 'RESOLVED'", template)
        self.assertIn('data-domain-status="DEFECT"', template)
        self.assertIn('data-status="{{ record.status_code }}"', template)
        self.assertIn("record.status_is_terminal", template)
