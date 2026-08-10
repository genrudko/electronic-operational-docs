# MODULE-ACTIVATION-CONTRACT-001 — архитектурное решение

**Статус:** `PROPOSED FOR OWNER ACCEPTANCE / IMPLEMENTATION CONTRACT COMPLETE`
**Work item:** `MODULE-ACTIVATION-CONTRACT-001`
**Issue / PR:** `#61 / #62`
**Тип:** `ARCHITECTURE`
**Runtime impact:** `NONE`
**Preview:** `UNTOUCHED`

## 1. Решение

ЭОД остаётся одним modular Django monolith: один deployable product, одна версия приложения и одна общая совместимая БД. Код optional module может присутствовать в продукте, но capability активируется независимо для поддерживаемого organizational context. Module activation не создаёт отдельную редакцию продукта, отдельный deployment или отдельную БД.

Отключение, `READ_ONLY`, `INACTIVE` и `RETIRED` никогда не означают удаление исторических данных.

Этот work item принимает архитектурный contract для будущего `MODULE-REGISTRY-001`; registry/control plane здесь не реализуется.

Machine-readable contract:

`docs/work-items/active/MODULE-ACTIVATION-CONTRACT-001/MODULE_ACTIVATION_CONTRACT.json`

Fail-closed checker:

`scripts/module_activation_contract.py`

## 2. Factual current-gap inventory

На текущем baseline:

- Django apps подключены глобально через `INSTALLED_APPS`;
- URL namespaces подключены глобально в `eod_config.urls`;
- `/admin/` является общесистемным route;
- `EquipmentDefectRouteGuardMiddleware` — специализированный redirect guard для DEFECT/generic operational-document routes, а не universal activation guard;
- DEFECT service actions выполняют domain writes/transitions без общего module capability predicate;
- отдельной registry/resolver/access-decision semantics сейчас нет.

Фактическая scope topology:

- `Organization`;
- `Division -> Organization`;
- `Workplace -> Organization`, optional `Division`;
- `EnergySite -> Organization`;
- `EquipmentAsset -> Organization + EnergySite`.

Прямой ORM-связи `Workplace -> EnergySite` нет. Activation v1 не изображает рабочее место дочерним объектом энергообъекта.

`pyproject.toml` не объявляет отдельный API/background-queue framework. Тем не менее `API` и `BACKGROUND_JOB` входят в future guard contract, чтобы их появление не создало bypass.

## 3. Canonical module manifest

Минимальные manifest fields:

| Field | Contract |
|---|---|
| `module_id` | stable identity; не меняется при reactivation |
| `human_name` | human-readable name |
| `manifest_contract_version` | versioned manifest shape |
| `activation_policy` | `ALWAYS_ON` или `SCOPED_OPTIONAL` |
| `supported_scopes` | supported v1 scope types |
| `required_dependencies` | только доказанные hard dependencies |
| `optional_integrations` | отдельно от hard dependencies |
| `capabilities` | stable capability IDs + operations |
| `activation_prerequisites` | configuration-readiness checks |
| `history_policy` | optional modules: `PRESERVE` |
| `migration_policy` | `ALWAYS_WITH_PRODUCT` |
| `lifecycle_contract_version` | versioned lifecycle semantics |

Manifest не владеет `release_status`, work-item status, current main, active PR или accepted SHA. Единственным planning-status owner остаётся `DEMO_RELEASE_PLAN.yaml`.

Для `SCOPED_OPTIONAL` отсутствие scoped rule означает fail-closed `AVAILABLE`, а не implicit `ACTIVE`.

## 4. Lifecycle state machine

| State | Семантика |
|---|---|
| `AVAILABLE` | code/manifest есть, но scope ещё не готов к operational use |
| `CONFIGURED` | configuration/prerequisites валидны, normal operation не включена |
| `ACTIVE` | normal operation разрешена при прохождении dependency/auth/domain checks |
| `READ_ONLY` | mutation frozen; read/history/export preserved |
| `INACTIVE` | explicit disable с сохранением history |
| `RETIRED` | capability выведена из эксплуатации; identity/history preserved |

`INACTIVE` намеренно не смешивается с `CONFIGURED` или `RETIRED`.

Allowed transitions:

| From | To |
|---|---|
| `AVAILABLE` | `CONFIGURED` |
| `CONFIGURED` | `ACTIVE`, `INACTIVE`, `RETIRED` |
| `ACTIVE` | `READ_ONLY`, `INACTIVE`, `RETIRED` |
| `READ_ONLY` | `ACTIVE`, `INACTIVE`, `RETIRED` |
| `INACTIVE` | `CONFIGURED`, `RETIRED` |
| `RETIRED` | `CONFIGURED` |

Forbidden direct transitions:

- `AVAILABLE -> ACTIVE`;
- `INACTIVE -> ACTIVE`;
- `RETIRED -> ACTIVE`.

Reactivation paths:

```text
INACTIVE -> CONFIGURED -> ACTIVE
RETIRED  -> CONFIGURED -> ACTIVE
```

