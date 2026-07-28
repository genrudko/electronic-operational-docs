# ЭОД — roadmap

**Актуализировано:** 28.07.2026

## Принцип

Roadmap управляется фактическим состоянием GitHub, runtime evidence и пользовательской приёмкой. Наличие кода или green CI само по себе не завершает продуктовый этап.

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

current documentation main at roadmap update:
13cbfb1a03bd46046f3f33719e3998c93d47d56e

accepted runtime/application main before documentation handoff:
6959b9767ce411e74fc4788d5da8dac97f41018f

last accepted product work item:
DEFECT-001 / PR #16 / MERGED / ACCEPTED

completed infrastructure work item:
DEV-FAST-001 / issue #18 / COMPLETED

next work item:
UX-FOUNDATION-001 / NOT STARTED
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
| DEV-FAST-001 / PR #19 + repair PR #21 | Accepted and merged | Trusted presentation-only hot refresh |

---

## DEFECT-001 — reference product slice

```text
source head:
79f3db7e5c47e1ac8ab2568028d06e4043c2c70e

merge commit:
883a108c8be2a8cd075846fdd175916917911ef6

user acceptance:
CONFIRMED

preview:
UNTOUCHED
```

Журнал дефектов остаётся первым reference screen для общего UX/UI foundation. Предметная модель, lifecycle, evidence и связи считаются принятыми. Legacy-визуальный стиль не считается целевым.

---

## DEV-FAST-001 — completed

```text
issue #18:
CLOSED / COMPLETED

PR #19:
MERGED

repair PR #21:
MERGED

canary PR #20:
CLOSED / NOT MERGED

preview:
UNTOUCHED
```

Доказано:

- exact PR/SHA validation;
- presentation-only overlay для `src/templates/**` и `src/static/**`;
- app-only restart/health;
- rollback через clean app recreate;
- повторный exact run;
- отсутствие database operations и automatic merge.

Механизм применяется для быстрых промежуточных UX/UI repairs. Полный suite не является условием каждого hot refresh.

---

## Следующий work item: UX-FOUNDATION-001

Утверждённое визуальное направление:

```text
Direction A — спокойное светлое документно-операционное
```

Цель — создать минимальный переиспользуемый UI-layer на основе журнала дефектов:

- application shell и navigation;
- compact page header;
- desktop registry/table pattern;
- mobile list/card pattern;
- sorting, search and filters;
- record cards and forms;
- date/time controls;
- status/action hierarchy;
- validation/notifications;
- typography, spacing, density and CSS tokens.

Это не полная брендовая полировка приложения и не новый product vertical slice.

Implementation выполняется в отдельном чате по:

```text
docs/project/UX_FOUNDATION_001_NEW_CHAT_STARTER.md
```

Один work item сохраняет одну ветку и один Draft PR на весь цикл замечаний. Merge выполняется только после финальной приёмки и отдельной команды в Chat 0.

---

## Следующие product vertical slices

После UX-FOUNDATION-001:

1. PRODUCT-D2 — Журнал заявок.
2. PRODUCT-D3 — Журнал распоряжений.
3. Operational Journal lifecycle: handover, shift close, action evidence and editor stabilization.
4. PRODUCT-D4 — ввод оборудования в работу.
5. PRODUCT-D5 — РЗА и телемеханика.
6. Журналы работ — после нормативного решения.

Каждый следующий журнал переиспользует принятый UX foundation и повторяет source-bound pattern: источник, специализированные правила, dedicated UI, связи, presentation data, automated gates, runtime evidence и user acceptance.

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
- подписи и action evidence.

### Минимальный контур переключений

- реестр и карточка;
- оборудование и основание;
- участники и даты;
- файл/вложение;
- связь с оперативным журналом;
- ручная последовательность операций.

Автоматическая генерация БП/ТБП/ТПП, topology и interlocks остаются более поздними этапами.

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
- regression и user acceptance.

---

## Правила изменения roadmap

- GitHub является источником фактического кода и PR-state;
- VPS используется только для runtime/test evidence;
- preview не используется для разработки;
- automatic merge запрещён;
- пользователь не выполняет штатные VPS-команды для функциональных PR;
- микро-repair получают профильные проверки и быстрый refresh;
- полный gate выполняется один раз на final exact head;
- canonical context обновляется после merge, смены приоритета и создания нового active PR.
