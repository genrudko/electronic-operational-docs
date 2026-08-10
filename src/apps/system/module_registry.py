from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.equipment.models import EnergySite
from apps.organizations.models import Organization, Workplace

from .models import (
    ModuleActivationAuditEvent,
    ModuleActivationRule,
    ModuleLifecycleState,
    ModuleScopeType,
)


class ActivationPolicy(StrEnum):
    ALWAYS_ON = "ALWAYS_ON"
    SCOPED_OPTIONAL = "SCOPED_OPTIONAL"


class EntryPointClass(StrEnum):
    NAVIGATION_UI = "NAVIGATION_UI"
    HTTP_ROUTE = "HTTP_ROUTE"
    SERVICE = "SERVICE"
    API = "API"
    ADMIN = "ADMIN"
    MANAGEMENT_COMMAND = "MANAGEMENT_COMMAND"
    EXPORT = "EXPORT"
    BACKGROUND_JOB = "BACKGROUND_JOB"
    CROSS_MODULE_ACTION = "CROSS_MODULE_ACTION"


class ModuleOperation(StrEnum):
    READ = "READ"
    HISTORY = "HISTORY"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    TRANSITION = "TRANSITION"
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    BACKGROUND_MUTATE = "BACKGROUND_MUTATE"


MUTATING_OPERATIONS: Final[frozenset[ModuleOperation]] = frozenset(
    {
        ModuleOperation.CREATE,
        ModuleOperation.UPDATE,
        ModuleOperation.TRANSITION,
        ModuleOperation.DELETE,
        ModuleOperation.BACKGROUND_MUTATE,
    }
)
READ_OPERATIONS: Final[frozenset[ModuleOperation]] = frozenset(
    {ModuleOperation.READ, ModuleOperation.HISTORY, ModuleOperation.EXPORT}
)


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    module_id: str
    human_name: str
    activation_policy: ActivationPolicy
    supported_scopes: frozenset[str]
    required_dependencies: tuple[str, ...]
    optional_integrations: tuple[str, ...]
    capabilities: frozenset[str]
    operations: frozenset[ModuleOperation]
    activation_prerequisites: tuple[str, ...] = ("CONFIGURATION_READY",)
    manifest_contract_version: str = "1"
    lifecycle_contract_version: str = "1"
    history_policy: str = "PRESERVE"
    migration_policy: str = "ALWAYS_WITH_PRODUCT"


ALL_SCOPES: Final[frozenset[str]] = frozenset(ModuleScopeType.values)
ALL_OPERATIONS: Final[frozenset[ModuleOperation]] = frozenset(ModuleOperation)


def _manifest(
    module_id: str,
    human_name: str,
    *,
    policy: ActivationPolicy,
    capabilities: tuple[str, ...],
    dependencies: tuple[str, ...] = (),
    optional_integrations: tuple[str, ...] = (),
) -> ModuleManifest:
    return ModuleManifest(
        module_id=module_id,
        human_name=human_name,
        activation_policy=policy,
        supported_scopes=ALL_SCOPES,
        required_dependencies=dependencies,
        optional_integrations=optional_integrations,
        capabilities=frozenset(capabilities),
        operations=ALL_OPERATIONS,
        activation_prerequisites=() if policy is ActivationPolicy.ALWAYS_ON else ("CONFIGURATION_READY",),
    )


