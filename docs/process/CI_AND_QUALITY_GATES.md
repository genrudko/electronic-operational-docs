# ЭОД — CI и quality gates

## Цель

Автоматические gates должны обнаруживать технические и governance-дефекты до
пользовательской приёмки и не создавать ложного ощущения готовности.

## Базовый CI

Текущий основной pipeline использует Ubuntu 24.04, Python 3.13 и PostgreSQL
18.4. Применимые проверки:

- dependency installation;
- Ruff;
- compileall;
- Django system check;
- `makemigrations --check --dry-run`;
- PostgreSQL migrations;
- актуальный профильный architecture gate;
- collectstatic;
- полный текущий Django test suite;
- clean checkout verification.

## Development stack smoke

Отдельный workflow проверяет shell syntax, Compose config, image build, startup,
health, database identity `eod_development`, bind приложения только на
`127.0.0.1:8766`, отсутствие опубликованного PostgreSQL port и teardown.

## Documentation Contract

Documentation Contract является постоянным fail-closed gate. Он проверяет:

### Базовую целостность

- наличие обязательных документов и непустых canonical files;
- корректность относительных Markdown links;
- наличие PR template и `AGENTS.md`;
- отсутствие tracked secret-like files;
- navigation-only характер `CURRENT_HANDOFF.md`.

### Единственных владельцев

- `CURRENT_STATE.md` — accepted main, active work item/issue/PR/branch,
  runtime/Preview;
- `DEMO_RELEASE_PLAN.yaml` — release/module/capability/work-item planning status;
- `INDUSTRIALIZATION_PROGRAM.yaml` — неизменяемое определение фаз, зависимостей,
  risk treatment и gates;
- derived Markdown views не могут объявлять owner-style volatile fields.

### Planning/program consistency

- уникальность module/work-item IDs;
- существование module/work-item/dependency references;
- существование каждого risk-register `proposed_work_item`;
- отсутствие обычной зависимости от более поздней фазы;
- существование обязательных элементов gates;
- прямая и транзитивная замкнутость
  `PILOT-READY.required_core_work_items`;
- отсутствие скрытых scope-dependent dependencies mandatory core;
- accepted evidence, module status и work-item status не расходятся;
- accepted work items отсутствуют в execution queue;
- текущий active work item из `CURRENT_STATE.md` имеет planning status
  `IN_PROGRESS`.

### Exact derived projections

Следующие файлы воспроизводимо генерируются и сравниваются побайтно:

- `docs/product/MODULE_MAP.md`;
- `docs/product/IMPLEMENTATION_SEQUENCE.md`;
- `docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md`;
- `docs/project/INDUSTRIALIZATION_PROGRAM.md`.

Любое ручное расхождение считается stale derived view и блокирует gate.

### Fail-closed fixtures

`tests/process/fixtures/documentation_state_contract.json` содержит positive
baseline и negative cases:

- missing work-item reference;
- duplicate work-item ID;
- dependency on absent work item;
- mandatory-core dependency outside mandatory core;
- hidden dependency on scope-dependent work item;
- reverse interphase dependency;
- missing gate work item;
- stale accepted status;
- duplicate volatile owner;
- Markdown/YAML projection mismatch;
- stale derived view.

Каждая ошибка обязана сообщать file, identifier, rule, expected и actual.

## Риск-ориентированный выбор gates

| Изменение | Обязательные дополнительные gates |
|---|---|
| Models/migrations | migration plan, clean DB migrate, PostgreSQL data checks |
| Numbering/concurrency | TransactionTestCase/PostgreSQL locking tests |
| Imports | raw/normalized/conflict/idempotency/publication tests |
| Auth/rights | permission matrix, denial paths, audit |
| Document registration | immutability, snapshot, integrity and numbering |
| UI/editor | browser acceptance and regression checklist |
| Docker/settings | container smoke, private ports, secret separation |
| Data reset | backup, restore, counts, demo auth, preview isolation |
| Documentation/governance | Documentation Contract, positive/negative fixtures, exact projections |

## Исторические gates

`gate_patch_*.py` отражают контракт конкретного исторического baseline. Они не
образуют автоматически кумулятивный набор. В постоянный CI включается актуальный
architecture/documentation gate, а старые сохраняются для истории и targeted
diagnosis.

## Test discovery and evidence

- ноль tests — failure;
- число tests ниже явно установленного minimum — failure;
- skipped tests перечисляются и оцениваются;
- parallel runner не должен скрывать traceback;
- SQLite-only success не доказывает PostgreSQL behavior.

Для каждого run фиксируются workflow name, run ID, exact commit SHA,
status/conclusion, relevant failures и artifacts.

## Failure discipline

При failure нельзя объявлять change технически готовым. Требуется установить
root cause, сделать repair commit, получить новые exact-head checks и повторить
применимые runtime/acceptance gates. Любой новый commit аннулирует прежнее
exact-head evidence.

## CI не заменяет

- нормативное исследование;
- предметную проверку формы;
- оценку UX;
- presentation scenario;
- разрешение merge;
- post-merge preview gate.
