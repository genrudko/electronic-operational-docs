# ЭОД — roadmap

**Актуализировано:** 28.07.2026

## Принцип

Roadmap управляется фактическим состоянием GitHub, runtime evidence и пользовательской приёмкой. Наличие кода или green CI само по себе не завершает продуктовый этап. Для значимого work item сохраняются exact head, профильные проверки, финальный gate, runtime evidence, пользовательское решение и отдельная команда на merge.

При этом действует принцип минимально достаточного решения: промежуточные микро-repair не должны автоматически запускать полный PostgreSQL suite, пять workflow и полноценный deployment. Полный gate выполняется один раз на окончательном head перед merge.

## Current baseline

```text
repository:
genrudko/electronic-operational-docs

accepted main merge commit:
883a108c8be2a8cd075846fdd175916917911ef6

accepted application baseline:
937d2cd2b187c17fac3088ccfc52079fc4608306

last accepted product work item:
DEFECT-001 / PR #16 / MERGED / ACCEPTED

next work item:
DEV-FAST-001 / issue #18 / NOT STARTED
```

## Завершено

| Этап | Статус | Основной результат |
|---|---|---|
| INFRA-001–003 | Accepted | Linux/PostgreSQL CI, preview, isolated development |
| DOCS-001–003 | Accepted | Canonical docs and provisional UX contract |
| QUALITY-001 | Accepted | Full `python manage.py test apps` discovery |
| AUTO-000 | Accepted | Automation/security/acceptance contract |
| AUTO-001A | Accepted | Trusted controller foundation |
| AUTO-001B | Accepted | Restricted exact-SHA VPS development controller |
| PLAN-001 / PR #7 | Accepted and merged | Evidence audit, classifier repair and first slice decision |
| DEFECT-001 / PR #16 | Accepted and merged | Source-bound equipment defect journal vertical slice |

## DEFECT-001 — accepted reference slice

```text
source head:
79f3db7e5c47e1ac8ab2568028d06e4043c2c70e

merge commit:
883a108c8be2a8cd075846fdd175916917911ef6

five exact-head workflows:
GREEN

full PostgreSQL/Django suite:
SUCCESS

trusted development deployment:
SUCCESS

user acceptance:
CONFIRMED

preview:
UNTOUCHED
```

Реализовано и принято:

- exact published type `journal-equipment-defects`;
- source trace к И-00-007-ОР-2025, версия 2, раздел 11, приложение 8;
- шесть утверждённых граф в рабочем и печатном представлении;
- dedicated registry, card and action routes;
- обязательная связь с оборудованием и snapshot диспетчерского наименования;
- роли участников и lifecycle `REGISTERED → IN_PROGRESS → RESOLVED → CLOSED`;
- versioned продление срока и immutable action evidence;
- explicit immutable link с зарегистрированной записью оперативного журнала;
- минимальный non-cloning contract томов;
- deterministic presentation dataset;
- desktop/mobile presentation;
- финальный row-click repair с сохранением обычного поведения интерактивных элементов и выделения текста.

Текущий визуальный стиль остаётся legacy-интерфейсом и не является принятым целевым UX/UI.

## Следующий work item: DEV-FAST-001

Issue: `#18 — Trusted hot refresh from PR comment`.

Цель:

```text
чат создаёт микро-repair в активном PR
→ выполняет профильные проверки
→ публикует /eod-hot-refresh <exact-head-sha>
→ restricted workflow проверяет actor / PR / SHA / paths
→ обновляет только разрешённые presentation files в development
→ restart / collectstatic / health-check
→ пользователь сразу получает адрес проверки
```

Первая версия допускает только:

```text
src/templates/**
src/static/**
```

Запрещены модели, миграции, settings, services, dependencies, Compose, controller-controlled product deployment, database operations и preview.

DEV-FAST-001 затрагивает trusted security boundary, поэтому выполняется в одном отдельном PR. После однократной полной проверки механизм используется для быстрых промежуточных UX/UI repairs без полного suite на каждый commit.

## После DEV-FAST-001: UX/UI foundation

Не косметическая полировка всего приложения, а общий рабочий слой компонентов:

- application shell и навигация;
- desktop/mobile registry patterns;
- таблицы, сортировка, поиск и фильтры;
- карточки записей;
- формы и date/time controls;
- statuses и action hierarchy;
- validation/notification patterns;
- typography, spacing, density и CSS tokens.

Журнал дефектов используется как первый reference screen. Следующие журналы должны переиспользовать общие компоненты, а не копировать legacy UI.

## Следующие product vertical slices

После DEV-FAST-001 и минимального UX/UI foundation:

1. PRODUCT-D2 — Журнал заявок.
2. PRODUCT-D3 — Журнал распоряжений.
3. Operational Journal lifecycle: handover, shift close, action evidence и editor stabilization.
4. PRODUCT-D4 — ввод оборудования в работу.
5. PRODUCT-D5 — РЗА и телемеханика.
6. Журналы работ — после нормативного решения.

Каждый slice повторяет source-bound pattern: источник, специализированные правила, dedicated UI, связи, presentation data, automated gates, exact-SHA runtime и пользовательская приёмка.

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

## Правила изменения roadmap

- GitHub является источником фактического кода и PR-state;
- VPS используется только для runtime/test evidence;
- один work item может продолжаться в нескольких implementation chats, но сохраняет одну ветку и один PR;
- автоматический merge запрещён;
- merge требует отдельной явной команды пользователя;
- preview не используется для разработки;
- пользователь не выполняет штатные VPS-команды для функциональных PR;
- контекст обновляется после каждого merge, смены приоритета, появления нового active PR и перед завершением основного интеграционного чата.
