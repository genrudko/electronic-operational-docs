# PROJECT-STATE-RECONCILIATION-001 — каноническое состояние и защита от drift

## Состояние

```text
work item: PROJECT-STATE-RECONCILIATION-001
issue: #50 / OPEN
branch: governance/project-state-reconciliation-001
PR: #51 / OPEN / DRAFT / NOT MERGED
accepted program baseline: 916a6d708ff4bd8433218068a204547b4a9abf84
coordination baseline main: 44193bac6ba23c9c7a9d9c9025dd0e26df5932aa
risk profile: DOCS / GOVERNANCE / DOCUMENTATION_AUTOMATION
runtime impact: NONE
preview: UNTOUCHED
user acceptance: ABSENT
merge authorization: ABSENT
```

## Цель

Восстановить согласованное каноническое состояние проекта после принятия
`PROJECT-SUSTAINABILITY-001` и сделать расхождение planning/state views
автоматически обнаруживаемым.

Это первый work item фазы 0 программы индустриализации и обязательная
зависимость gate `SAFE-CONTINUATION`.

## Подтверждённая проблема

Аудит `PROJECT-SUSTAINABILITY-001` установил, что фактическая история GitHub,
`DEMO_RELEASE_PLAN.yaml`, module/work-item views и отдельные history/compatibility
документы расходятся. Текущий Documentation Contract не доказывает полную
согласованность accepted state, dependencies и gate projections.

## Обязательный factual preflight

Перед изменениями проверить:

1. current `main` и историю merged PR;
2. open/closed issues и фактические accepted exact heads;
3. `AGENTS.md`;
4. `docs/INDEX.md`;
5. `docs/project/CURRENT_STATE.md`;
6. `docs/project/CURRENT_HANDOFF.md`;
7. `docs/project/DEMO_RELEASE_PLAN.yaml`;
8. `docs/project/INDUSTRIALIZATION_PROGRAM.yaml`;
9. `docs/project/INDUSTRIALIZATION_PROGRAM.md`;
10. `docs/product/MODULE_MAP.md`;
11. `docs/product/IMPLEMENTATION_SEQUENCE.md`;
12. `docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md`;
13. `docs/project/BASELINE_HISTORY.md`;
14. `docs/project/ACCEPTANCE_HISTORY.md`;
15. Documentation Contract workflow, scripts and tests.

GitHub state сильнее документации. Не исправлять статусы по памяти или только по
названиям исторических work items.

## Scope

### 1. Factual reconciliation

- построить factual ledger merged PR, closed issues, exact heads и merge commits;
- установить фактические accepted capabilities и незавершённые work items;
- отделить accepted application/product baselines от documentation coordination tips;
- зафиксировать `VERIFY`, когда evidence недостаточно.

### 2. Canonical ownership

- сохранить `CURRENT_STATE.md` единственным владельцем volatile state;
- сохранить `DEMO_RELEASE_PLAN.yaml` единственным machine-readable владельцем
  release/module/capability/work-item planning state;
- оставить `CURRENT_HANDOFF.md` навигатором без volatile values;
- не превращать compatibility pointers и history documents в конкурирующих
  владельцев статуса.

### 3. Plan and derived views

Без изменения принятого предметного Demo scope согласовать:

- `docs/project/DEMO_RELEASE_PLAN.yaml`;
- `docs/product/MODULE_MAP.md`;
- `docs/product/IMPLEMENTATION_SEQUENCE.md`;
- `docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md`;
- применимые compatibility pointers;
- baseline и acceptance history.

В частности корректно отразить принятые:

- `PERSONNEL-AUTHORITY-001`;
- `OPJ-LIFECYCLE-001`;
- `PROJECT-SUSTAINABILITY-001`.

### 4. Permanent documentation validation

Интегрировать постоянные проверки:

- work-item references существуют;
- dependencies ссылаются на существующие work items;
- последовательная фаза не зависит от более поздней фазы;
- gate work items существуют;
- прямые и транзитивные зависимости mandatory `PILOT-READY` core также входят в
  mandatory core;
- scope-dependent work item не становится скрытой зависимостью mandatory core;
- Markdown/YAML projections согласованы;
- accepted/module/work-item state не устарел относительно canonical ledger;
- volatile fact не имеет нескольких владельцев;
- derived views совпадают с machine-readable owner.

### 5. Negative fixtures

Проверки обязаны падать как минимум при:

- ссылке на отсутствующий work item;
- dependency outside mandatory core;
- hidden scope-dependent dependency;
- stale accepted state;
- duplicate owner volatile values;
- Markdown/YAML projection drift.

## Out of scope

- product code и пользовательское предметное поведение;
- models, migrations и data;
- runtime, VPS, deployment и Preview;
- module registry/activation implementation;
- UX foundation или общий UX refactor;
- `SHIFT-HANDOVER-001`;
- новые журналы и предметные модули;
- изменение утверждённых gate boundaries или состава программы без отдельного
  решения владельца продукта.

## Allowed boundary

Ожидаемый diff ограничен:

- canonical и derived project/product/process documentation;
- documentation validation scripts/tests/workflow только в объёме постоянного
  consistency gate;
- work-item evidence.

Любое изменение `src/`, migrations, product templates/static или runtime Compose
запрещено.

## Acceptance

- factual GitHub ledger воспроизводим;
- canonical owners не противоречат друг другу;
- release plan и обязательные derived views совпадают;
- accepted work items отражены корректно;
- permanent validator воспроизводит принятые one-off consistency rules;
- negative fixtures доказательно отклоняются;
- Documentation Contract и применимые exact-head workflows зелёные;
- no product/runtime/schema/data/Preview impact;
- PR остаётся Draft до отдельной пользовательской приёмки;
- merge выполняется только по отдельной явной команде пользователя.

## Stop condition

Остановиться после:

1. factual reconciliation;
2. синхронизации canonical owner и derived views;
3. интеграции permanent validator и negative fixtures;
4. прохождения профильных checks;
5. обновления PR body по exact head;
6. представления содержательного отчёта пользователю.

Не переводить PR в Ready for Review и не выполнять merge.