Каждый transition требует actor authorization, reason, valid scope, configuration validation, required-dependency validation и append-only audit evidence. Любой failure = `DENY`; partial transition запрещён.

## 5. Activation scopes v1

Supported:

```text
ORGANIZATION
ENERGY_SITE
WORKPLACE
```

`DIVISION` и `OPERATIONAL_AREA` существуют в data model, но не являются activation scopes v1.

Requested context:

```text
organization: required
energy_site: optional
workplace: optional
```

Переданный `energy_site` и/или `workplace` обязан принадлежать requested Organization.

## 6. Deterministic scope resolution

Ordinary precedence:

```text
WORKPLACE > ENERGY_SITE > ORGANIZATION
```

Это decision precedence, а не parent-child assertion между Workplace и EnergySite.

Algorithm:

1. Validate manifest and required Organization.
2. Validate Site/Workplace membership in that Organization.
3. Reject unsupported scope type.
4. Require uniqueness of `(module_id, scope_type, scope_id)`; duplicate = `DENY / AMBIGUOUS_SCOPE_RULE`.
5. Collect applicable Organization/Site/Workplace explicit rules.
6. Select ordinary state by `WORKPLACE > ENERGY_SITE > ORGANIZATION`; if no rule, `AVAILABLE`.
7. Apply restrictive caps: any applicable `READ_ONLY`/`RETIRED` cannot be relaxed by a more-specific `ACTIVE`; `RETIRED` dominates `READ_ONLY`.
8. `INACTIVE` is not an ancestor safety cap. More-specific Site/Workplace may explicitly become `ACTIVE` after config/dependency validation. This enables phased rollout.
9. Validate configuration/dependencies. Failure denies access without silently rewriting stored lifecycle state.
10. Return one deterministic effective lifecycle state plus access result/reason.

Examples:

| Wider rule | More specific rule | Effective result |
|---|---|---|
| Org `ACTIVE` | none | inherited `ACTIVE` |
| Org `ACTIVE` | Workplace `INACTIVE` | `INACTIVE` |
| Org `INACTIVE` | Site `ACTIVE` | `ACTIVE` if config/deps valid |
| Org `INACTIVE` | Workplace `ACTIVE` | `ACTIVE` if config/deps valid |
| Org `READ_ONLY` | Workplace `ACTIVE` | `READ_ONLY` cap |
| Org `RETIRED` | Site `ACTIVE` | `RETIRED` cap |
| Site `ACTIVE` | Workplace `INACTIVE` | `INACTIVE` |
| Site `INACTIVE` | Workplace `ACTIVE` | Workplace `ACTIVE` if valid |
| no rule | none | `AVAILABLE`; operational writes denied |
| duplicate same-scope rules | any | fail closed |
| scope belongs another org | any | fail closed |
| stale configuration | requested `ACTIVE` | deny until revalidated |

Rules bind stable IDs, not names/path strings. Division movement inside the same Organization does not affect v1 activation. Organization mismatch after topology change fails closed until reconciled/audited.

## 7. Required dependency vs optional integration

### Required dependency

A dependency is hard only when the consumer cannot preserve its own invariants without the provider.

It must be:

- declared in manifest;
- checked before `ACTIVE`;
- checked on guarded operations that require it;
- fail closed;
- evaluated in same requested context by default;
- impossible to bypass via URL/service/API/admin/command;
- acyclic in the hard-dependency graph.

Loss of a required provider blocks affected operational actions but never deletes consumer history.

### Optional integration

Missing/inactive provider:

- does not block primary-module activation;
- denies/degrades only integration capability;
- preserves historical links/snapshots;
- does not promote itself to hard dependency without domain evidence.

Current example: accepted DEFECT contract declares `MASTER-DATA` as dependency. `CAP-DEFECT-OPJ-LINK` alone is not evidence that active OPJ is required; `DEFECT <-> OPJ` therefore remains optional integration unless future domain evidence proves otherwise.

## 8. Universal access-decision contract

Future predicate:

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

Decision output contains at least:

- module/capability IDs;
- normalized context;
- requested operation and entry-point class;
- selected scope rule;
- effective lifecycle state;
- configuration result;
- required-dependency results;
- optional-integration results;
- `ALLOW`/`DENY`;
- audit-safe denial reason code;
- contract version.

Final permission is conjunction:

```text
module decision ALLOW
AND identity/RBAC/authority ALLOW
AND domain invariants ALLOW
```

Module activation never replaces authorization/domain checks.

## 9. Entry-point guard matrix

| Entry point | Contract |
|---|---|
| Navigation/UI | visibility from predicate; never a security boundary |
| Direct HTTP | predicate before module action; manual URL cannot bypass |
| Service | mutation boundary must invoke same decision semantics |
| API | same predicate + guarded service |
| Admin | no implicit superuser/module bypass |
| Management command | explicit context + same predicate |
| Export | state-aware read/export predicate |
| Background job | state re-evaluated at execution; mutation requires predicate |
| Cross-module action | source/target decisions; integration is not bypass |

