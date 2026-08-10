from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse

from apps.system.models import ModuleLifecycleState, ModuleScopeType
from apps.system.module_registry import normalize_context, transition_module_state

from .templatetags.equipment_defect_tags import operational_defect_entry_rows
from .test_support import EquipmentDefectSourceBoundBase


class DefectModuleRegistryIntegrationTests(EquipmentDefectSourceBoundBase, TestCase):
    def _module_context(self):
        return normalize_context(
            organization=self.fixture["organization"],
            workplace=self.fixture["workplace"],
        )

    def _deactivate_defect(self) -> None:
        transition_module_state(
            module_id="DEFECT",
            context=self._module_context(),
            scope_type=ModuleScopeType.ORGANIZATION,
            new_state=ModuleLifecycleState.INACTIVE,
            actor_identity="tests/module-registry-integration",
            reason="prove inactive cross-module action is denied",
        )

    def _navigation_rows(self):
        path = reverse("operational_log:detail", args=[self.journal.pk])
        request = RequestFactory().get(path)
        request.user = self.operator.user
        request.resolver_match = resolve(path)
        return operational_defect_entry_rows({"request": request})

    def test_active_defect_offers_real_opj_cross_module_action(self) -> None:
        rows = self._navigation_rows()
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["can_create_defect"])

        self.client.force_login(self.operator.user)
        response = self.client.get(
            reverse(
                "equipment_defects:create_from_operational_log",
                args=[self.operational_entry.pk],
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_inactive_defect_hides_action_and_denies_http_and_service(self) -> None:
        self._deactivate_defect()
        self.assertEqual(self._navigation_rows(), [])

        self.client.force_login(self.operator.user)
        response = self.client.get(
            reverse(
                "equipment_defects:create_from_operational_log",
                args=[self.operational_entry.pk],
            )
        )
        self.assertEqual(response.status_code, 403)

        with self.assertRaises(PermissionDenied):
            self.register(link_to_log=True)

    def test_inactive_defect_preserves_existing_opj_link_history(self) -> None:
        record = self.register(link_to_log=True)
        self._deactivate_defect()

        rows = self._navigation_rows()
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["can_create_defect"])
        self.assertEqual(rows[0]["defect_links"][0].record_id, record.pk)
