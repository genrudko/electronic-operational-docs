from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EquipmentDefectUXFoundationTests(SimpleTestCase):
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
        self.registry_path = self.template_root / "registry.html"
        self.detail_path = self.template_root / "detail.html"
        self.registration_path = self.template_root / "registration_form.html"
        self.action_path = self.template_root / "action_form.html"
        self.stylesheet_path = self.static_root / "ux_foundation.css"
        self.bridge_path = self.static_root / "ux_foundation_legacy_bridge.css"
        self.repair_stylesheet_path = self.static_root / "ux_foundation_repair1.css"
        self.repair_script_path = self.static_root / "ux_foundation_repair1.js"

    def test_registry_loads_foundation_and_repair_layers_in_order(self) -> None:
        template = self.registry_path.read_text(encoding="utf-8")

        markers = (
            "equipment_defects/defects.css",
            "equipment_defects/ux_foundation.css",
            "equipment_defects/ux_foundation_legacy_bridge.css",
            "equipment_defects/ux_foundation_repair1.css",
            "equipment_defects/defects.js",
            "equipment_defects/ux_foundation_repair1.js",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, template)
        positions = [template.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("?v=uxf001r1", template)

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

    def test_legacy_bridge_forces_light_shell_and_compact_mobile_header(self) -> None:
        bridge = self.bridge_path.read_text(encoding="utf-8")

        required_contract = (
            "background: rgba(255, 255, 255, .97) !important",
            "color: var(--ux-text) !important",
            "color: var(--ux-text-secondary) !important",
            "@media (max-width: 860px)",
            "@media (max-width: 760px)",
            "flex-direction: row",
            ".presentation-topbar .presentation-nav.open",
        )
        for marker in required_contract:
            with self.subTest(marker=marker):
                self.assertIn(marker, bridge)

    def test_registry_defaults_to_work_queue_and_retains_exact_journal_view(self) -> None:
        template = self.registry_path.read_text(encoding="utf-8")

        work_markers = (
            "Рабочий список",
            "Форма журнала",
            'data-defect-view="work"',
            'data-defect-view-panel="work"',
            'data-defect-view-panel="journal"',
            "Следующий шаг",
            "Назначить срок и ответственного",
            "Контролировать устранение",
            "Ознакомление и закрытие",
        )
        for marker in work_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, template)

        source_columns = (
            "Дата обнаружения дефекта",
            "Наименование ЛЭП, оборудования, устройства",
            "Срок устранения",
            "Дата устранения дефекта",
            "Содержание выполненных работ",
            "Ф.И.О., подписи оперативного персонала",
        )
        positions = [template.index(marker) for marker in source_columns]
        self.assertEqual(positions, sorted(positions))

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

    def test_repair_assets_implement_view_switch_and_operator_layout(self) -> None:
        stylesheet = self.repair_stylesheet_path.read_text(encoding="utf-8")
        script = self.repair_script_path.read_text(encoding="utf-8")

        stylesheet_markers = (
            ".defect-work-item",
            ".defect-journal-view",
            ".defect-lifecycle",
            ".defect-record-layout",
            ".defect-form-layout",
            "@media (max-width: 760px)",
        )
        for marker in stylesheet_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)

        script_markers = (
            "eod-defect-registry-view",
            "data-defect-view-switch",
            "data-defect-view-panel",
            'const initial = allowed.has(stored) ? stored : "work"',
            'event.key === "Escape"',
        )
        for marker in script_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_detail_and_forms_share_the_same_repair_foundation(self) -> None:
        templates = {
            "detail": self.detail_path.read_text(encoding="utf-8"),
            "registration": self.registration_path.read_text(encoding="utf-8"),
            "action": self.action_path.read_text(encoding="utf-8"),
        }

        for name, template in templates.items():
            with self.subTest(template=name):
                self.assertIn("equipment_defects/ux_foundation.css", template)
                self.assertIn("equipment_defects/ux_foundation_legacy_bridge.css", template)
                self.assertIn("equipment_defects/ux_foundation_repair1.css", template)
                self.assertIn("defects.js?v=defect004", template)

        self.assertIn("defect-lifecycle", templates["detail"])
        self.assertIn("Следующее действие", templates["detail"])
        self.assertIn("defect-form-steps", templates["registration"])
        self.assertIn("Что произойдёт после регистрации", templates["registration"])
        self.assertIn("Проверка перед отправкой", templates["action"])

    def test_registry_uses_operator_facing_status_and_filter_copy(self) -> None:
        template = self.registry_path.read_text(encoding="utf-8")

        self.assertIn("Новые", template)
        self.assertIn("В работе", template)
        self.assertIn("Устранены", template)
        self.assertIn("Закрыты", template)
        self.assertIn("Состояние: {{ label }}", template)
        self.assertNotIn("Состояние: {{ filters.status }}", template)
