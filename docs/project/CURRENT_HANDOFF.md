# ЭОД — текущий handoff

**Обновлено:** 25.07.2026

**Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

**Current main history HEAD:** `4237aadc2cfdee518567024c2b45b653f49c16e7`

**Current work:** `AUTO-000 — Development Automation Contract`

**Parallel open Draft:** `PLAN-001 — PR #7`

## Проект

Независимый демонстрационный прототип электронной оперативной документации для энергетики. Пользователь — начальник смены ВЭС, владелец продукта и предметный эксперт; программирование, commits, PR и техническая диагностика выполняются ассистентом.

## Рабочая модель

Основной цикл GitHub-first/VPS-first:

1. ассистент создаёт complete change в active GitHub branch;
2. GitHub Actions выполняет gates;
3. `/srv/eod/development` получает branch через `git pull --ff-only`;
4. выполняются development refresh/check/test/status;
5. пользователь проверяет UI, данные и предметную логику через SSH tunnel;
6. repair commits создаёт ассистент;
7. merge выполняется только по явной команде пользователя;
8. `/srv/eod/repository` синхронизируется с новым `main` и проходит post-merge gate;
9. применимые canonical docs актуализируются вместе с изменением или metadata follow-up.

Пользователь не должен вручную редактировать код, собирать файлы, применять patch scripts или выполнять Git write operations.

До принятия AUTO-001 остаётся действующим ручной VPS-этап: переключение development branch, запуск refresh/check/test/status и передача результата в чат. AUTO-001 должен исключить этот штатный механический этап, не меняя пользовательскую предметную и визуальную приёмку и не получая права merge.

## Контуры VPS

### Preview

```text
/srv/eod/repository
main only
eod-preview
eod_preview
127.0.0.1:8765
/srv/eod/secrets/preview.env
```

### Development

```text
/srv/eod/development
active non-main branch
eod-development
eod_development
127.0.0.1:8766
/srv/eod/secrets/development.env
```

PostgreSQL host ports отсутствуют. Контуры изолированы. VPS deploy key для получения кода из GitHub остаётся read-only.

## Что принято последним

### DOCS-001

- PR #4 принят пользователем;
- exact accepted head: `1f0b71b927fbee0ef08957eac157b2480d2e9a8c`;
- squash merge commit: `e18872face7f27f489056b72fed31e5586121b0c`;
- canonical documentation tree, README, AGENTS and index;
- GitHub-first/VPS-first operating system;
- project/process/runbooks/acceptance/releases documents;
- sequential journal strategy;
- paper-first scope for the keys journal;
- UX-001 brief and parallel UI/UX workstream.

DOCS-001 является accepted application baseline.

### DOCS-002

- PR #5 принят пользователем и squash-merged;
- merge commit: `a2d686b0061fac513c02540a2176850640496884`;
- зафиксированы DOCS-001 post-merge evidence, baseline history and PLAN-001 transition;
- metadata-only follow-up не создаёт новый application baseline;
- preview после merge: clean `main`, documentation contract OK, containers healthy, health OK, HTTP 200.

### DOCS-003

- PR #6 принят пользователем и squash-merged;
- merge commit: `62ce0a611b0d36a4c0f1f28ac6083cac5d305fb5`;
- UX-001 v0.3 сохранён как provisional project contract;
- runtime, domain model, lifecycle and runtime data не менялись;
- visual acceptance и implementation authorization отсутствуют.

### QUALITY-001

- PR #8 принят пользователем и squash-merged;
- exact accepted PR head: `4bf055d681ef35a881c8bf5dc28e8945c1948e0d`;
- main merge commit: `4237aadc2cfdee518567024c2b45b653f49c16e7`;
- EOD CI, EOD Development Stack и EOD Documentation Contract успешны;
- development database identity: `eod_development`;
- development worktree clean;
- полный PostgreSQL suite: `497/497 OK`.

Штатная команда полного suite:

```text
python manage.py test apps --verbosity 2
```

Устаревшее утверждение `0 test(s)` закрыто QUALITY-001.

Accepted application baseline остаётся `e18872f…` до отдельной принятой фиксации post-merge preview evidence для нового application merge commit.

## Текущая работа

### AUTO-000 — Development Automation Contract

```text
branch: docs/004-auto-000-development-automation-contract
change type: documentation-only
runtime impact: none
AUTO-001 implementation: absent
```

AUTO-000 фиксирует:

- automation master plan;
- AUTO-001 functional contract;
- security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- актуализацию current state, handoff, roadmap, open items and release notes после QUALITY-001.

