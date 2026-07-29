# ЭОД — roadmap

**Актуализировано:** 29.07.2026

## Принцип

Roadmap управляется фактическим состоянием GitHub, runtime evidence и пользовательской приёмкой. Наличие кода или green CI само по себе не завершает этап.

Для значимого work item сохраняются exact head, профильные проверки, final gate, runtime evidence, пользовательское решение и отдельная команда на merge.

Во время серии UX-замечаний действует короткий цикл:

```text
micro-repair
→ focused checks
→ trusted hot refresh
→ пользовательская проверка
```

Полный gate выполняется один раз на окончательном head перед merge.

---

## Current baseline

```text
repository:
genrudko/electronic-operational-docs

accepted main merge:
a880a632b750309c7fbfb918af15b49d99b5a93f

last accepted UX work item:
UX-FOUNDATION-001 / issue #22 / PR #23 / MERGED / ACCEPTED

accepted UX source head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89

last accepted product vertical slice:
DEFECT-001 / PR #16 / MERGED / ACCEPTED

completed infrastructure work item:
DEV-FAST-001 / issue #18 / COMPLETED

next planned work item:
OPJ-UX-001 / NOT STARTED
```

---

## Завершено

| Этап | Статус | Основной результат |
|---|---|---|
| INFRA-001–003 | Accepted | Linux/PostgreSQL CI, preview, isolated development |
| DOCS-001–003 | Accepted | Canonical docs and provisional UX contract |
| QUALITY-001 | Accepted | Full `python manage.py test apps` discovery |
| AUTO-000 | Accepted | Automation/security/acceptance contract |
| AUTO-001A | Accepted | Trusted controller foundation |
| AUTO-001B | Accepted | Restricted exact-SHA VPS development controller |
| PLAN-001 / PR #7 | Accepted and merged | Evidence audit and first slice decision |
| DEFECT-001 / PR #16 | Accepted and merged | Source-bound equipment defect journal |
| DEV-FAST-001 / PR #19 + PR #21 | Accepted and merged | Trusted presentation-only hot refresh |
| UX-FOUNDATION-001 / PR #23 | Accepted and merged | Direction A shell, responsive registry/cards, hierarchy selectors, first-party pickers and status/lifecycle patterns |

---

## UX-FOUNDATION-001 — accepted baseline

```text
issue #22:
CLOSED / COMPLETED

PR #23:
MERGED

source head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89

merge commit:
a880a632b750309c7fbfb918af15b49d99b5a93f

five exact-head workflows:
SUCCESS

EOD CI:
557 / OK

mobile and desktop acceptance:
CONFIRMED

preview:
UNTOUCHED
```

Принятый foundation:

- Direction A — спокойное светлое документно-операционное направление;
- reusable shell and navigation;
- desktop registry and mobile card patterns;
- searchable equipment/personnel/workplace trees;
- first-party light date/time pickers with manual input;
- persistent sorting and view mode;
- reusable status chips and lifecycle semantics;
- contained print preview without changing the A4 contract.

---

## Следующий work item: OPJ-UX-001

Рабочее название:

```text
OPJ-UX-001 — Direction A operational journal workspace
```

Цель — перевести существующий оперативный журнал на принятый UX foundation без механического превращения его в generic registry.

Переиспользовать:

- shell, navigation and page hierarchy;
- typography, density and CSS tokens;
- buttons, alerts and action hierarchy;
- hierarchy selectors;
- date/time picker;
- responsive patterns.

Специализированный scope:

- контекст смены и состояние журнала;
- последовательная лента зарегистрированных записей;
- рабочий редактор новой записи;
- templates, abbreviations and suggestions;
- semantic links;
- keyboard behavior;
- незавершённые дела;
- подготовка, сдача и приёмка смены;
- draft/registration boundaries and action evidence.

До branch/PR implementation-чат обязан проверить фактические models, services, routes, templates, static assets and tests.

Starter:

```text
docs/project/OPJ_UX_001_NEW_CHAT_STARTER.md
```

---

## Следующие product vertical slices

После OPJ-UX-001:

1. PRODUCT-D2 — Журнал заявок.
2. PRODUCT-D3 — Журнал распоряжений.
3. PRODUCT-D4 — ввод оборудования в работу.
4. PRODUCT-D5 — РЗА и телемеханика.
5. Журналы работ — после нормативного решения.

Каждый structured journal переиспользует accepted UX foundation и повторяет source-bound pattern: источник, специализированные правила, dedicated UI, связи, presentation data, automated gates, runtime evidence и user acceptance.

---

## Work permits and switching

### Наряды и распоряжения на работы

После нормативного исследования:

- реестр и карточка;
- целевые инструктажи;
- первичный и ежедневный допуск;
- изменения бригады и рабочего места;
- приостановка/возобновление;
- окончание/закрытие/хранение;
- paper/hybrid/electronic boundaries;
- signatures and action evidence.

### Минимальный контур переключений

- реестр и карточка;
- оборудование и основание;
- участники и даты;
- файл/вложение;
- связь с оперативным журналом;
- ручная последовательность операций.

Автоматическая генерация БП/ТБП/ТПП, topology и interlocks остаются более поздними этапами.

---

## Infrastructure follow-up

Текущий development VPS периодически испытывает длительные сетевые простои. После окончания оплаченного периода планируется отдельный migration work item на другого hosting provider. До этого VPS остаётся действующим runtime/test-контуром.

---

## Internal Prototype Release

Exit criteria:

- whole-system demonstration;
- 6–8 сквозных сценариев;
- deterministic presentation reset;
- accepted defect/application/disposition flows;
- operational journal lifecycle;
- basic permit/switching registries;
- честные paper-first ограничения;
- regression and user acceptance.

---

## Правила изменения roadmap

- GitHub является источником фактического кода и PR-state;
- VPS используется только для runtime/test evidence;
- preview не используется для разработки;
- automatic merge запрещён;
- пользователь не выполняет штатные VPS-команды для функциональных PR;
- микро-repair получают focused checks and trusted hot refresh;
- полный gate выполняется один раз на final exact head;
- canonical context обновляется после merge, смены приоритета и создания нового active PR.