# Runtime manifests cover the canonical module identities that already have product
# code in the repository. Planned-only catalogue modules are intentionally not made
# activatable merely by appearing in planning documentation.
_MANIFESTS: Final[dict[str, ModuleManifest]] = {
    item.module_id: item
    for item in (
        _manifest(
            "PLATFORM",
            "Платформенные механизмы",
            policy=ActivationPolicy.ALWAYS_ON,
            capabilities=("CAP-PLATFORM-RUNTIME",),
        ),
        _manifest(
            "UX",
            "Общая UX-платформа",
            policy=ActivationPolicy.ALWAYS_ON,
            capabilities=("CAP-UX-SHARED", "CAP-UX-THEME"),
            dependencies=("PLATFORM",),
        ),
        _manifest(
            "NORMATIVE-EVIDENCE",
            "Нормативные режимы и evidence-события",
            policy=ActivationPolicy.ALWAYS_ON,
            capabilities=(
                "CAP-NORMATIVE-LEGAL-MODES",
                "CAP-NORMATIVE-EVENTS",
                "CAP-NORMATIVE-PEP",
            ),
            dependencies=("PLATFORM",),
        ),
        _manifest(
            "MASTER-DATA",
            "Организации, объекты и оборудование",
            policy=ActivationPolicy.ALWAYS_ON,
            capabilities=(
                "CAP-MASTER-EQUIPMENT",
                "CAP-MASTER-ORG",
                "CAP-MASTER-DISPATCH",
            ),
            dependencies=("PLATFORM",),
        ),
        _manifest(
            "PERSONNEL-AUTHORITY",
            "Персонал и оперативные полномочия",
            policy=ActivationPolicy.ALWAYS_ON,
            capabilities=(
                "CAP-PERSONNEL-REGISTRY",
                "CAP-AUTHORITY-GRANTS",
                "CAP-AUTHORITY-ACTION-TIME",
                "CAP-AUTHORITY-EXTERNAL",
            ),
            dependencies=("MASTER-DATA", "NORMATIVE-EVIDENCE"),
        ),
        _manifest(
            "WORKPLACE-DOCS",
            "Документация рабочего места",
            policy=ActivationPolicy.SCOPED_OPTIONAL,
            capabilities=("CAP-WORKPLACE-DOCS-DEMO",),
            dependencies=("MASTER-DATA", "PERSONNEL-AUTHORITY"),
        ),
        _manifest(
            "OPJ",
            "Оперативный журнал и переговоры",
            policy=ActivationPolicy.SCOPED_OPTIONAL,
            capabilities=(
                "CAP-OPJ-DEMO",
                "CAP-OPJ-DRAFT",
                "CAP-OPJ-REGISTER",
                "CAP-OPJ-CORRECTION",
                "CAP-OPJ-COMMUNICATION",
            ),
            dependencies=("MASTER-DATA", "PERSONNEL-AUTHORITY"),
        ),
        _manifest(
            "DEFECT",
            "Журнал дефектов оборудования",
            policy=ActivationPolicy.SCOPED_OPTIONAL,
            capabilities=(
                "CAP-DEFECT-DEMO",
                "CAP-DEFECT-REGISTRY",
                "CAP-DEFECT-LIFECYCLE",
                "CAP-DEFECT-OPJ-LINK",
            ),
            dependencies=("MASTER-DATA",),
            optional_integrations=("OPJ",),
        ),
    )
}


def manifests() -> tuple[ModuleManifest, ...]:
    return tuple(_MANIFESTS[module_id] for module_id in sorted(_MANIFESTS))


def manifest_for(module_id: str) -> ModuleManifest:
    normalized = str(module_id).strip().upper()
    try:
        return _MANIFESTS[normalized]
    except KeyError as error:
        raise KeyError(f"unknown EOD module: {normalized}") from error


@dataclass(frozen=True, slots=True)
class ModuleScopeContext:
    organization_id: int
    energy_site_id: int | None = None
    workplace_id: int | None = None


@dataclass(frozen=True, slots=True)
class EffectiveModuleState:
    module_id: str
    state: str
    matched_scope_type: str | None
    matched_scope_id: int | None
    explicit_rule_id: int | None
    applied_restrictive_cap: str | None = None


@dataclass(frozen=True, slots=True)
class ModuleAccessDecision:
    allowed: bool
    module_id: str
    capability_id: str
    operation: str
    entry_point_class: str
    effective_state: str
    reason_code: str


