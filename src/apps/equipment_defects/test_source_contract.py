from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .constants import (
    DOCUMENT_TYPE_CODE,
    DOCUMENT_TYPE_NAME,
    FIELD_DEFINITIONS,
    NUMBER_PREFIX,
    PARTICIPANT_ROLE_DEFINITIONS,
    ROLE_DISCOVERED_BY,
    SOURCE_APPENDIX,
    SOURCE_DOCUMENT,
    SOURCE_SECTION,
    STATUS_DEFINITIONS,
    STATUS_REGISTERED,
    TRANSITION_DEFINITIONS,
)
from .services import ensure_defect_document_type, register_defect
from .test_support import EquipmentDefectSourceBoundBase


class EquipmentDefectSourceContractTests(EquipmentDefectSourceBoundBase, TestCase):
    def test_exact_source_contract_is_published_idempotently_and_immutable(self) -> None:
        revision = ensure_defect_document_type(self.operator)
        second = ensure_defect_document_type(self.operator)

        self.assertEqual(revision.pk, second.pk)
        self.assertEqual(revision.document_type.code, DOCUMENT_TYPE_CODE)
        self.assertEqual(revision.document_type.name, DOCUMENT_TYPE_NAME)
        self.assertEqual(revision.number_prefix, NUMBER_PREFIX)
        self.assertEqual(revision.field_definitions, FIELD_DEFINITIONS)
        self.assertEqual(revision.status_definitions, STATUS_DEFINITIONS)
        self.assertEqual(revision.transition_definitions, TRANSITION_DEFINITIONS)
        self.assertEqual(
            revision.participant_role_definitions,
            PARTICIPANT_ROLE_DEFINITIONS,
        )
        self.assertEqual(len(revision.sha256), 64)
        self.assertEqual(SOURCE_DOCUMENT, "И-00-007-ОР-2025 версия 2")
        self.assertEqual(SOURCE_SECTION, "11")
        self.assertEqual(SOURCE_APPENDIX, "8")

        revision.number_prefix = "ИЗМ"
        with self.assertRaises(ValidationError):
            revision.save()

    def test_registration_requires_equipment_and_separates_created_and_discovered(self) -> None:
        record = self.register()
        discovered = record.participants.get(role_code=ROLE_DISCOVERED_BY)

        self.assertEqual(record.status_code, STATUS_REGISTERED)
        self.assertEqual(record.created_by, self.operator)
        self.assertEqual(discovered.employee, self.discoverer)
        self.assertNotEqual(record.created_by_id, discovered.employee_id)
        self.assertEqual(record.equipment_links.count(), 1)
        self.assertTrue(record.equipment_links.get().dispatcher_name_snapshot)

        with self.assertRaises(ValidationError):
            register_defect(
                actor=self.operator,
                workplace=self.fixture["workplace"],
                equipment=self.other_fixture["equipment"],
                discovered_by=self.discoverer,
                detected_at=timezone.now() - timedelta(hours=1),
                defect_description="Недопустимая межорганизационная связь.",
            )
