# PROJECT-SUSTAINABILITY-001 — аудит и программа промышленной подготовки ЭОД

## Состояние

```text
work item: PROJECT-SUSTAINABILITY-001
issue: #48
branch: audit/project-sustainability-001
PR: PENDING
baseline main: c57a84752fae7a5265f393f77568849365be50a7
risk profile: DOCS / ARCHITECTURE / AUDIT
runtime impact: NONE
preview: UNTOUCHED
user acceptance: ABSENT
merge authorization: ABSENT
```

## Цель

Сформировать доказательную, risk-ranked и исполнимую программу превращения
текущего ЭОД из демонстрационного продукта в сопровождаемую промышленную
платформу до продолжения массовой реализации предметных модулей.

Этот work item не реализует саму промышленную архитектуру. Он устанавливает
фактический baseline, gaps, target contracts, последовательность и критерии
последующих ограниченных work items.

## Обязательный factual preflight

Перед выводами самостоятельно проверить фактическое состояние GitHub и прочитать:

1. `AGENTS.md`;
2. `README.md`;
3. `docs/INDEX.md`;
4. `docs/project/CURRENT_STATE.md`;
5. `docs/project/DEMO_RELEASE_PLAN.yaml`;
6. `docs/project/CURRENT_HANDOFF.md`;
7. `docs/project/SYSTEM_ARCHITECTURE.md`;
8. `docs/project/DOMAIN_INVARIANTS.md`;
9. `docs/project/PRODUCT_UX_PRINCIPLES.md`;
10. `docs/ux/UX_UI_CONTRACT_V1.md`;
11. `docs/ux/COMPONENT_CATALOG.md`;
12. `docs/ux/ROUTE_REFERENCE_MATRIX.csv`;
13. `docs/process/PROJECT_OPERATING_SYSTEM.md`;
14. `docs/process/DEVELOPMENT_WORKFLOW.md`;
15. `docs/process/CI_AND_QUALITY_GATES.md`;
16. `docs/process/RELEASE_PROCESS.md`;
17. `docs/process/PARALLEL_CHAT_WORKFLOW.md`;
18. `docs/product/MODULE_MAP.md`;
19. `docs/product/IMPLEMENTATION_SEQUENCE.md`;
20. применимые runbooks, workflows, Compose/infra/config files и фактический code layout.

Не считать документацию верной без проверки кода и GitHub state.

## Принятые пользовательские решения

Следующие положения уже заданы владельцем продукта и не являются свободными
предложениями исполнителя:

- GitHub — единственный источник кода и канонической документации;
- VPS — runtime/testing, но не источник кода;
- сохраняется направление modular Django monolith;
- микросервисы не вводятся без доказанного требования;
- журналы и функциональные контуры должны быть подключаемыми модулями одного
  продукта с поэтапной активацией по организации, энергообъекту и/или рабочему
  месту;
- отключение модуля не удаляет исторические данные;
- требуется единая UX-платформа, shared components, design tokens, типовые
  страницы и профили журналов;
- существующий смешанный UX мигрирует постепенно, без big-bang rewrite;
- Google Drive допустим как библиотека материалов, но не как конкурирующий
  canonical owner;
- пользователь не должен вручную передавать SHA, handoff и отчёты между чатами;
- личные и общие заметки входят в target architecture как будущий модуль;
- интеграция с локальным Exchange остаётся wishlist последней очереди и не
  является зависимостью первого пилота;
- следующий предметный work item после OPJ временно не начинается до принятия
  программы промышленной подготовки.

## Audit domains

### 1. Repository and maintainability

- code/module layout;
- dependency direction and coupling;
- duplicated services/templates/static assets;
- legacy layers and dead paths;
- configuration and environment boundaries;
- documentation ownership and contradictions;
- bus factor and independent maintainability.

### 2. Modular platform

