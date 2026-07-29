# ЭОД — открытые вопросы и отложенные задачи

**Актуализировано:** 29.07.2026

## 1. Фактическое состояние

```text
accepted UX work item:
UX-FOUNDATION-001 / issue #22 / PR #23 / MERGED / ACCEPTED

accepted UX source head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89

accepted main merge:
a880a632b750309c7fbfb918af15b49d99b5a93f

accepted product vertical slice:
DEFECT-001 / PR #16 / MERGED / ACCEPTED

completed infrastructure work item:
DEV-FAST-001 / issue #18 / COMPLETED

open PR:
NONE

preview:
UNTOUCHED
```

UX-FOUNDATION-001 принят на mobile и desktop. Direction A, hierarchy selectors, first-party pickers, responsive registry/cards, status chips и lifecycle presentation считаются reusable baseline.

---

## 2. Next planned item — OPJ-UX-001

Рабочее название:

```text
OPJ-UX-001 — Direction A operational journal workspace
```

Статус:

```text
issue: NOT CREATED
branch: NOT CREATED
Draft PR: NONE
implementation: NOT STARTED
```

Starter:

```text
docs/project/OPJ_UX_001_NEW_CHAT_STARTER.md
```

Первый implementation result должен установить фактическое состояние operational journal и разделить:

- presentation-only changes;
- editor interaction/stability repairs;
- lifecycle/domain gaps;
- reusable components;
- work, который нельзя безопасно включать в первый UX slice.

До factual audit не создавать branch или Draft PR.

### UX scope

- Direction A shell and navigation;
- compact shift/journal context;
- chronological registered-entry workspace;
- active entry editor;
- templates, abbreviations and suggestions;
- semantic equipment/personnel/document links;
- accepted hierarchy selectors where applicable;
- accepted date/time picker where applicable;
- responsive mobile representation;
- keyboard-first work.

### Existing operational journal gaps

Lifecycle:

- draft → immutable registered entry;
- handover preparation;
- сдача/приёмка смены;
- close shift;
- unfinished draft checks;
- signatures/action evidence.

Editor/stability:

- caret at end;
- Ctrl+Left/Right/Home/End within current entry;
- PgUp/PgDown without page scroll;
- editable semantic links;
- no duplicated marker on copy/paste;
- no page jump outside sheet;
- templates, abbreviations and suggestions.

Первый UX work item не должен молча объявлять эти lifecycle gaps решёнными.

---

## 3. UX foundation follow-ups

Выносить selectors, pickers и shell в общий reusable layer следует при появлении второго реального потребителя, а не отдельным абстрактным refactor без использования.

При OPJ-UX-001 проверить:

- какие части текущего equipment-defect shell уже безопасно переиспользуются;
- какие CSS/JS файлы являются фактическим reusable baseline;
- требуется ли минимальная консолидация Repair-файлов;
- не ломает ли консолидация accepted reference screen.

Не проводить массовый cleanup только ради красивой структуры файлов.

---

## 4. Следующие structured journals

Очередность после OPJ-UX-001:

1. PRODUCT-D2 — Журнал заявок.
2. PRODUCT-D3 — Журнал распоряжений.
3. Ввод оборудования в работу.
4. РЗА и телемеханика.
5. Журналы работ — после нормативного решения.

Каждый журнал требует source traceability, специализированных правил, dedicated UI, связей, presentation data, automated gates and user acceptance. Generic registry сам по себе не считается законченным журналом.

---

## 5. DEV-FAST-001 — closed

```text
#18 — DEV-FAST-001: Trusted hot refresh from PR comment
CLOSED / COMPLETED
```

Hot refresh доступен только для added/modified regular `100644` files:

```text
src/templates/**
src/static/**
```

Запрещены deletions, renames, copies, type changes, symlinks, executable blobs, models, migrations, settings, urls, services, dependencies, Dockerfile, Compose, database operations, presentation reset, preview и automatic merge.

При сетевом SSH timeout повторяется только упавший job после подтверждения точной причины; такой timeout не считается дефектом controller.

---

## 6. Hosting migration

Текущий development VPS повторно демонстрирует длительные сетевые простои и блокирует пользовательскую приёмку.

После окончания оплаченного периода требуется отдельный migration work item:

```text
HOST-MOVE-001 — migrate isolated development runtime to a new provider
```

До начала:

- выбрать provider и конфигурацию;
- проверить доступность IPv4, SSH, snapshots/backups и допустимость GitHub Actions access;
- не смешивать migration с активным product acceptance;
- сохранить старый VPS как rollback на ограниченный переходный период;
- не переносить preview без отдельного решения.

Provider пока не выбран.

---

## 7. Data

Остаётся открытым:

- публикация accepted canonical power-system dataset;
- разделение staging/import и canonical publication;
- personnel rights and qualifications;
- personnel/workplace source publications;
- unified deterministic presentation reset beyond defect journal;
- managed RU→EN domain lexicon;
- сохранение общей ЩПТ/ШОТ technical equipment family.

---

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

---

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

Automatic generation, topology and interlocks остаются позже.

---

## 10. Keys journal

Paper-first boundary:

- бумажный журнал остаётся рабочим оригиналом;
- полный электронный issue/return lifecycle не является обязательным для первого прототипа;
- optional reference/control contour требует отдельного решения.

---

## 11. Deferred quality/deployment work

### CI-OPT-001

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

## 12. Непереговорные границы

- GitHub — единственный источник кода и canonical docs;
- VPS — runtime/test contour, а не источник кода;
- preview не используется для разработки;
- automatic merge запрещён;
- пользователь не выполняет штатные VPS-команды для функциональных PR;
- микро-repair получают focused checks and trusted hot refresh;
- полный gate выполняется один раз на final exact head;
- контекст обновляется после merge, смены приоритета, появления нового active PR и перед handoff.