def normalize_context(
    *,
    organization: Organization | int,
    energy_site: EnergySite | int | None = None,
    workplace: Workplace | int | None = None,
) -> ModuleScopeContext:
    organization_id = organization.pk if isinstance(organization, Organization) else int(organization)
    if not Organization.objects.filter(pk=organization_id).exists():
        raise ValidationError("Неизвестная организация в контексте модуля.")

    energy_site_id: int | None = None
    if energy_site is not None:
        energy_site_id = energy_site.pk if isinstance(energy_site, EnergySite) else int(energy_site)
        if not EnergySite.objects.filter(
            pk=energy_site_id,
            organization_id=organization_id,
        ).exists():
            raise ValidationError("Энергообъект не относится к указанной организации.")

    workplace_id: int | None = None
    if workplace is not None:
        workplace_id = workplace.pk if isinstance(workplace, Workplace) else int(workplace)
        if not Workplace.objects.filter(
            pk=workplace_id,
            organization_id=organization_id,
        ).exists():
            raise ValidationError("Рабочее место не относится к указанной организации.")

    return ModuleScopeContext(
        organization_id=organization_id,
        energy_site_id=energy_site_id,
        workplace_id=workplace_id,
    )


def _candidate_rules(module_id: str, context: ModuleScopeContext) -> list[ModuleActivationRule]:
    keys = [(ModuleScopeType.ORGANIZATION, context.organization_id)]
    if context.energy_site_id is not None:
        keys.append((ModuleScopeType.ENERGY_SITE, context.energy_site_id))
    if context.workplace_id is not None:
        keys.append((ModuleScopeType.WORKPLACE, context.workplace_id))
    rules = list(
        ModuleActivationRule.objects.filter(
            module_id=module_id,
            organization_id=context.organization_id,
        )
    )
    allowed_keys = set(keys)
    return [rule for rule in rules if (rule.scope_type, rule.scope_id) in allowed_keys]


def resolve_effective_state(
    *,
    module_id: str,
    context: ModuleScopeContext,
) -> EffectiveModuleState:
    manifest = manifest_for(module_id)
    if manifest.activation_policy is ActivationPolicy.ALWAYS_ON:
        return EffectiveModuleState(
            module_id=manifest.module_id,
            state=ModuleLifecycleState.ACTIVE,
            matched_scope_type=None,
            matched_scope_id=None,
            explicit_rule_id=None,
        )

    rules = _candidate_rules(manifest.module_id, context)
    retired = next((rule for rule in rules if rule.state == ModuleLifecycleState.RETIRED), None)
    if retired is not None:
        return EffectiveModuleState(
            module_id=manifest.module_id,
            state=ModuleLifecycleState.RETIRED,
            matched_scope_type=retired.scope_type,
            matched_scope_id=retired.scope_id,
            explicit_rule_id=retired.pk,
            applied_restrictive_cap=ModuleLifecycleState.RETIRED,
        )
    read_only = next((rule for rule in rules if rule.state == ModuleLifecycleState.READ_ONLY), None)
    if read_only is not None:
        return EffectiveModuleState(
            module_id=manifest.module_id,
            state=ModuleLifecycleState.READ_ONLY,
            matched_scope_type=read_only.scope_type,
            matched_scope_id=read_only.scope_id,
            explicit_rule_id=read_only.pk,
            applied_restrictive_cap=ModuleLifecycleState.READ_ONLY,
        )

    precedence = {
        ModuleScopeType.ORGANIZATION: 1,
        ModuleScopeType.ENERGY_SITE: 2,
        ModuleScopeType.WORKPLACE: 3,
    }
    if rules:
        selected = max(rules, key=lambda rule: precedence[rule.scope_type])
        return EffectiveModuleState(
            module_id=manifest.module_id,
            state=selected.state,
            matched_scope_type=selected.scope_type,
            matched_scope_id=selected.scope_id,
            explicit_rule_id=selected.pk,
        )
    return EffectiveModuleState(
        module_id=manifest.module_id,
        state=ModuleLifecycleState.AVAILABLE,
        matched_scope_type=None,
        matched_scope_id=None,
        explicit_rule_id=None,
    )


