# ЭОД — текущее состояние

**Дата проверки:** 25.07.2026

**Принятый application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

**Текущий Git HEAD main:** `a2d686b0061fac513c02540a2176850640496884`

**Активная рабочая ветка:** `docs/003-ux001-provisional-contract`

## 1. Статус проекта

Проект является независимым демонстрационным прототипом электронной оперативной документации для энергетики. Инициатива не является официальным поручением работодателя. Производственные серверы, фактические оперативные записи и реальные персональные данные в разработке не используются.

Базовый функциональный, инфраструктурный и процессный скелет проекта существует. DOCS-001 принят и сделал репозиторий главным онлайн-источником истины. DOCS-002 зафиксировал accepted application baseline и переход к PLAN-001. Основной фокус возвращается к продуктовой разработке; инфраструктурные расширения выполняются только по подтверждённой необходимости.

## 2. Принятый application baseline и main history

```text
application baseline branch: main
application baseline HEAD: e18872face7f27f489056b72fed31e5586121b0c
included: INFRA-001 + INFRA-002 + INFRA-003 + DOCS-001
current main history HEAD: a2d686b0061fac513c02540a2176850640496884
current main addition: DOCS-002 metadata follow-up
```

PR #4 `DOCS-001: Project operating system and canonical documentation` принят пользователем и squash-merged 25.07.2026.

Post-merge preview verification DOCS-001 подтвердил:

- `/srv/eod/repository` находится на точном merge commit;
- branch `main`, worktree clean;
- documentation contract: OK, 43 required files;
- preview app and database healthy;
- health endpoint: `{"status": "ok"}`;
- main page: HTTP 200;
- database identity: `eod_preview`;
- pending migrations отсутствуют.

PR #5 `DOCS-002: Finalize DOCS-001 accepted baseline` squash-merged в `a2d686b0061fac513c02540a2176850640496884`. Это documentation-only metadata follow-up: он не меняет application behavior, schema, migrations or runtime data и не создаёт новый application baseline. После merge preview синхронизирован, documentation contract прошёл, containers healthy, health endpoint OK и главная страница HTTP 200.

## 3. Инфраструктура

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

Оба контура изолированы. PostgreSQL host ports не публикуются. Доступ к приложениям выполняется через SSH tunnel.

## 4. Данные

Accepted preview содержит presentation profile:

- 8303 fixture objects;
- 84 Django models;
- две демонстрационные учётные записи;
- вымышленные персональные данные и безопасные презентационные справочники.

Development-база создаётся как отдельная копия accepted preview, после чего на неё применяются миграции активной ветки.

## 5. Реализованные функциональные области

### Подтверждено реализовано

- Django application foundation;
- организация, подразделения, должности, сотрудники, учётные записи, роли и замещения;
- документарное ядро: черновики, версии, регистрация, нумерация, связи и аудит;
- повторная аутентификация, канонический snapshot и SHA-256 integrity status;
- нормативный реестр и редакции организационной конфигурации;
- энергообъекты, оборудование, диспетчерские наименования и их история;
- диспетчерское и технологическое управление и ведение;
- импорт оборудования, персонала, оперативных прав и документации рабочего места;
- специализированный оперативный журнал и сменная работа в объёме текущего прототипа;
- общее ядро структурированных журналов;
- source-bound каталог рабочих форм;
- GitHub Actions CI на Linux/PostgreSQL;
- безопасный preview и изолированный development на VPS;
- канонический DOCS-контур, runbooks, acceptance documents и documentation CI gate.

### Реализовано частично или требует предметной приёмки

- формы конкретных структурированных журналов;
- связи между журналами и оперативным журналом;
- жизненные циклы заявок, распоряжений, дефектов, нарядов и переключений;
- шаблоны, сокращения и контекстная помощь оперативного журнала;
- печатные формы, экспорт и архивные представления;
- роли и переходы состояний полного демонстрационного контура;
- возможный электронный справочный/контрольный контур журнала ключей.

### Не подтверждено как завершённое

- полный Structured Journals Pack;
- полноценный реестр нарядов и распоряжений;
- полный lifecycle допуска и работ;
- полный контур документов переключений;
- автоматическая генерация БП/ТБП/ТПП;
- юридически значимая электронная подпись;
- промышленная эксплуатационная готовность.

Полный электронный lifecycle выдачи и возврата ключей не входит в обязательный внутренний прототип: основной режим журнала ключей считается paper-first до отдельного предметного и UX-решения.

## 6. Текущий процесс разработки

1. Ассистент создаёт complete change в отдельной GitHub branch.
2. GitHub Actions выполняет gates.
3. VPS development получает branch через `git pull --ff-only`.
4. Выполняются refresh/check/test/status.
5. Пользователь проводит предметную и визуальную приёмку.
6. Merge выполняется только после явного разрешения пользователя.
7. Preview синхронизируется с `main` и проходит post-merge gate.
8. Применимые canonical docs актуализируются вместе с изменением или обязательным metadata follow-up.

Пользователь исключён из механической части программирования, но сохраняет постановку задачи и приёмку.

## 7. Текущий обязательный продуктовый этап

`PLAN-001 — ревизия фактической реализации`.

Нужно доказательно сопоставить для каждого модуля:

```text
требование
→ models/migrations
→ services/constraints
→ UI routes
→ tests/gates
→ presentation data
→ acceptance evidence
→ remaining deficit
```

Результат:

- master plan v3.0;
- подтверждённый первый журнальный vertical slice;
- реалистичная последовательность следующих работ;
- минимальный обязательный smoke/integration test suite.

## 8. UX-001

`UX-001 v0.3` оформляется в отдельной ветке как **предварительный проектный контракт для визуального прототипирования**.

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Структурно пакет включает evidence-based audit, visual direction, principles, candidate tokens, component/interaction contracts, page archetypes, three reference-screen contracts and staged roadmap.

Сейчас не приняты визуально:

- concrete palette;
- typography scale;
- density;
- radii and shadows;
- shell composition;
- внешний вид reference screens.

Следующий UX gate: два компактных визуальных направления для application shell и одного показательного structured-journal screen → выбор пользователя → ограниченный runtime prototype → визуальная корректировка → фиксация accepted tokens.

Журнал дефектов остаётся сильным кандидатом на reference vertical slice, но окончательный выбор принимает PLAN-001.

## 9. Согласованное продуктовое направление

```text
минимальный общий контракт
→ один журнал полностью
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Связи не откладываются до завершения всего пакета. Полная универсальная timeline не проектируется заранее без подтверждённых отношений.

## 10. Критический технический долг

Текущая Django test command обнаруживает `0 test(s)`. Это не считается доказательством регрессионной защиты. PLAN-001 должен определить минимальный автоматический набор, а каждый следующий product slice обязан добавлять профильные tests/gates.
