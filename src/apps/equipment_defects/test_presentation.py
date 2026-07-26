from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.operational_documents.models import OperationalDocumentRecord

from .constants import (
    APPROVED_PRINT_COLUMNS,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_REGISTERED,
    STATUS_RESOLVED,
)
from .models import DefectActionCode, EquipmentDefectActionEvidence, EquipmentDefectContext
from .test_support import EquipmentDefectSourceBoundBase


class EquipmentDefectPresentationTests(EquipmentDefectSourceBoundBase, TestCase):
    def test_dedicated_routes_and_exact_six_column_print_contract(self) -> None:
        record = self.register(link_to_log=True)
        self.client.force_login(self.operator.user)

        registry_response = self.client.get(reverse("equipment_defects:registry"))
        self.assertEqual(registry_response.status_code, 200)
        registry_html = registry_response.content.decode("utf-8")
        registry_markers = (
            "Дата обнаружения дефекта",
            "Наименование ЛЭП, оборудования, устройства",
            "Срок устранения",
            "Дата устранения дефекта",
            "Содержание выполненных работ",
            "Ф.И.О., подписи оперативного персонала",
        )
        positions = [registry_html.index(marker) for marker in registry_markers]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("Конструктор формы", registry_html)
        self.assertNotIn("JSON schema", registry_html)

        detail_response = self.client.get(
            reverse("equipment_defects:detail", args=[record.public_id])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Подтвердить срок")
        self.assertContains(detail_response, "authenticated user")
        self.assertContains(detail_response, "не УКЭП")

        source_response = self.client.get(
            reverse(
                "equipment_defects:create_from_operational_log",
                args=[self.operational_entry.pk],
            )
        )
        self.assertEqual(source_response.status_code, 200)
        self.assertContains(
            source_response,
            f"Запись № {self.operational_entry.sequence_number}",
        )

        print_response = self.client.get(
            reverse("equipment_defects:print"),
            {"volume": record.equipment_defect_context.volume.public_id},
        )
        self.assertEqual(print_response.status_code, 200)
        print_html = print_response.content.decode("utf-8")
        print_positions = [print_html.index(column) for column in APPROVED_PRINT_COLUMNS]
        self.assertEqual(print_positions, sorted(print_positions))
        self.assertNotIn("SHA-256 формы", print_html)
        self.assertNotIn(record.registration_number, print_html)
        self.assertIn("print-signature-line", print_html)

    def test_presentation_seed_is_idempotent_and_has_all_five_examples(self) -> None:
        call_command("seed_equipment_defects", verbosity=0)
        first_ids = set(
            EquipmentDefectContext.objects.exclude(presentation_key__isnull=True)
            .values_list("record_id", flat=True)
        )
        call_command("seed_equipment_defects", verbosity=0)
        second_ids = set(
            EquipmentDefectContext.objects.exclude(presentation_key__isnull=True)
            .values_list("record_id", flat=True)
        )

        self.assertEqual(first_ids, second_ids)
        self.assertEqual(len(first_ids), 5)
        states = set(
            OperationalDocumentRecord.objects.filter(pk__in=first_ids).values_list(
                "status_code",
                flat=True,
            )
        )
        self.assertEqual(
            states,
            {STATUS_REGISTERED, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_CLOSED},
        )
        self.assertTrue(
            EquipmentDefectActionEvidence.objects.filter(
                record_id__in=first_ids,
                action_code=DefectActionCode.DEADLINE_EXTENDED,
            ).exists()
        )


