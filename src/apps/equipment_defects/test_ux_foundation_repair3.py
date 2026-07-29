from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from apps.equipment_defects.forms import (
    DeadlineConfirmationForm,
    DefectRegistrationForm,
    EquipmentTreeSelect,
    PersonnelTreeSelect,
    ResolutionConfirmationForm,
)


class EquipmentDefectUXFoundationRepairThreeTests(SimpleTestCase):
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

    def test_defect_forms_use_hierarchical_equipment_and_personnel_widgets(self) -> None:
        self.assertIsInstance(
            DefectRegistrationForm.base_fields["equipment"].widget,
            EquipmentTreeSelect,
        )
        self.assertIsInstance(
            DefectRegistrationForm.base_fields["discovered_by"].widget,
            PersonnelTreeSelect,
        )
        self.assertIsInstance(
            DeadlineConfirmationForm.base_fields["responsible"].widget,
            PersonnelTreeSelect,
        )
        self.assertIsInstance(
            ResolutionConfirmationForm.base_fields["responsible"].widget,
            PersonnelTreeSelect,
        )
        self.assertEqual(
            DefectRegistrationForm.base_fields["equipment"].widget.attrs[
                "data-defect-tree-select"
            ],
            "equipment",
        )
        self.assertEqual(
            DefectRegistrationForm.base_fields["discovered_by"].widget.attrs[
                "data-defect-tree-select"
            ],
            "personnel",
        )

    def test_repair_three_assets_are_loaded_after_repair_two(self) -> None:
        for filename in (
            "registry.html",
            "detail.html",
            "registration_form.html",
            "action_form.html",
        ):
            with self.subTest(template=filename):
                template = (self.template_root / filename).read_text(encoding="utf-8")
                repair_two_css = "equipment_defects/ux_foundation_repair2.css"
                repair_three_css = "equipment_defects/ux_foundation_repair3.css"
                repair_two_js = "equipment_defects/ux_foundation_repair2.js"
                repair_three_js = "equipment_defects/ux_foundation_repair3.js"
                for marker in (
                    repair_two_css,
                    repair_three_css,
                    repair_two_js,
                    repair_three_js,
                    "?v=uxf001r3",
                ):
                    self.assertIn(marker, template)
                self.assertLess(template.index(repair_two_css), template.index(repair_three_css))
                self.assertLess(template.index(repair_two_js), template.index(repair_three_js))

    def test_tree_script_searches_real_equipment_and_personnel_hierarchies(self) -> None:
        script = (self.static_root / "ux_foundation_repair3.js").read_text(
            encoding="utf-8"
        )
        required = (
            "buildEquipmentTree",
            "buildPersonnelTree",
            "data-defect-tree-select",
            "treeParent",
            "treePosition",
            "Энергообъект → оборудование",
            "Подразделение → должность → сотрудник",
            'role", "combobox',
            "aria-selected",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_masked_datetime_replaces_native_android_picker_without_losing_guard(self) -> None:
        script = (self.static_root / "ux_foundation_repair3.js").read_text(
            encoding="utf-8"
        )
        required = (
            "digitsMask",
            "ДД.ММ.ГГГГ",
            "ЧЧ:ММ",
            'dateInput.type = "text"',
            'timeInput.type = "text"',
            "defect-datetime-control",
            "data-defect-time-trust",
            "Europe/Moscow",
            'native.dispatchEvent(new Event("change", { bubbles: true }))',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_mobile_contract_uses_cards_and_contains_horizontal_overflow(self) -> None:
        stylesheet = (self.static_root / "ux_foundation_repair3.css").read_text(
            encoding="utf-8"
        )
        required = (
            "overflow-x: clip",
            "@media (max-width: 720px)",
            ".defect-da-work-head",
            "display: none !important",
            "grid-template-areas:",
            '"number date"',
            '"equipment equipment"',
            '"description description"',
            ".defect-tree-panel",
            "position: fixed",
            ".defect-manual-datetime",
            "overflow-wrap: anywhere",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)

    def test_mobile_print_preview_does_not_shrink_the_a4_landscape_sheet(self) -> None:
        template = (self.template_root / "print.html").read_text(encoding="utf-8")
        required = (
            "print-mobile-hint",
            "print-preview-scroll",
            "print-document",
            "width: 1120px",
            "overflow-x: auto",
            "@media print",
            "width: auto",
            "min-width: 0",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, template)
