from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EquipmentDefectUXFoundationTests(SimpleTestCase):
    def setUp(self) -> None:
        self.template_path = (
            Path(settings.BASE_DIR)
            / "src"
            / "templates"
            / "equipment_defects"
            / "registry.html"
        )
        self.stylesheet_path = (
            Path(settings.BASE_DIR)
            / "src"
            / "static"
            / "equipment_defects"
            / "ux_foundation.css"
        )

    def test_registry_loads_isolated_foundation_after_legacy_styles(self) -> None:
        template = self.template_path.read_text(encoding="utf-8")

        legacy_marker = "equipment_defects/defects.css"
        foundation_marker = "equipment_defects/ux_foundation.css"
        self.assertIn(legacy_marker, template)
        self.assertIn(foundation_marker, template)
        self.assertLess(template.index(legacy_marker), template.index(foundation_marker))
        self.assertIn("?v=uxf001", template)

    def test_foundation_declares_light_document_operational_tokens(self) -> None:
        stylesheet = self.stylesheet_path.read_text(encoding="utf-8")

        required_contract = (
            "color-scheme: light",
            "--ux-canvas:",
            "--ux-surface:",
            "--ux-blue:",
            "--ux-focus:",
            ".presentation-topbar",
            ".defect-status-strip",
            ".defect-register thead th",
            "text-align: center",
            "@media (max-width: 1050px)",
            ".defect-mobile-card",
        )
        for marker in required_contract:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)

    def test_registry_keeps_source_columns_and_interaction_markers(self) -> None:
        template = self.template_path.read_text(encoding="utf-8")

        source_columns = (
            "Дата обнаружения дефекта",
            "Наименование ЛЭП, оборудования, устройства",
            "Срок устранения",
            "Дата устранения дефекта",
            "Содержание выполненных работ",
            "Ф.И.О., подписи оперативного персонала",
        )
        for marker in source_columns:
            with self.subTest(marker=marker):
                self.assertIn(marker, template)

        interaction_markers = (
            "data-defect-desktop-register",
            "data-defect-mobile-register",
            "data-defect-sort",
            "data-defect-row-link",
            "defect-sequence-number",
            'colspan="7"',
        )
        for marker in interaction_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, template)

    def test_registry_uses_operator_facing_status_and_filter_copy(self) -> None:
        template = self.template_path.read_text(encoding="utf-8")

        self.assertIn("Зарегистрированы", template)
        self.assertIn("В работе", template)
        self.assertIn("Устранены", template)
        self.assertIn("Закрыты", template)
        self.assertIn("Состояние: {{ label }}", template)
        self.assertNotIn("Состояние: {{ filters.status }}", template)
