# MODULE-ACTIVATION-CONTRACT-001 — архитектурное решение

**Статус:** `PROPOSED FOR OWNER ACCEPTANCE / IMPLEMENTATION CONTRACT COMPLETE`  
**Work item:** `MODULE-ACTIVATION-CONTRACT-001`  
**Issue / PR:** `#61 / #62`  
**Тип:** `ARCHITECTURE`  
**Runtime impact:** `NONE`  
**Preview:** `UNTOUCHED`

## 1. Решение

ЭОД остаётся **одним модульным Django-монолитом**:

- один deployable product;
- одна версия приложения на установке;
- одна общая совместимая схема БД;
- код модуля может присутствовать в продукте, но capability может быть не активна для конкретного организационного контекста;
- разные организации, энергообъекты и рабочие места могут эксплуатировать разные наборы optional modules;
- включение/отключение модуля не создаёт отдельную редакцию продукта;
- отдельные module deployments и микросервисы не вводятся;
- отключение, read-only и retirement никогда не являются удалением данных.

Это решение определяет контракт для будущего `MODULE-REGISTRY-001`. Сам registry/control plane здесь **не реализуется**.

Machine-readable representation:

`docs/work-items/active/MODULE-ACTIVATION-CONTRACT-001/MODULE_ACTIVATION_CONTRACT.json`

Fail-closed architecture checker:

`scripts/module_activation_contract.py`

## 2. Factual inventory текущего приложения

### 2.1. Что есть сейчас

На текущем baseline Django applications подключены глобально через `INSTALLED_APPS`.
URL namespaces также подключены глобально в `eod_config.urls`; `/admin/` является
общесистемным маршрутом.

Фактическая модель организационного контекста:

- `Organization`;
- `Division` принадлежит `Organization`;
- `Workplace` принадлежит `Organization` и опционально `Division`;
- `EnergySite` принадлежит `Organization`;
- `EquipmentAsset` принадлежит `Organization` и `EnergySite`.

**Прямой связи `Workplace -> EnergySite` в текущей модели нет.**
Поэтому архитектура activation v1 не имеет права изображать рабочее место дочерним
объектом энергообъекта.

Для журнала дефектов существует специализированный
`EquipmentDefectRouteGuardMiddleware`, но он решает узкую задачу маршрутизации
generic operational-document routes в специализированный DEFECT UI. Он не является
универсальным module-activation guard.

`equipment_defects.services.actions` выполняет предметные записи/переходы напрямую
через service layer. Общего module capability predicate в этих service paths сейчас нет.

В `pyproject.toml` отсутствует отдельный background-queue framework и API framework,
но архитектурный контракт всё равно резервирует `API` и `BACKGROUND_JOB` как
обязательные entry-point classes: появление такого входа не должно создавать обход
activation semantics.

### 2.2. Чего сейчас нет и что обязан реализовать MODULE-REGISTRY-001

Сейчас отсутствуют:

- canonical runtime registry optional modules;
- DB records scoped activation;
- единая resolver semantics `context + module -> effective state`;
- универсальный capability/access predicate;
- единая защита navigation / HTTP / service / API / admin / command / export / jobs;
- activation audit events;
- runtime mixed-scope evidence.

Это осознанный implementation gap, а не «частично существующий registry».

## 3. Canonical module manifest

Каждый module manifest имеет стабильную identity и **не владеет release/work-item status**.

Минимальные поля:

| Поле | Смысл |
|---|---|
| `module_id` | Стабильный технический ID; не меняется при disable/reactivation |
| `human_name` | Отображаемое имя |
| `manifest_contract_version` | Версия структуры manifest |
| `activation_policy` | `ALWAYS_ON` или `SCOPED_OPTIONAL` |
| `supported_scopes` | Разрешённые scope types v1 |
| `required_dependencies` | Только доказанные hard dependencies |
| `optional_integrations` | Необязательные интеграции, отдельно от dependencies |
| `capabilities` | Стабильные capability IDs и поддерживаемые операции |
| `activation_prerequisites` | Проверки configuration readiness |
| `history_policy` | Для optional modules — `PRESERVE` |
| `migration_policy` | `ALWAYS_WITH_PRODUCT` |
| `lifecycle_contract_version` | Версия lifecycle semantics |

