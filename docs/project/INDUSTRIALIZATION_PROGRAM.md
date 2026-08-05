# ЭОД — программа индустриализации платформы

**Версия:** `1.0-candidate-repair1`
**Дата:** 05.08.2026
**Источник:** `PROJECT-SUSTAINABILITY-001`
**Machine-readable owner:** `docs/project/INDUSTRIALIZATION_PROGRAM.yaml`
**Статус:** `PROPOSAL / USER RE-ACCEPTANCE REQUIRED`

## 1. Назначение

- **[DECISION]** Программа превращает текущий демонстрационный ЭОД в сопровождаемую single-product platform без смены modular Django monolith и без big-bang rewrite.
- **[DECISION]** Программа не заменяет `DEMO_RELEASE_PLAN.yaml`: release plan владеет предметным scope, а эта программа владеет industrial prerequisites, risk treatment и platform gates.
- **[PROPOSAL]** Все work items программы должны ссылаться на risk IDs из `PROJECT_SUSTAINABILITY_RISK_REGISTER_20260805.csv`; работа без закрываемого риска или capability запрещена.
- **[PROPOSAL]** Программа исполняется последовательно по правилу one active product work item. Возможная параллельная аналитика не создаёт конкурирующие branches/PRs.

## 2. Почему не нужен «рефакторинг всего»

- **[FACT]** Текущий продукт уже имеет 716 passing tests, PostgreSQL CI, доменные invariants, immutable document patterns, authority snapshots, shared UX direction и рабочие reference modules.
- **[FACT]** Наибольшие риски сосредоточены не в выборе framework, а в управлении конфигурацией модулей, эксплуатационной воспроизводимости, recovery, security, observability и canonical state.
- **[DECISION]** Переписывание с нуля, микросервисы и массовая перестройка репозитория отвергаются как непропорциональные риску.
- **[PROPOSAL]** Каждая фаза должна давать проверяемую capability и не создавать долгую «платформенную ветку», которую невозможно принимать частями.

## 3. Два обязательных gate

### GATE SC — SAFE-CONTINUATION

Закрывается до отдельного решения владельца о возобновлении ограниченной предметной работы.

Обязательный состав work items:

1. `PROJECT-STATE-RECONCILIATION-001`;
2. `INDUSTRIALIZATION-PROGRAM-EXECUTION-001`;
3. `MODULE-ACTIVATION-CONTRACT-001`;
4. `SECRET-HYGIENE-001`;
5. `DEPENDENCY-PROVENANCE-001`;
6. `DEPLOYMENT-PROFILE-001`;
7. `BACKUP-RESTORE-DRILL-001`;
8. `SECURITY-BASELINE-001`.

Условия gate:

1. canonical planning state согласован и автоматически проверяется;
2. module activation target contract принят до реализации models/migrations;
3. публичные/постоянные demo credentials устранены из логов;
4. зависимости и container bases воспроизводимо зафиксированы;
5. pilot/production configuration contract определён и fail-closed;
6. выполнен и сертифицирован контрольный restore на non-production контуре;
7. risk register и industrial backlog имеют владельцев и acceptance.

- **[PROPOSAL]** После GATE SC отдельным решением владельца может быть разрешена ограниченная работа над существующим принятым контуром, например `SHIFT-HANDOVER-001`.
- **[PROPOSAL]** GATE SC сам по себе не разрешает массовую реализацию новых журналов и модулей и не означает готовность к пилоту.

### GATE PR — PILOT-READY

Закрывается до подключения реального пилотного объекта, пользователей или operational data. Восемь фаз остаются полной программой индустриализации, но gate не требует механического завершения всех фаз и всех work items.

#### Обязательный core-набор

