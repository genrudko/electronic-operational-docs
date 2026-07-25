# ЭОД — текущее состояние

**Дата проверки:** 25.07.2026

**Принятый application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

**Текущий Git HEAD main:** `4237aadc2cfdee518567024c2b45b653f49c16e7`

**Открытые рабочие ветки:**

- `plan/001-evidence-audit` — PR #7, Draft;
- `docs/004-auto-000-development-automation-contract` — текущий documentation-only AUTO-000.

## 1. Статус проекта

Проект является независимым демонстрационным прототипом электронной оперативной документации для энергетики. Инициатива не является официальным поручением работодателя. Производственные серверы, фактические оперативные записи и реальные персональные данные не используются.

GitHub является главным онлайн-источником истины. Рабочая модель — GitHub-first/VPS-first. Пользователь задаёт цель, проверяет предметную корректность и UX и единолично разрешает merge; программирование, commits, PR, CI/VPS analysis и repair выполняет AI-разработчик.

## 2. Baseline и main history

```text
accepted application baseline: e18872face7f27f489056b72fed31e5586121b0c
current main history HEAD: 4237aadc2cfdee518567024c2b45b653f49c16e7
current main addition: QUALITY-001
```

Accepted application baseline остаётся `e18872f…` до отдельной фиксации post-merge preview evidence для нового application commit.

## 3. Последнее принятое изменение

PR #8 `QUALITY-001: Repair PostgreSQL test execution` принят пользователем и squash-merged в:

```text
4237aadc2cfdee518567024c2b45b653f49c16e7
```

На exact PR head подтверждено:

- EOD CI — success;
- EOD Development Stack — success;
- EOD Documentation Contract — success;
- полный PostgreSQL suite: `497/497 OK`;
- database identity: `eod_development`;
- clean development worktree.

Исправлены test discovery, test environment, PostgreSQL row locks, staticfiles testing storage, thread-local DB connections и deterministic ZIP fixtures.

Долг `0 test(s)` закрыт. Штатный полный test command:

```text
python manage.py test apps --verbosity 2
```

`development_stack.sh test` вызывает этот label.

## 4. Инфраструктура

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
checkout: /srv/eod/development
branch: active non-main branch
compose project: eod-development
application: 127.0.0.1:8766
database/user: eod_development
secrets: /srv/eod/secrets/development.env
```

Контуры изолированы. PostgreSQL host ports не публикуются. VPS Git deploy key read-only.

## 5. Реализованные функциональные области

Подтверждены:

- Django foundation;
- организация, персонал, роли и замещения;
- document core, registration, versioning and audit;
- re-authentication, canonical snapshot and SHA-256 integrity;
- normative registry and organizational configuration revisions;
- equipment, dispatch names and authority/supervision;
- import equipment, personnel, rights and workplace documentation;
- operational journal and shift work в текущем объёме;
- common structured-document core;
- source-bound working forms;
- Linux/PostgreSQL CI;
- accepted preview and isolated development;
- canonical documentation and runbooks;
- полный обнаруживаемый PostgreSQL test suite.

Частично или требует приёмки:

- конкретные structured journals;
- cross-document links;
- lifecycle заявок, распоряжений, дефектов, нарядов и переключений;
- operational-journal assistance;
- print/export/archive;
- full role/state-transition demonstration;
- electronic reference/control contour журнала ключей.

Не подтверждено завершённым:

- полный Structured Journals Pack;
- полный work-permit lifecycle;
- полный switching contour;
- автоматическая генерация БП/ТБП/ТПП;
- legally significant electronic signature;
- industrial readiness.

## 6. Текущая фаза

Перед продолжением PLAN-001 выполняется короткий infrastructure sprint:

```text
AUTO-000 documentation contract
→ AUTO-001 MVP
→ return to PLAN-001
```

AUTO-000 документирует архитектуру, security model и acceptance. Он не меняет runtime или VPS.

AUTO-001 должен убрать ручной мост `PR → VPS development → logs`, но не реализует полный набор AUTO-002+ и не получает право merge.

## 7. PLAN-001

PR #7 остаётся открытым Draft и выполняет evidence audit:

```text
requirement
→ models/migrations
→ services/constraints
→ UI routes
→ tests/gates
→ presentation data
→ acceptance evidence
→ remaining deficit
```

После принятого AUTO-001 MVP PLAN-001 продолжается и определяет master plan v3.0 и первый journal vertical slice.

## 8. UX-001

UX-001 v0.3 остаётся provisional:

```text
visual acceptance: pending
implementation authorization: not granted
```

Следующий gate — два компактных visual directions, выбор пользователя и ограниченный runtime prototype. Массовое внедрение не разрешено.

## 9. Предметные инварианты

- UI только русский; internals — professional technical English.
- Operational journal остаётся специализированным.
- Structured forms только source-bound.
- Журналы развиваются последовательными vertical slices.
- Keys journal paper-first до отдельного решения.
- Управление и ведение раздельны.
- Информационное ведение — характеристика ведения.
- ЩПТ и ШОТ — одна equipment family с сохранением исходного обозначения.
- Electronic work permit не объявляется юридически допустимым без актуального исследования.
- Secrets и реальные данные не коммитятся.