Manifest не содержит:

- release status;
- work-item status;
- current main SHA;
- active PR;
- accepted head;
- runtime/Preview status.

Таким образом manifest не становится вторым `DEMO_RELEASE_PLAN.yaml`.

### 3.1. Activation policy

`ALWAYS_ON` применяется к фундаментальной capability, которую нельзя отключать
scope-level control plane без отдельного архитектурного решения.

`SCOPED_OPTIONAL` означает: код/manifest присутствует в общей версии продукта,
но operational capability активируется отдельно по поддерживаемым scopes.

Отсутствие scoped activation record для optional module означает fail-closed
`AVAILABLE`, а не «по умолчанию ACTIVE».

## 4. Lifecycle state machine

Canonical states:

| State | Семантика |
|---|---|
| `AVAILABLE` | Код/manifest присутствует в продукте, но scope ещё не готов к operational use |
| `CONFIGURED` | Configuration/prerequisites валидны, но operational use не включён |
| `ACTIVE` | Нормальная эксплуатация разрешена при прохождении dependency/auth/domain checks |
| `READ_ONLY` | Мутации заморожены, история/чтение/экспорт сохраняются |
| `INACTIVE` | Модуль явно отключён на scope, история сохраняется |
| `RETIRED` | Capability выведена из эксплуатации на scope, identity/history сохраняются |

`INACTIVE` выделен отдельно намеренно. Он не равен:

- `CONFIGURED` — «готов, но ещё не включён»;
- `READ_ONLY` — «заморожен для записи»;
- `RETIRED` — «выведен из эксплуатации».

### 4.1. Разрешённые transitions

| From | To |
|---|---|
| `AVAILABLE` | `CONFIGURED` |
| `CONFIGURED` | `ACTIVE`, `INACTIVE`, `RETIRED` |
| `ACTIVE` | `READ_ONLY`, `INACTIVE`, `RETIRED` |
| `READ_ONLY` | `ACTIVE`, `INACTIVE`, `RETIRED` |
| `INACTIVE` | `CONFIGURED`, `RETIRED` |
| `RETIRED` | `CONFIGURED` |

Прямые переходы запрещены:

- `AVAILABLE -> ACTIVE`;
- `INACTIVE -> ACTIVE`;
- `RETIRED -> ACTIVE`.

Reactivation всегда проходит через повторную configuration validation:

```text
INACTIVE -> CONFIGURED -> ACTIVE
RETIRED  -> CONFIGURED -> ACTIVE
```

### 4.2. Preconditions перехода

Любой lifecycle transition требует одновременно:

1. валидного module manifest;
2. валидного scope;
3. полномочия actor;
4. записанной причины;
5. configuration validation для target state;
6. validation required dependencies;
7. append-only audit evidence.

Ошибка любого prerequisite — `DENY`; частичного перехода нет.

## 5. Activation scope v1

Поддерживаемые scope types:

```text
ORGANIZATION
ENERGY_SITE
WORKPLACE
```

`DIVISION` и `OPERATIONAL_AREA` существуют в предметной модели, но **не являются
activation scopes v1**. Добавлять каждый существующий organizational object как
scope без доказанной потребности запрещено.

Requested context:

```text
organization: required
energy_site: optional
workplace: optional
```

Если передан `energy_site`, он обязан принадлежать requested organization.
Если передан `workplace`, он обязан принадлежать requested organization.

`EnergySite` и `Workplace` в текущей модели — две независимые scoped dimensions
внутри одной Organization; `Workplace` не объявляется child объекта.

## 6. Deterministic scope resolution

Обычный specificity order:

```text
WORKPLACE > ENERGY_SITE > ORGANIZATION
```

Это **decision precedence**, а не утверждение об ORM parent-child relation.

Алгоритм `requested context + module -> effective lifecycle state`:

1. Проверить manifest и наличие `organization`.
2. Проверить принадлежность optional `energy_site`/`workplace` этой organization.
3. Отклонить scope types, которых нет в `supported_scopes`.
4. Для каждого `(module_id, scope_type, scope_id)` должна существовать не более
   чем одна explicit rule. Дубликат = `DENY / AMBIGUOUS_SCOPE_RULE`.
