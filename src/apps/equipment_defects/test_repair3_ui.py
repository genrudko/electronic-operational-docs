from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from .forms import DefectRegistrationForm
from .test_support import EquipmentDefectSourceBoundBase


class EquipmentDefectRepairThreeUITests(EquipmentDefectSourceBoundBase, TestCase):
    def setUp(self) -> None:
        self.client.force_login(self.operator.user)

    def test_registry_has_compact_sortable_desktop_and_mobile_views(self) -> None:
        record = self.register()

        response = self.client.get(reverse("equipment_defects:registry"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-defect-sort")
        self.assertContains(response, "data-defect-desktop-register")
        self.assertContains(response, "data-defect-mobile-register")
        self.assertContains(response, "defect-sequence-number")
        self.assertContains(
            response,
            f'aria-label="Открыть дефект № {record.sequence_value}"',
        )
        self.assertContains(response, "Сначала новые")
        self.assertContains(response, "Быстрый фильтр по состоянию")
        self.assertContains(response, "defects.js?v=defect004")
        self.assertNotContains(response, "SOURCE-BOUND ФОРМА")

    def test_registration_uses_time_trust_and_friendly_log_link(self) -> None:
        response = self.client.get(reverse("equipment_defects:create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Системное время приложения (МСК)")
        self.assertContains(response, "data-time-sensitive-form")
        self.assertContains(response, "data-defect-datetime")
        self.assertContains(response, "Связать с записью оперативного журнала")
        self.assertContains(response, "Основной сценарий — создать дефект непосредственно")
        self.assertNotContains(response, "authenticated user")

        form = DefectRegistrationForm(employee=self.operator)
        choices = list(form.fields["operational_log_entry"].choices)
        self.assertGreaterEqual(len(choices), 2)
        self.assertIn("Запись №", choices[1][1])
        self.assertIn("При осмотре выявлено замечание", choices[1][1])

    def test_detail_is_subject_first_russian_and_time_guarded(self) -> None:
        record = self.register(link_to_log=True)

        response = self.client.get(
            reverse("equipment_defects:detail", args=[record.public_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Карточка дефекта")
        self.assertContains(response, "Что произошло")
        self.assertContains(response, "Срок и ответственность")
        self.assertContains(response, "Результат устранения")
        self.assertContains(response, "История действий")
        self.assertContains(response, "аутентифицированной учётной записью")
        self.assertContains(response, "data-defect-time-trust")
        self.assertNotContains(response, "authenticated user")

    def test_static_contract_blocks_large_clock_drift_and_uses_card_breakpoint(self) -> None:
        static_root = Path(settings.BASE_DIR) / "src" / "static" / "equipment_defects"
        script = (static_root / "defects.js").read_text(encoding="utf-8")
        stylesheet = (static_root / "defects.css").read_text(encoding="utf-8")

        self.assertIn("setTimeSensitiveFormsBlocked", script)
        self.assertIn("dataset.maxDriftSeconds", script)
        self.assertIn("MOSCOW_TIME_ZONE", script)
        self.assertIn("@media (max-width: 1050px)", stylesheet)
        self.assertIn(".defect-register-wrap { display: none; }", stylesheet)
        self.assertIn(".defect-mobile-list { display: grid;", stylesheet)
        self.assertIn("text-align: center", stylesheet)
