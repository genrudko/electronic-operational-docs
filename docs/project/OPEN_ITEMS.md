# ЭОД — открытые вопросы и отложенные задачи

**Актуализировано:** 28.07.2026

## 1. Фактическое состояние

```text
accepted product work item:
DEFECT-001 / PR #16 / MERGED / ACCEPTED

accepted product merge:
883a108c8be2a8cd075846fdd175916917911ef6

completed infrastructure work item:
DEV-FAST-001 / issue #18 / COMPLETED

current documentation main at update:
44917d56ce60a682bfffacffa8ec5bed8fba625d

open PR:
NONE

preview:
UNTOUCHED
```

Предметная и функциональная приёмка журнала дефектов выполнена. Его legacy-визуальный стиль не считается принятым целевым UX/UI.

---

## 2. Next item — UX-FOUNDATION-001

Статус:

```text
issue: NOT CREATED
branch: NOT CREATED
Draft PR: NONE
implementation: NOT STARTED
```

Implementation должен выполняться в отдельном чате по:

```text
docs/project/UX_FOUNDATION_001_NEW_CHAT_STARTER.md
```

Утверждённое визуальное направление:

```text
Direction A — спокойное светлое документно-операционное
```

Цель — минимальный общий UI-layer на основе принятого журнала дефектов:

- application shell;
- compact navigation and page header;
- registry/table patterns;
- mobile list/card patterns;
- search, filters and sorting;
- cards and forms;
- date/time controls;
- statuses and action hierarchy;
- validation/notifications;
- typography, spacing, density and CSS tokens.

Обязательные пользовательские замечания:

1. центрировать заголовки таблицы;
2. уменьшить шапку и служебные блоки;
3. сделать карточки менее техническими;
4. добавить сквозную пользовательскую нумерацию строк;
5. сделать связь с оперативной записью понятной оператору;
6. добавить нормальные сортировку, поиск и фильтры;
7. переработать date/time controls;
8. сделать статусы визуально явными;
9. обеспечить полноценную мобильную читаемость.

Границы:

- не менять модели, migrations, services, lifecycle или evidence только ради визуального слоя;
- сохранять одну ветку и один Draft PR на весь цикл замечаний;
- использовать DEV-FAST-001 для промежуточных template/static repairs;
- выполнить один полный final gate перед merge;
- не использовать preview;
- не выполнять automatic merge.

---

## 3. DEV-FAST-001 — closed

```text
issue #18:
CLOSED / COMPLETED

PR #19:
MERGED

repair PR #21:
MERGED

canary PR #20:
CLOSED / NOT MERGED
```

Hot refresh доступен только для added/modified regular `100644` files:

```text
src/templates/**
src/static/**
```

Запрещены deletions, renames, copies, type changes, symlinks, executable blobs, models, migrations, settings, urls, services, dependencies, Dockerfile, Compose, database operations, presentation reset, preview и automatic merge.

При сетевом SSH timeout повторяется только упавший job после подтверждения точной причины; такой timeout не считается дефектом controller.

---

## 4. Следующие structured journals

Очередность после UX-FOUNDATION-001:

1. PRODUCT-D2 — Журнал заявок.
2. PRODUCT-D3 — Журнал распоряжений.
3. Ввод оборудования в работу.
4. РЗА и телемеханика.
5. Журналы работ — после нормативного решения.

Каждый журнал требует source traceability, специализированных правил, dedicated UI, связей, presentation data, automated gates и user acceptance. Generic registry сам по себе не считается законченным журналом.

---

## 5. Operational Journal

Blocking lifecycle gaps:

- draft → immutable registered entry;
- handover preparation;
- сдача/приёмка смены;
- close shift;
- unfinished draft checks;
- signatures/action evidence.

Editor/stability backlog:

- caret at end;
- Ctrl+Left/Right/Home/End within entry;
- PgUp/PgDown without page scroll;
- editable semantic links;
- no duplicated marker on copy/paste;
- no page jump outside sheet;
- templates, abbreviations and suggestions.

---

## 6. Data

Остаётся открытым:

- публикация accepted canonical power-system dataset;
- разделение staging/import и canonical publication;
- personnel rights and qualifications;
- personnel/workplace source publications;
- unified deterministic presentation reset beyond defect journal;
- managed RU→EN domain lexicon;
- сохранение общей ЩПТ/ШОТ technical equipment family.

---

## 7. Work permits and orders

Открытые нормативные и продуктовые вопросы:

- original mode;
- отдельные журналы работ;
- целевые инструктажи;
- первичный/ежедневный допуск;
- изменения состава бригады;
- переводы на другое рабочее место;
- приостановка/возобновление;
- завершение/закрытие/хранение;
- signatures/action evidence;
- перечни эксплуатационных работ.

---

## 8. Switching

Минимальный контур:

- registry/card;
- types/statuses;
- equipment;
- application/disposition basis;
- executor/controller;
- dates/file;
- operational-log link;
- manual operation sequence.

Automatic generation, topology и interlocks остаются позже.

---

## 9. Keys journal

Paper-first boundary:

- бумажный журнал остаётся рабочим оригиналом;
- полный электронный issue/return lifecycle не является обязательным для первого прототипа;
- optional reference/control contour требует отдельного решения.

---

## 10. Deferred quality/deployment work

### CI-OPT-001

После стабилизации UX-FOUNDATION-001:

- один полный PostgreSQL suite на final exact head;
- отсутствие повторного полного suite на VPS deployment;
- migration/runtime/presentation smoke при deployment;
- path-based gates без ослабления required checks;
- optional nightly full suite.

### DATA-DEPLOY-001

Убрать безусловную presentation seed-логику из `post_migrate`:

```text
migrate
→ explicit presentation seed
→ explicit seed result
→ runtime smoke
```

---

## 11. Непереговорные границы

- GitHub — единственный источник кода и canonical docs;
- VPS — runtime/test contour, а не источник кода;
- preview не используется для разработки;
- automatic merge запрещён;
- пользователь не выполняет штатные VPS-команды для функциональных PR;
- микро-repair получают focused checks и trusted hot refresh;
- полный gate выполняется один раз на final exact head;
- контекст обновляется после merge, смены приоритета, появления нового active PR и перед handoff.