_ALLOWED_TRANSITIONS: Final[dict[str, frozenset[str]]] = {
    ModuleLifecycleState.AVAILABLE: frozenset({ModuleLifecycleState.CONFIGURED}),
    ModuleLifecycleState.CONFIGURED: frozenset(
        {ModuleLifecycleState.ACTIVE, ModuleLifecycleState.INACTIVE, ModuleLifecycleState.RETIRED}
    ),
    ModuleLifecycleState.ACTIVE: frozenset(
        {ModuleLifecycleState.READ_ONLY, ModuleLifecycleState.INACTIVE, ModuleLifecycleState.RETIRED}
    ),
    ModuleLifecycleState.READ_ONLY: frozenset(
        {ModuleLifecycleState.ACTIVE, ModuleLifecycleState.INACTIVE, ModuleLifecycleState.RETIRED}
    ),
    ModuleLifecycleState.INACTIVE: frozenset(
        {ModuleLifecycleState.CONFIGURED, ModuleLifecycleState.RETIRED}
    ),
    ModuleLifecycleState.RETIRED: frozenset({ModuleLifecycleState.CONFIGURED}),
}


def _rule_scope_context(rule: ModuleActivationRule) -> ModuleScopeContext:
    return ModuleScopeContext(
        organization_id=rule.organization_id,
        energy_site_id=(rule.scope_id if rule.scope_type == ModuleScopeType.ENERGY_SITE else None),
        workplace_id=(rule.scope_id if rule.scope_type == ModuleScopeType.WORKPLACE else None),
    )


def _dependency_validation(manifest: ModuleManifest, context: ModuleScopeContext) -> tuple[bool, str]:
    failures: list[str] = []
    for dependency_id in manifest.required_dependencies:
        dependency_state = resolve_effective_state(module_id=dependency_id, context=context)
        if dependency_state.state != ModuleLifecycleState.ACTIVE:
            failures.append(f"{dependency_id}:{dependency_state.state}")
    if failures:
        return False, "required dependencies not ACTIVE: " + ", ".join(failures)
    return True, "required dependencies ACTIVE"


def _write_audit(
    *,
    module_id: str,
    scope_type: str,
    scope_id: int,
    organization_id: int,
    previous_explicit_state: str,
    previous_effective_state: str,
    requested_new_state: str,
    resulting_effective_state: str,
    actor_identity: str,
    reason: str,
    configuration_validation: str,
    dependency_validation: str,
    result: str,
    denial_reason_code: str = "",
) -> ModuleActivationAuditEvent:
    manifest = manifest_for(module_id)
    return ModuleActivationAuditEvent.objects.create(
        module_id=manifest.module_id,
        scope_type=scope_type,
        scope_id=scope_id,
        organization_id=organization_id,
        previous_explicit_state=previous_explicit_state,
        previous_effective_state=previous_effective_state,
        requested_new_state=requested_new_state,
        resulting_effective_state=resulting_effective_state,
        actor_identity=actor_identity,
        reason=reason,
        configuration_validation=configuration_validation,
        dependency_validation=dependency_validation,
        result=result,
        denial_reason_code=denial_reason_code,
        manifest_contract_version=manifest.manifest_contract_version,
    )


