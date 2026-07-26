# ЭОД — текущее состояние

**Дата проверки:** 26.07.2026

```text
accepted application baseline:
main / 937d2cd2b187c17fac3088ccfc52079fc4608306

current main history HEAD:
37a2390a2a45e2abb73e60318d5429ed326efb53

active branch:
plan/001-evidence-audit

active PR:
#7 / OPEN / DRAFT / NOT MERGED
```

## 1. Статус проекта

ЭОД — независимый демонстрационный прототип электронной оперативной
документации для энергетики. Он не является официальной системой работодателя.
Производственные серверы, реальные оперативные записи, реальные персональные
данные и secrets предприятия не используются.

GitHub является единственным источником кода и канонической документации. VPS
является единственным runtime/test-контуром. Accepted preview и active
development изолированы.

## 2. Принятые инфраструктурные этапы

Приняты и practically verified:

- INFRA-001–003;
- DOCS-001–003;
- QUALITY-001;
- AUTO-000;
- AUTO-001A trusted-controller foundation;
- AUTO-001B restricted VPS development controller;
- repair trusted request validator.

Текущий `main` — `37a2390a2a45e2abb73e60318d5429ed326efb53`.

Штатный AUTO-001B маршрут:

```text
trusted PR label
→ пять green exact-head workflows
→ trusted request validation from main
→ restricted forced SSH gateway
→ exact PR SHA fetch
→ exact-SHA image
→ isolated PostgreSQL checks and full tests
→ development backup/migrations/health
→ confirm or rollback
```

Automatic merge отсутствует. Preview не используется и не изменяется
controller’ом.

## 3. Runtime-контуры

### Accepted preview

```text
checkout: /srv/eod/repository
branch: main only
compose project: eod-preview
application: 127.0.0.1:8765
database: eod_preview
secrets: /srv/eod/secrets/preview.env
```

### Active development

```text
controller releases: /srv/eod/automation/releases/<exact-sha>
compose project: eod-development
application: 127.0.0.1:8766
database/user: eod_development
secrets: /srv/eod/secrets/development.env
controller: /usr/local/sbin/eod-development-controller
state: /srv/eod/automation/state
```

Development больше не зависит от PR-controlled Git checkout или запуска
PR-controlled host script от root.

## 4. PLAN-001 evidence

Первый evidence run принят постоянным интеграционным Чатом 0:

```text
evidence exact head:
fb313f270254720b0f7d7815fffc2cb05d577901

evidence package SHA-256:
58df47f83d1758d2e6aa8b32e1d5a70efb8c453454d8759e25d913e7f031619a

result:
ACCEPTED

executed Django tests:
502 / OK
```

Подтверждено:

- development PostgreSQL `eod_development`;
- exact release/image source parity;
- migration drift отсутствует;
- global executable gates passed;
- manifest и payload checksums корректны;
- preview остался healthy и untouched;
- transaction `NONE`, pending run ID `NONE`.

## 5. Решение интеграционного Чата 0

```text
generic structured-journal core:
SUBSTANTIALLY IMPLEMENTED

structured journals pack:
NOT COMPLETE

operational journal:
ADVANCED BUT LIFECYCLE INCOMPLETE

work permits/orders:
NOT IMPLEMENTED AS VERTICAL SLICE

switching documents:
NOT IMPLEMENTED AS VERTICAL SLICE

repeatable presentation dataset:
BLOCKING GAP

recommended first vertical slice:
DEFECT JOURNAL
```

Это ручное integration decision, а не machine verdict.

## 6. Фактическая функциональная готовность

### Существенно реализовано

- организация, сотрудники, должности, рабочие места и базовые роли;
- equipment/dispatching/import foundation;
- документационное ядро;
- документация рабочего места;
- specialized operational journal;
- generic `apps.operational_documents` core;
- source-bound catalog;
- immutable revisions, snapshots, audit and links;
- PostgreSQL CI/runtime foundation.

### Частично

- canonical equipment/personnel/workplace datasets;
- operational rights and qualifications;
- конкретные source-bound structured journals;
- связь structured record ↔ operational-log entry;
- operational-journal shift finalization/handover;
- print/export/archive;
- repeatable presentation reset.

### Не реализовано как vertical slice

- work permits/orders lifecycle;
- work-permit work journals;
- switching documents minimum contour;
- automatic БП/ТБП/ТПП generation;
- legally significant electronic signature.

Журнал ключей остаётся paper-first.

## 7. Текущая работа

PR #7 ещё не принят. Он выполняет узкий repair:

- explicit ownership map вместо broad keyword readiness;
- отдельные `absent`, `unknown`, `not applicable`;
- runtime data classes:
  `canonical`, `staging/import`, `presentation/demo`, `system/internal`;
- source catalog отдельно от installed/published type и records;
- manual Chat 0 decision в `REPORT.md`;
- canonical documentation sync;
- regression tests против false zero/false positive.

Product implementation Defect Journal до завершения этого gate не начинается.

## 8. Следующий gate PR #7

1. Новый exact head.
2. Пять green exact-head workflows.
3. Обычный AUTO-001B exact-SHA deployment.
4. Один последний evidence run.
5. Manifest и ZIP SHA-256.
6. Исправленная FACT MATRIX без известных false zero/false positive.
7. Development health, transaction `NONE`, pending `NONE`.
8. Preview health и `UNTOUCHED`.
9. Draft/not merged.
10. Отдельное решение пользователя о merge.

## 9. Непереговорные правила

- UI конечного пользователя только русский.
- Internals используют professional technical English.
- Оперативный журнал остаётся специализированным.
- Остальные журналы используют общее ядро и source-bound формы.
- Оператор не конструирует произвольные рабочие журналы.
- ЩПТ и ШОТ — одна technical equipment family с сохранением обозначения.
- Paper/hybrid/electronic modes не объявляются юридически эквивалентными без
  нормативного основания.
- Реальные данные и secrets не коммитятся.
- Merge выполняется только по явной команде пользователя.

## 10. Сохранённый source-bound контракт

В проекте действует **source-bound каталог рабочих форм**. PLAN-001 — ревизия
фактической реализации — подтвердила рабочий принцип: **один журнал полностью**
доводится до automated and user acceptance, затем начинается следующий.
