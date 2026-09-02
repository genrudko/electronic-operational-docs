# ЭОД — ускорение и автоматизация разработки

**Статус:** canonical process contract / implementation backlog  
**Дата:** 29.07.2026

## 1. Цель

Сократить время от изменения до пользовательской проверки без ослабления:

- exact-SHA guarantees;
- PostgreSQL coverage;
- preview isolation;
- rollback;
- security boundaries;
- пользовательского merge gate.

Оптимизируется не только машинное время CI, но и когнитивная нагрузка:

- меньше повторных ручных операций;
- меньше дублирования проверок;
- меньше переключений между чатами и инструментами;
- более короткая диагностика;
- единый UX/component contract;
- один понятный evidence summary для каждого candidate head.

## 2. Непереговорные границы

Не автоматизируются:

- automatic merge;
- запись в preview из product PR;
- обход required gates для высокорисковых изменений;
- доверие к ветке без exact live-head re-check;
- изменение БД без migrations и rollback contract;
- принятие UX без пользователя;
- автоматическое превращение исследовательской гипотезы в requirement.

## 3. Четыре уровня рабочего цикла

### Level 0 — factual preflight

До branch/PR:

- проверить current main и открытые PR;
- прочитать canonical docs;
- изучить фактический код затрагиваемого контура;
- определить domain, UX и data boundaries;
- классифицировать риск;
- сформулировать первый вертикальный slice.

Результат — `READY TO IMPLEMENT` либо доказанный blocker. Большой повторный аудит запрещён, если факты уже зафиксированы и не изменились.

### Level 1 — быстрый repair loop

Для presentation-only изменений в существующем PR:

```text
working-tree repair
→ diff/path validation
→ focused source-contract tests
→ `scripts/vps_candidate.sh verify [focused_test_label ...]`
→ VPS-local candidate health/browser evidence
→ пользовательская проверка
→ repeat без промежуточного commit/push
```

VPS-local candidate запускается прямо из текущего repository working tree через `scripts/vps_candidate.sh`. Он использует cached hashed browser/runtime venv, отдельную SQLite и временный localhost `127.0.0.1:18766`; GitHub SHA, Docker и root для обычного repair-loop не требуются.

Полный PostgreSQL suite, container/trusted delivery и GitHub workflows не запускаются после каждого малого visual repair.

### Level 2 — candidate profile

Когда delivery slice готов к связной проверке:

- профильные Django tests;
- Ruff/compile/check;
- migration check по применимости;
- container smoke;
- VPS-local candidate из текущего working tree;
- ready push только после локальной проверки и acceptance;
- acceptance route;
- автоматически сформированный evidence summary.

Candidate profile применяется после содержательного среза, а не после каждой правки отступа.

### Level 3 — final gate

Один раз на окончательном accepted head перед merge:

- полный актуальный PostgreSQL suite;
- все required exact-head workflows;
- container preview smoke;
- migrations and data boundary;
- trusted development delivery;
- desktop/mobile functional and visual acceptance;
- exact head re-check;
- merge только после отдельной команды пользователя.

Новый commit после final gate делает gate устаревшим.

## 4. Профили риска

| Профиль | Примеры | До пользовательской проверки | Перед merge |
|---|---|---|---|
| `DOCS` | canonical docs, research mapping | documentation checks | documentation gate |
| `PRESENTATION` | templates, CSS, JS без domain logic | focused tests + VPS-local candidate | final full gate один раз после ready push |
| `APP_LOGIC` | views, forms, services без schema | profile tests + VPS-local candidate | PostgreSQL/exact-head/trusted full gate после ready push |
| `SCHEMA_DATA` | models, migrations, seed/import | PostgreSQL migrations + focused/full tests | full gate + backup/rollback evidence |
| `SECURITY_INFRA` | controller, workflows, secrets boundary, Compose | профильный security/infra gate | полный профильный gate и controlled runtime evidence |

Изменение классифицируется по максимальному фактическому риску, а не по названию work item.

## 5. Немедленно действующие ускорители

### 5.1. Один work item — один PR — весь repair cycle

Не создаются новые PR для:

- visual repair;
- повторной пользовательской проверки;
- CSS cleanup;
- уточнения компонентов;
- исправления CI на том же head family.

Новый work item нужен только при отдельной цели или risk boundary.

### 5.2. Один полный suite на final head

Полный suite не повторяется на GitHub и VPS без доказанной необходимости.

Целевая модель:

```text
VPS working-tree focused/profile checks
→ VPS-local candidate + browser acceptance
→ PostgreSQL checks для final candidate по риску
→ ready push готового состояния
→ один GitHub exact-head final gate
→ trusted final verification того же exact head
```

Повтор полного suite на VPS допускается для:

