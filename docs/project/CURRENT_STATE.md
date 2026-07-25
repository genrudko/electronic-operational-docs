# ЭОД — текущее состояние

**Дата проверки:** 25.07.2026

**Принятый application baseline:** `main / 937d2cd2b187c17fac3088ccfc52079fc4608306`

**Текущий Git HEAD main:** `937d2cd2b187c17fac3088ccfc52079fc4608306`

**Текущая metadata-работа:** `docs/005-auto000-baseline-finalization` — Draft PR #10

**Открытая продуктовая ревизия:** `plan/001-evidence-audit` — Draft PR #7

## 1. Статус проекта

Проект является независимым демонстрационным прототипом электронной оперативной документации для энергетики. Инициатива не является официальным поручением работодателя. Производственные серверы, фактические оперативные записи и реальные персональные данные в разработке не используются.

GitHub является единственным источником кода и канонической документации. Accepted preview и active development изолированы на VPS.

Последние принятые этапы:

- DOCS-001 — project operating system;
- DOCS-002 — metadata finalization DOCS-001 baseline;
- DOCS-003 — provisional UX-001 v0.3 contract;
- QUALITY-001 — восстановление полного PostgreSQL test execution;
- AUTO-000 — принятый development automation contract.

## 2. Текущий baseline и main history

```text
accepted application baseline branch: main
accepted application baseline HEAD: 937d2cd2b187c17fac3088ccfc52079fc4608306
current main history HEAD: 937d2cd2b187c17fac3088ccfc52079fc4608306
```

Baseline включает INFRA-001–003, DOCS-001–003, QUALITY-001 и AUTO-000.

### QUALITY-001

PR #8 принят пользователем и squash-merged в `4237aadc2cfdee518567024c2b45b653f49c16e7`.

На exact accepted PR head подтверждено:

- EOD CI — success;
- EOD Development Stack — success;
- EOD Documentation Contract — success;
- full PostgreSQL suite: `497/497 OK`;
- database identity: `eod_development`;
- development worktree: clean.

### AUTO-000

PR #9 принят пользователем и squash-merged в `937d2cd2b187c17fac3088ccfc52079fc4608306`.

AUTO-000 — documentation-only operating-system milestone. Он зафиксировал architecture, security boundaries, exact-SHA contract, acceptance criteria и roadmap AUTO-001, но не реализовал automation runtime.

### Post-merge preview verification

На `/srv/eod/repository` подтверждено:

- branch `main`;
- exact HEAD `937d2cd2b187c17fac3088ccfc52079fc4608306`;
- clean worktree;
- preview app image rebuilt from current checkout;
- app container recreated и healthy;
- preview database container не пересоздавался и healthy;
- health endpoint: `{"status": "ok"}`;
- main page: HTTP 200 на `127.0.0.1:8765`;
- database identity: `eod_preview`;
- `migrate --check`: success;
- `makemigrations --check --dry-run`: no changes detected;
- host `src` и container `/app/src` совпадают после исключения generated `electronic_operational_docs.egg-info/*`;
- итоговый marker: `FINAL PREVIEW GATE PASSED`.

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
branch: active non-main branch only
compose project: eod-development
application: 127.0.0.1:8766
database/user: eod_development
secrets: /srv/eod/secrets/development.env
```

Оба контура изолированы. PostgreSQL host ports не публикуются. Доступ выполняется через SSH tunnel. VPS deploy key остаётся read-only. Development checkout не переводится на `main` после merge.

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
- повторная аутентификация, snapshot и SHA-256 integrity status;
- нормативный реестр и редакции организационной конфигурации;
- энергообъекты, оборудование, диспетчерские наименования и их история;
- диспетчерское и технологическое управление и ведение;
- импорт оборудования, персонала, оперативных прав и документации рабочего места;
- специализированный оперативный журнал и сменная работа в объёме текущего прототипа;
- общее ядро структурированных журналов;
- source-bound каталог рабочих форм;
- GitHub Actions CI на Linux/PostgreSQL;
- безопасный preview и изолированный development на VPS;
- канонический documentation/acceptance/runbook contour;
- обнаруживаемый полный PostgreSQL suite `497/497`.

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

Журнал ключей остаётся paper-first до отдельного предметного и UX-решения.

## 6. Текущий процесс разработки

1. Ассистент создаёт complete change в отдельной GitHub branch.
2. GitHub Actions выполняет gates.
3. VPS development получает exact branch/SHA.
4. Выполняются refresh/rebuild, checks, tests и status.
5. Пользователь проводит предметную и визуальную приёмку.
6. Repair commits создаются в той же branch/PR.
7. Merge выполняется только после явного разрешения пользователя.
8. Preview синхронизируется с `main` и проходит post-merge gate.
9. Canonical docs актуализируются в том же PR или обязательном metadata follow-up.

До принятия AUTO-001 пользователь ещё участвует в механическом VPS execution/log-transfer этапе. Для защиты длинных операций на VPS установлен `tmux`.

## 7. Текущая работа и следующий этап

### DOCS-005

```text
branch: docs/005-auto000-baseline-finalization
PR: #10 Draft
change type: documentation-only metadata follow-up
runtime impact: none
```

DOCS-005 фиксирует уже доказанный baseline `937d2cd…`, AUTO-000 acceptance и handoff для нового Чата 0. Собственный merge SHA DOCS-005 не создаёт новый application baseline.

### AUTO-001 — следующий implementation work item

```text
trusted PR trigger
→ green required checks for current head
→ restricted VPS gateway
→ exact-SHA development deployment
→ explicitly selected refresh/rebuild
→ check
→ full test apps
→ status
→ sanitised evidence in GitHub
```

Не входят в MVP:

- automatic merge;
- automatic preview deployment;
- browser automation и visual regression;
- automatic development database reset;
- autonomous code repair.

Exit gate:

- два последовательных successful deployments;
- один intentional negative case;
- exact-SHA и superseded proof;
- preview isolation proof;
- отсутствие ручных VPS-команд пользователя в штатном run;
- отдельная явная пользовательская приёмка.

После AUTO-001 MVP продуктовая работа возвращается к PLAN-001. AUTO-002+ не являются блокерами.

## 8. PLAN-001 — ревизия фактической реализации

PR #7 остаётся Draft. После AUTO-001 необходимо доказательно сопоставить для каждого модуля:

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

Результаты:

- master plan v3.0;
- подтверждённый первый журнальный vertical slice;
- реалистичная последовательность следующих работ;
- минимальный обязательный smoke/integration suite поверх полного PostgreSQL baseline.

Рабочий принцип: один журнал полностью → минимальные реальные связи → automated and user acceptance → следующий журнал.

## 9. UX-001

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Следующий UX gate: два компактных визуальных направления для application shell и одного показательного structured-journal screen → решение пользователя → ограниченный runtime prototype → корректировка → фиксация accepted tokens.

Журнал дефектов остаётся кандидатом на reference vertical slice, но окончательный выбор принимает PLAN-001.

## 10. Непереговорные предметные правила

- UI конечного пользователя только русский;
- internals — professional technical English;
- оперативный журнал остаётся специализированным модулем;
- остальные журналы строятся на общем ядре, но рабочие формы source-bound;
- оператор не конструирует произвольные рабочие журналы;
- управление и ведение моделируются раздельно;
- информационное ведение — характеристика ведения;
- ЩПТ и ШОТ относятся к одной технической equipment family с сохранением исходного обозначения/варианта исполнения;
- электронный, гибридный и бумажный режимы наряда не объявляются юридически эквивалентными без доказанного нормативного основания;
- реальные данные и secrets не коммитятся;
- automatic merge запрещён.