- core versus optional modules;
- module registry and manifest;
- activation scopes;
- required dependencies versus optional integrations;
- route/service/task/API/permission guards;
- module lifecycle: available/configured/active/read-only/retired;
- data retention and reactivation;
- upgrade behavior with inactive modules;
- mixed module sets across sites.

### 3. UX platform

- route and component inventory;
- legacy/partial/compliant classification;
- shared shell and primitives;
- page templates;
- standard journal, specialist workspace, registry and process profiles;
- visual regression and browser/viewport/theme gates;
- reference migrations using DEFECT and OPJ;
- removal strategy for obsolete CSS/templates without overlay accumulation.

### 4. Data and reliability

- schema ownership;
- migrations and backward compatibility;
- immutable/registered facts;
- audit/history/evidence consistency;
- backup, restore and restore testing;
- retention, archive and attachment handling;
- data export and portability;
- failure and rollback boundaries.

### 5. Deployment and operations

- environment topology;
- clean installation;
- configuration/secrets;
- release, update and rollback;
- observability and health;
- logs and incident diagnosis;
- runbooks and support handover;
- Preview/development isolation;
- disaster recovery readiness.

### 6. Security and access

- authentication and session handling;
- RBAC/scope evaluation;
- privileged operations;
- secrets and credentials;
- file/upload safety;
- auditability;
- personal and operational data exposure;
- threat model and hardening priorities.

### 7. Knowledge and source governance

- source registry;
- stable source IDs;
- module-to-source matrix;
- Google Drive library structure;
- publication/copyright boundaries;
- version and freshness tracking;
- automatic completeness and link checks.

### 8. Product plan

- current Demo scope versus industrial prerequisites;
- dependency-safe pause/resume point;
- NOTES target placement and dependencies;
- MAIL-INTEGRATION deferred wishlist;
- pilot-readiness gates;
- work-item decomposition and ordering.

## Обязательные артефакты

Минимально требуются:

```text
docs/audits/PROJECT_SUSTAINABILITY_BASELINE_20260805.md
docs/audits/PROJECT_SUSTAINABILITY_RISK_REGISTER_20260805.csv
docs/project/INDUSTRIALIZATION_PROGRAM.md
docs/project/INDUSTRIALIZATION_PROGRAM.yaml
docs/decisions/PROJECT_SUSTAINABILITY_001_DECISIONS.md
```

Допускается добавить только доказанно необходимые machine-readable matrices.

## Требования к выводам

Каждый существенный пункт должен быть классифицирован:

- `FACT` — подтверждён GitHub/code/runtime evidence;
- `GAP` — подтверждённое расхождение или отсутствие;
- `DECISION` — явное решение пользователя или принятый canonical decision;
- `PROPOSAL` — рекомендация, ещё не принятая пользователем;
- `WISHLIST` — отложенная необязательная возможность;
- `VERIFY` — данных недостаточно, требуется отдельная проверка.

Для каждого риска указать:

- identifier;
- domain;
- severity;
- evidence;
- impact;
- recommended treatment;
- proposed owner/work item;
- dependency;
- acceptance evidence.

## Out of scope

- product code;
- models, migrations and data;
- runtime/VPS changes;
- создание module registry;
- реализация UX platform;
- notes или mail implementation;
- массовая перестройка структуры репозитория;
- изменение Preview;
- Ready for Review или merge без отдельной команды пользователя.

## Проверки

Профиль `DOCS`:

- documentation contract;
- release-plan/schema validation;
- links and duplicate-owner checks;
- consistency of generated/human-readable views;
- no application/runtime/schema diff.

Полный application suite не требуется, если diff остаётся строго документационным.

## Stop condition

Остановиться после:

1. завершения factual audit;
2. публикации всех обязательных артефактов;
3. прохождения documentation gates;
4. обновления Draft PR body по exact head;
5. представления пользователю краткого содержательного отчёта и очереди следующих
   work items.

Не переводить PR в Ready for Review и не выполнять merge.
