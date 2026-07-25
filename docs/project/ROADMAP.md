# ЭОД — roadmap

## Принцип

Roadmap управляется доказательствами, а не только исторической нумерацией патчей. Каждый этап начинается после проверки текущего baseline и заканчивается технической и пользовательской приёмкой.

## Принятый baseline

```text
main / 937d2cd2b187c17fac3088ccfc52079fc4608306
```

Он включает INFRA-001–003, DOCS-001–003, QUALITY-001 и AUTO-000.

## Последние завершённые этапы

### DOCS-001 — Project operating system

**Статус:** принят, squash-merged PR #4, post-merge verified.

Выходы:

- canonical documentation tree;
- README and AGENTS contracts;
- current state, handoff, master plan, roadmap and domain invariants;
- preview/development runbooks;
- PR template and documentation CI gate;
- sequential journal strategy;
- paper-first keys journal;
- UX-001 parallel workstream.

DOCS-002 зафиксировал baseline metadata. DOCS-003 сохранил UX-001 v0.3 как provisional contract.

### QUALITY-001 — PostgreSQL test execution repair

**Статус:** принят, squash-merged PR #8.

```text
merge commit: 4237aadc2cfdee518567024c2b45b653f49c16e7
full PostgreSQL suite: 497/497 OK
test command: python manage.py test apps --verbosity 2
```

Нулевой test discovery закрыт. Следующие product slices сохраняют full suite и добавляют профильные tests/gates.

### AUTO-000 — Development automation contract

**Статус:** принят, squash-merged PR #9, post-merge verified.

```text
accepted PR head: 3a4b4770e1fce41405813efa1e931288bf1a26b8
merge commit: 937d2cd2b187c17fac3088ccfc52079fc4608306
change type: documentation-only operating-system milestone
```

Выходы:

- automation master plan;
- GitHub/VPS orchestrator contract;
- exact-SHA and fail-closed invariants;
- restricted security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- explicit ban on automatic merge and preview write.

Post-merge preview rebuilt from current main and verified: healthy app/db, HTTP 200, `eod_preview`, migrations clean, exact SHA/worktree clean, host/container source match.

## Текущий metadata follow-up

### DOCS-005 — AUTO-000 baseline finalization

**Статус:** Draft PR #10.

```text
branch: docs/005-auto000-baseline-finalization
runtime impact: none
```

Цель:

- записать accepted baseline `937d2cd…`;
- синхронизировать state/handoff/history/roadmap/open items/release notes;
- подготовить новый постоянный Chat 0;
- сохранить границу: собственный merge SHA DOCS-005 не создаёт новый application baseline.

## Следующий короткий инфраструктурный этап

### AUTO-001 — Development orchestrator MVP

Начинается после принятия DOCS-005 и в отдельном implementation chat/branch/PR.

Перед реализацией обязателен gap analysis actual infrastructure:

1. main, exact SHA, open PR and branches;
2. `AGENTS.md`, canonical docs and all `docs/automation/`;
3. actual workflows, compose, scripts and runbooks;
4. network route GitHub-hosted runner → VPS;
5. restricted transport and permissions;
6. только затем executable workflow/gateway.

Минимальный infrastructure vertical slice:

```text
trusted PR trigger
→ green current-head CI
→ restricted VPS gateway
→ exact-SHA development deployment
→ explicit refresh/rebuild
→ check
→ full test apps
→ status
→ preview isolation proof
→ sanitised GitHub evidence
```

Gate завершения:

- два successive successful deployments;
- один intentional negative case;
- exact-SHA and superseded proof;
- preview isolation proof;
- normal cycle without manual VPS commands from user;
- automatic merge absent;
- explicit user acceptance.

Не входят:

- automatic preview deployment;
- browser automation;
- visual regression;
- automatic development DB reset;
- autonomous code repair.

После AUTO-001 MVP продуктовая работа возвращается к PLAN-001. AUTO-002+ не являются блокерами.

## Следующая обязательная продуктовая работа

### PLAN-001 — ревизия фактической реализации

PR #7 остаётся Draft и перед продолжением должен быть синхронизирован с accepted main без потери instrumentation.

Цель: установить, что сделано, не сделано, сделано частично или иначе, чем планировалось.

Обязательная матрица:

| Область | Проверяется |
|---|---|
| Требования | исходный master plan и предметные решения |
| Данные | models, migrations, fixtures and importers |
| Backend | services, constraints, transitions and audit |
| UI | реальные пользовательские маршруты |
| Тесты | unit, integration, gates and CI |
| Demo | presentation data and end-to-end scenarios |
| Приёмка | подтверждённые видео/логи и open defects |

PLAN-001 обязан определить:

