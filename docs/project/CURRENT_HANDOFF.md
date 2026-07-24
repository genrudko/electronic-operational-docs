# ЭОД — текущий handoff

**Обновлено:** 25.07.2026

**Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

**Current main history HEAD:** `a2d686b0061fac513c02540a2176850640496884`

**Active branch:** `docs/003-ux001-provisional-contract`

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

## Текущая работа

`DOCS-003 — provisional UX-001 v0.3 contract`:

- исходный UX-пакет сохраняется в `docs/ux/UX-001_v0.3/`;
- package manifest сохраняет контроль исходных файлов;
- `docs/ux/README.md` задаёт канонический статус и следующий visual gate;
- current state, handoff, roadmap, open items and decision log синхронизируются;
- production code, domain model, lifecycle and runtime data не меняются.

Текущий статус UX-001:

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Пользователь не видел визуально новое направление и разрешил оформить контракт как обратимую основу для дальнейшего прототипирования. Concrete palette, typography, density, radii, shadows, shell composition и внешний вид reference screens не приняты.

## Следующая обязательная продуктовая работа

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

## Следующий UX gate

1. Подготовить два компактных visual directions на application shell и одном показательном structured-journal screen.
2. Пользователь выбирает, комбинирует или отклоняет направление.
3. Выбранное направление реализуется как ограниченный runtime prototype на development contour.
4. Проверяются плотность, длинные русские значения, states, focus, overlays and target desktop.
5. Только после визуальной приёмки фиксируются accepted tokens и разрешается постепенное внедрение.

UX-001 не должен останавливать PLAN-001. Defect journal остаётся кандидатом, а не утверждённым первым slice.

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

## Тестовый долг

Команда `development_stack.sh test` обнаруживает `0 test(s)` и не считается достаточным evidence. PLAN-001 должен определить минимальный автоматический suite, а каждый следующий product slice — добавлять профильные tests/gates.

## Источники истины

1. accepted application baseline and `main` Git history;
2. `docs/project/CURRENT_STATE.md`;
3. migrations, tests, CI and VPS diagnostics;
4. `docs/project/CURRENT_HANDOFF.md`;
5. decision/baseline/acceptance histories;
6. `docs/ux/README.md` for UX-001 status;
7. current chat;
8. historical local plans and context archives.

При расхождении факт проверяется, а документы исправляются в той же рабочей ветке.