1. `PROJECT-STATE-RECONCILIATION-001`;
2. `INDUSTRIALIZATION-PROGRAM-EXECUTION-001`;
3. `MODULE-ACTIVATION-CONTRACT-001`;
4. `SECRET-HYGIENE-001`;
5. `DEPENDENCY-PROVENANCE-001`;
6. `DEPLOYMENT-PROFILE-001`;
7. `BACKUP-RESTORE-DRILL-001`;
8. `SECURITY-BASELINE-001`;
9. `MODULE-REGISTRY-001`;
10. `DATA-INTEGRITY-HARDENING-001`;
11. `MIGRATION-SAFETY-001`;
12. `MODULE-MIGRATION-COMPATIBILITY-001`;
13. `DATA-GOVERNANCE-001`;
14. `RELEASE-ROLLBACK-001`;
15. `OBSERVABILITY-001`;
16. `INCIDENT-RESPONSE-001`;
17. `AUTH-RBAC-HARDENING-001`;
18. `SECURITY-PIPELINE-001`;
19. `UX-BROWSER-GATES-001`;
20. `SUPPORT-HANDOVER-001`;
21. `PILOT-READINESS-001`.

#### Risk и scope policy

- **[PROPOSAL]** Каждый применимый `CRITICAL`-риск закрывается либо явно принимается владельцем с ограниченным сроком, compensating controls, ответственным и условиями пересмотра.
- **[PROPOSAL]** Неприменимость риска к конкретному pilot scope должна быть доказана и зафиксирована; молчаливое исключение запрещено.
- **[PROPOSAL]** Pilot-scope-dependent work items становятся обязательными по своим triggers: `UPLOAD-HARDENING-001`, `DATA-PORTABILITY-001`, `LEGACY-UX-MIGRATION-001`, `UX-PLATFORM-FOUNDATION-001`, `PAGE-TEMPLATE-LIBRARY-001`, `MODULE-SOURCE-GOVERNANCE-001`, `DRIVE-LIBRARY-GOVERNANCE-001`, `PERFORMANCE-BASELINE-001`.
- **[PROPOSAL]** Остаточные `HIGH`/`MEDIUM`-риски должны быть закрыты, либо включены в датированный residual-risk register с owner, compensating controls, сроком и явным решением владельца.
- **[PROPOSAL]** Неприменимые к pilot scope долгосрочные работы не блокируют pilot автоматически; решение и обоснование фиксирует `PILOT-READINESS-001`.
- **[DECISION]** Финальное разрешение pilot всегда даёт владелец продукта отдельным явным решением с опубликованными ограничениями.

## 4. Risk-ranked последовательность

## Фаза 0 — восстановить управляемость источника истины

### 0.1 `PROJECT-STATE-RECONCILIATION-001`

**Риски:** PSR-001, PSR-002, PSR-034
**Тип:** documentation/process automation

- **[FACT]** Current release plan and human-readable views содержат stale statuses.
- **[PROPOSAL]** Сверить accepted work items, main history, release plan, module map и implementation sequence; определить, какие views generated/derived.
- **[PROPOSAL]** Documentation contract должен блокировать stale accepted status, duplicate owner и очередь, противоречащую active/accepted state.

**Acceptance:** один canonical status owner; derived views совпадают; intentional gaps marked `VERIFY`; exact-head documentation gates green.

### 0.2 `INDUSTRIALIZATION-PROGRAM-EXECUTION-001`

**Риски:** PSR-034
**Тип:** governance

- **[PROPOSAL]** После принятия этой программы добавить work items в canonical plan без изменения предметного Demo scope.
- **[PROPOSAL]** Каждому work item назначить severity, dependencies, allowed files, runtime profile and acceptance evidence.

**Acceptance:** machine-readable industrial backlog связан с risk register; GATE SC/GATE PR отображаются в master checklist.

## Фаза 1 — SAFE-CONTINUATION architecture and runtime baseline

### 1.1 `MODULE-ACTIVATION-CONTRACT-001`

**Риски:** PSR-004, PSR-005, PSR-014

Документационный/architecture work item после governance reconciliation:

- manifest schema;
- lifecycle states;
- scope precedence;
- dependency/conflict rules;
- data preservation/reactivation;
- migration behavior;
- route/service/task/admin/export guard contract;
- audit events and UX behavior.

**Acceptance:** owner accepts all ambiguous semantics before models/migrations.

### 1.2 `SECRET-HYGIENE-001`

**Риск:** PSR-021
**Приоритет:** немедленно

- удалить passwords из CI output;
- заменить постоянные demo credentials на generated/ephemeral либо masked values;
- проверить историю, artifacts, example env и docs;
- установить rotation rule.