Closing a route while direct service mutation remains possible is architecturally invalid.

## 10. Lifecycle behaviour matrix

`ALLOW` means only the module-activation layer; authorization/domain rules still apply.

| State | List/read | Detail/history | Create | Edit/transition | Delete | Export | Background mutation |
|---|---|---|---|---|---|---|---|
| `ACTIVE` | ALLOW | ALLOW | ALLOW | ALLOW | only capability+domain policy | ALLOW | ALLOW if declared |
| `READ_ONLY` | ALLOW | ALLOW | DENY | DENY | DENY | read-only ALLOW | DENY |
| `INACTIVE` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | DENY |
| `RETIRED` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | DENY |
| `CONFIGURED` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | DENY |
| `AVAILABLE` | retained history only if supported | generic retained-history path | DENY | DENY | DENY | retained export if supported | DENY |

Historical operational/legal records are never physically deleted because of module state.

## 11. History and reactivation

Invariants:

- records, snapshots, audit and relations survive disable/read-only/retire;
- stable module ID survives reactivation;
- reactivation uses retained history;
- a new independent module identity is forbidden;
- stale configuration is revalidated;
- required dependencies are revalidated;
- failed reactivation does not grant active access.

## 12. Migration semantics

Software/database migrations belong to product version, never activation state.

```text
same product version
=> one compatible schema evolution
=> shipped migrations apply regardless module ACTIVE/INACTIVE
```

Therefore:

- inactive-module migrations are applied;
- retained inactive data migrate safely;
- migration never auto-activates module;
- upgrade preserves explicit activation state;
- installations of the same product version do not diverge into different schemas because of module set;
- reactivation uses already-migrated retained data.

Executable `active/inactive x N-1/N` matrix remains explicitly deferred to `MODULE-MIGRATION-COMPATIBILITY-001`.

## 13. Activation audit

Every attempted state change leaves append-only evidence with:

- module ID;
- scope type/id and Organization ID;
- previous explicit/effective states;
- requested/resulting states;
- actor identity;
- timestamp;
- reason;
- configuration validation;
- dependency validation;
- result and denial reason;
- correlation/trace identity;
- manifest contract version.

This work item defines evidence requirements but does not build a separate audit subsystem.

## 14. Negative architecture evidence

Machine checker/fixtures reject:

1. UI hidden but direct URL operationally works.
2. Route denied but service write works.
3. Optional integration becomes hard dependency without domain evidence.
4. Required dependency missing but activation succeeds.
5. Disable deletes records/history.
6. `READ_ONLY` permits write/transition.
7. Upgrade auto-activates inactive module.
8. Inactive module skips its schema migrations.
9. Scope conflict/duplicates use random/first-match resolution.
10. Reactivation creates a new module identity.

Additional fixtures protect manifest minimum, `SERVICE` entry-point coverage, no direct `RETIRED -> ACTIVE`, and exact scope precedence.

## 15. Current implementation-gap mapping

| Area | Current code | `MODULE-REGISTRY-001` obligation |
|---|---|---|
| Django apps | globally installed | remain installed; activation does not change `INSTALLED_APPS` |
| URL namespaces | globally included | runtime capability guards |
| DEFECT middleware | specialized redirect | not a generic activation engine |
| Navigation | no universal predicate | same decision semantics |
| HTTP | no generic module guard | common decision |
| Service writes | domain services without module predicate | mandatory mutation boundary |
| API | no universal registry semantics | any future API uses predicate |
| Admin | global route | no activation bypass |
| Commands | no universal module context guard | explicit scope + predicate |
| Exports | module-specific | state-aware read/export decision |
| Background | no universal registry semantics | re-evaluate at execution |
| Cross-module links | point integrations | source/target decisions |
| Scope records | absent | registry/control-plane tables |
| Activation audit | absent | append-only transition evidence |
| Migrations | product migrations | remain product-version property |

## 16. Residual implementation handed to MODULE-REGISTRY-001

Future implementation must provide:

1. manifest loading/validation;
2. stable module/capability registry;
3. unique scoped activation records;
4. exact v1 resolver;
5. lifecycle transition service;
6. configuration/dependency validation;
7. `ModuleAccessDecision`;
8. mutation service guard;
9. UI/route/API/admin/command/export/job/cross-module adapters;
10. append-only activation audit;
11. mixed Organization/EnergySite/Workplace runtime tests;
12. disable/read-only/retire/reactivation evidence.

It must not reopen the fundamental decisions in sections 1–14.

## 17. Scope boundary of PR #62

This PR does not change:

- product/domain models;
- migrations;
- working data;
- runtime configuration;
- live VPS/Preview;
- UX/page templates;
- journals/modules;
- `SHIFT-HANDOVER-001`;
- runtime `MODULE-REGISTRY-001`.

The architecture is technically ready for owner acceptance only when this decision, machine contract, checker, negative fixtures, canonical transition and all applicable exact-head gates agree on one final head.
