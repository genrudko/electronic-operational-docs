# ЭОД — workflow разработки

**Актуализировано:** 01.08.2026

## 1. Нормальный цикл

```text
Пользователь формулирует цель
→ AI проверяет current main, active PR и canonical docs
→ factual audit затрагиваемого контура
→ issue / branch / Draft PR
→ implementation slice
→ focused/profile checks
→ trusted exact-head delivery в isolated development
→ пользователь проходит acceptance route
→ repairs в том же PR
→ один full final gate на окончательном head
→ пользователь разрешает merge
→ merge commit
→ post-merge baseline/docs
```

GitHub — источник кода и постоянной памяти. VPS — runtime/test contour. Пользователь не является техническим оркестратором или курьером между чатами.

## 2. Что пользователь не делает

- не редактирует code, templates, CSS/JS или migrations;
- не собирает файлы из фрагментов;
- не исправляет lint/syntax/test failures;
- не выполняет commits, push, PR и normal deployment;
- не переносит базы;
- не собирает вручную evidence по нескольким workflow;
- не запускает штатные VPS-команды для functional PR;
- не переносит handoff, SHA, отчёты и технические команды между чатами или AI-исполнителями.

Пользователь задаёт цель, предметные правила, UX-оценку и merge decision.

## 2.1. Единый пользовательский контур и восстановление нового чата

Один активный чат ведёт work item от preflight до post-merge coordination. Техническая декомпозиция, GitHub operations, CI diagnosis, delivery и repairs остаются внутри этого контура и не перекладываются на пользователя.

Новый чат создаётся только когда текущий разговор технически переполнен или деградировал. Стартовая команда может быть одной строкой:

```text
Продолжай EOD по фактическому состоянию GitHub.
```

После такой команды исполнитель обязан самостоятельно:

1. прочитать `AGENTS.md`, `CURRENT_STATE.md`, release plan и профильный work-item contract;
2. определить current `main`, active issue/PR/branch и exact head;
3. проверить PR body или machine-owned evidence comment;
4. проверить changed-file boundary, CI, runtime state и blockers;
5. продолжить ближайший безопасный action без запроса ручного handoff.

При доступном GitHub запрещено требовать от пользователя starter-файл, отчёт старого чата или повторную передачу фактов, уже опубликованных в issue/PR/canonical docs. Чат является временным интерфейсом; GitHub хранит состояние между циклами.

Для каждого активного PR его body либо один machine-owned comment должен содержать актуальные:

```text
OBJECTIVE
BASE
BRANCH
EXACT HEAD
ALLOWED / FORBIDDEN BOUNDARY
CURRENT BLOCKER
NEXT ACTION
CI STATE
RUNTIME STATE
ACCEPTANCE STATE
```

## 3. Factual preflight

До создания branch:

1. проверить current `main`;
2. проверить active/open PR и work item;
3. прочитать `AGENTS.md`, current state/handoff, domain и product/UX principles;
4. изучить фактические models/services/routes/templates/static/tests;
5. отделить существующее от предполагаемого;
6. определить критический пользовательский маршрут;
7. определить shared и specialized UI;
8. выбрать risk profile;
9. сформулировать first delivery slice и acceptance criteria.

Результат:

```text
READY TO IMPLEMENT
```

либо:

```text
BLOCKED — IMPLEMENTATION MUST NOT START
```

Повторный большой аудит не проводится без изменения фактов.

## 4. Единица работы

```text
one work item
→ one issue
→ one branch
→ one Draft PR
→ all repairs
```

Новый PR не создаётся для каждого visual repair или CI fix.

Large work item делится на reviewable commits/slices внутри того же PR, пока цель и risk boundary остаются общими.

## 5. Реализация

- code создаётся только в GitHub branch;
- VPS не является автором source code;
- commit имеет законченную цель;
- documentation changes идут вместе с изменением либо обязательным post-merge follow-up;
- real data и secrets не попадают в Git;
- feature-specific визуальный слой не копируется для нового модуля;
- shared component меняется с cross-screen проверкой.

## 6. Risk profiles

### `DOCS`

- canonical docs;
- research mapping;
- process contract.

Проверки: documentation contract, links, consistency.

### `PRESENTATION`

- templates;
- CSS;
- browser JS без domain state change.

Проверки: changed-path validation, focused tests, source-contract tests, hot refresh, browser acceptance.

### `APP_LOGIC`

- views;
- forms;
- application services без schema.

Проверки: Ruff, compile, Django check, focused/profile tests, migration check, trusted deployment.

