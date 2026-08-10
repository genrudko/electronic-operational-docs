# ЭОД — системная архитектура

## 1. Архитектурный стиль

Приложение развивается как модульный Django monolith:

- единый deployment unit;
- разделение по предметным приложениям и services;
- PostgreSQL как основная серверная СУБД;
- общие механизмы истории, аудита, доступа и связей;
- предметные правила остаются внутри профильных модулей.

Микросервисное разделение не является текущей целью и не должно вводиться без доказанной необходимости.

## 2. Основные слои

```text
Browser UI
    ↓
Django views/forms/templates
    ↓
Application services and transitions
    ↓
Domain models, constraints and snapshots
    ↓
PostgreSQL
```

Поперечные механизмы:

- authentication and authorization;
- versioned configuration;
- audit events;
- immutable snapshots;
- source traceability;
- search and filtering;
- imports and publication;
- tests and gates.

## 3. Предметные модули

Точный статус приведён в `MODULE_MAP.md`. Крупные области:

- organizations and personnel;
- documents;
- normatives;
- equipment;
- dispatching;
- imports;
- workplace documentation;
- operational log;
- operational documentation core;
- будущие work permits, switching documents and cross-document timeline.

## 4. Оперативный журнал

Оперативный журнал сохраняет отдельную модель и UI, потому что его основной объект — последовательная текстовая запись с временем события, временем регистрации, semantic references и сменным контекстом.

Он интегрируется с общим ядром через ссылки и события, но не превращается в динамическую табличную форму.

## 5. Общее ядро структурированных журналов

Ядро предоставляет механизмы:

- published document type/schema;
- source binding;
- record and field values;
- participants;
- equipment references;
- document relations;
- states and transitions;
- revisions and audit;
- search index and filtering.

Профильный журнал добавляет:

- утверждённый набор граф;
- обязательность;
- специализированные validation rules;
- допустимые роли и переходы;
- представление списка и карточки;
- traceability tests.

## 6. История и snapshot

Историческая устойчивость обеспечивается не только foreign keys. При регистрации или публикации сохраняются канонические snapshots значимых данных:

- наименование организации;
- Ф.И.О., должность и подразделение;
- оборудование и диспетчерское наименование;
- содержимое документа;
- версия формы или источника;
- полномочия и подтверждение действия.

## 7. Импорт

Импорт проходит стадии:

```text
source file → raw staging → normalization → conflicts → review → publication
```

Исходное значение не теряется. Повторный импорт должен быть идемпотентным или явно показывать конфликт.

## 8. Runtime-контуры

### Preview

- accepted `main`;
- `/srv/eod/repository`;
- `eod-preview`;
- `eod_preview`;
- `127.0.0.1:8765`;
- стабильные presentation data.

### Development

- активная feature branch, никогда `main`;
- `/srv/eod/development`;
- `eod-development`;
- `eod_development`;
- `127.0.0.1:8766`;
- отдельные volume, secrets и networks.

## 9. CI

GitHub Actions является обязательным независимым gate. Основной pipeline проверяет Linux/Python/PostgreSQL, а отдельный development smoke подтверждает container configuration и isolation.

VPS не используется как self-hosted runner и сохраняет read-only deploy key.

## 10. Доступ

Приложения слушают только loopback. Пользователь подключается через SSH local port forwarding. Публичный reverse proxy, HTTPS и domain не являются текущим условием разработки.

## 11. Конфигурация

Локальные особенности не зашиваются в код:

- организационная структура;
- типы и формы документов;
- roles and permissions;
- numbering;
- equipment and aliases;
- dispatching relations;
- normative editions.

Они хранятся как управляемые и, где требуется, публикуемые редакции.

## 12. Будущие границы

Отдельными компонентами могут стать только после доказанной необходимости:

- генератор и safety engine переключений;
- signature/cryptography service;
- integration adapters;
- document rendering service;
- offline/mobile synchronization.