def transition_module_state(
    *,
    module_id: str,
    context: ModuleScopeContext,
    scope_type: str,
    new_state: str,
    actor_identity: str,
    reason: str,
    configuration_ready: bool | None = None,
    configuration: dict[str, object] | None = None,
) -> ModuleActivationRule:
    manifest = manifest_for(module_id)
    if manifest.activation_policy is ActivationPolicy.ALWAYS_ON:
        raise ValidationError("ALWAYS_ON modules do not accept scoped lifecycle rules.")
    if scope_type not in manifest.supported_scopes:
        raise ValidationError("Модуль не поддерживает указанную область активации.")
    if new_state not in ModuleLifecycleState.values:
        raise ValidationError("Неизвестное lifecycle state модуля.")
    normalized_actor = actor_identity.strip()
    normalized_reason = reason.strip()
    if not normalized_actor or not normalized_reason:
        raise ValidationError("Для lifecycle transition требуются actor и reason.")

    if scope_type == ModuleScopeType.ORGANIZATION:
        scope_id = context.organization_id
    elif scope_type == ModuleScopeType.ENERGY_SITE and context.energy_site_id is not None:
        scope_id = context.energy_site_id
    elif scope_type == ModuleScopeType.WORKPLACE and context.workplace_id is not None:
        scope_id = context.workplace_id
    else:
        raise ValidationError("Запрошенная область отсутствует в нормализованном контексте.")

    previous_effective = resolve_effective_state(module_id=manifest.module_id, context=context)
    rule = ModuleActivationRule.objects.filter(
        module_id=manifest.module_id,
        scope_type=scope_type,
        scope_id=scope_id,
    ).first()
    previous_explicit = rule.state if rule is not None else ModuleLifecycleState.AVAILABLE

    allowed = _ALLOWED_TRANSITIONS.get(previous_explicit, frozenset())
    if new_state not in allowed:
        _write_audit(
            module_id=manifest.module_id,
            scope_type=scope_type,
            scope_id=scope_id,
            organization_id=context.organization_id,
            previous_explicit_state=previous_explicit if rule is not None else "",
            previous_effective_state=previous_effective.state,
            requested_new_state=new_state,
            resulting_effective_state=previous_effective.state,
            actor_identity=normalized_actor,
            reason=normalized_reason,
            configuration_validation="not evaluated",
            dependency_validation="not evaluated",
            result=ModuleActivationAuditEvent.Result.DENIED,
            denial_reason_code="FORBIDDEN_TRANSITION",
        )
        raise ValidationError(
            f"Запрещён переход {previous_explicit} -> {new_state}."
        )

    prospective_ready = (
        configuration_ready
        if configuration_ready is not None
        else (rule.configuration_ready if rule is not None else False)
    )
    config_validation = "ready" if prospective_ready else "not ready"
    dependency_ok, dependency_validation = _dependency_validation(manifest, context)
    if new_state == ModuleLifecycleState.ACTIVE and (
        not prospective_ready or not dependency_ok
    ):
        reason_code = "CONFIGURATION_NOT_READY" if not prospective_ready else "REQUIRED_DEPENDENCY_INACTIVE"
        _write_audit(
            module_id=manifest.module_id,
            scope_type=scope_type,
            scope_id=scope_id,
            organization_id=context.organization_id,
            previous_explicit_state=previous_explicit if rule is not None else "",
            previous_effective_state=previous_effective.state,
            requested_new_state=new_state,
            resulting_effective_state=previous_effective.state,
            actor_identity=normalized_actor,
            reason=normalized_reason,
            configuration_validation=config_validation,
            dependency_validation=dependency_validation,
            result=ModuleActivationAuditEvent.Result.DENIED,
            denial_reason_code=reason_code,
        )
        raise ValidationError("Модуль нельзя активировать до успешной проверки конфигурации и зависимостей.")

    try:
        with transaction.atomic():
            if rule is None:
                rule = ModuleActivationRule(
                    module_id=manifest.module_id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    organization_id=context.organization_id,
                    state=new_state,
                    configuration_ready=prospective_ready,
                    configuration=dict(configuration or {}),
                )
            else:
                rule.state = new_state
                if configuration_ready is not None:
                    rule.configuration_ready = configuration_ready
                if configuration is not None:
                    rule.configuration = dict(configuration)
            rule.save()
            resulting = resolve_effective_state(module_id=manifest.module_id, context=context)
            _write_audit(
                module_id=manifest.module_id,
                scope_type=scope_type,
                scope_id=scope_id,
                organization_id=context.organization_id,
                previous_explicit_state=previous_explicit if rule.pk is not None else "",
                previous_effective_state=previous_effective.state,
                requested_new_state=new_state,
                resulting_effective_state=resulting.state,
                actor_identity=normalized_actor,
                reason=normalized_reason,
                configuration_validation=config_validation,
                dependency_validation=dependency_validation,
                result=ModuleActivationAuditEvent.Result.ALLOWED,
            )
    except IntegrityError as error:
        _write_audit(
            module_id=manifest.module_id,
            scope_type=scope_type,
            scope_id=scope_id,
            organization_id=context.organization_id,
            previous_explicit_state=previous_explicit if rule is not None else "",
            previous_effective_state=previous_effective.state,
            requested_new_state=new_state,
            resulting_effective_state=previous_effective.state,
            actor_identity=normalized_actor,
            reason=normalized_reason,
            configuration_validation=config_validation,
            dependency_validation=dependency_validation,
            result=ModuleActivationAuditEvent.Result.DENIED,
            denial_reason_code="DUPLICATE_SCOPE_RULE",
        )
        raise ValidationError("Для этого модуля и области уже существует правило.") from error
    return rule