**Acceptance:** secret scan и manual grep не находят active credentials; tests не печатают passwords; demo access reproducible through safe procedure.

### 1.3 `DEPENDENCY-PROVENANCE-001`

**Риски:** PSR-017, PSR-023, PSR-016

- exact lock/constraints with hashes;
- pinned image digests;
- controlled dependency update process;
- SBOM and build provenance;
- vulnerability severity policy.

**Acceptance:** две сборки одного commit разрешают одинаковый dependency set; SBOM привязан к image digest; critical vulnerabilities block release.

### 1.4 `DEPLOYMENT-PROFILE-001`

**Риски:** PSR-003, PSR-022, PSR-018

- отдельный pilot/production mode;
- fail-closed validation secrets, PostgreSQL, DEBUG, hosts, TLS/proxy and secure cookies;
- environment contract and clean-install path;
- immutable release image and configuration separation.

**Acceptance:** unsafe settings refuse start; `manage.py check --deploy` and external session/TLS smoke pass; Preview semantics unchanged.

### 1.5 `BACKUP-RESTORE-DRILL-001`

**Риски:** PSR-015, PSR-013

- определить RPO/RTO and retention candidate;
- создать off-host encrypted backup policy;
- выполнить restore representative database to isolated target;
- verify migrations, auth, counts, digests and critical scenarios;
- сохранить restore certificate.

**Acceptance:** successful restore with checksum, measured duration, object/integrity evidence and owner decision.

### 1.6 `SECURITY-BASELINE-001`

**Риски:** PSR-022, PSR-023, PSR-024, PSR-033

- threat model and trust boundaries;
- secure session/cookie/proxy settings;
- privileged operations and admin surface;
- password/re-auth/MFA target;
- rate limiting/lockout and security headers;
- security remediation SLA.

**Acceptance:** security checklist and negative tests; no protected workflow bypass through admin; accepted residual risks documented.

### GATE SC decision

- **[PROPOSAL]** GATE SC review проводится после Phase 0 и work items 1.1–1.6.
- **[PROPOSAL]** Ограниченная работа над существующим принятым контуром, включая возможный `SHIFT-HANDOVER-001`, требует отдельного решения владельца по результатам GATE SC.
- **[PROPOSAL]** Массовая реализация новых журналов и модулей не начинается до `MODULE-REGISTRY-001`, `UX-PLATFORM-FOUNDATION-001`, `PAGE-TEMPLATE-LIBRARY-001` и `MODULE-SOURCE-GOVERNANCE-001`.

## Фаза 2 — modular platform control plane

### 2.1 `MODULE-REGISTRY-001`

**Риски:** PSR-004, PSR-005

Implementation work item после `MODULE-ACTIVATION-CONTRACT-001`:

- registry models/services;
- scoped activation;
- common capability resolver;
- read-only/retired behavior;
- audit history;
- admin/configuration UX;
- guards and tests.

**Acceptance:** matrix with at least two organizations, two sites and multiple workplaces; mixed module sets; disable preserves history; no bypass.

### 2.2 `MODULE-BOUNDARY-GATES-001`

**Риски:** PSR-006, PSR-007

- machine-readable app ownership;
- dependency/import rules;
- public service interfaces;
- complexity/ignore budget;
- maintainability hotspot ownership;
- dead-path and duplicate-service inventory.

**Acceptance:** CI dependency graph cycle-free; prohibited imports fail; hot spots have explicit owners; new ignores require explicit decision and debt trend does not worsen.

## Фаза 3 — data reliability and controlled release

### 3.1 `DATA-INTEGRITY-HARDENING-001`

**Риски:** PSR-011, PSR-012

- least-privilege DB application role;
- protected maintenance path;
- integrity scan for snapshots/signatures/audit chains;
- break-glass procedure;
- immutable integrity report retention.

### 3.2 `MIGRATION-SAFETY-001`

**Риск:** PSR-013

- accepted DB fixtures/snapshots;
- N-1/N-2 upgrade tests;
- expand/migrate/contract policy for destructive changes;
- migration runtime and lock analysis.

### 3.3 `MODULE-MIGRATION-COMPATIBILITY-001`

**Риски:** PSR-013, PSR-014

