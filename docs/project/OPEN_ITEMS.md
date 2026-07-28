# ЭОД — открытые вопросы и отложенные задачи

**Актуализировано:** 28.07.2026

## 1. Фактическое состояние после DEFECT-001

```text
accepted product work item:
DEFECT-001 / PR #16 / MERGED / ACCEPTED

source head:
79f3db7e5c47e1ac8ab2568028d06e4043c2c70e

merge commit:
883a108c8be2a8cd075846fdd175916917911ef6

open product PR:
NONE

preview:
UNTOUCHED
```

Предметная и функциональная приёмка журнала дефектов выполнена. Текущий legacy-визуальный стиль не считается принятым целевым UX/UI.

## 2. Следующий active item — DEV-FAST-001

```text
issue:
#18 — Trusted hot refresh from PR comment

status:
READY TO START / IMPLEMENTATION NOT STARTED
```

Цель — убрать повторяющееся ожидание полного CI/deployment при каждом малом presentation repair.

Требуемый контракт:

```text
profile repair
→ focused checks
→ /eod-hot-refresh <exact-head-sha>
→ actor / PR / exact SHA / path policy
→ restricted development-only overlay
→ collectstatic / restart / health
→ immediate user check
```

Разрешённые пути первой версии:

- `src/templates/**`;
- `src/static/**`.

Явно запрещены:

- models и migrations;
- settings, URLs, services и management commands;
- dependencies, Dockerfile и Compose;
- database operations и presentation reset;
- preview;
- automatic merge.

Открытые решения внутри DEV-FAST-001:

1. точный формат служебной PR-команды;
2. allowlist и проверка diff относительно deployed/base state;
3. backup/rollback presentation files;
4. state marker с overlay SHA;
5. безопасное возвращение к полноценному exact-SHA deployment;
6. профильные тесты workflow/controller boundary;
7. однократный final security/runtime gate перед merge.

## 3. ACCESS-001 / PR #17

ACCESS-001 создавался для публичного HTTPS-доступа к development через nginx/Certbot.

Фактическое решение пользовательской задачи было достигнуто более простым host-local механизмом включения/выключения доступа. Большой PR больше не является текущим приоритетом и не должен смешиваться с DEV-FAST-001.

Целевое состояние:

```text
PR #17:
CLOSED / NOT MERGED / SUPERSEDED

branch:
may remain for history

future HTTPS work:
only by separate explicit decision
```

## 4. UX/UI foundation

После DEV-FAST-001 требуется узкий общий UI-layer на основе принятого журнала дефектов:

- application shell;
- навигация;
- registry/table patterns;
- mobile list/card patterns;
- поиск, фильтры и сортировка;
- формы и date/time controls;
- статусы и action hierarchy;
- validation/notifications;
- typography, spacing, density и CSS tokens.

Цель — создать повторно используемые компоненты перед следующим журналом, а не проводить полную декоративную переработку всего приложения.

## 5. Следующие structured journals

Очередность:

1. Журнал заявок.
2. Журнал распоряжений.
3. Ввод оборудования в работу.
4. РЗА и телемеханика.
5. Журналы работ — после нормативного решения.

Каждый журнал требует source traceability, специализированных правил, dedicated UI, связей, presentation data, automated gates и user acceptance. Generic registry сам по себе не считается законченным журналом.

## 6. Operational Journal

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

## 7. Data

Остаётся открытым:

- публикация accepted canonical power-system dataset;
- разделение staging/import и canonical publication;
- personnel rights and qualifications;
- personnel/workplace source publications;
- unified deterministic presentation reset beyond defect journal;
- managed RU→EN domain lexicon;
- сохранение общей ЩПТ/ШОТ technical equipment family.

## 8. Work permits and orders

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

## 9. Switching

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

## 10. Keys journal

Paper-first boundary:

- бумажный журнал остаётся рабочим оригиналом;
- полный электронный issue/return lifecycle не является обязательным для первого прототипа;
- optional reference/control contour требует отдельного решения.

## 11. Quality and deployment follow-ups

### CI diagnostics — implemented

В `main` добавлено сохранение компактной диагностики Django failures и полного `django-test.log` в artifact. Это не заменяет точное расследование, но исключает зависимость от обрезанного connector log для будущих падений.

### CI-OPT-001 — deferred

После стабилизации DEV-FAST-001:

- один полный PostgreSQL suite на final exact head;
- отсутствие повторного полного suite на VPS deployment;
- migration/runtime/presentation smoke при deployment;
- path-based gates без ослабления required checks;
- optional nightly full suite.

### DATA-DEPLOY-001 — deferred

Убрать безусловную presentation seed-логику из `post_migrate`:

```text
migrate
→ explicit presentation seed
→ explicit seed result
→ runtime smoke
```

## 12. Непереговорные границы

- GitHub — единственный источник кода и canonical docs;
- VPS — runtime/test contour, а не источник кода;
- preview не используется для разработки;
- automatic merge запрещён;
- пользователь не выполняет штатные VPS-команды для функциональных PR;
- микро-repair получают профильные проверки и быстрый refresh;
- полный gate выполняется один раз на final exact head;
- контекст обновляется после merge, смены приоритета, появления нового active PR и перед handoff.
