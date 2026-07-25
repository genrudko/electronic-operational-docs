# ЭОД — текущее состояние

**Дата проверки:** 25.07.2026

**Принятый application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

**Текущий Git HEAD main:** `4237aadc2cfdee518567024c2b45b653f49c16e7`

**Открытые рабочие ветки:**

- `plan/001-evidence-audit` — PR #7, Draft;
- `docs/004-auto-000-development-automation-contract` — текущий AUTO-000.

## 1. Статус проекта

Проект является независимым демонстрационным прототипом электронной оперативной документации для энергетики. Инициатива не является официальным поручением работодателя. Производственные серверы, фактические оперативные записи и реальные персональные данные в разработке не используются.

Базовый функциональный, инфраструктурный и процессный скелет проекта существует. DOCS-001 сделал репозиторий главным онлайн-источником истины. DOCS-002 зафиксировал accepted application baseline и переход к PLAN-001. DOCS-003 сохранил UX-001 v0.3 как provisional contract. QUALITY-001 восстановил фактическое выполнение полного PostgreSQL test suite.

Перед продолжением PLAN-001 выполняется короткий инфраструктурный спринт AUTO-000/AUTO-001, устраняющий ручной мост между green PR и VPS development. Полный набор последующей автоматизации не является блокером продуктовой разработки.

## 2. Принятый application baseline и main history

```text
application baseline branch: main
application baseline HEAD: e18872face7f27f489056b72fed31e5586121b0c
included in accepted baseline: INFRA-001 + INFRA-002 + INFRA-003 + DOCS-001
current main history HEAD: 4237aadc2cfdee518567024c2b45b653f49c16e7
current main additions: DOCS-002 + DOCS-003 + QUALITY-001
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

PR #5 `DOCS-002: Finalize DOCS-001 accepted baseline` squash-merged в `a2d686b0061fac513c02540a2176850640496884`. Это documentation-only metadata follow-up: он не меняет application behavior, schema, migrations or runtime data и не создаёт новый application baseline.

PR #6 `DOCS-003: Add provisional UX-001 v0.3 contract` squash-merged в `62ce0a611b0d36a4c0f1f28ac6083cac5d305fb5`. Он не меняет runtime и не означает visual acceptance.

PR #8 `QUALITY-001: Repair PostgreSQL test execution` принят пользователем и squash-merged в `4237aadc2cfdee518567024c2b45b653f49c16e7`.

На exact accepted PR head подтверждено:

- EOD CI — success;
- EOD Development Stack — success;
- EOD Documentation Contract — success;
- full PostgreSQL suite: `497/497 OK`;
- database identity: `eod_development`;
- development worktree: clean.

Accepted application baseline остаётся `e18872f…` до отдельной фиксации post-merge preview evidence для нового application merge commit.

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

Оба контура изолированы. PostgreSQL host ports не публикуются. Доступ к приложениям выполняется через SSH tunnel. VPS deploy key остаётся read-only.

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
- канонический DOCS-контур, runbooks, acceptance documents и documentation CI gate;
- обнаруживаемый полный PostgreSQL test suite.

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

Пользователь исключён из механической части программирования, но до AUTO-001 ещё участвует в механическом VPS execution/log-transfer этапе.

## 7. Текущий обязательный инфраструктурный этап

```text
AUTO-000 documentation contract
→ AUTO-001 development orchestrator MVP
→ return to PLAN-001
```

AUTO-000 документирует архитектуру, security model, acceptance и roadmap. Он не меняет runtime, workflows, VPS или secrets.

AUTO-001 должен автоматически выполнить exact-SHA development deployment, явно выбранный `refresh`/`rebuild`, `check`, полный `test apps`, `status` и публикацию evidence в GitHub. Automatic merge запрещён.

AUTO-002 и дальнейшая автоматизация не блокируют возврат к продуктовой разработке.

## 8. PLAN-001

`PLAN-001 — ревизия фактической реализации` остаётся открытым Draft PR #7.

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
- минимальный обязательный smoke/integration suite поверх действующего полного test baseline.

PLAN-001 продолжается после принятого AUTO-001 MVP.

## 9. UX-001

`UX-001 v0.3` является предварительным проектным контрактом для визуального прототипирования.

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

## 10. Согласованное продуктовое направление

```text
минимальный общий контракт
→ один журнал полностью
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Связи не откладываются до завершения всего пакета. Полная универсальная timeline не проектируется заранее без подтверждённых отношений.

## 11. QUALITY-001 — закрытый технический долг

Полный test command:

```text
python manage.py test apps --verbosity 2
```

На exact accepted PR head выполнено `497/497 OK`. Нулевое test discovery больше не считается текущим долгом. Следующие product slices обязаны сохранять полный suite и добавлять профильные tests/gates.