- master plan v3.0;
- ближайший journal vertical slice;
- реалистичную последовательность product work;
- updated acceptance criteria;
- минимальный smoke/integration suite поверх full `497/497` baseline;
- technical debt, который реально блокирует продукт.

## Параллельная UX-фаза

### UX-001 — UI design system and interaction contract

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Следующий visual gate:

```text
два compact visual directions
для application shell + одного structured-journal screen
→ user decision
→ limited runtime prototype
→ visual correction and acceptance
→ accepted tokens
```

До этого concrete palette, typography, density, radii, shadows, shell composition и reference-screen appearance не являются стандартом.

UX-001 не блокирует PLAN-001. UI/UX проверяется на выбранном real journal slice и operational journal.

## Принцип product queue после PLAN-001

```text
минимальный общий контракт
→ один журнал полностью
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Минимальные связи с operational journal, equipment, participants and basis появляются в каждом vertical slice. Full cross-document timeline не проектируется заранее.

## Предварительные product phases

Порядок ниже остаётся гипотезой до PLAN-001.

### PRODUCT-A1 — Defect journal vertical slice

Предварительный кандидат:

- source-bound defect form;
- equipment;
- initiator and responsible person;
- statuses and history;
- link to operational record;
- presentation data;
- automated gates;
- user acceptance.

UX-001 может использовать defect family как reference contract, но это не окончательный выбор.

### PRODUCT-A2 — Application journal vertical slice

- application and basis;
- equipment, dates and participants;
- minimal statuses;
- link to defect and operational journal;
- acceptance scenario.

### PRODUCT-A3 — Disposition journal vertical slice

- disposition;
- issuer/recipient/content;
- minimal transitions;
- link `application → disposition`;
- link to operational journal;
- acceptance scenario.

### PRODUCT-A4+ — Remaining structured journals

Очередность уточняет PLAN-001:

- equipment commissioning;
- relay protection and telemechanics;
- work permit journal;
- disposition-work journal;
- other source-bound journals.

Keys journal does not enter mandatory electronic lifecycle. Primary mode remains paper-first.

### PRODUCT-B — Work permit and switching minimum slice

- basic work permit/disposition register;
- participants and roles;
- work, place, equipment and safety measures;
- minimal statuses/transitions;
- paper/hybrid/electronic original mode;
- minimal switching document register;
- links to applications, dispositions and operational journal.

### PRODUCT-C — Operational journal assistance and stabilization

- templates and parameters;
- abbreviation dictionary;
- equipment/personnel/document suggestions;
- keyboard workflow;
- editor and semantic-link stability;
- marker duplication repair;
- stable focus/overlay/drawer geometry.

Blocking editor repairs are not deferred automatically until full redesign.

### RELEASE-A — Internal prototype

- 6–8 end-to-end scenarios;
- presentation reset;
- regression checklist;
- blocking defects removed;
- route from shift start to shift handover;
- paper-first keys limitations shown honestly.

### PRODUCT-D — Cross-document lifecycle

- application → disposition → work;
- defect → equipment → work;
- work permit → admissions → completion → closure;
- switching → application → disposition → operational record;
- unified timeline after evidence exists.

### PRODUCT-E — Electronic work permit lifecycle

Only after normative research:

- target briefings;
- primary/daily admission;
- crew changes;
- workplace transfers;
- suspension/resumption;
- completion/closure;
- signatures and action evidence;
- storage/archive.

### RELEASE-B — Full demonstration

- roles and permissions;
- full audit;
- print/export;
- user/admin guidance;
- test program and methodology;
- final functional acceptance.

## Automation after MVP

Only by confirmed need:

- AUTO-002 change classification after several real product PRs;
- AUTO-003 structured evidence;
- AUTO-004 Playwright browser acceptance;
- visual regression after accepted design tokens;
- automatic development DB reset;
- trusted preview deployment.

AUTO-002 is not started automatically after AUTO-001. Readiness is assessed after approximately 3–5 real product PRs through the MVP.

## Дальняя очередь

Only after separate enterprise decision:

- AD/LDAP;
- HR/EDMS integrations;
- legally significant electronic signature;
- cryptoprovider/certificates;
- read-only SCADA/CIM integrations;
- mobile offline mode;
- high availability and industrial commissioning;
- cancellation of paper duplication.

## Правила изменения roadmap

- новый этап не добавляется только потому, что звучит полезно;
- direction change записывается в `DECISION_LOG.md`;
- status `готово` требует Definition of Done and acceptance evidence;
- provisional UX contract не считается visual acceptance;
- partially implemented feature не считается завершённым этапом;
- infrastructure scope не расширяется без доказанной необходимости;
- merge выполняется только по явной команде пользователя.