До этого они проектируются как явные границы внутри монолита.

## 13. ADR: MODULE-ACTIVATION-CONTRACT-001

**Decision status:** `PROPOSED FOR OWNER ACCEPTANCE / IMPLEMENTATION CONTRACT COMPLETE`

**Work item:** `MODULE-ACTIVATION-CONTRACT-001`

**Runtime impact:** `NONE`

**Preview:** `UNTOUCHED`

### 13.1. Decision

ЭОД остаётся одним modular Django monolith: один deployable product, одна версия приложения и одна общая совместимая БД. Optional module является частью установленного продукта, но его capability может быть не активна в конкретном organizational context. Активация не создаёт отдельный build, product edition, database или module deployment.

`MODULE-REGISTRY-001` реализует этот contract позже и не должен повторно открывать фундаментальные lifecycle/scope/dependency решения.

### 13.2. Factual current gap

На текущем baseline:

- Django apps глобально включены в `INSTALLED_APPS`;
- URL namespaces глобально включены в `eod_config.urls`;
- `/admin/` является общесистемным route;
- `EquipmentDefectRouteGuardMiddleware` — специализированный redirect guard, а не universal activation guard;
- DEFECT service actions выполняют domain writes/transitions без общего module predicate;
- runtime registry, scoped activation records, resolver и activation audit отсутствуют.

Фактическая scope topology:

- `Organization`;
- `Division -> Organization`;
- `Workplace -> Organization`, optional `Division`;
- `EnergySite -> Organization`;
- `EquipmentAsset -> Organization + EnergySite`.

Прямой ORM-связи `Workplace -> EnergySite` нет. Архитектура не имеет права изображать её существующей.

### 13.3. Canonical module manifest

Каждый optional module manifest обязан иметь:

| Field | Semantics |
|---|---|
| `module_id` | stable module identity |
| `human_name` | human-readable name |
| `manifest_contract_version` | versioned manifest shape |
| `activation_policy` | `ALWAYS_ON` или `SCOPED_OPTIONAL` |
| `supported_scopes` | supported v1 activation scopes |
| `required_dependencies` | доказанные hard dependencies |
| `optional_integrations` | отдельно от hard dependencies |
| `capabilities` | stable capability IDs + operations |
| `activation_prerequisites` | configuration readiness checks |
| `history_policy` | optional modules: `PRESERVE` |
| `migration_policy` | `ALWAYS_WITH_PRODUCT` |
| `lifecycle_contract_version` | versioned lifecycle semantics |

Manifest не владеет release/work-item status, current main, active PR или acceptance SHA и поэтому не становится вторым planning-state owner.

Для `SCOPED_OPTIONAL` отсутствие explicit scope rule означает fail-closed `AVAILABLE`, а не implicit `ACTIVE`.

### 13.4. Lifecycle

Canonical states:

```text
AVAILABLE
CONFIGURED
ACTIVE
READ_ONLY
INACTIVE
RETIRED
```

`INACTIVE` намеренно отделён от `CONFIGURED` и `RETIRED`:

- `CONFIGURED` — готово к включению, но не активно;
- `INACTIVE` — явно выключено с сохранённой историей;
- `RETIRED` — выведено из эксплуатации с сохранённой identity/history.

Allowed transitions:

| From | To |
|---|---|
| `AVAILABLE` | `CONFIGURED` |
| `CONFIGURED` | `ACTIVE`, `INACTIVE`, `RETIRED` |
| `ACTIVE` | `READ_ONLY`, `INACTIVE`, `RETIRED` |
| `READ_ONLY` | `ACTIVE`, `INACTIVE`, `RETIRED` |
| `INACTIVE` | `CONFIGURED`, `RETIRED` |
| `RETIRED` | `CONFIGURED` |

Direct `AVAILABLE -> ACTIVE`, `INACTIVE -> ACTIVE` и `RETIRED -> ACTIVE` запрещены. Reactivation проходит через повторную configuration/dependency validation:

```text
INACTIVE -> CONFIGURED -> ACTIVE
RETIRED  -> CONFIGURED -> ACTIVE
```

Каждый transition требует valid scope, authorized actor, reason, configuration validation, required-dependency validation и append-only audit evidence. Любой failure = `DENY`; partial transition запрещён.

### 13.5. Activation scope v1

Supported scopes:

```text
ORGANIZATION
ENERGY_SITE
WORKPLACE
```

`DIVISION` и `OPERATIONAL_AREA` не являются activation scopes v1.

Requested context:

```text
organization: required
energy_site: optional
workplace: optional
```

Site и Workplace, если переданы, обязаны принадлежать requested Organization.

Ordinary decision precedence:

```text
WORKPLACE > ENERGY_SITE > ORGANIZATION
```

Это precedence rule, а не ORM parent-child assertion между Workplace и EnergySite.

Resolver algorithm:

1. Validate manifest and required Organization.
2. Validate optional Site/Workplace membership in Organization.
3. Reject unsupported scope type.
4. Enforce uniqueness of `(module_id, scope_type, scope_id)`; duplicate = fail closed.
5. Collect applicable explicit Organization/Site/Workplace rules.
6. Select ordinary state by `WORKPLACE > ENERGY_SITE > ORGANIZATION`; no rule = `AVAILABLE`.
7. Apply restrictive caps: any applicable `READ_ONLY`/`RETIRED` cannot be relaxed by a more-specific `ACTIVE`; `RETIRED` dominates `READ_ONLY`.
8. `INACTIVE` is not an ancestor safety cap. A more-specific Site/Workplace may explicitly become `ACTIVE` after config/dependency validation. This is required for phased rollout.
9. Validate configuration and hard dependencies without silently rewriting stored lifecycle state.
10. Return exactly one effective lifecycle state plus one access result/reason.

Examples:

| Wider rule | More specific rule | Result |
|---|---|---|
| Org `ACTIVE` | none | inherited `ACTIVE` |
| Org `ACTIVE` | Workplace `INACTIVE` | `INACTIVE` |
| Org `INACTIVE` | Site `ACTIVE` | `ACTIVE` if config/deps valid |
| Org `INACTIVE` | Workplace `ACTIVE` | `ACTIVE` if config/deps valid |
| Org `READ_ONLY` | Workplace `ACTIVE` | `READ_ONLY` cap |
| Org `RETIRED` | Site `ACTIVE` | `RETIRED` cap |
| Site `ACTIVE` | Workplace `INACTIVE` | `INACTIVE` |
| Site `INACTIVE` | Workplace `ACTIVE` | Workplace `ACTIVE` if valid |
| no rule | — | `AVAILABLE`; operational mutation denied |
| duplicate same-scope rules | — | `DENY / AMBIGUOUS_SCOPE_RULE` |
| scope from another Organization | — | `DENY` |
| stale configuration | requested `ACTIVE` | `DENY` until revalidated |

Rules bind stable IDs, not names/path strings. Division movement inside one Organization does not affect activation v1. Organization mismatch after topology change fails closed until reconciled/audited.

### 13.6. Required dependency and optional integration

A **required dependency** exists only when the consumer cannot preserve its own invariants without the provider. It is declared in manifest, checked before activation and guarded operations, fails closed, uses the same requested context by default and cannot be bypassed through direct URL/service/API/admin/command. Hard-dependency cycles are forbidden.

An **optional integration** never blocks primary-module activation. Missing/inactive provider disables only the integration capability and preserves historical links/snapshots.

Current `DEFECT <-> OPJ` link remains optional integration unless future domain evidence proves a hard invariant dependency. Accepted DEFECT dependency is `MASTER-DATA`; presence of `CAP-DEFECT-OPJ-LINK` alone is insufficient evidence for hard OPJ dependency.

