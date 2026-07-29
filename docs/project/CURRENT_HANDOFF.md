# CHAT 0 — CURRENT HANDOFF

**Проект:** Электронная оперативная документация (ЭОД)  
**Репозиторий:** `genrudko/electronic-operational-docs`  
**Дата handoff:** 29.07.2026  
**Назначение:** восстановление основного интеграционного контекста и передача следующего work item в отдельный implementation-чат.

---

## 1. Роли чатов

Основной интеграционный чат отвечает за архитектурные решения, baseline, accepted state, выбор work item, итоговую пользовательскую приёмку и отдельное разрешение на merge.

Implementation-чат отвечает за фактическую разработку одного work item, профильные проверки, быстрый development refresh и обработку пользовательских замечаний.

```text
work item = одна ветка + один PR
implementation chat = рабочая сессия
```

Merge выполняется только после отдельной явной команды пользователя.

---

## 2. Непереговорные правила

- GitHub — единственный источник кода и canonical documentation.
- VPS — runtime/test-контур, а не источник кода.
- Пользователь не редактирует код и не выполняет штатные VPS-команды для функциональных PR.
- Preview не используется для разработки и не изменяется без отдельного решения.
- Automatic merge запрещён.
- End-user UI — русский.
- Internals используют профессиональный technical English.
- Реальные персональные и производственные оперативные данные, а также enterprise secrets, в Git не помещаются.
- Проект является независимым прототипом, а не официальной системой работодателя.

### Минимально достаточное решение

Во время серии визуальных замечаний применяется цикл:

```text
micro-repair
→ focused/profile checks
→ trusted hot refresh
→ пользовательская проверка
```

Полный PostgreSQL suite, пять exact-head workflows и полноценный trusted deployment не запускаются после каждого малого изменения. Один полный final gate выполняется на окончательном head перед merge.

---

## 3. Фактический baseline

Текущий accepted `main`:

```text
a880a632b750309c7fbfb918af15b49d99b5a93f
Merge pull request #23 from genrudko/ux/ux-foundation-001
```

Последний accepted UX work item:

```text
UX-FOUNDATION-001 / issue #22 / PR #23 / MERGED / ACCEPTED
source head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89
merge commit:
a880a632b750309c7fbfb918af15b49d99b5a93f
```

Последний accepted product vertical slice:

```text
DEFECT-001 / PR #16 / MERGED / ACCEPTED
source head:
79f3db7e5c47e1ac8ab2568028d06e4043c2c70e
merge commit:
883a108c8be2a8cd075846fdd175916917911ef6
```

Accepted application baseline, используемый в проектной документации:

```text
937d2cd2b187c17fac3088ccfc52079fc4608306
```

На момент handoff открытых PR нет.

---

## 4. UX-FOUNDATION-001 — завершён и принят

```text
issue #22:
CLOSED / COMPLETED

PR #23:
CLOSED / MERGED

source branch:
ux/ux-foundation-001 / DELETED

accepted exact head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89

merge commit:
a880a632b750309c7fbfb918af15b49d99b5a93f
```

Принято на mobile и desktop:

- Direction A — спокойное светлое документно-операционное направление;
- светлая оболочка с левой навигацией и верхней служебной панелью;
- responsive registry и mobile defect cards;
- поисковые деревья оборудования, персонала и рабочих мест;
- собственные светлые date/time pickers плюс ручной ввод;
- persistent sorting и выбор режима реестра;
- статусные chips со светлым фоном, отдельной цветной точкой и normal-case текстом;
- отдельные палитры `REGISTERED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`;
- systematic lifecycle semantics для completed/current/future stages;
- contained mobile print preview при сохранении exact A4 landscape print contract.

Технический gate принятого head:

- пять exact-head workflows — SUCCESS;
- EOD CI — `557 / OK`;
- isolated container preview — SUCCESS;
- trusted exact-SHA development delivery — SUCCESS;
- preview — `UNTOUCHED`.

Предметные контракты DEFECT-001 не изменены: models, migrations, lifecycle services, permissions, routes, evidence, operational-log binding и печатная форма сохранены.

---

## 5. DEFECT-001 — reference product slice

Журнал дефектов остаётся первым accepted reference screen.

Реализовано и принято:

- source-bound форма по И-00-007-ОР-2025, версия 2, раздел 11, приложение 8;
- published type `journal-equipment-defects`;
- dedicated registry, card, actions and print;
- обязательная связь с оборудованием и snapshot диспетчерского наименования;
- lifecycle `REGISTERED → IN_PROGRESS → RESOLVED → CLOSED`;
- versioned продление срока;
- immutable action evidence;
- explicit immutable operational-log link;
- deterministic presentation dataset;
- desktop/mobile representation.

---

## 6. DEV-FAST-001 — завершён

```text
#18 — DEV-FAST-001: Trusted hot refresh from PR comment
CLOSED / COMPLETED
```

Основная реализация: PR #19 / merged.  
Container-copy repair: PR #21 / merged.  
Canary: PR #20 / closed without merge.

Разрешены только added/modified regular `100644` blobs:

```text
src/templates/**
src/static/**
```

Запрещены deletions, renames, symlinks, executable blobs, models, migrations, settings, urls, services, dependencies, Dockerfile, Compose, database operations, presentation reset, preview и automatic merge.

---

## 7. Development access

Host-local convenience commands:

```text
sudo dev-on
sudo dev-off
sudo dev-status
```

Development reference URL:

```text
http://5.181.177.72:8766/operations/defects/
```

Публичный HTTP на `8766` включается только на время проверки и не является production-доступом.

Текущий VPS периодически испытывает длительные сетевые простои. После окончания оплаченного периода запланирован переезд на другой hosting provider. До отдельного migration work item текущий сервер остаётся development runtime.

---

## 8. Следующий плановый work item — OPJ-UX-001

Рабочее название:

```text
OPJ-UX-001 — Direction A operational journal workspace
```

Статус:

```text
issue: NOT CREATED
branch: NOT CREATED
PR: NONE
implementation: NOT STARTED
```

Цель — привести существующий оперативный журнал к принятому Direction A, сохранив его специализированную предметную и редакторскую архитектуру.

Переиспользовать:

- application shell и navigation;
- typography, spacing, density and tokens;
- buttons, notifications and action hierarchy;
- date/time picker;
- equipment/personnel/workplace selectors;
- mobile responsive patterns.

Оставить специализированными:

- последовательную ленту зарегистрированных записей;
- рабочий редактор новой записи;
- шаблоны, сокращения и предложения;
- semantic links с оборудованием и документами;
- keyboard navigation;
- draft → immutable registered entry;
- незавершённые дела;
- подготовку и передачу смены;
- close shift и action evidence.

Первый implementation-чат обязан сначала проверить фактические models, services, routes, templates, static assets и tests оперативного журнала. До factual audit не создавать branch или Draft PR.

Starter:

```text
docs/project/OPJ_UX_001_NEW_CHAT_STARTER.md
```

---

## 9. После OPJ-UX-001

Плановая последовательность:

```text
PRODUCT-D2 — Журнал заявок
→ PRODUCT-D3 — Журнал распоряжений
→ другие source-bound journals
```

Оперативный журнал не превращается в generic registry. Следующие structured journals переиспользуют accepted UX foundation, но сохраняют собственные source-bound правила.

---

## 10. Контекст и merge

Canonical context обновляется после каждого merge, смены приоритета, создания нового active PR и перед передачей work item в новый чат.

Automatic merge отсутствует. Любой merge требует отдельной явной команды пользователя в Chat 0.
