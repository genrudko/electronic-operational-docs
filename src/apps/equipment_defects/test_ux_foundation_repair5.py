from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.test import SimpleTestCase

from .constants import DOCUMENT_TYPE_CODE
from .templatetags.equipment_defect_tags import equipment_defect_status_presentation


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
            "--da-lifecycle-future-text: color-mix(in srgb, var(--theme-text-muted) 95%, var(--theme-text))",
            "border-color: var(--theme-border)",
            "background: var(--theme-surface-soft)",
            "color: var(--da-lifecycle-future-text)",
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

    def test_operational_documents_uses_defect_domain_presentation_owner(self) -> None:
        template = (
            self.project_template_root / "operational_documents" / "registry.html"
        ).read_text(encoding="utf-8")

        self.assertIn("{% load equipment_defect_tags %}", template)
        self.assertIn(
            "{% equipment_defect_status_presentation record as defect_status %}",
            template,
        )
        self.assertIn('data-domain-status="{{ defect_status.domain }}"', template)
        self.assertIn('data-status="{{ record.status_code }}"', template)
        self.assertIn("record.status_is_terminal", template)
        self.assertNotIn("record.document_type.code == 'DEFECTS'", template)
        self.assertNotIn("record.status_code == 'REGISTERED'", template)
        self.assertNotIn("record.status_code == 'IN_PROGRESS'", template)
        self.assertNotIn("record.status_code == 'RESOLVED'", template)

    def test_defect_presentation_tag_uses_canonical_document_code_and_schema_tone(self) -> None:
        record = SimpleNamespace(
            document_type=SimpleNamespace(code=DOCUMENT_TYPE_CODE),
            schema_revision=SimpleNamespace(
                status_definitions=[
                    {"code": "REGISTERED", "name": "Зарегистрирован", "tone": "info"},
                    {"code": "IN_PROGRESS", "name": "В работе", "tone": "warning"},
                ]
            ),
            status_code="REGISTERED",
        )
        presentation = equipment_defect_status_presentation(record)
        self.assertEqual(
            presentation,
            {"domain": "DEFECT", "tone": "info", "class_name": "is-info"},
        )

        generic = SimpleNamespace(
            document_type=SimpleNamespace(code="technical-record"),
            schema_revision=record.schema_revision,
            status_code="REGISTERED",
        )
        self.assertIsNone(equipment_defect_status_presentation(generic))

    def test_sequence_number_badges_keep_compact_status_cues_without_dominating(self) -> None:
        repair5 = (self.static_root / "ux_foundation_repair5.css").read_text(
            encoding="utf-8"
        )
        self.assertIn('.defect-da-sequence-badge[data-status="REGISTERED"]', repair5)
        self.assertIn('.defect-da-sequence-badge[data-status="IN_PROGRESS"]', repair5)
        self.assertIn('.defect-da-sequence-badge[data-status="RESOLVED"]', repair5)
        self.assertIn('inset 4px 0 0', repair5)
        self.assertIn('.defect-da-work-number > small', repair5)
        self.assertIn('overflow-wrap: anywhere', repair5)

    def test_defect_journal_column_geometry_prevents_status_overlap_at_1280(self) -> None:
        stylesheet = (self.static_root / "ux_foundation_repair5.css").read_text(
            encoding="utf-8"
        )
        # Journal table date/status column 2 must have explicit width/min-width in repair5
        self.assertIn(".defect-journal-view .defect-register th:nth-child(2)", stylesheet)
        self.assertIn("min-width: 138px", stylesheet)

    def test_defect_detail_density_is_bounded_and_normalized(self) -> None:
        repair2_detail = (
            self.static_root / "ux_foundation_repair2_detail.css"
        ).read_text(encoding="utf-8")

        # Title is normalized to bounded size, not oversized 2.4rem
        self.assertNotIn("clamp(1.75rem,3vw,2.4rem)", repair2_detail)

        # Lifecycle stays substantially denser than the original 94px blocks, but must fit labels.
        self.assertNotIn("min-height:94px", repair2_detail)
        self.assertIn("min-height:82px", repair2_detail)
        self.assertIn("white-space:normal", repair2_detail)
        self.assertIn("overflow-wrap:anywhere", repair2_detail)
