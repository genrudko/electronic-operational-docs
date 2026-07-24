# ЭОД — текущий handoff

**Обновлено:** 25.07.2026

**Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

**Active branch:** `docs/002-docs001-baseline-finalization`

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

PostgreSQL host ports отсутствуют. Контуры изолированы.

## Что принято последним

DOCS-001:

- PR #4 принят пользователем;
- exact accepted head: `1f0b71b927fbee0ef08957eac157b2480d2e9a8c`;
- squash merge commit: `e18872face7f27f489056b72fed31e5586121b0c`;
- canonical documentation tree, README, AGENTS and index;
- GitHub-first/VPS-first operating system;
- project/process/runbooks/acceptance/releases documents;
- PR template and documentation contract CI;
- migration and removal of active `docs/project_state/`;
- sequential journal strategy;
- paper-first scope for the keys journal;
- UX-001 brief and parallel UI/UX workstream;
- mandatory DOCS continuity after accepted changes.

## Post-merge evidence DOCS-001

На `/srv/eod/repository` подтверждено:

- branch `main`;
- HEAD `e18872face7f27f489056b72fed31e5586121b0c`;
- clean worktree;
- documentation contract OK, 43 required files;
- preview app and db healthy;
- health `{"status": "ok"}`;
- main page HTTP 200;
- database identity `eod_preview`;
- pending migrations отсутствуют.

DOCS-001 не менял application behavior, models, migrations or runtime data; container rebuild не требовался.

## Текущая работа

`docs/002-docs001-baseline-finalization` — короткий metadata follow-up:

- фиксирует accepted application baseline `e18872f…`;
- обновляет current state, handoff, baseline/acceptance histories and release notes;
- переводит roadmap и open items на PLAN-001;
- уточняет, что metadata-only follow-up не создаёт бесконечную рекурсию baseline SHA.

После merge этого follow-up accepted application baseline остаётся `e18872f…`, потому что ветка изменяет только документационную фиксацию уже принятого состояния и не меняет application/runtime baseline.

## Следующая обязательная работа

PLAN-001 — доказательная ревизия плана и реализации.

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
- минимальный smoke/integration test suite.

Параллельно UX-001 выполняет evidence-based audit текущего интерфейса и формирует design/interaction contract без остановки продуктового потока.

## Принятые продуктовые решения

### Последовательная журнальная разработка

```text
минимальный общий контракт
→ один журнал полностью
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Связи не откладываются до завершения всего пакета, но универсальная timeline не проектируется заранее без подтверждённых кейсов.

Предварительный первый кандидат — журнал дефектов. Окончательный выбор выполняется PLAN-001.

### Журнал ключей

- бумажный журнал остаётся основным оригиналом;
- полный электронный lifecycle выдачи/возврата не входит в обязательный внутренний прототип;
- электронный справочный/контрольный контур требует отдельной предметной и UX-оценки.

### UI/UX

UX-001 формирует principles, tokens, component and interaction contracts, page archetypes, reference screens and implementation roadmap. Основной интеграционный чат сохраняет domain/architecture decisions и реализацию.

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

## Тестовый долг

Команда `development_stack.sh test` обнаруживает `0 test(s)` и не считается достаточным evidence. PLAN-001 должен определить минимальный автоматический suite, а каждый следующий product slice — добавлять профильные tests/gates.

## Источники истины

1. accepted application baseline and `main` Git history;
2. `docs/project/CURRENT_STATE.md`;
3. migrations, tests, CI and VPS diagnostics;
4. `docs/project/CURRENT_HANDOFF.md`;
5. decision/baseline/acceptance histories;
6. current chat;
7. historical local plans and context archives.

При расхождении факт проверяется, а документы исправляются в той же рабочей ветке.