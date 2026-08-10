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
    {
        ModuleOperation.READ,
        ModuleOperation.HISTORY,
        ModuleOperation.EXPORT,
    }
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
    prerequisites = () if policy is ActivationPolicy.ALWAYS_ON else ("CONFIGURATION_READY",)
    return ModuleManifest(
        module_id=module_id,
        human_name=human_name,
        activation_policy=policy,
        supported_scopes=ALL_SCOPES,
        required_dependencies=dependencies,
        optional_integrations=optional_integrations,
        capabilities=frozenset(capabilities),
        operations=ALL_OPERATIONS,
        activation_prerequisites=prerequisites,
    )


# Only canonical identities backed by current product code are runtime manifests.
# Planned-only catalogue entries do not become activatable merely because they exist
# in planning documentation.
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


def _context_for_scope(
    context: ModuleScopeContext,
    scope_type: str,
) -> ModuleScopeContext:
    if scope_type == ModuleScopeType.ORGANIZATION:
        return ModuleScopeContext(organization_id=context.organization_id)
    if scope_type == ModuleScopeType.ENERGY_SITE and context.energy_site_id is not None:
        return ModuleScopeContext(
            organization_id=context.organization_id,
            energy_site_id=context.energy_site_id,
        )
    if scope_type == ModuleScopeType.WORKPLACE and context.workplace_id is not None:
        return ModuleScopeContext(
            organization_id=context.organization_id,
            workplace_id=context.workplace_id,
        )
    raise ValidationError("Запрошенная область отсутствует в нормализованном контексте.")


def _scope_id(context: ModuleScopeContext, scope_type: str) -> int:
    if scope_type == ModuleScopeType.ORGANIZATION:
        return context.organization_id
    if scope_type == ModuleScopeType.ENERGY_SITE and context.energy_site_id is not None:
        return context.energy_site_id
    if scope_type == ModuleScopeType.WORKPLACE and context.workplace_id is not None:
        return context.workplace_id
    raise ValidationError("Запрошенная область отсутствует в нормализованном контексте.")


def _scope_rank(scope_type: str) -> int:
    return {
        ModuleScopeType.ORGANIZATION: 1,
        ModuleScopeType.ENERGY_SITE: 2,
        ModuleScopeType.WORKPLACE: 3,
    }[scope_type]


def _candidate_rules(
    module_id: str,
    context: ModuleScopeContext,
) -> list[ModuleActivationRule]:
    keys = {(ModuleScopeType.ORGANIZATION, context.organization_id)}
    if context.energy_site_id is not None:
        keys.add((ModuleScopeType.ENERGY_SITE, context.energy_site_id))
    if context.workplace_id is not None:
        keys.add((ModuleScopeType.WORKPLACE, context.workplace_id))
    rules = ModuleActivationRule.objects.filter(
        module_id=module_id,
        organization_id=context.organization_id,
    )
    return [rule for rule in rules if (rule.scope_type, rule.scope_id) in keys]


def _strongest_cap(
    rules: list[ModuleActivationRule],
) -> ModuleActivationRule | None:
    for state in (ModuleLifecycleState.RETIRED, ModuleLifecycleState.READ_ONLY):
        matches = [rule for rule in rules if rule.state == state]
        if matches:
            return max(matches, key=lambda rule: _scope_rank(rule.scope_type))
    return None


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
    restrictive_cap = _strongest_cap(rules)
    if restrictive_cap is not None:
        return EffectiveModuleState(
            module_id=manifest.module_id,
            state=restrictive_cap.state,
            matched_scope_type=restrictive_cap.scope_type,
            matched_scope_id=restrictive_cap.scope_id,
            explicit_rule_id=restrictive_cap.pk,
            applied_restrictive_cap=restrictive_cap.state,
        )

    if rules:
        selected = max(rules, key=lambda rule: _scope_rank(rule.scope_type))
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
        {
            ModuleLifecycleState.ACTIVE,
            ModuleLifecycleState.INACTIVE,
            ModuleLifecycleState.RETIRED,
        }
    ),
    ModuleLifecycleState.ACTIVE: frozenset(
        {
            ModuleLifecycleState.READ_ONLY,
            ModuleLifecycleState.INACTIVE,
            ModuleLifecycleState.RETIRED,
        }
    ),
    ModuleLifecycleState.READ_ONLY: frozenset(
        {
            ModuleLifecycleState.ACTIVE,
            ModuleLifecycleState.INACTIVE,
            ModuleLifecycleState.RETIRED,
        }
    ),
    ModuleLifecycleState.INACTIVE: frozenset(
        {ModuleLifecycleState.CONFIGURED, ModuleLifecycleState.RETIRED}
    ),
    ModuleLifecycleState.RETIRED: frozenset({ModuleLifecycleState.CONFIGURED}),
}