### 13.7. Universal access decision

Future canonical predicate:

```text
decide_module_access(
    normalized_context,
    module_id,
    capability_id,
    operation,
    entry_point_class,
) -> ModuleAccessDecision
```

Mandatory entry-point classes:

```text
NAVIGATION_UI
HTTP_ROUTE
SERVICE
API
ADMIN
MANAGEMENT_COMMAND
EXPORT
BACKGROUND_JOB
CROSS_MODULE_ACTION
```

Decision output includes module/capability, normalized context, requested operation, entry-point class, selected scope rule, effective lifecycle state, configuration result, required dependencies, optional integrations, `ALLOW`/`DENY`, audit-safe denial reason and contract version.

Hidden UI is not protection. Route-only denial is not complete protection. Mutation enforcement belongs at the service/capability boundary; admin, management commands and background jobs have no implicit activation bypass.

Final permission is conjunctive:

```text
module decision ALLOW
AND identity/RBAC/authority ALLOW
AND domain invariants ALLOW
```

Module activation never replaces authorization or domain invariants.

### 13.8. Entry-point matrix

| Entry point | Contract |
|---|---|
| Navigation/UI | visibility from predicate; never security boundary |
| Direct HTTP | predicate; manual URL cannot bypass |
| Service | mandatory predicate for module mutation |
| API | same decision + guarded service |
| Admin | no implicit superuser/module bypass |
| Management command | explicit scope + same predicate |
| Export | lifecycle-aware read/export predicate |
| Background job | re-evaluate state at execution; mutation guarded |
| Cross-module action | relevant source/target decisions; integration is not bypass |

### 13.9. Lifecycle behaviour matrix

`ALLOW` below refers only to module-activation layer; normal authorization/domain rules still apply.

| State | List/read | Detail/history | Create | Edit/transition | Delete | Export | Background mutation |
|---|---|---|---|---|---|---|---|
| `ACTIVE` | ALLOW | ALLOW | ALLOW | ALLOW | only capability+domain policy | ALLOW | ALLOW if declared |
| `READ_ONLY` | ALLOW | ALLOW | DENY | DENY | DENY | read-only ALLOW | DENY |
| `INACTIVE` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | DENY |
| `RETIRED` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | DENY |
| `CONFIGURED` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | DENY |
| `AVAILABLE` | retained history if supported | generic retained-history path | DENY | DENY | DENY | retained export if supported | DENY |

Operationally/legal significant records are never physically deleted because of module state.

### 13.10. History and reactivation

Disable/read-only/retire preserve records, snapshots, audit, relations and stable module ID. Reactivation continues existing history; creating a new independent module identity is forbidden. Stale configuration and required dependencies are revalidated before return to `ACTIVE`.

### 13.11. Migration semantics

Software/database migrations are a property of **product version**, not activation state:

```text
same product version
=> one compatible schema evolution
=> shipped migrations apply regardless module ACTIVE/INACTIVE
```

Inactive-module migrations are applied; retained inactive data migrate safely; migration never auto-activates module; upgrade preserves explicit activation state. Installations of the same product version must not diverge into different schemas because of module set.

The executable matrix `active/inactive module × N-1/N` belongs to `MODULE-MIGRATION-COMPATIBILITY-001` and is not implemented here.

### 13.12. Activation audit

Every attempted state transition requires append-only evidence containing:

- module ID;
- scope type/id and Organization ID;
- previous explicit/effective state;
- requested new and resulting effective state;
- actor identity;
- timestamp;
- reason;
- configuration-validation result;
- required-dependency validation;
- `ALLOWED`/`REJECTED` result;
- audit-safe denial reason;
- correlation/trace identity;
- manifest contract version.

### 13.13. Current implementation gap handed to MODULE-REGISTRY-001

