from __future__ import annotations

from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.equipment.models import EnergySite
from apps.organizations.models import Organization, Workplace
from apps.system.models import (
    ModuleActivationAuditEvent,
    ModuleActivationRule,
    ModuleLifecycleState,
    ModuleScopeType,
)
from apps.system.module_registry import (
    _MANIFESTS,
    ActivationPolicy,
    EntryPointClass,
    ModuleManifest,
    ModuleOperation,
    decide_module_access,
    manifest_for,
    normalize_context,
    require_module_access,
    resolve_effective_state,
    transition_module_state,
)


class ModuleRegistryTests(TestCase):
    def setUp(self) -> None:
        self.org = Organization.objects.create(code="MR-ORG", name="Registry Org")
        self.other_org = Organization.objects.create(code="MR-OTHER", name="Other Org")
        self.workplace = Workplace.objects.create(
            organization=self.org,
            code="MR-WP",
            name="Registry Workplace",
        )
        self.other_workplace = Workplace.objects.create(
            organization=self.other_org,
            code="MR-OTHER-WP",
            name="Other Workplace",
        )
        self.site = EnergySite.objects.create(
            organization=self.org,
            code="mr-site",
            name="Registry Site",
            site_type=EnergySite.SiteType.WIND_POWER_PLANT,
        )
        self.other_site = EnergySite.objects.create(
            organization=self.other_org,
            code="mr-other-site",
            name="Other Site",
            site_type=EnergySite.SiteType.WIND_POWER_PLANT,
        )
        self.context = normalize_context(
            organization=self.org,
            energy_site=self.site,
            workplace=self.workplace,
        )

    def configure(self, module_id: str, scope_type: str) -> ModuleActivationRule:
        return transition_module_state(
            module_id=module_id,
            context=self.context,
            scope_type=scope_type,
            new_state=ModuleLifecycleState.CONFIGURED,
            actor_identity="tests/module-registry",
            reason="configure for focused test",
            configuration_ready=True,
        )

    def activate(self, module_id: str, scope_type: str) -> ModuleActivationRule:
        self.configure(module_id, scope_type)
        return transition_module_state(
            module_id=module_id,
            context=self.context,
            scope_type=scope_type,
            new_state=ModuleLifecycleState.ACTIVE,
            actor_identity="tests/module-registry",
            reason="activate for focused test",
        )

    def transition(self, module_id: str, scope_type: str, state: str) -> ModuleActivationRule:
        return transition_module_state(
            module_id=module_id,
            context=self.context,
            scope_type=scope_type,
            new_state=state,
            actor_identity="tests/module-registry",
            reason=f"transition to {state}",
        )

    def test_runtime_manifest_registry_uses_canonical_current_module_ids(self) -> None:
        self.assertEqual(manifest_for("OPJ").module_id, "OPJ")
        self.assertEqual(manifest_for("DEFECT").optional_integrations, ("OPJ",))
        self.assertEqual(
            manifest_for("MASTER-DATA").activation_policy,
            ActivationPolicy.ALWAYS_ON,
        )
        with self.assertRaises(KeyError):
            manifest_for("MADE-UP-MODULE")

    def test_optional_module_without_rule_fails_closed_to_available(self) -> None:
        effective = resolve_effective_state(module_id="OPJ", context=self.context)
        self.assertEqual(effective.state, ModuleLifecycleState.AVAILABLE)
        create_decision = decide_module_access(
            context=self.context,
            module_id="OPJ",
            capability_id="CAP-OPJ-REGISTER",
            operation=ModuleOperation.CREATE,
            entry_point_class=EntryPointClass.SERVICE,
        )
        history_decision = decide_module_access(
            context=self.context,
            module_id="OPJ",
            capability_id="CAP-OPJ-REGISTER",
            operation=ModuleOperation.HISTORY,
            entry_point_class=EntryPointClass.SERVICE,
        )
        self.assertFalse(create_decision.allowed)
        self.assertEqual(create_decision.reason_code, "MODULE_NOT_ACTIVE")
        self.assertTrue(history_decision.allowed)
        self.assertEqual(history_decision.reason_code, "ALLOW_RETAINED_HISTORY")

    def test_scope_membership_is_validated_without_inventing_workplace_site_hierarchy(self) -> None:
        context = normalize_context(
            organization=self.org,
            energy_site=self.site,
            workplace=self.workplace,
        )
        self.assertEqual(context.organization_id, self.org.pk)
        self.assertEqual(context.energy_site_id, self.site.pk)
        self.assertEqual(context.workplace_id, self.workplace.pk)
        with self.assertRaises(ValidationError):
            normalize_context(organization=self.org, energy_site=self.other_site)
        with self.assertRaises(ValidationError):
            normalize_context(organization=self.org, workplace=self.other_workplace)

    def test_exact_scope_rule_rejects_foreign_membership_and_duplicate(self) -> None:
        with self.assertRaises(ValidationError):
            ModuleActivationRule.objects.create(
                module_id="OPJ",
                scope_type=ModuleScopeType.WORKPLACE,
                scope_id=self.other_workplace.pk,
                organization_id=self.org.pk,
                state=ModuleLifecycleState.CONFIGURED,
                configuration_ready=True,
            )
        self.configure("OPJ", ModuleScopeType.ORGANIZATION)
        with self.assertRaises(ValidationError):
            ModuleActivationRule.objects.create(
                module_id="OPJ",
                scope_type=ModuleScopeType.ORGANIZATION,
                scope_id=self.org.pk,
                organization_id=self.org.pk,
                state=ModuleLifecycleState.CONFIGURED,
                configuration_ready=True,
            )

    def test_workplace_overrides_broader_inactive_for_phased_rollout(self) -> None:
        self.configure("OPJ", ModuleScopeType.ORGANIZATION)
        self.transition("OPJ", ModuleScopeType.ORGANIZATION, ModuleLifecycleState.INACTIVE)
        self.activate("OPJ", ModuleScopeType.WORKPLACE)
        effective = resolve_effective_state(module_id="OPJ", context=self.context)
        self.assertEqual(effective.state, ModuleLifecycleState.ACTIVE)
        self.assertEqual(effective.matched_scope_type, ModuleScopeType.WORKPLACE)

    def test_read_only_and_retired_are_restrictive_caps(self) -> None:
        self.activate("OPJ", ModuleScopeType.ORGANIZATION)
        self.activate("OPJ", ModuleScopeType.WORKPLACE)
        self.transition("OPJ", ModuleScopeType.ORGANIZATION, ModuleLifecycleState.READ_ONLY)
        read_only = resolve_effective_state(module_id="OPJ", context=self.context)
        self.assertEqual(read_only.state, ModuleLifecycleState.READ_ONLY)
        self.assertEqual(read_only.applied_restrictive_cap, ModuleLifecycleState.READ_ONLY)
        self.transition("OPJ", ModuleScopeType.ORGANIZATION, ModuleLifecycleState.RETIRED)
        retired = resolve_effective_state(module_id="OPJ", context=self.context)
        self.assertEqual(retired.state, ModuleLifecycleState.RETIRED)
        self.assertEqual(retired.applied_restrictive_cap, ModuleLifecycleState.RETIRED)

    def test_forbidden_direct_activation_is_denied_and_audited(self) -> None:
        with self.assertRaises(ValidationError):
            transition_module_state(
                module_id="OPJ",
                context=self.context,
                scope_type=ModuleScopeType.ORGANIZATION,
                new_state=ModuleLifecycleState.ACTIVE,
                actor_identity="tests/module-registry",
                reason="forbidden shortcut",
                configuration_ready=True,
            )
        audit = ModuleActivationAuditEvent.objects.get()
        self.assertEqual(audit.result, ModuleActivationAuditEvent.Result.DENIED)
        self.assertEqual(audit.denial_reason_code, "FORBIDDEN_TRANSITION")
        self.assertFalse(ModuleActivationRule.objects.exists())

    def test_active_requires_configuration_and_hard_dependency(self) -> None:
        self.configure("OPJ", ModuleScopeType.ORGANIZATION)
        base = manifest_for("OPJ")
        strict_manifest = ModuleManifest(
            module_id=base.module_id,
            human_name=base.human_name,
            activation_policy=base.activation_policy,
            supported_scopes=base.supported_scopes,
            required_dependencies=("WORKPLACE-DOCS",),
            optional_integrations=base.optional_integrations,
            capabilities=base.capabilities,
            operations=base.operations,
        )
        with patch.dict(_MANIFESTS, {"OPJ": strict_manifest}):
            with self.assertRaises(ValidationError):
                self.transition(
                    "OPJ",
                    ModuleScopeType.ORGANIZATION,
                    ModuleLifecycleState.ACTIVE,
                )
        audit = ModuleActivationAuditEvent.objects.filter(result="DENIED").latest("pk")
        self.assertEqual(audit.denial_reason_code, "REQUIRED_DEPENDENCY_INACTIVE")

    def test_optional_integration_does_not_block_primary_module_activation(self) -> None:
        self.activate("DEFECT", ModuleScopeType.ORGANIZATION)
        defect = resolve_effective_state(module_id="DEFECT", context=self.context)
        opj = resolve_effective_state(module_id="OPJ", context=self.context)
        self.assertEqual(defect.state, ModuleLifecycleState.ACTIVE)
        self.assertEqual(opj.state, ModuleLifecycleState.AVAILABLE)

    def test_read_only_denies_service_mutation_but_preserves_history(self) -> None:
        self.activate("OPJ", ModuleScopeType.ORGANIZATION)
        self.transition("OPJ", ModuleScopeType.ORGANIZATION, ModuleLifecycleState.READ_ONLY)
        with self.assertRaises(PermissionDenied):
            require_module_access(
                context=self.context,
                module_id="OPJ",
                capability_id="CAP-OPJ-REGISTER",
                operation=ModuleOperation.CREATE,
                entry_point_class=EntryPointClass.SERVICE,
            )
        decision = require_module_access(
            context=self.context,
            module_id="OPJ",
            capability_id="CAP-OPJ-REGISTER",
            operation=ModuleOperation.HISTORY,
            entry_point_class=EntryPointClass.SERVICE,
        )
        self.assertTrue(decision.allowed)

    def test_unknown_access_dimensions_fail_closed(self) -> None:
        common = {
            "context": self.context,
            "module_id": "OPJ",
            "capability_id": "CAP-OPJ-REGISTER",
            "operation": ModuleOperation.READ,
            "entry_point_class": EntryPointClass.SERVICE,
        }
        self.assertEqual(
            decide_module_access(**{**common, "module_id": "UNKNOWN"}).reason_code,
            "UNKNOWN_MODULE",
        )
        self.assertEqual(
            decide_module_access(**{**common, "capability_id": "UNKNOWN"}).reason_code,
            "UNKNOWN_CAPABILITY",
        )
        self.assertEqual(
            decide_module_access(**{**common, "operation": "UNKNOWN"}).reason_code,
            "UNKNOWN_OPERATION",
        )
        self.assertEqual(
            decide_module_access(
                **{**common, "entry_point_class": "UNKNOWN"}
            ).reason_code,
            "UNKNOWN_ENTRY_POINT",
        )

    def test_reactivation_reuses_same_rule_identity_and_history(self) -> None:
        rule = self.activate("OPJ", ModuleScopeType.ORGANIZATION)
        original_pk = rule.pk
        self.transition("OPJ", ModuleScopeType.ORGANIZATION, ModuleLifecycleState.INACTIVE)
        self.transition("OPJ", ModuleScopeType.ORGANIZATION, ModuleLifecycleState.CONFIGURED)
        reactivated = self.transition(
            "OPJ",
            ModuleScopeType.ORGANIZATION,
            ModuleLifecycleState.ACTIVE,
        )
        self.assertEqual(reactivated.pk, original_pk)
        self.assertEqual(ModuleActivationRule.objects.count(), 1)
        self.assertEqual(ModuleActivationAuditEvent.objects.count(), 5)

    def test_activation_audit_is_append_only(self) -> None:
        self.configure("OPJ", ModuleScopeType.ORGANIZATION)
        audit = ModuleActivationAuditEvent.objects.get()
        audit.reason = "attempted rewrite"
        with self.assertRaises(ValidationError):
            audit.save()
        with self.assertRaises(ValidationError):
            ModuleActivationAuditEvent.objects.all().delete()
        self.assertEqual(ModuleActivationAuditEvent.objects.count(), 1)

    def test_existing_history_is_not_deleted_by_deactivation(self) -> None:
        rule = self.activate("OPJ", ModuleScopeType.ORGANIZATION)
        self.transition("OPJ", ModuleScopeType.ORGANIZATION, ModuleLifecycleState.INACTIVE)
        rule.refresh_from_db()
        self.assertEqual(rule.state, ModuleLifecycleState.INACTIVE)
        self.assertEqual(ModuleActivationRule.objects.count(), 1)
        self.assertGreaterEqual(ModuleActivationAuditEvent.objects.count(), 3)

    def test_direct_rule_save_bypass_is_rejected(self) -> None:
        direct = ModuleActivationRule(
            module_id="OPJ",
            scope_type=ModuleScopeType.ORGANIZATION,
            scope_id=self.org.pk,
            organization_id=self.org.pk,
            state=ModuleLifecycleState.CONFIGURED,
            configuration_ready=True,
        )
        with self.assertRaises(ValidationError):
            direct.save()

        rule = self.configure("OPJ", ModuleScopeType.ORGANIZATION)
        rule.state = ModuleLifecycleState.ACTIVE
        with self.assertRaises(ValidationError):
            rule.save()
        rule.refresh_from_db()
        self.assertEqual(rule.state, ModuleLifecycleState.CONFIGURED)

    def test_mixed_scope_module_sets_are_deterministic(self) -> None:
        self.configure("OPJ", ModuleScopeType.ORGANIZATION)
        self.transition(
            "OPJ",
            ModuleScopeType.ORGANIZATION,
            ModuleLifecycleState.INACTIVE,
        )
        self.activate("OPJ", ModuleScopeType.ENERGY_SITE)
        self.activate("DEFECT", ModuleScopeType.WORKPLACE)

        organization_context = normalize_context(organization=self.org)
        site_context = normalize_context(
            organization=self.org,
            energy_site=self.site,
        )
        workplace_context = normalize_context(
            organization=self.org,
            energy_site=self.site,
            workplace=self.workplace,
        )
        other_context = normalize_context(
            organization=self.other_org,
            energy_site=self.other_site,
            workplace=self.other_workplace,
        )

        self.assertEqual(
            resolve_effective_state(
                module_id="OPJ", context=organization_context
            ).state,
            ModuleLifecycleState.INACTIVE,
        )
        self.assertEqual(
            resolve_effective_state(module_id="OPJ", context=site_context).state,
            ModuleLifecycleState.ACTIVE,
        )
        self.assertEqual(
            resolve_effective_state(
                module_id="DEFECT", context=site_context
            ).state,
            ModuleLifecycleState.AVAILABLE,
        )
        self.assertEqual(
            resolve_effective_state(
                module_id="DEFECT", context=workplace_context
            ).state,
            ModuleLifecycleState.ACTIVE,
        )
        self.assertEqual(
            resolve_effective_state(module_id="OPJ", context=other_context).state,
            ModuleLifecycleState.AVAILABLE,
        )
        self.assertEqual(
            resolve_effective_state(
                module_id="DEFECT", context=other_context
            ).state,
            ModuleLifecycleState.AVAILABLE,
        )
