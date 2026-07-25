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

Пользователь не должен вручную редактировать код, собирать файлы, применять patch scripts или выполнять Git write operations. AUTO-001 дополнительно исключит штатные ручные VPS deployment/test commands и передачу полных логов в чат.

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

PostgreSQL host ports отсутствуют. Контуры изолированы. VPS deploy key read-only.

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

DOCS-001 остаётся accepted application baseline до отдельного принятого post-merge baseline update.

### DOCS-002

- PR #5 принят и squash-merged в `a2d686b0061fac513c02540a2176850640496884`;
- metadata-only follow-up не создаёт новый application baseline;
- preview после merge был clean and healthy.

### DOCS-003

- PR #6 принят и squash-merged в `62ce0a611b0d36a4c0f1f28ac6083cac5d305fb5`;
- UX-001 v0.3 сохранён как provisional contract;
- runtime, domain model and data unchanged;
- visual acceptance и implementation authorization отсутствуют.

### QUALITY-001

- PR #8 принят и squash-merged;
- merge commit: `4237aadc2cfdee518567024c2b45b653f49c16e7`;
- exact accepted PR head: `4bf055d681ef35a881c8bf5dc28e8945c1948e0d`;
- GitHub gates green;
- development database identity correct;
- clean worktree;
- PostgreSQL suite `497/497 OK`.

Штатный test command:

```text
python manage.py test apps --verbosity 2
```

Устаревшее утверждение `0 test(s)` закрыто QUALITY-001.

## Текущая работа

### AUTO-000 — Development Automation Contract

Branch:

```text
docs/004-auto-000-development-automation-contract
```

AUTO-000 является documentation-only и должен зафиксировать:

- automation master plan;
- AUTO-001 functional contract;
- security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- актуальные current state/handoff/roadmap/open items.

AUTO-000 не меняет application code, models, migrations, workflows, VPS, secrets или data.

## Следующий implementation work item

### AUTO-001 — GitHub/VPS Development Orchestrator MVP

Целевой маршрут:

```text
trusted PR trigger
→ green required checks for current head
→ restricted VPS gateway
→ exact-SHA development deployment
→ explicit refresh/rebuild
→ check
→ test apps
→ status
→ structured evidence in GitHub
```

Не входят в MVP:

- automatic merge;
- browser automation;
- visual regression;
- automatic DB reset;
- automatic preview deployment;
- autonomous code repair.

Gate возврата к продукту:

1. два успешных deployment;
2. один намеренно отрицательный case;
3. exact-SHA proof;
4. preview isolation proof;
5. ноль ручных VPS-команд пользователя в штатном run.

AUTO-002+ не блокируют PLAN-001.

## PLAN-001

PR #7 остаётся Draft и выполняет доказательную ревизию:

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

После AUTO-001 MVP:

- обновить branch от принятого `main`;
- выполнить evidence audit;
- сформировать master plan v3.0;
- выбрать первый journal vertical slice;
- определить актуальный smoke/integration suite поверх полного test baseline.

## UX-001

Текущий статус:

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Пользователь не принимал concrete palette, typography, density, radii, shadows, shell composition и внешний вид reference screens.

Следующий gate:

1. два compact visual directions;
2. выбор/корректировка пользователя;
3. limited runtime prototype;
4. проверка long Russian data, density, states, focus and overlays;
5. accepted tokens только после visual acceptance.

UX не блокирует PLAN-001. Defect journal остаётся кандидатом, а не утверждённым первым slice.

## Принятые продуктовые решения

### Последовательная журнальная разработка

```text
минимальный общий контракт
→ один журнал полностью
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Связи не откладываются до завершения всего пакета, но универсальная timeline не проектируется заранее.

### Журнал ключей

- бумажный журнал остаётся основным оригиналом;
- полный электронный lifecycle не входит в обязательный внутренний прототип;
- вспомогательный электронный контур требует отдельной оценки.

### UI/UX

- visual goal: современная операционная платформа;
- visual identity самостоятельна;
- UI только русский, internals — professional technical English;
- operational journal остаётся специализированной document-first environment.

## Предметные правила, которые нельзя потерять

- operational journal specialised;
- structured forms source-bound;
- journals developed one by one with minimal real links;
- keys journal paper-first;
- UI Russian-only;
- management and supervision separate;
- informational supervision is a property of supervision;
- ЩПТ/ШОТ — one technical equipment family with source designation preserved;
- electronic work permit requires current normative evidence;
- real data and secrets are not committed;
- canonical docs updated with accepted changes.

## Источники истины

1. accepted application baseline and `main` history;
2. `docs/project/CURRENT_STATE.md`;
3. migrations, tests, CI and VPS diagnostics;
4. `docs/project/CURRENT_HANDOFF.md`;
5. decision/baseline/acceptance histories;
6. `docs/automation/` for AUTO contract;
7. `docs/ux/README.md` for UX status;
8. current chat;
9. historical plans and context archives.

При расхождении факт проверяется, а документы исправляются в той же рабочей ветке.