def _dependency_validation(
    manifest: ModuleManifest,
    context: ModuleScopeContext,
) -> tuple[bool, str]:
    failures: list[str] = []
    for dependency_id in manifest.required_dependencies:
        dependency = resolve_effective_state(
            module_id=dependency_id,
            context=context,
        )
        if dependency.state != ModuleLifecycleState.ACTIVE:
            failures.append(f"{dependency_id}:{dependency.state}")
    if failures:
        return False, "required dependencies not ACTIVE: " + ", ".join(failures)
    return True, "required dependencies ACTIVE"


def _persist_activation_rule(rule: ModuleActivationRule) -> None:
    """Persist lifecycle state only after transition service validation."""

    rule.full_clean()
    super(ModuleActivationRule, rule).save()


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


def _audit_denial(
    *,
    manifest: ModuleManifest,
    scope_type: str,
    scope_id: int,
    context: ModuleScopeContext,
    previous_explicit_state: str,
    previous_effective_state: str,
    requested_new_state: str,
    actor_identity: str,
    reason: str,
    configuration_validation: str,
    dependency_validation: str,
    denial_reason_code: str,
) -> None:
    _write_audit(
        module_id=manifest.module_id,
        scope_type=scope_type,
        scope_id=scope_id,
        organization_id=context.organization_id,
        previous_explicit_state=previous_explicit_state,
        previous_effective_state=previous_effective_state,
        requested_new_state=requested_new_state,
        resulting_effective_state=previous_effective_state,
        actor_identity=actor_identity,
        reason=reason,
        configuration_validation=configuration_validation,
        dependency_validation=dependency_validation,
        result=ModuleActivationAuditEvent.Result.DENIED,
        denial_reason_code=denial_reason_code,
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

    actor = actor_identity.strip()
    transition_reason = reason.strip()
    if not actor or not transition_reason:
        raise ValidationError("Для lifecycle transition требуются actor и reason.")

    scoped_context = _context_for_scope(context, scope_type)
    scope_id = _scope_id(scoped_context, scope_type)
    previous_effective = resolve_effective_state(
        module_id=manifest.module_id,
        context=scoped_context,
    )
    rule = ModuleActivationRule.objects.filter(
        module_id=manifest.module_id,
        scope_type=scope_type,
        scope_id=scope_id,
    ).first()
    previous_state = rule.state if rule is not None else ModuleLifecycleState.AVAILABLE
    audit_explicit_state = rule.state if rule is not None else ""

    if new_state not in _ALLOWED_TRANSITIONS.get(previous_state, frozenset()):
        _audit_denial(
            manifest=manifest,
            scope_type=scope_type,
            scope_id=scope_id,
            context=scoped_context,
            previous_explicit_state=audit_explicit_state,
            previous_effective_state=previous_effective.state,
            requested_new_state=new_state,
            actor_identity=actor,
            reason=transition_reason,
            configuration_validation="not evaluated",
            dependency_validation="not evaluated",
            denial_reason_code="FORBIDDEN_TRANSITION",
        )
        raise ValidationError(f"Запрещён переход {previous_state} -> {new_state}.")

    ready = (
        configuration_ready
        if configuration_ready is not None
        else (rule.configuration_ready if rule is not None else False)
    )
    configuration_validation = "ready" if ready else "not ready"
    dependency_ok, dependency_validation = _dependency_validation(
        manifest,
        scoped_context,
    )
    if new_state == ModuleLifecycleState.ACTIVE and (not ready or not dependency_ok):
        denial_code = (
            "CONFIGURATION_NOT_READY"
            if not ready
            else "REQUIRED_DEPENDENCY_INACTIVE"
        )
        _audit_denial(
            manifest=manifest,
            scope_type=scope_type,
            scope_id=scope_id,
            context=scoped_context,
            previous_explicit_state=audit_explicit_state,
            previous_effective_state=previous_effective.state,
            requested_new_state=new_state,
            actor_identity=actor,
            reason=transition_reason,
            configuration_validation=configuration_validation,
            dependency_validation=dependency_validation,
            denial_reason_code=denial_code,
        )
        raise ValidationError(
            "Модуль нельзя активировать до успешной проверки конфигурации и зависимостей."
        )

    try:
        with transaction.atomic():
            if rule is None:
                rule = ModuleActivationRule(
                    module_id=manifest.module_id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    organization_id=scoped_context.organization_id,
                    state=new_state,
                    configuration_ready=ready,
                    configuration=dict(configuration or {}),
                )
            else:
                rule.state = new_state
                if configuration_ready is not None:
                    rule.configuration_ready = configuration_ready
                if configuration is not None:
                    rule.configuration = dict(configuration)
            _persist_activation_rule(rule)
            resulting = resolve_effective_state(
                module_id=manifest.module_id,
                context=scoped_context,
            )
            _write_audit(
                module_id=manifest.module_id,
                scope_type=scope_type,
                scope_id=scope_id,
                organization_id=scoped_context.organization_id,
                previous_explicit_state=audit_explicit_state,
                previous_effective_state=previous_effective.state,
                requested_new_state=new_state,
                resulting_effective_state=resulting.state,
                actor_identity=actor,
                reason=transition_reason,
                configuration_validation=configuration_validation,
                dependency_validation=dependency_validation,
                result=ModuleActivationAuditEvent.Result.ALLOWED,
            )
    except IntegrityError as error:
        _audit_denial(
            manifest=manifest,
            scope_type=scope_type,
            scope_id=scope_id,
            context=scoped_context,
            previous_explicit_state=audit_explicit_state,
            previous_effective_state=previous_effective.state,
            requested_new_state=new_state,
            actor_identity=actor,
            reason=transition_reason,
            configuration_validation=configuration_validation,
            dependency_validation=dependency_validation,
            denial_reason_code="DUPLICATE_SCOPE_RULE",
        )
        raise ValidationError(
            "Для этого модуля и области уже существует правило."
        ) from error
    return rule


def _value(value: str | StrEnum) -> str:
    return value.value if isinstance(value, StrEnum) else str(value)


def _decision(
    *,
    allowed: bool,
    module_id: str,
    capability_id: str,
    operation: str | StrEnum,
    entry_point_class: str | StrEnum,
    effective_state: str,
    reason_code: str,
) -> ModuleAccessDecision:
    return ModuleAccessDecision(
        allowed=allowed,
        module_id=module_id,
        capability_id=capability_id,
        operation=_value(operation),
        entry_point_class=_value(entry_point_class),
        effective_state=effective_state,
        reason_code=reason_code,
    )


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
        return _decision(
            allowed=False,
            module_id=normalized_module,
            capability_id=normalized_capability,
            operation=operation,
            entry_point_class=entry_point_class,
            effective_state="UNKNOWN",
            reason_code="UNKNOWN_MODULE",
        )

    if normalized_capability not in manifest.capabilities:
        return _decision(
            allowed=False,
            module_id=manifest.module_id,
            capability_id=normalized_capability,
            operation=operation,
            entry_point_class=entry_point_class,
            effective_state="UNKNOWN",
            reason_code="UNKNOWN_CAPABILITY",
        )
    try:
        normalized_operation = ModuleOperation(_value(operation))
    except ValueError:
        return _decision(
            allowed=False,
            module_id=manifest.module_id,
            capability_id=normalized_capability,
            operation=operation,
            entry_point_class=entry_point_class,
            effective_state="UNKNOWN",
            reason_code="UNKNOWN_OPERATION",
        )
    try:
        normalized_entry_point = EntryPointClass(_value(entry_point_class))
    except ValueError:
        return _decision(
            allowed=False,
            module_id=manifest.module_id,
            capability_id=normalized_capability,
            operation=normalized_operation,
            entry_point_class=entry_point_class,
            effective_state="UNKNOWN",
            reason_code="UNKNOWN_ENTRY_POINT",
        )
    if normalized_operation not in manifest.operations:
        return _decision(
            allowed=False,
            module_id=manifest.module_id,
            capability_id=normalized_capability,
            operation=normalized_operation,
            entry_point_class=normalized_entry_point,
            effective_state="UNKNOWN",
            reason_code="OPERATION_NOT_DECLARED",
        )

    effective = resolve_effective_state(
        module_id=manifest.module_id,
        context=context,
    )
    if effective.state == ModuleLifecycleState.ACTIVE:
        dependencies_ok, _ = _dependency_validation(manifest, context)
        if normalized_operation in MUTATING_OPERATIONS and not dependencies_ok:
            return _decision(
                allowed=False,
                module_id=manifest.module_id,
                capability_id=normalized_capability,
                operation=normalized_operation,
                entry_point_class=normalized_entry_point,
                effective_state=effective.state,
                reason_code="REQUIRED_DEPENDENCY_INACTIVE",
            )
        return _decision(
            allowed=True,
            module_id=manifest.module_id,
            capability_id=normalized_capability,
            operation=normalized_operation,
            entry_point_class=normalized_entry_point,
            effective_state=effective.state,
            reason_code="ALLOW_ACTIVE",
        )

    if effective.state == ModuleLifecycleState.READ_ONLY:
        if normalized_operation in READ_OPERATIONS:
            return _decision(
                allowed=True,
                module_id=manifest.module_id,
                capability_id=normalized_capability,
                operation=normalized_operation,
                entry_point_class=normalized_entry_point,
                effective_state=effective.state,
                reason_code="ALLOW_READ_ONLY",
            )
        return _decision(
            allowed=False,
            module_id=manifest.module_id,
            capability_id=normalized_capability,
            operation=normalized_operation,
            entry_point_class=normalized_entry_point,
            effective_state=effective.state,
            reason_code="READ_ONLY_MUTATION_DENIED",
        )

    if normalized_operation in READ_OPERATIONS and manifest.history_policy == "PRESERVE":
        return _decision(
            allowed=True,
            module_id=manifest.module_id,
            capability_id=normalized_capability,
            operation=normalized_operation,
            entry_point_class=normalized_entry_point,
            effective_state=effective.state,
            reason_code="ALLOW_RETAINED_HISTORY",
        )
    return _decision(
        allowed=False,
        module_id=manifest.module_id,
        capability_id=normalized_capability,
        operation=normalized_operation,
        entry_point_class=normalized_entry_point,
        effective_state=effective.state,
        reason_code="MODULE_NOT_ACTIVE",
    )


def require_module_access(**kwargs: object) -> ModuleAccessDecision:
    decision = decide_module_access(**kwargs)  # type: ignore[arg-type]
    if not decision.allowed:
        raise PermissionDenied(
            f"Module access denied: {decision.module_id}/{decision.capability_id} "
            f"{decision.operation} ({decision.reason_code})."
        )
    return decision