- upgrade tests for active/inactive combinations;
- reactivation after upgrade;
- no data deletion on retirement;
- compatibility matrix by release.

**Dependencies:** `MODULE-REGISTRY-001`, `MIGRATION-SAFETY-001`.

**Acceptance:** representative combinations migrate and rollback decision is documented.

### 3.4 `DATA-GOVERNANCE-001`

**Риски:** PSR-026, PSR-032

- classification;
- retention/archive/legal hold;
- personal data handling;
- canonical export schema;
- attachment/source linkage;
- deletion prohibitions and allowed anonymization.

### 3.5 `DATA-PORTABILITY-001`

**Риск:** PSR-032

- versioned export package;
- records, snapshots, authorities, audit, source IDs and files;
- checksums/manifests;
- round-trip verification into isolated environment.

### 3.6 `RELEASE-ROLLBACK-001`

**Риски:** PSR-016, PSR-015

- immutable image and release manifest;
- migration compatibility;
- deployment rehearsal;
- rollback hierarchy and measured exercise;
- release evidence bundle.

## Фаза 4 — эксплуатация и security completion

### 4.1 `OBSERVABILITY-001`

**Риски:** PSR-018, PSR-019

- structured JSON logs;
- request/correlation IDs;
- security and domain audit correlation;
- liveness/readiness/dependency health;
- metrics, dashboards, alerts and retention;
- backup freshness and migration state signals.

### 4.2 `INCIDENT-RESPONSE-001`

**Риск:** PSR-020

- severity and ownership;
- communication/escalation;
- incident commander;
- forensic preservation;
- tabletop and technical drills;
- postmortem and preventive action tracking.

### 4.3 `AUTH-RBAC-HARDENING-001`

**Риски:** PSR-024, PSR-033

- joiner/mover/leaver;
- privileged roles and assurance levels;
- periodic access review;
- break-glass;
- admin surface;
- cross-scope and module guard tests.

### 4.4 `SECURITY-PIPELINE-001`

**Риск:** PSR-023

- secret/SAST/dependency/container scans;
- SBOM and provenance verification;
- exception process and remediation SLA;
- branch protection required checks.

### 4.5 `UPLOAD-HARDENING-001`

**Риск:** PSR-025

- complete upload/import inventory;
- centralized policy: size, MIME, extension, filename, quarantine, AV, storage, download authorization, retention;
- malicious fixture tests.

## Фаза 5 — единая UX-платформа без big-bang rewrite

### 5.1 `UX-PLATFORM-FOUNDATION-001`

**Риски:** PSR-008, PSR-009, PSR-010

- executable tokens and primitives;
- standard page profiles;
- component examples/states;
- shared interaction and accessibility contracts;
- reference modules DEFECT and OPJ.

### 5.2 `LEGACY-UX-MIGRATION-001`

- route/template/static inventory;
- migration waves by user scenario;
- source contract preventing overlay accumulation;
- deletion evidence for obsolete layers;
- no parallel visual system.

### 5.3 `UX-BROWSER-GATES-001`

- critical route browser tests;
- Edge-compatible Chromium and Chrome;
- theme, viewport, print and keyboard gates;
- controlled screenshot baselines;
- stale asset/cache-busting checks.

### 5.4 `PAGE-TEMPLATE-LIBRARY-001`

- `REGISTRY_PAGE`;
- `STANDARD_JOURNAL`;
- `SPECIALIST_WORKSPACE`;
- `PROCESS_TIMELINE`;
- empty/loading/error/read-only/disabled-module states.

## Фаза 6 — knowledge/source governance

### 6.1 `MODULE-SOURCE-GOVERNANCE-001`

**Риск:** PSR-027

- module/capability → required source IDs;
- required local instructions;
- freshness/owner/publication state;
- work-item preflight checker;
- normative evidence versus product decision separation.

### 6.2 `DRIVE-LIBRARY-GOVERNANCE-001`

**Риск:** PSR-028

- Drive taxonomy;
- stable locator and checksum;
- access/ownership;
- version/freshness review;
- GitHub decision linkage;
- no duplicate canonical owner.

## Фаза 7 — pilot and handover

### 7.1 `PERFORMANCE-BASELINE-001`

