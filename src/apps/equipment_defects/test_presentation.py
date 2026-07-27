from __future__ import annotations

from django.apps import apps as django_apps
from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.operational_documents.models import OperationalDocumentRecord

from .constants import (
    APPROVED_PRINT_COLUMNS,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_REGISTERED,
    STATUS_RESOLVED,
)
from .models import DefectActionCode, EquipmentDefectActionEvidence, EquipmentDefectContext
from .test_numbering import create_generic_record, create_same_prefix_revision
from .test_support import EquipmentDefectSourceBoundBase


class EquipmentDefectPresentationTests(EquipmentDefectSourceBoundBase, TestCase):
    def create_occupied_first_candidate(self) -> OperationalDocumentRecord:
        revision = create_same_prefix_revision(
            actor=self.operator,
            code="presentation-existing-same-prefix",
        )
        return create_generic_record(
            revision=revision,
            actor=self.operator,
            workplace=self.fixture["workplace"],
            event_at=timezone.now().replace(second=0, microsecond=0),
            note=(
                "Существующая запись до установки презентационного "
                "журнала дефектов."
            ),
        )

    def assert_five_presentation_examples(self) -> set[int]:
        presentation_ids = set(
            EquipmentDefectContext.objects.exclude(presentation_key="").values_list(
                "record_id",
                flat=True,
            )
        )
        self.assertEqual(len(presentation_ids), 5)
        states = set(
            OperationalDocumentRecord.objects.filter(pk__in=presentation_ids).values_list(
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
                record_id__in=presentation_ids,
                action_code=DefectActionCode.DEADLINE_EXTENDED,
            ).exists()
        )
        return presentation_ids

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
        self.assertContains(detail_response, "аутентифицированной учётной записью")
        self.assertContains(detail_response, "не называется УКЭП")
        self.assertNotContains(detail_response, "authenticated user")

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

    def test_presentation_seed_handles_populated_database_and_is_idempotent(self) -> None:
        occupied = self.create_occupied_first_candidate()
        occupied_number = occupied.registration_number
        records_before = OperationalDocumentRecord.objects.count()
        actions_before = EquipmentDefectActionEvidence.objects.count()

        call_command("seed_equipment_defects", verbosity=0)

        first_ids = self.assert_five_presentation_examples()
        first_action_ids = set(
            EquipmentDefectActionEvidence.objects.filter(record_id__in=first_ids).values_list(
                "pk",
                flat=True,
            )
        )
        records_after_first = OperationalDocumentRecord.objects.count()
        actions_after_first = EquipmentDefectActionEvidence.objects.count()

        self.assertEqual(records_after_first, records_before + 5)
        self.assertGreater(actions_after_first, actions_before)
        self.assertTrue(OperationalDocumentRecord.objects.filter(pk=occupied.pk).exists())
        self.assertEqual(
            OperationalDocumentRecord.objects.get(pk=occupied.pk).registration_number,
            occupied_number,
        )
        self.assertFalse(
            OperationalDocumentRecord.objects.filter(
                pk__in=first_ids,
                registration_number=occupied_number,
            ).exists()
        )

        call_command("seed_equipment_defects", verbosity=0)

        second_ids = self.assert_five_presentation_examples()
        second_action_ids = set(
            EquipmentDefectActionEvidence.objects.filter(record_id__in=second_ids).values_list(
                "pk",
                flat=True,
            )
        )
        self.assertEqual(first_ids, second_ids)
        self.assertEqual(first_action_ids, second_action_ids)
        self.assertEqual(OperationalDocumentRecord.objects.count(), records_after_first)
        self.assertEqual(EquipmentDefectActionEvidence.objects.count(), actions_after_first)

    def test_post_migrate_path_handles_existing_operational_document_record(self) -> None:
        occupied = self.create_occupied_first_candidate()
        occupied_number = occupied.registration_number
        app_config = django_apps.get_app_config("equipment_defects")
        records_before = OperationalDocumentRecord.objects.count()

        post_migrate.send(
            sender=app_config,
            app_config=app_config,
            verbosity=0,
            interactive=False,
            using="default",
            plan=[],
            apps=django_apps,
        )

        first_ids = self.assert_five_presentation_examples()
        first_actions = set(
            EquipmentDefectActionEvidence.objects.filter(record_id__in=first_ids).values_list(
                "pk",
                flat=True,
            )
        )
        self.assertEqual(OperationalDocumentRecord.objects.count(), records_before + 5)
        self.assertEqual(
            OperationalDocumentRecord.objects.get(pk=occupied.pk).registration_number,
            occupied_number,
        )

        post_migrate.send(
            sender=app_config,
            app_config=app_config,
            verbosity=0,
            interactive=False,
            using="default",
            plan=[],
            apps=django_apps,
        )

        self.assertEqual(self.assert_five_presentation_examples(), first_ids)
        self.assertEqual(
            set(
                EquipmentDefectActionEvidence.objects.filter(record_id__in=first_ids).values_list(
                    "pk",
                    flat=True,
                )
            ),
            first_actions,
        )
        self.assertEqual(OperationalDocumentRecord.objects.count(), records_before + 5)