5. Собрать applicable explicit rules для Organization, requested EnergySite и
   requested Workplace.
6. Для обычных states выбрать наиболее specific explicit rule:
   `WORKPLACE`, затем `ENERGY_SITE`, затем `ORGANIZATION`.
7. Если explicit rule отсутствует — effective lifecycle `AVAILABLE`.
8. После ordinary selection применить restrictive caps:
   любой applicable `READ_ONLY` или `RETIRED` на более широком контексте нельзя
   ослабить дочерним `ACTIVE`; при одновременном наличии `RETIRED` сильнее
   `READ_ONLY`.
9. `INACTIVE` не является ancestor safety cap. Более specific scope **может**
   явно стать `ACTIVE` поверх более широкого `INACTIVE`; именно это позволяет
   поэтапный rollout по объектам/рабочим местам.
10. Configuration readiness и required dependencies проверяются после state
    resolution. Они не переписывают stored lifecycle silently; failure даёт
    deterministic `DENY` с reason code.

### 6.1. Примеры

| Parent/context | More specific | Результат |
|---|---|---|
| Organization `ACTIVE` | нет child rule | inherited `ACTIVE` |
| Organization `ACTIVE` | Workplace `INACTIVE` | `INACTIVE` |
| Organization `INACTIVE` | EnergySite `ACTIVE` | `ACTIVE`, если config/deps valid |
| Organization `INACTIVE` | Workplace `ACTIVE` | `ACTIVE`, если config/deps valid |
| Organization `READ_ONLY` | Workplace `ACTIVE` | `READ_ONLY` cap; write denied |
| Organization `RETIRED` | EnergySite `ACTIVE` | `RETIRED` cap; operational use denied |
| Site `ACTIVE` | Workplace `INACTIVE` | `INACTIVE` for context containing both |
| Site `INACTIVE` | Workplace `ACTIVE` | Workplace wins ordinary precedence |
| нет rule | — | `AVAILABLE`, operational writes denied |
| duplicate same-scope rules | — | fail closed `DENY` |
| scope belongs another org | — | fail closed `DENY` |
| configuration stale | requested `ACTIVE` | activation/operation denied until revalidated |

### 6.2. Hierarchy/topology changes

Rules bind stable IDs, not names or path strings.

- Workplace move between Divisions inside one Organization does not affect
  activation v1 because Division is not a scope.
- If a scope no longer belongs to requested Organization, resolver fails closed.
- Organization reassignment/topology changes require reconciliation/audit.
- New scope type requires versioned architecture/manifest change; implementation
  must not invent precedence ad hoc.

## 7. Required dependency vs optional integration

### 7.1. Required dependency

Hard dependency exists only when module cannot preserve its own invariants without
another module/capability.

Required dependency:

- declared in manifest;
- checked before transition to `ACTIVE`;
- checked by guarded operations that depend on it;
- fail closed;
- uses the same requested context by default;
- cannot be bypassed by direct URL/service/API/admin/command;
- forms an acyclic hard-dependency graph;
- does not erase historical reads when provider later becomes inactive.

### 7.2. Optional integration

Optional integration means primary module remains independently valid.

If provider is absent/inactive:

- primary module activation remains possible;
- only integration capability is denied/degraded;
- existing historical links/snapshots remain;
- missing provider does not destroy records;
- integration may not be silently promoted to hard dependency.

### 7.3. DEFECT ↔ OPJ

Current accepted `DEFECT` module contract declares `MASTER-DATA` as dependency.
The existence of accepted `CAP-DEFECT-OPJ-LINK` does **not** prove that OPJ is a
hard dependency.

Therefore v1 classifies `DEFECT -> OPJ` as optional integration unless a future
domain decision provides evidence that DEFECT cannot maintain its own invariants
without active OPJ.

## 8. Universal access-decision contract

Будущий registry использует одну decision semantics:

```text
decide_module_access(
    normalized_context,
    module_id,
    capability_id,
    operation,
    entry_point_class,
) -> ModuleAccessDecision
```

Обязательные entry-point classes:

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