| Area | Current code | Future implementation |
|---|---|---|
| Django apps | globally installed | stay installed; activation does not change `INSTALLED_APPS` |
| URL namespaces | globally wired | runtime capability guards |
| DEFECT middleware | specialized redirect | not generic activation engine |
| Navigation | no universal predicate | same decision semantics |
| HTTP | no generic module guard | common decision |
| Service writes | domain services without module predicate | mandatory mutation boundary |
| API | no universal registry semantics | future API uses same predicate |
| Admin | global route | no activation bypass |
| Management commands | no universal scoped guard | explicit scope + predicate |
| Exports | module-specific | lifecycle-aware read/export decision |
| Background paths | no universal registry semantics | re-evaluate at execution |
| Cross-module links | point integrations | source/target capability decisions |
| Scope records | absent | registry/control-plane tables |
| Activation audit | absent | append-only transition evidence |
| Migrations | product migrations | remain product-version property |

`MODULE-REGISTRY-001` must implement manifest loading/validation, stable registry, unique scoped records, exact v1 resolver, lifecycle transition service, configuration/dependency validation, `ModuleAccessDecision`, mutation service guard, entry-point adapters, append-only activation audit and mixed-scope runtime tests. It must not reopen sections 13.3–13.12.

### 13.14. Machine-readable architecture contract

The fenced JSON below is deliberately embedded in the existing canonical architecture owner instead of creating a second architecture/status owner. `scripts/check_documentation_contract.py` parses and validates it fail closed. Negative mutations live in the existing process fixture catalog.