**Риск:** PSR-031

- user/concurrency/data-volume model;
- latency and resource targets;
- load, soak and database-growth tests;
- capacity headroom and maintenance.

### 7.2 `SUPPORT-HANDOVER-001`

**Риск:** PSR-029

- service catalog;
- install/upgrade/restore/rollback runbooks;
- access and secret ownership;
- maintenance calendar;
- L1/L2/L3 and escalation;
- independent specialist exercise.

### 7.3 `PILOT-READINESS-001`

**Риск:** PSR-030

Independent evidence review:

- product scope and limitations;
- mandatory core work items;
- applicable CRITICAL risks;
- pilot-scope-dependent work;
- residual HIGH/MEDIUM risks;
- module activation;
- identity/security;
- data/recovery;
- operations/incident;
- UX/browser;
- performance where triggered by pilot scope;
- support/handover;
- pilot-specific local instructions and data profile.

**Acceptance:** mandatory core complete; every applicable CRITICAL risk closed or explicitly accepted with bounded compensating controls; scope-dependent evidence resolved; residual risks recorded; owner explicitly approves pilot.

## 5. Отношение к предметной очереди

- **[DECISION]** `SHIFT-HANDOVER-001` не начинается внутри текущего audit work item.
- **[PROPOSAL]** После GATE SC владелец может отдельным решением разрешить один ограниченный work item в существующем принятом контуре, например `SHIFT-HANDOVER-001`. Решение фиксируется в canonical plan, а не только в чате.
- **[PROPOSAL]** Массовая реализация новых журналов и модулей начинается только после реализации `MODULE-REGISTRY-001`, базовой `UX-PLATFORM-FOUNDATION-001` вместе с `PAGE-TEMPLATE-LIBRARY-001` и `MODULE-SOURCE-GOVERNANCE-001`.
- **[PROPOSAL]** SAFE-CONTINUATION не утверждает, что ещё не реализованные source requirements или page profiles уже доступны; до их реализации они остаются prerequisites, а не действующими capabilities.
- **[PROPOSAL]** Исключение из этой границы требует отдельного ADR и явного решения владельца с ограниченным scope и принятыми рисками.
- **[DECISION]** OPJ и DEFECT не переписываются; они становятся reference implementations и мигрируют только по доказанным gaps.

## 6. NOTES и MAIL-INTEGRATION

### NOTES

- **[DECISION]** Личные и общие заметки входят в target product architecture как optional module.
- **[PROPOSAL]** `NOTES-ARCHITECTURE-001` допускается после MODULE-REGISTRY, DATA-GOVERNANCE и UX page profiles.
- **[PROPOSAL]** Notes не должны маскироваться под зарегистрированные operational facts; требуются отдельные retention, sharing, search and conversion-to-document rules.

### MAIL-INTEGRATION

- **[WISHLIST]** Local Exchange integration остаётся последней очередью.
- **[DECISION]** Она не входит в GATE SC, GATE PR и первый pilot.
- **[PROPOSAL]** Будущий work item начинается только после доказанного доступного integration contract предприятия и security review.

## 7. Machine-readable consistency contract

- **[FACT]** `INDUSTRIALIZATION_PROGRAM.yaml` содержит machine-readable `consistency_contract` для проверки risk/work-item references, dependency references, межфазного порядка, gate existence и ключевой Markdown/YAML projection.
- **[PROPOSAL]** В этом documentation-only repair consistency contract проверяется отдельной одноразовой валидацией; превращение его в постоянный executable Documentation Contract относится к `PROJECT-STATE-RECONCILIATION-001`, а не к текущему scope.
- **[DECISION]** Machine-readable owner остаётся YAML; Markdown не вводит самостоятельный состав gates или work items.

## 8. Change control

- **[PROPOSAL]** `INDUSTRIALIZATION_PROGRAM.yaml` — единственный machine-readable owner этой программы.
- **[PROPOSAL]** MD является human-readable projection; расхождение блокирует acceptance программы.
- **[PROPOSAL]** Изменение sequence, gates или risk ownership выполняется отдельным decision record.
- **[DECISION]** Merge/Ready for Review текущего PR требует отдельной команды владельца.
