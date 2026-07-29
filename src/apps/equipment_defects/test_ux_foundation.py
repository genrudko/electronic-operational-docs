from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EquipmentDefectUXFoundationTests(SimpleTestCase):
    def setUp(self) -> None:
        self.template_root = (
            Path(settings.BASE_DIR) / "src" / "templates" / "equipment_defects"
        )
        self.shared_template_root = (
            Path(settings.BASE_DIR) / "src" / "templates" / "shared" / "direction_a"
        )
        self.static_root = (
            Path(settings.BASE_DIR) / "src" / "static" / "equipment_defects"
        )
        self.registry_path = self.template_root / "registry.html"
        self.registry_header_path = self.template_root / "_registry_repair2_header.html"
        self.registry_worklist_path = self.template_root / "_registry_repair2_worklist.html"
        self.registry_journal_path = self.template_root / "_registry_repair2_journal.html"
        self.detail_path = self.template_root / "detail.html"
        self.detail_header_path = self.template_root / "_detail_repair2_header.html"
        self.detail_main_path = self.template_root / "_detail_repair2_main.html"
        self.detail_aside_path = self.template_root / "_detail_repair2_aside.html"
        self.registration_path = self.template_root / "registration_form.html"
        self.action_path = self.template_root / "action_form.html"
        self.sidebar_path = self.shared_template_root / "_sidebar.html"
        self.topbar_path = self.shared_template_root / "_topbar.html"
        self.shared_base_path = self.shared_template_root / "base.html"
        self.stylesheet_path = self.static_root / "ux_foundation.css"
        self.bridge_path = self.static_root / "ux_foundation_legacy_bridge.css"
        self.repair2_stylesheet_paths = (
            self.static_root / "ux_foundation_repair2.css",
            self.static_root / "ux_foundation_repair2_shell.css",
            self.static_root / "ux_foundation_repair2_registry.css",
            self.static_root / "ux_foundation_repair2_detail.css",
            self.static_root / "ux_foundation_repair2_responsive.css",
        )
        self.repair2_script_path = self.static_root / "ux_foundation_repair2.js"

    @staticmethod
    def _read(*paths: Path) -> str:
        return "\n".join(path.read_text(encoding="utf-8") for path in paths)

    def test_registry_loads_foundation_and_repair_layers_in_order(self) -> None:
        template = self.registry_path.read_text(encoding="utf-8")
        markers = (
            "equipment_defects/defects.css",
            "equipment_defects/ux_foundation.css",
            "equipment_defects/ux_foundation_legacy_bridge.css",
            "equipment_defects/ux_foundation_repair1.css",
            "equipment_defects/ux_foundation_repair2.css",
            "equipment_defects/defects.js",
            "equipment_defects/ux_foundation_repair1.js",
            "equipment_defects/ux_foundation_repair2.js",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, template)
        positions = [template.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("?v=uxf001r2", template)

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

    def test_legacy_bridge_remains_available_during_shell_transition(self) -> None:
        bridge = self.bridge_path.read_text(encoding="utf-8")
        for marker in (
            "background: rgba(255, 255, 255, .97) !important",
            "color: var(--ux-text) !important",
            "@media (max-width: 860px)",
            "@media (max-width: 760px)",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, bridge)

    def test_direction_a_shell_is_shared_sidebar_first_and_uses_real_routes(self) -> None:
        sidebar = self.sidebar_path.read_text(encoding="utf-8")
        topbar = self.topbar_path.read_text(encoding="utf-8")
        shared_base = self.shared_base_path.read_text(encoding="utf-8")
        for marker in (
            "da-sidebar defect-da-sidebar",
            "data-direction-a-sidebar",
            "ЭОД",
            "Рабочий стол",
            "Оперативная документация",
            "Оперативный журнал",
            "Журналы",
            "Журнал дефектов",
            "Оперативные документы",
            "Оборудование",
            "Управление и ведение",
            "Справочники и данные",
            "organizations:account",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, sidebar)
        for marker in (
            "da-topbar defect-da-topbar",
            "data-direction-a-topbar",
            "Рабочее место",
            "data-direction-a-toggle",
            "data-defect-shell-toggle",
            "system:health",
            "organizations:logout",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, topbar)
        self.assertIn('data-direction-a-shell', shared_base)
        self.assertIn('shared/direction_a/_sidebar.html', shared_base)
        self.assertIn('shared/direction_a/_topbar.html', shared_base)

    def test_registry_uses_dense_work_list_and_retains_exact_journal_view(self) -> None:
        template = self._read(
            self.registry_path,
            self.registry_header_path,
            self.registry_worklist_path,
            self.registry_journal_path,
        )
        for marker in (
            "Рабочий список",
            "Форма журнала",
            'data-defect-view="work"',
            'data-defect-view-panel="work"',
            'data-defect-view-panel="journal"',
            "defect-da-work-table",
            "defect-da-work-row",
            "defect-da-sequence-badge",
            "defect-da-status",
            "Выбор сохраняется до следующего изменения.",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, template)

        journal = self.registry_journal_path.read_text(encoding="utf-8")
        source_columns = (
            "Дата обнаружения дефекта",
            "Наименование ЛЭП, оборудования, устройства",
            "Срок устранения",
            "Дата устранения дефекта",
            "Содержание выполненных работ",
            "Ф.И.О., подписи оперативного персонала",
        )
        positions = [journal.index(marker) for marker in source_columns]
        self.assertEqual(positions, sorted(positions))
        for marker in (
            "data-defect-desktop-register",
            "data-defect-mobile-register",
            "data-defect-sort",
            "data-defect-row-link",
            "defect-sequence-number",
            'colspan="7"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, template)

    def test_repair2_assets_implement_direction_a_and_persistent_preferences(self) -> None:
        stylesheet = self._read(*self.repair2_stylesheet_paths)
        script = self.repair2_script_path.read_text(encoding="utf-8")
        for marker in (
            "--da-sidebar-width:",
            ".defect-da-shell",
            ".defect-da-sidebar",
            ".defect-da-topbar",
            ".defect-da-work-table",
            ".defect-da-sequence-badge",
            ".defect-da-status",
            ".defect-da-lifecycle-card",
            '[data-current-status="REGISTERED"]',
            '[data-current-status="IN_PROGRESS"]',
            '[data-current-status="RESOLVED"]',
            '[data-current-status="CLOSED"]',
            ".defect-time-trust-sentinel .defect-time-trust:not(.is-warning)",
            "@media (max-width:860px)",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)
        for marker in (
            'const SORT_STORAGE_KEY = "eod-defect-sort"',
            "window.localStorage",
            "window.sessionStorage",
            "data-defect-sort",
            "data-defect-shell-toggle",
            "data-defect-shell-sidebar",
            'event.key === "Escape"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_detail_uses_explicit_lifecycle_without_visible_clock_panel(self) -> None:
        template = self._read(
            self.detail_path,
            self.detail_header_path,
            self.detail_main_path,
            self.detail_aside_path,
        )
        for marker in (
            "defect-da-record-layout",
            "defect-da-lifecycle-card",
            "defect-lifecycle",
            'data-step="REGISTERED"',
            'data-step="IN_PROGRESS"',
            'data-step="RESOLVED"',
            'data-step="CLOSED"',
            "Доступное действие",
            "defect-time-trust-sentinel",
            "Аудит и история",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, template)
        self.assertNotIn("Системное время и фиксация", template)
        self.assertNotIn("Как фиксируются действия", template)

    def test_detail_uses_shared_shell_and_forms_keep_accepted_contract(self) -> None:
        detail = self.detail_path.read_text(encoding="utf-8")
        self.assertIn('{% extends "shared/direction_a/base.html" %}', detail)
        self.assertIn("equipment_defects/ux_foundation_repair2.css", detail)
        self.assertIn("equipment_defects/ux_foundation_repair2.js", detail)
        self.assertIn("equipment_defects/defects.js", detail)
        self.assertIn("?v=defect004", detail)

        templates = {
            "registration": self.registration_path.read_text(encoding="utf-8"),
            "action": self.action_path.read_text(encoding="utf-8"),
        }
        for name, template in templates.items():
            with self.subTest(template=name):
                self.assertIn("equipment_defects/_direction_a_sidebar.html", template)
                self.assertIn("equipment_defects/_direction_a_topbar.html", template)
                self.assertIn("equipment_defects/ux_foundation_repair2.css", template)
                self.assertIn("equipment_defects/ux_foundation_repair2.js", template)
                self.assertIn("equipment_defects/defects.js", template)
                self.assertIn("?v=defect004", template)
        self.assertIn("defect-form-steps", templates["registration"])
        self.assertIn("После регистрации", templates["registration"])
        self.assertIn("Проверка перед отправкой", templates["action"])

    def test_registry_uses_operator_facing_status_and_filter_copy(self) -> None:
        template = self._read(self.registry_header_path, self.registry_worklist_path)
        self.assertIn("Зарегистрированы", template)
        self.assertIn("В работе", template)
        self.assertIn("Устранены", template)
        self.assertIn("Закрыты", template)
        self.assertIn("Состояние: {{ label }}", template)
        self.assertNotIn("Состояние: {{ filters.status }}", template)
