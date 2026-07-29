from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from apps.equipment_defects.forms import DefectRegistrationForm, WorkplaceTreeSelect


class EquipmentDefectUXFoundationRepairFourTests(SimpleTestCase):
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

    def test_registration_uses_workplace_hierarchy_widget(self) -> None:
        widget = DefectRegistrationForm.base_fields["workplace"].widget
        self.assertIsInstance(widget, WorkplaceTreeSelect)
        self.assertEqual(widget.attrs["data-defect-tree-select"], "workplace")
        self.assertEqual(
            widget.attrs["data-tree-placeholder"],
            "Введите подразделение или рабочее место",
        )

    def test_workplace_tree_uses_real_division_metadata(self) -> None:
        forms_source = (
            Path(settings.BASE_DIR)
            / "src"
            / "apps"
            / "equipment_defects"
            / "forms.py"
        ).read_text(encoding="utf-8")
        required = (
            "class WorkplaceTreeSelect",
            '"data-tree-organization"',
            '"data-tree-division-id"',
            '"data-tree-division-parent"',
            '"data-tree-division-parent-name"',
            'select_related("organization", "division", "division__parent")',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, forms_source)

    def test_workplace_tree_script_runs_before_generic_tree_enhancement(self) -> None:
        template = (self.template_root / "registration_form.html").read_text(
            encoding="utf-8"
        )
        workplace_script = "equipment_defects/ux_foundation_repair4_workplace.js"
        generic_script = "equipment_defects/ux_foundation_repair3.js"
        self.assertIn(workplace_script, template)
        self.assertIn(generic_script, template)
        self.assertLess(template.index(workplace_script), template.index(generic_script))

        script = (self.static_root / "ux_foundation_repair4_workplace.js").read_text(
            encoding="utf-8"
        )
        required = (
            'select[data-defect-tree-select="workplace"]',
            "buildHierarchy",
            "defect-tree-workplace-division",
            "Подразделение → рабочее место",
            "divisionParentId",
            'select.dataset.treeEnhanced = "true"',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_repair_four_css_is_loaded_across_direction_a_pages(self) -> None:
        marker = "equipment_defects/ux_foundation_repair4.css"
        for filename in (
            "registry.html",
            "detail.html",
            "registration_form.html",
            "action_form.html",
        ):
            with self.subTest(template=filename):
                template = (self.template_root / filename).read_text(encoding="utf-8")
                self.assertIn(marker, template)
                self.assertIn("?v=uxf001r4", template)

    def test_desktop_polish_contains_one_lifecycle_colour_system(self) -> None:
        stylesheet = (self.static_root / "ux_foundation_repair4.css").read_text(
            encoding="utf-8"
        )
        required = (
            "--da-sidebar-width: 292px",
            ".defect-da-user strong",
            "white-space: normal",
            "176px",
            "--da-complete",
            'data-current-status="IN_PROGRESS"',
            'data-current-status="RESOLVED"',
            'data-current-status="CLOSED"',
            'content: "✓"',
            ".defect-tree-workplace-division",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)