<!-- MODULE-ACTIVATION-CONTRACT-001:BEGIN -->
```json
{
  "schema_version": 1,
  "contract_id": "MODULE-ACTIVATION-CONTRACT-001",
  "architecture": {
    "style": "MODULAR_DJANGO_MONOLITH",
    "deployable_products": 1,
    "application_versions_per_release": 1,
    "database_model": "ONE_SHARED_DATABASE",
    "separate_module_deployments": false,
    "activation_changes_product_version": false
  },
  "manifest": {
    "required_fields": [
      "module_id",
      "human_name",
      "manifest_contract_version",
      "activation_policy",
      "supported_scopes",
      "required_dependencies",
      "optional_integrations",
      "capabilities",
      "activation_prerequisites",
      "history_policy",
      "migration_policy",
      "lifecycle_contract_version"
    ],
    "forbidden_status_fields": [
      "release_status",
      "work_item_status",
      "current_main",
      "active_pr",
      "accepted_head"
    ],
    "activation_policies": ["ALWAYS_ON", "SCOPED_OPTIONAL"],
    "supported_scope_types_v1": ["ORGANIZATION", "ENERGY_SITE", "WORKPLACE"],
    "default_scoped_optional_state": "AVAILABLE",
    "stable_identity": true,
    "history_policy_required": "PRESERVE",
    "migration_policy_required": "ALWAYS_WITH_PRODUCT"
  },
  "lifecycle": {
    "states": ["AVAILABLE", "CONFIGURED", "ACTIVE", "READ_ONLY", "INACTIVE", "RETIRED"],
    "allowed_transitions": {
      "AVAILABLE": ["CONFIGURED"],
      "CONFIGURED": ["ACTIVE", "INACTIVE", "RETIRED"],
      "ACTIVE": ["READ_ONLY", "INACTIVE", "RETIRED"],
      "READ_ONLY": ["ACTIVE", "INACTIVE", "RETIRED"],
      "INACTIVE": ["CONFIGURED", "RETIRED"],
      "RETIRED": ["CONFIGURED"]
    },
    "forbidden_direct_transitions": ["AVAILABLE->ACTIVE", "INACTIVE->ACTIVE", "RETIRED->ACTIVE"],
    "reactivation_paths": {
      "INACTIVE": ["INACTIVE", "CONFIGURED", "ACTIVE"],
      "RETIRED": ["RETIRED", "CONFIGURED", "ACTIVE"]
    },
    "transition_requires": [
      "actor_authorized",
      "reason_recorded",
      "scope_valid",
      "configuration_valid_for_target",
      "required_dependencies_valid_for_target",
      "audit_event_written"
    ],
    "disable_is_delete": false,
    "retire_is_delete": false
  },
  "scope_resolution": {
    "required_context": ["organization"],
    "optional_context": ["energy_site", "workplace"],
    "non_scope_models_v1": ["DIVISION", "OPERATIONAL_AREA"],
    "workplace_is_child_of_energy_site": false,
    "ordinary_precedence": ["WORKPLACE", "ENERGY_SITE", "ORGANIZATION"],
    "default_when_no_rule": "AVAILABLE",
    "same_scope_duplicate_result": "DENY",
    "invalid_or_missing_required_scope_result": "DENY",
    "unsupported_scope_result": "DENY",
    "restrictive_caps": ["READ_ONLY", "RETIRED"],
    "restrictive_cap_precedence": ["RETIRED", "READ_ONLY"],
    "inactive_is_restrictive_cap": false,
    "child_may_override_parent_inactive_to_active": true
  },
  "dependencies": {
    "required_dependency": {
      "declared_in_manifest": true,
      "checked_before_active_transition": true,
      "checked_on_guarded_operations": true,
      "fail_closed": true,
      "same_requested_context_by_default": true,
      "must_not_be_inferred_from_cross_link": true,
      "historical_reads_survive_dependency_loss": true,
      "cycles_forbidden": true
    },
    "optional_integration": {
      "declared_separately": true,
      "blocks_primary_module_activation": false,
      "missing_provider_result": "INTEGRATION_CAPABILITY_DENY_ONLY",
      "historical_links_preserved": true,
      "must_not_be_promoted_without_domain_evidence": true
    },
    "current_example": {
      "consumer": "DEFECT",
      "provider": "OPJ",
      "classification": "OPTIONAL_INTEGRATION_UNLESS_FUTURE_DOMAIN_EVIDENCE_PROVES_REQUIRED"
    }
  },
  "access_decision": {
    "predicate_name": "decide_module_access",
    "entry_point_classes": [
      "NAVIGATION_UI",
      "HTTP_ROUTE",
      "SERVICE",
      "API",
      "ADMIN",
      "MANAGEMENT_COMMAND",
      "EXPORT",
      "BACKGROUND_JOB",
      "CROSS_MODULE_ACTION"
    ],
    "required_inputs": ["normalized_context", "module_id", "capability_id", "operation", "entry_point_class"],
    "required_outputs": [
      "module_id",
      "capability_id",
      "normalized_context",
      "requested_operation",
      "entry_point_class",
      "selected_scope_rule",
      "effective_lifecycle_state",
      "configuration_result",
      "dependency_results",
      "optional_integration_results",
      "access_result",
      "denial_reason_code",
      "contract_version"
    ],
    "ui_visibility_is_security_boundary": false,
    "route_only_guard_is_complete": false,
    "mutation_service_guard_required": true,
    "module_decision_replaces_domain_authorization": false
  },
  "behavior_matrix": {
    "ACTIVE": {"create": "ALLOW", "edit_transition": "ALLOW", "delete": "ALLOW_ONLY_IF_CAPABILITY_AND_DOMAIN_POLICY_ALLOW", "detail_history": "ALLOW", "background_mutate": "ALLOW"},
    "READ_ONLY": {"create": "DENY", "edit_transition": "DENY", "delete": "DENY", "detail_history": "ALLOW", "background_mutate": "DENY"},
    "INACTIVE": {"create": "DENY", "edit_transition": "DENY", "delete": "DENY", "detail_history": "ALLOW_RETAINED_HISTORY", "background_mutate": "DENY"},
    "RETIRED": {"create": "DENY", "edit_transition": "DENY", "delete": "DENY", "detail_history": "ALLOW_RETAINED_HISTORY", "background_mutate": "DENY"},
    "CONFIGURED": {"create": "DENY", "edit_transition": "DENY", "delete": "DENY", "detail_history": "ALLOW_RETAINED_HISTORY", "background_mutate": "DENY"},
    "AVAILABLE": {"create": "DENY", "edit_transition": "DENY", "delete": "DENY", "detail_history": "ALLOW_RETAINED_HISTORY_IF_SUPPORTED", "background_mutate": "DENY"}
  },
  "history_and_reactivation": {
    "deactivation_deletes_records": false,
    "deactivation_deletes_snapshots": false,
    "deactivation_deletes_audit": false,
    "deactivation_breaks_relations": false,
    "module_id_changes_on_reactivation": false,
    "reactivation_creates_new_module_identity": false,
    "reactivation_uses_retained_history": true,
    "stale_configuration_revalidated_before_active": true,
    "direct_inactive_or_retired_to_active": false
  },
  "migrations": {
    "owned_by_product_version": true,
    "conditioned_on_module_activation": false,
    "inactive_module_migrations_apply": true,
    "same_product_version_requires_compatible_schema": true,
    "upgrade_activates_module": false,
    "upgrade_preserves_explicit_activation_state": true,
    "inactive_data_migrates_safely": true,
    "full_active_inactive_n1_n_matrix_deferred_to": "MODULE-MIGRATION-COMPATIBILITY-001"
  },
  "activation_audit": {
    "append_only_required": true,
    "required_fields": [
      "module_id",
      "scope_type",
      "scope_id",
      "organization_id",
      "previous_explicit_state",
      "previous_effective_state",
      "requested_new_state",
      "resulting_effective_state",
      "actor_identity",
      "occurred_at",
      "reason",
      "configuration_validation",
      "dependency_validation",
      "result",
      "denial_reason_code",
      "correlation_id",
      "manifest_contract_version"
    ]
  },
  "negative_architecture_invariants": [
    "N01_UI_HIDDEN_DIRECT_URL_MUST_DENY",
    "N02_ROUTE_DENIED_SERVICE_WRITE_MUST_DENY",
    "N03_OPTIONAL_INTEGRATION_MUST_NOT_BECOME_REQUIRED_WITHOUT_EVIDENCE",
    "N04_REQUIRED_DEPENDENCY_MISSING_MUST_BLOCK_ACTIVATION",
    "N05_DISABLE_MUST_NOT_DELETE_RECORDS",
    "N06_READ_ONLY_MUST_DENY_WRITE_TRANSITION",
    "N07_UPGRADE_MUST_NOT_AUTO_ACTIVATE",
    "N08_INACTIVE_MODULE_MUST_NOT_SKIP_SCHEMA_MIGRATIONS",
    "N09_SCOPE_CONFLICT_MUST_NOT_RESOLVE_RANDOMLY",
    "N10_REACTIVATION_MUST_PRESERVE_MODULE_IDENTITY"
  ],
  "implementation_boundary": {
    "product_models_changed": false,
    "domain_migrations_changed": false,
    "runtime_preview_changed": false,
    "registry_runtime_implementation_deferred_to": "MODULE-REGISTRY-001"
  }
}
```
<!-- MODULE-ACTIVATION-CONTRACT-001:END -->

### 13.15. Negative architecture requirements

The permanent checker must fail closed when any of these is introduced:

1. UI hidden but direct URL remains operationally usable.
2. Route denied but direct service write remains usable.
3. Optional integration becomes required dependency without domain evidence.
4. Missing required dependency does not block activation.
5. Disable deletes records/history.
6. `READ_ONLY` allows write/transition.
7. Upgrade auto-activates inactive module.
8. Inactive module skips schema migrations.
9. Scope conflicts/duplicates are resolved by random/first-match behaviour.
10. Reactivation creates a new module identity.

These scenarios are machine-mutated from the embedded contract by the existing Documentation Contract checker. No runtime registry implementation is claimed by this ADR.