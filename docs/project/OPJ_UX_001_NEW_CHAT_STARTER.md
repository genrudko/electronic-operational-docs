# OPJ-UX-001 — NEW CHAT STARTER

## Цель

Привести существующий оперативный журнал к принятому визуальному и interaction-направлению:

```text
Direction A — спокойное светлое документно-операционное
```

Оперативный журнал остаётся специализированным модулем. Его нельзя механически заменить generic registry или скопировать разметку журнала дефектов.

Это отдельный implementation work item. Финальная пользовательская приёмка и разрешение на merge выполняются в Chat 0.

---

## Источник истины

GitHub — единственный источник кода и canonical documentation. VPS используется только для runtime/test evidence.

На старте проверить фактически:

- current `main`;
- `AGENTS.md`;
- `docs/project/CURRENT_HANDOFF.md`;
- `docs/project/ROADMAP.md`;
- `docs/project/OPEN_ITEMS.md`;
- accepted UX merge `a880a632b750309c7fbfb918af15b49d99b5a93f`;
- accepted UX source head `688ca4ed3f306bcb6e32d145c0da6f32d5f37c89`;
- отсутствие открытого competing product PR.

Не использовать локальный репозиторий пользователя как источник истины.

---

## До implementation

Сначала изучить фактические:

- operational journal models;
- services and registration boundaries;
- routes and views;
- templates and template composition;
- static CSS/JS;
- editor behavior;
- template/abbreviation/suggestion implementation;
- equipment/personnel/document linking;
- shift and handover implementation;
- presentation data;
- tests and current known gaps.

Не полагаться только на старые handoff или roadmap descriptions.

До завершения factual implementation check:

- не создавать branch;
- не создавать issue;
- не создавать Draft PR;
- не менять VPS;
- не выполнять deployment;
- не расширять lifecycle на основе предположений.

---

## Первый ответ

Первый результат должен содержать только:

```text
FACT
IMPLEMENTATION CONTRACT
FIRST DELIVERY SLICE
OPEN DECISIONS
READY TO IMPLEMENT
```

Либо:

```text
BLOCKED — IMPLEMENTATION MUST NOT START
```

Не проводить повторный большой аудит DEFECT-001, DEV-FAST-001 или UX-FOUNDATION-001. Проверять их только там, где требуется фактическое переиспользование компонентов.

---

## Принятый reusable baseline

Из UX-FOUNDATION-001 разрешено переиспользовать после фактической проверки:

- Direction A shell;
- sidebar navigation and topbar;
- typography, spacing, density and CSS tokens;
- buttons, alerts and action hierarchy;
- equipment hierarchy selector;
- personnel hierarchy selector;
- workplace hierarchy selector;
- first-party light date picker;
- first-party light time picker;
- responsive mobile patterns;
- status chip language where semantics совпадают.

Не проводить абстрактный mass-refactor только ради выделения компонентов. Reusable extraction выполняется минимально и только при втором реальном потребителе.

---

## Специализированный operational journal scope

Рабочая область должна учитывать:

```text
контекст смены и состояние журнала
→ последовательная лента зарегистрированных записей
→ активный редактор новой записи
→ templates / abbreviations / suggestions
→ semantic equipment, personnel and document links
→ незавершённые дела
→ подготовка и передача смены
```

Оперативный журнал не должен становиться таблицей дефектов.

### Editor and keyboard expectations

Проверить и при необходимости включить в первый delivery slice:

- caret остаётся в ожидаемой позиции, обычно в конце активной записи;
- Ctrl+Left/Right/Home/End работают внутри текущей записи;
- PgUp/PgDown не прокручивают всю страницу неожиданно;
- semantic links редактируемы;
- copy/paste не создаёт duplicated marker;
- blank click не вызывает page jump;
- templates, abbreviations and suggestions не мешают ручному вводу;
- equipment picker использует accepted hierarchy pattern, если это соответствует фактическому data contract.

---

## Lifecycle boundaries

Не считать реализованными без фактического доказательства:

- draft → immutable registered entry;
- handover preparation;
- сдача/приёмка смены;
- close shift;
- unfinished draft checks;
- signatures/action evidence.

Первый UX slice может визуализировать только существующее фактическое состояние. Domain/lifecycle changes должны быть явно отделены от presentation work и обоснованы блокирующим пользовательским сценарием.

---

## Work process after READY TO IMPLEMENT

После factual audit и подтверждения `READY TO IMPLEMENT`:

1. создать один issue;
2. создать одну branch;
3. создать один Draft PR;
4. сохранять этот PR на весь цикл замечаний;
5. использовать focused checks и DEV-FAST-001 для presentation-only repairs;
6. выполнять один full final gate на окончательном accepted head;
7. не использовать preview;
8. не выполнять automatic merge.

Пользователь выполняет предметную, функциональную и визуальную приёмку. Штатных VPS-команд для functional PR пользователь не выполняет.

---

## Current accepted baseline

```text
main merge:
a880a632b750309c7fbfb918af15b49d99b5a93f

UX-FOUNDATION-001 source head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89

UX-FOUNDATION-001:
issue #22 / PR #23 / MERGED / ACCEPTED

DEFECT-001:
PR #16 / MERGED / ACCEPTED

DEV-FAST-001:
issue #18 / COMPLETED

preview:
UNTOUCHED
```