def decide_module_access(
    *,
    context: ModuleScopeContext,
    module_id: str,
    capability_id: str,
    operation: str | ModuleOperation,
    entry_point_class: str | EntryPointClass,
) -> ModuleAccessDecision:
    normalized_module = str(module_id).strip().upper()
    normalized_capability = str(capability_id).strip().upper()
    try:
        manifest = manifest_for(normalized_module)
    except KeyError:
        return ModuleAccessDecision(
            allowed=False,
            module_id=normalized_module,
            capability_id=normalized_capability,
            operation=str(operation),
            entry_point_class=str(entry_point_class),
            effective_state="UNKNOWN",
            reason_code="UNKNOWN_MODULE",
        )
    if normalized_capability not in manifest.capabilities:
        return ModuleAccessDecision(False, manifest.module_id, normalized_capability, str(operation), str(entry_point_class), "UNKNOWN", "UNKNOWN_CAPABILITY")
    try:
        normalized_operation = ModuleOperation(str(operation))
    except ValueError:
        return ModuleAccessDecision(False, manifest.module_id, normalized_capability, str(operation), str(entry_point_class), "UNKNOWN", "UNKNOWN_OPERATION")
    try:
        normalized_entry_point = EntryPointClass(str(entry_point_class))
    except ValueError:
        return ModuleAccessDecision(False, manifest.module_id, normalized_capability, normalized_operation.value, str(entry_point_class), "UNKNOWN", "UNKNOWN_ENTRY_POINT")
    if normalized_operation not in manifest.operations:
        return ModuleAccessDecision(False, manifest.module_id, normalized_capability, normalized_operation.value, normalized_entry_point.value, "UNKNOWN", "OPERATION_NOT_DECLARED")

    effective = resolve_effective_state(module_id=manifest.module_id, context=context)
    if effective.state == ModuleLifecycleState.ACTIVE:
        dependency_ok, _ = _dependency_validation(manifest, context)
        if normalized_operation in MUTATING_OPERATIONS and not dependency_ok:
            return ModuleAccessDecision(False, manifest.module_id, normalized_capability, normalized_operation.value, normalized_entry_point.value, effective.state, "REQUIRED_DEPENDENCY_INACTIVE")
        return ModuleAccessDecision(True, manifest.module_id, normalized_capability, normalized_operation.value, normalized_entry_point.value, effective.state, "ALLOW_ACTIVE")
    if effective.state == ModuleLifecycleState.READ_ONLY:
        if normalized_operation in READ_OPERATIONS:
            return ModuleAccessDecision(True, manifest.module_id, normalized_capability, normalized_operation.value, normalized_entry_point.value, effective.state, "ALLOW_READ_ONLY")
        return ModuleAccessDecision(False, manifest.module_id, normalized_capability, normalized_operation.value, normalized_entry_point.value, effective.state, "READ_ONLY_MUTATION_DENIED")
    if normalized_operation in READ_OPERATIONS and manifest.history_policy == "PRESERVE":
        return ModuleAccessDecision(True, manifest.module_id, normalized_capability, normalized_operation.value, normalized_entry_point.value, effective.state, "ALLOW_RETAINED_HISTORY")
    return ModuleAccessDecision(False, manifest.module_id, normalized_capability, normalized_operation.value, normalized_entry_point.value, effective.state, "MODULE_NOT_ACTIVE")


def require_module_access(**kwargs: object) -> ModuleAccessDecision:
    decision = decide_module_access(**kwargs)  # type: ignore[arg-type]
    if not decision.allowed:
        raise PermissionDenied(
            f"Module access denied: {decision.module_id}/{decision.capability_id} "
            f"{decision.operation} ({decision.reason_code})."
        )
    return decision
