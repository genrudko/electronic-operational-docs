# ЭОД — master plan

**Версия:** post-PLAN-001 integration decision  
**Актуализировано:** 26.07.2026  
**Текущий main:** `37a2390a2a45e2abb73e60318d5429ed326efb53`

## 1. Цель

Создать независимый внутренний рабочий прототип электронной оперативной
документации, а затем функциональную демонстрационную версию. Система должна
показывать цельный рабочий процесс, а не набор несвязанных экранов.

Ориентиры исходного плана:

- внутренний рабочий прототип: 3–4 недели;
- функциональная демонстрационная версия: 1,5–2 месяца.

Сроки уточняются по фактическим product slices, а не по историческим номерам
патчей.

## 2. Архитектурная граница

### Оперативный журнал

Остаётся специализированным модулем. Ему нужны:

- последовательный свободный текст;
- shift workspace;
- стабильный editor;
- autosave/conflict handling;
- templates, abbreviations and suggestions;
- semantic links;
- draft → immutable registration;
- сдача/приёмка и закрытие смены.

### Остальные журналы

Строятся поверх `apps.operational_documents`:

- source-bound document type and published revision;
- fields;
- statuses/transitions;
- participants;
- equipment;
- documents and record relations;
- numbering;
- immutable revisions;
- audit;
- search/filter;
- presentation and acceptance.

Общее ядро не является пользовательским конструктором произвольных журналов.

## 3. PLAN-001 decision

Принятый evidence package:

```text
exact head:
fb313f270254720b0f7d7815fffc2cb05d577901

ZIP SHA-256:
58df47f83d1758d2e6aa8b32e1d5a70efb8c453454d8759e25d913e7f031619a
```

Ручное решение Чата 0:

- generic structured-journal core — **substantially implemented**;
- structured journals pack — **not complete**;
- operational journal — **advanced but lifecycle incomplete**;
- work permits/orders — **not implemented as vertical slice**;
- switching documents — **not implemented as vertical slice**;
- repeatable presentation dataset — **blocking gap**;
- первый structured-journal slice — **Defect Journal**.

## 4. Текущий gate

До продуктовой реализации завершить PR #7:

- explicit ownership map;
- three-state absence semantics;
- runtime data provenance split;
- source catalog/published type/records split;
- manual integration decision in report;
- canonical docs;
- regression tests;
- final exact-head CI/deployment/evidence.

PR #7 остаётся Draft и не merged до отдельного решения пользователя.

## 5. Первый product vertical slice

### Defect Journal Vertical Slice

В scope:

1. точная source-bound форма журнала дефектов;
2. published type revision;
3. предметные поля;
4. equipment mandatory link;
5. initiator/responsible participants;
6. create → update → resolve → close;
7. immutable revisions and audit;
8. terminal lock;
9. минимальная явная связь с operational-log entry;
10. deterministic presentation seed/reset;
11. search/filter/numbering/org isolation;
12. browser/runtime acceptance;
13. сквозной сценарий обнаружение → запись → дефект → устранение → закрытие.

Не входят:

- work permit lifecycle;
- switching automation;
- universal timeline;
- новая signature architecture;
- automatic БП/ТБП/ТПП generation;
- произвольный journal constructor;
- реальные production data.

## 6. Последовательность structured journals

```text
Defect Journal
→ Application Journal
→ Disposition Journal
→ Equipment Commissioning
→ RZA/Telemechanics
→ work journals after normative decision
```

Для каждого slice:

```text
source
→ schema/models
→ specialized rules
→ UI
→ equipment/participants/basis
→ audit/history
→ presentation data
→ tests/gates
→ user acceptance
```

Связи добавляются по мере реальных сценариев. Universal timeline не
проектируется заранее.

## 7. Оперативный журнал

Отдельный stabilization/lifecycle этап должен закрыть:

- draft finalization into immutable entries;
- shift handover preparation;
- сдача/приёмка смены;
- закрытие смены;
- проверки незавершённых draft entries;
- signatures/action evidence;
- editor keyboard/focus/link defects;
- templates and abbreviations.

Он не подменяет первый structured-journal slice.

## 8. Наряды и распоряжения

Только после актуального нормативно-практического решения:

- register;
- paper/hybrid/electronic original mode;
- target briefings;
- primary/daily admission;
- crew changes;
- transfers;
- suspension/resumption;
- completion/closure/storage;
- action evidence and signatures;
- separate work journals where required.

Нельзя объявлять full electronic lifecycle без нормативного основания.

## 9. Переключения

Минимальный поздний slice:

- registry and card;
- type/status/number;
- equipment;
- application/disposition basis;
- executor/controller;
- dates;
- attachment;
- operational-log link;
- manual operation sequence.

Automatic generation, topology and interlock engine — отдельная дальняя очередь.

## 10. Presentation and acceptance

Internal prototype требует:

- unified deterministic presentation reset;
- безопасные реалистичные справочники;
- 6–8 end-to-end scenarios;
- regression checklist;
- browser acceptance;
- documented limitations;
- no blocking defects.

Seed-команды без доказанного repeatable reset не считаются готовым dataset.

## 11. Инфраструктура

AUTO-001A/B считается достаточным фундаментом. Новая инфраструктурная работа
выполняется только при доказанной product-необходимости.

Непереговорно:

- GitHub source of truth;
- VPS runtime/test only;
- PostgreSQL;
- exact-SHA;
- preview isolation;
- fail-closed controller;
- automatic merge forbidden;
- merge only by explicit user command.

## 12. Дальняя очередь

Только после отдельного enterprise decision:

- AD/LDAP;
- HR/EDMS integrations;
- legally significant electronic signature;
- cryptoproviders/certificates;
- SCADA/CIM integrations;
- mobile offline;
- HA and industrial commissioning;
- cancellation of paper duplication.