Минимальный output:

- module ID;
- capability ID;
- normalized context;
- requested operation;
- entry-point class;
- selected scope rule;
- effective lifecycle state;
- configuration result;
- dependency results;
- optional integration results;
- `ALLOW` / `DENY`;
- audit-safe denial reason code;
- contract version.

### 8.1. Где ставится защита

UI/menu visibility — только UX/defence in depth.

**Security/invariant boundary для mutation — service/capability decision**, поэтому:

- скрытый пункт меню не защищает URL;
- закрытый URL не защищает direct service call;
- admin не имеет implicit bypass;
- management command не имеет implicit bypass;
- background job не имеет implicit bypass;
- cross-module write не имеет implicit bypass.

Итоговое разрешение действия:

```text
module access ALLOW
AND identity/RBAC/authority ALLOW
AND domain invariants ALLOW
```

Module activation **не заменяет** RBAC и предметные полномочия.

## 9. Entry-point guard matrix

| Entry point | Read | Mutation | Требование |
|---|---|---|---|
| Navigation/UI | predicate before render/action link | no UI-only write | hidden UI never sufficient |
| Direct HTTP route | predicate | predicate + guarded service | manual URL cannot bypass |
| Service layer | predicate where module capability is used | **mandatory predicate** | canonical mutation boundary |
| API | predicate | predicate + guarded service | same semantics as UI |
| Admin | predicate | predicate + domain policy | superuser is not module-activation bypass |
| Management command | predicate/context required | predicate + explicit scope | no global hidden bypass |
| Export | read predicate | n/a unless export mutates | state-specific historical export allowed |
| Background job | read-safe predicate | mutation predicate | state re-evaluated at execution time |
| Cross-module action | target/source decision | both relevant decisions | integration ≠ bypass |

## 10. Lifecycle behaviour matrix

`ALLOW` ниже означает только module-activation layer; normal authorization/domain
rules всё равно применяются.

| Effective state | List/read | Detail/history | Create | Edit/transition | Delete | Export | Background | Cross-links |
|---|---|---|---|---|---|---|---|---|
| `ACTIVE` | ALLOW | ALLOW | ALLOW | ALLOW | only capability+domain policy | ALLOW | read+mutate if declared | subject to target decision |
| `READ_ONLY` | ALLOW | ALLOW | DENY | DENY | DENY | read-only ALLOW | read-safe only | read-only |
| `INACTIVE` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | history-safe only | retained links |
| `RETIRED` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | history-safe only | retained links + retired marker |
| `CONFIGURED` | history only | retained history ALLOW | DENY | DENY | DENY | retained-history ALLOW | history-safe only | retained links |
| `AVAILABLE` | retained history only if supported | generic retained-history path | DENY | DENY | DENY | retained export if supported | no mutation | preserve reference; deny operational action |

Для operationally/legal significant records module state никогда не является
основанием physical delete.

## 11. History and reactivation

Обязательные invariants:

- disable/read-only/retire не удаляет records;
- snapshots остаются;
- audit остаётся;
- relations остаются;
- stable module ID не меняется;
- reactivation продолжает существующую history;
- нельзя создать «новый экземпляр модуля» вместо reactivation;
- stale configuration проверяется заново;
- required dependencies проверяются заново;
- failed reactivation не меняет effective active access.

## 12. Migration semantics

Software/database migrations принадлежат **версии продукта**, не activation state.

Обязательный contract:

```text
same product version
=> one compatible schema evolution
=> migrations shipped with product apply regardless module ACTIVE/INACTIVE
```

Следствия:

- inactive module migrations не пропускаются;
- retained inactive data мигрируют безопасно;
- migration не активирует module;
- upgrade не меняет explicit activation state сам по себе;
- после upgrade inactive/read-only/retired module остаётся таким же;
- последующая reactivation использует уже migrated retained data;
- разные installations одной версии не получают разные DB schemas из-за module set.

Полная executable matrix:

```text
active/inactive module × N-1/N upgrade/reactivation
```

отложена **строго** в `MODULE-MIGRATION-COMPATIBILITY-001`.

## 13. Activation audit contract

Каждая попытка изменить state обязана оставить append-only evidence:

- `module_id`;
- `scope_type`;
- `scope_id`;
- `organization_id`;
- previous explicit state;
- previous effective state;
- requested new state;
- resulting effective state;
- actor identity;
- timestamp;
- reason;
- configuration-validation result;
- dependency-validation result;
- result (`ALLOWED` / `REJECTED`);
- denial reason code;
- correlation/trace identity;
- manifest contract version.

Не требуется строить отдельную огромную audit subsystem в этом work item.
Требуется, чтобы будущая реализация не могла «просто обновить флаг» без evidence.

## 14. Negative architecture evidence

Machine checker и fixtures обязаны отклонять следующие варианты:

1. `N01`: UI скрыт, direct URL остаётся operationally доступен.
2. `N02`: route закрыт, но service write остаётся доступен.
3. `N03`: optional integration превращена в required dependency без domain evidence.
4. `N04`: required dependency отсутствует, но activation проходит.
5. `N05`: disable приводит к удалению records/history.
6. `N06`: `READ_ONLY` допускает write/transition.
7. `N07`: upgrade автоматически активирует inactive module.
8. `N08`: inactive module пропускает schema migrations.
9. `N09`: конфликт/duplicate scope rules разрешается случайным first-match.
10. `N10`: reactivation создаёт новую module identity.

Дополнительные negative fixtures проверяют:

- drift manifest minimum;
- отсутствие `SERVICE` entry-point class;
- прямой `RETIRED -> ACTIVE`;
- изменение canonical scope precedence.

## 15. Current implementation-gap mapping

| Контур | Сейчас | MODULE-REGISTRY-001 |
|---|---|---|
| Django apps | globally installed | остаются installed; activation не меняет `INSTALLED_APPS` |
| URL namespaces | globally included | guards enforce capability at runtime |
| DEFECT middleware | specialized route redirect | не использовать как generic activation engine |
| Navigation | нет universal activation predicate | render from same decision semantics |
| Direct HTTP | нет generic module guard | common decision before module action |
| Services | domain services существуют без module predicate | mutation service boundary must guard |
| API | generic registry semantics отсутствует | any future API uses same predicate |
| Admin | global `/admin/` route | no activation bypass |
| Management commands | no universal module context guard | explicit scope + same predicate |
| Exports | module-specific behavior | state-aware read/export decision |
| Background paths | no universal registry semantics | re-evaluate state at execution |
| Cross-module links | point integrations exist | source/target capability decisions |
| Scope records | отсутствуют | registry tables/control plane |
| Activation audit | отсутствует | append-only transition evidence |
| Migrations | product migrations | remain product-version property |

## 16. Boundaries handed to MODULE-REGISTRY-001

`MODULE-REGISTRY-001` получает уже закрытые архитектурные решения и должен реализовать:

1. manifest loading/validation;
2. stable module/capability registry;
3. unique scoped activation records;
4. resolver with the exact v1 scope algorithm;
5. lifecycle transition service;
6. configuration/dependency validation;
7. universal `ModuleAccessDecision`;
8. service mutation guard;
9. adapters for UI/routes/API/admin/commands/exports/jobs/cross-module actions;
10. append-only activation audit;
11. mixed Organization/EnergySite/Workplace tests;
12. disable/read-only/retire/reactivation runtime evidence.

Он **не должен** заново решать:

- является ли EOD микросервисной системой;
- нужно ли динамически ставить/удалять Django apps;
- можно ли пропускать migrations выключенного модуля;
- можно ли удалять историю при disable;
- можно ли считать hidden menu защитой;
- precedence scope rules;
- hard-vs-optional dependency semantics;
- reactivation identity.

## 17. Что этим PR не меняется

Не меняются:

- product/domain models;
- migrations;
- рабочие данные;
- runtime configuration;
- live VPS;
- Preview;
- UX/page templates;
- предметные журналы;
- `SHIFT-HANDOVER-001`;
- `MODULE-REGISTRY-001` implementation.

`MODULE-ACTIVATION-CONTRACT-001` считается технически готовым к owner acceptance,
когда machine contract, checker, negative fixtures, canonical transition и
applicable exact-head gates согласованы на одном final head.
