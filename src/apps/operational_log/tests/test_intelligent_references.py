from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.organizations.models import Employee

from .base import OperationalLogTestCase


class IntelligentReferenceCatalogTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(
            get_user_model().objects.get(username="operator.demo")
        )

    def workspace_response(self):
        return self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )

    def test_catalog_contains_active_equipment_aliases(self) -> None:
        response = self.workspace_response()
        self.assertEqual(response.status_code, 200)
        catalog = response.context["semantic_reference_catalog"]
        item = next(
            row
            for row in catalog["equipment"]
            if row["reference"] == f"equipment:{self.equipment.public_id}"
        )
        self.assertIn("КТП 1", item["terms"])
        self.assertIn(self.equipment.code, item["terms"])

    def test_person_catalog_contains_morphology_source_terms(self) -> None:
        response = self.workspace_response()
        self.assertEqual(response.status_code, 200)
        catalog = response.context["semantic_reference_catalog"]
        employee = Employee.objects.get(
            organization=self.organization,
            last_name="Белов",
        )
        item = next(
            row
            for row in catalog["person"]
            if row["reference"] == f"employee:{employee.pk}"
        )
        self.assertIn("Белов", item["terms"])
        self.assertIn(employee.full_name, item["terms"])

    def test_workspace_exposes_inline_undo_and_auto_reference_mode(self) -> None:
        response = self.workspace_response()
        for marker in (
            "data-inline-undo",
            "data-inline-undo-button",
            "data-auto-reference-toggle",
            "data-auto-reference-scan",
            "Связь · авто включено",
            "?v=01132",
        ):
            self.assertContains(response, marker)