- изменений test/runtime environment;
- PostgreSQL-specific диагностики;
- migration/data-risk;
- недоверенного или отличающегося build artifact;
- явно доказанной потребности.

### 5.3. Автоматический evidence summary

Каждый candidate deployment должен собирать в один PR comment:

- PR и exact head;
- изменённые risk paths;
- выбранный profile;
- workflow run IDs и conclusions;
- количество тестов;
- migrations result;
- container/HTTP health;
- deployed SHA;
- rollback result;
- database operations;
- preview state;
- automatic merge state;
- acceptance URL и короткий маршрут проверки.

Пользователь не должен собирать эти данные по нескольким workflow.

### 5.4. Диагностика только при ошибке

Логи и artifacts сохраняются:

- при падении;
- при controlled rollback;
- при mismatch exact SHA;
- при flaky retry.

Успешный цикл возвращает компактный summary, а не многомегабайтный обязательный artifact.

### 5.5. Отмена устаревших запусков

Для нового commit в том же PR:

- queued/running non-final workflows старого head отменяются по concurrency group;
- final/deployment transaction не прерывается после перехода security boundary без controlled cancellation;
- пользователь не ждёт заведомо устаревший результат.

## 6. Ближайшие executable оптимизации

Они выполняются отдельным небольшим work item после завершения активного OPJ-UX-001, чтобы не занимать development во время приёмки.

### CI-OPT-001 — убрать доказанное дублирование

Цель:

- full PostgreSQL suite один раз на exact final head;
- VPS deployment выполняет migrations/check/collectstatic/runtime smoke вместо повторного полного suite;
- path/risk profile выбирается явно;
- required checks не ослабляются;
- PR summary показывает, какая проверка была источником доверия.

Обязательное условие: deployment использует тот же exact SHA и доказанно эквивалентное окружение.

### DEV-EVIDENCE-001 — единый отчёт кандидата

Автоматизировать создание и обновление одного machine-owned PR comment с technical evidence и acceptance route.

### UI-CONTRACT-001 — автоматическая проверка общего UX layer

Первый минимальный вариант:

- component/contract fixture page или детерминированный набор реальных routes;
- desktop и mobile viewport matrix;
- проверка загрузки shared assets;
- smoke interactions для sidebar, tabs, fields, status chips, selectors, pickers и overlays;
- screenshot artifacts для review, без хрупкого pixel-perfect blocker на первом этапе;
- source-contract test, запрещающий создание второго самостоятельного system layer.

Pixel-diff становится blocking только после стабилизации эталонов и доказательства низкой flaky rate.

### WORKITEM-BOOTSTRAP-001 — стандартный старт work item

Автоматически формировать из короткого machine-readable manifest:

- issue body;
- branch name;
- Draft PR body;
- acceptance checklist;
- risk profile;
- ожидаемые test groups;
- protected boundaries;
- evidence comment skeleton.

Manifest не генерирует domain requirements и не заменяет factual audit.

## 7. Дополнительные оптимизации по фактической выгоде

Вводятся только после измерения текущего bottleneck:

- pip/cache and Docker layer cache;
- разделение медленных test groups;
- parallel test execution;
- reuse prebuilt exact-SHA development image;
- deterministic scenario-specific presentation seed;
- browser smoke via Playwright;
- automatic changed-path test selection;
- flaky-test quarantine с обязательным owner и сроком исправления;
- automated source-contract check для shared UI primitives.

Не внедрять sharding, сложный build registry или preview-per-PR только потому, что они типичны для крупных проектов.

## 8. Метрики

После каждого значимого PR фиксируются:

- `commit_to_acceptance_url_minutes`;
- число full suite runs на accepted PR;
- GitHub CI minutes;
- VPS deployment minutes;
- число ручных команд пользователя;
- число repair cycles;
- время root-cause diagnosis;
- flaky retries;
- rollback count;
- UI consistency defects, найденные до пользовательской приёмки;
- accepted head changes after final gate.

Целевые ориентиры:

```text
ручные команды пользователя: 0
full suite до final head: 0 или только по доказанному риску
full suite на final head: 1 доверенный источник
visual micro-repair → acceptance URL: минуты, не десятки минут
automatic merge: 0
preview writes from product PR: 0
```

## 9. Приоритет внедрения

```text
NOW:
canonical product/UX contract
+ tiered process contract
+ использование `scripts/vps_candidate.sh` как VPS-local candidate до ready push

AFTER OPJ-UX-001:
CI-OPT-001
→ DEV-EVIDENCE-001
→ UI-CONTRACT-001

ONLY IF METRICS JUSTIFY:
advanced caching/sharding
→ reusable exact-SHA image
→ broader browser automation
```

Скорость достигается удалением повторной работы и ранним обнаружением расхождений, а не снижением качества final gate.