AUTO-000 не меняет application code, models, migrations, GitHub workflows, VPS configuration, secrets или data. Merge AUTO-000 принимает только документальный контракт и разрешает отдельную реализацию AUTO-001.

## Следующий implementation work item

### AUTO-001 — GitHub/VPS Development Orchestrator MVP

Целевой маршрут:

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
- browser automation;
- visual regression;
- automatic development database reset;
- automatic preview deployment;
- autonomous code repair.

Gate возврата к продуктовой разработке:

1. два последовательных успешных deployment;
2. один намеренно отрицательный case;
3. exact-SHA and superseded proof;
4. preview isolation proof;
5. отсутствие ручных VPS-команд пользователя в штатном run;
6. отдельная явная пользовательская приёмка.

AUTO-002 и последующие этапы автоматизации не блокируют PLAN-001.

## Следующая обязательная продуктовая работа

PLAN-001 — доказательная ревизия плана и реализации.

PR #7 остаётся Draft и продолжается после принятого AUTO-001 MVP.

Нужно сопоставить:

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
- возможная корректировка очередности;
- минимальный smoke/integration test suite поверх действующего полного PostgreSQL test baseline.

## UX-001

Текущий статус UX-001:

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Пользователь не видел визуально новое направление и разрешил оформить контракт как обратимую основу для дальнейшего прототипирования. Concrete palette, typography, density, radii, shadows, shell composition и внешний вид reference screens не приняты.

## Следующий UX gate

1. Подготовить два компактных visual directions на application shell и одном показательном structured-journal screen.
2. Пользователь выбирает, комбинирует или отклоняет направление.
3. Выбранное направление реализуется как ограниченный runtime prototype на development contour.
4. Проверяются плотность, длинные русские значения, states, focus, overlays and target desktop.
5. Только после визуальной приёмки фиксируются accepted tokens и разрешается постепенное внедрение.

UX-001 не должен останавливать PLAN-001. Defect journal остаётся кандидатом, а не утверждённым первым slice.

## Принятые продуктовые решения

### Последовательная журнальная разработка

Действующее правило: журналы доводятся по одному — сначала минимальный общий контракт, затем один журнал полностью с минимальными реальными связями, автоматизированной и пользовательской приёмкой.

```text
минимальный общий контракт
→ один журнал полностью
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Связи не откладываются до завершения всего пакета, но универсальная timeline не проектируется заранее без подтверждённых кейсов.

### Журнал ключей

- бумажный журнал остаётся основным оригиналом;
- полный электронный lifecycle выдачи/возврата не входит в обязательный внутренний прототип;
- электронный справочный/контрольный контур требует отдельной предметной и UX-оценки.

### UI/UX

- visual goal: современная операционная платформа, а не техническая administrative console;
- visual identity самостоятельна и не использует чужие logos, marks or official affiliation claims;
- UI только русский, internals — professional technical English;
- candidate visual tokens не становятся стандартом без runtime and user visual acceptance;
- operational journal остаётся специализированной document-first environment.

## Предметные правила, которые нельзя потерять

- оперативный журнал остаётся специализированным;
- рабочие structured forms только source-bound;
- журналы доводятся по одному с минимальными реальными связями;
- журнал ключей paper-first до отдельного решения;
- UI только русский, internals — professional technical English;
- управление и ведение раздельны;
- информационное ведение — характеристика ведения;
- ЩПТ и ШОТ — одна техническая equipment family с сохранением исходного обозначения;
- electronic work permit model не объявляется юридически допустимой без актуального исследования;
- реальные данные и secrets не коммитятся;
- принятие изменения включает актуализацию применимых canonical docs.

## Тестовый baseline и открытый quality scope

QUALITY-001 восстановил обнаружение и выполнение полного PostgreSQL suite:

```text
python manage.py test apps --verbosity 2
497/497 OK on accepted PR head
```

Нулевое test discovery больше не является текущим долгом. PLAN-001 должен определить быстрый обязательный smoke/integration subset поверх полного suite, а каждый следующий product slice обязан добавлять профильные tests/gates. Для semantic marker copy/paste/save/reload требуется отдельная automated regression при соответствующем repair.

## Источники истины

1. accepted application baseline and `main` Git history;
2. `docs/project/CURRENT_STATE.md`;
3. migrations, tests, CI and VPS diagnostics;
4. `docs/project/CURRENT_HANDOFF.md`;
5. decision/baseline/acceptance histories;
6. `docs/automation/` for AUTO-000/AUTO-001 contract;
7. `docs/ux/README.md` for UX-001 status;
8. current chat;
9. historical local plans and context archives.

При расхождении факт проверяется, а документы исправляются в той же рабочей ветке.