### `SCHEMA_DATA`

- models;
- migrations;
- seed/import;
- data contracts.

Проверки: PostgreSQL migrations/tests, identity, backup/rollback, final gate.

### `SECURITY_INFRA`

- workflows;
- controller;
- Compose;
- security boundaries.

Проверки: dedicated security/infra gates and controlled runtime evidence.

Используется максимальный фактический risk profile затронутого diff.

## 7. Быстрый visual repair loop

Для разрешённых added/modified regular files:

```text
src/templates/**
src/static/**
```

цикл:

```text
repair commit
→ focused checks
→ /eod-hot-refresh <exact-head-sha>
→ app health
→ acceptance URL
```

Не выполняются после каждого repair:

- полный PostgreSQL suite;
- все required workflow;
- full image rebuild;
- presentation reset;
- preview deployment.

При ошибке controller обязан clean-recreate development app из текущего полноценного image.

## 8. Candidate profile

Candidate создаётся, когда delivery slice готов к связной проверке.

Минимум:

- exact PR head;
- diff/path classification;
- profile tests;
- Django check;
- migrations check по применимости;
- collectstatic/container smoke;
- trusted deployment;
- health;
- acceptance route;
- machine-readable evidence summary.

Для Python/runtime change используется trusted rebuild/deploy profile. Для presentation-only candidate допускается hot refresh.

## 9. Final gate

Один раз на окончательном принятом head:

- all required exact-head workflows;
- full current PostgreSQL test suite;
- migrations;
- container smoke;
- preview isolation;
- trusted development exact-SHA confirmation;
- desktop/mobile acceptance;
- no blocking defects;
- PR evidence.

Любой новый commit после final gate требует актуального final gate заново.

## 10. CI discipline

- required checks не ослабляются;
- queued/running проверки устаревшего head отменяются по concurrency, если безопасно;
- diagnostics artifact создаётся при failure/rollback, а не обязательно при success;
- run IDs and conclusions собираются в один PR evidence comment;
- flaky retry не маскирует причину первого падения;
- infrastructure timeout отделяется от code defect;
- ноль тестов не считается success.

## 11. Trusted development delivery

Обязательны:

- exact requested SHA;
- live PR head re-check;
- same-repository PR;
- authorized actor;
- serialized deployment transaction;
- health confirmation;
- rollback contract;
- database operations summary;
- preview `UNTOUCHED`;
- automatic merge `ABSENT`.

Development никогда не остаётся на `main`.

## 12. Browser acceptance

Пользователю возвращаются:

- exact head;
- URL;
- 3–7 конкретных шагов;
- ожидаемый результат;
- известные ограничения;
- что изменено и что сознательно не входит в scope.

Проверяется сценарий, а не один красивый screenshot.

Для shared UX component сравниваются несколько реальных экранов при одинаковых desktop/mobile viewport.

## 13. Repair

```text
video/log/feedback
→ exact reproduced fact
→ smallest sufficient repair
→ same branch/PR
→ proportional checks
→ delivery
→ repeated acceptance
```

Во время серии visual remarks замечания накапливаются и доставляются небольшими пакетами. Full gate откладывается до финального head.

## 14. Merge

Перед merge AI проверяет:

- PR open and mergeable;
- Draft/Ready state;
- exact accepted head;
- актуальные required checks;
- accepted runtime evidence;
- acceptance comment;
- отсутствие unresolved blocker;
- явную команду пользователя.

Merge strategy определяется явным решением пользователя в текущем work-item контексте. Automatic merge запрещён.

## 15. После merge

1. зафиксировать source head и merge commit;
2. закрыть issue;
3. удалить branch по решению;
4. выполнить post-merge deployment только по актуальному release contract;
5. проверить preview health/data identity;
6. обновить current state, handoff, roadmap, open items, baseline and acceptance history;
7. определить следующий work item;
8. сохранить в GitHub достаточно состояния, чтобы новый чат продолжил работу без ручного handoff.

## 16. Documentation-only coordination

Небольшой цельный canonical update может быть выполнен direct-to-main, если:

- нет runtime/schema/data/security change;
- пользователь явно поручил обновление;
- нет конфликтующего docs PR;
- изменение проходит documentation checks;
- это не обход product review.

Такой commit не становится новым application baseline только потому, что изменил документацию.

## 17. Emergency fallback

Patch-file или manual copy используется только при технической невозможности normal GitHub write. Проверяемое состояние обязано быть немедленно воспроизведено committed source и пройти обычные gates.
