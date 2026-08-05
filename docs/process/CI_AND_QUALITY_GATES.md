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

CI-only PostgreSQL запускается в изолированном job network с `trust` для
одноразового service container, поэтому tracked или повторно используемый пароль
не требуется. Django secret и credentials container smoke генерируются заново в
каждом run, немедленно маскируются и не сохраняются в artifacts или summary.

Raw test, Compose и controller output не публикуется напрямую. Потенциально
credential-bearing вывод сначала записывается во временный файл, проходит
`scripts/secret_hygiene.py redact`, после чего только sanitised result может быть
напечатан, добавлен в summary или сохранён как artifact. Raw temporary files
удаляются независимо от результата проверки.

## Secret Hygiene

`EOD Secret Hygiene` является постоянным fail-closed gate и выполняет:

- AST-aware scan всех tracked text files;
- проверку явных credential assignments;
- обнаружение private-key markers, token-like values и secret-bearing DSN;
- обнаружение reusable demo credentials;
- проверку credential output и shell xtrace около secret-bearing commands;
- проверку workflow summary и artifact leakage;
- exact allowlist contract;
- demo/bootstrap contract;
- bounded report-only inventory последних 250 commits.

Диагностика содержит только:

```text
file; line; safe finding identifier; rule; expected; actual class
```

Полное найденное значение не выводится. Исторический inventory публикует только
глубину, количества по правилам и безопасные identifiers.

Allowlist хранится в `.github/secret-hygiene-allowlist.json` и допускает только
точный путь, точное правило и identifier конкретной находки. Обязательны
rationale, named owner и expiry. Wildcard paths/rules, просроченные, stale и
изменившиеся findings блокируют gate. Наличие разрешения для одного значения не
может скрыть новое значение в том же файле.

Positive/negative fixtures покрывают как минимум:

- committed password;
- bare workflow password;
- token-like value;
- private-key marker;
- database URL с credential;
- reusable demo credential;
- credential output;
- `set -x` около secret-bearing command;
- workflow summary leak;
- artifact leak;
- missing mandatory injection;
- overly broad allowlist;
- safe runtime/generated placeholders;
- sanitised artifact path;
- redaction без раскрытия полного fixture value.

## Development stack smoke

Отдельный workflow проверяет shell syntax, Compose config, image build, startup,
health, database identity `eod_development`, bind приложения только на
`127.0.0.1:8766`, отсутствие опубликованного PostgreSQL port и teardown.

Development/demo access не имеет публичного постоянного пароля. Значение
`EOD_DEMO_USER_PASSWORD` вводится локально, хранится только в root-owned env и не
выводится. При отсутствии injection demo accounts получают unusable password;
ранее опубликованное значение отвергается по SHA-256 без хранения plaintext.

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
- `docs/project/INDUSTRIALIZATION_PROGRAM.md`;
- `docs/project/INDUSTRIALIZATION_EXECUTION_BACKLOG.md`.

Любое ручное расхождение считается stale derived view и блокирует gate.

### Industrial execution contract

Дополнительно проверяются все 30 work items: owner role, evidence requirements,
risk/gate classification, state machine, dependency closure, Phase 0/1 start
policy, parallelization limits, frozen gate membership и residual-risk records.
Mutable execution state читается только из `DEMO_RELEASE_PLAN.yaml`; наличие
`status`/`execution_state` внутри program item считается вторым planning owner.

Residual risk не считается принятым по одному status: обязательны applicability,
роль и named accountable owner, controls, due date, review condition, affected
gate, acceptance authority/status/evidence и expiration/review date.

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
| Secret/bootstrap/logging | Secret Hygiene, injection denial, redaction, summary/artifact scan |
| Documentation/governance | Documentation Contract, positive/negative fixtures, exact projections |

## Исторические gates

`gate_patch_*.py` отражают контракт конкретного исторического baseline. Они не
образуют автоматически кумулятивный набор. В постоянный CI включается актуальный
architecture/documentation gate, а старые сохраняются для истории и targeted
diagnosis. Если исторический gate требует demo authentication, credential
передаётся только через текущий local-only injection contract.

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

Нельзя возвращать gate в зелёное состояние отключением правила, broad allowlist
или исключением крупного каталога. False positive устраняется более точной
семантической классификацией и positive/negative regression fixture.

## CI не заменяет

- нормативное исследование;
- предметную проверку формы;
- оценку UX;
- presentation scenario;
- разрешение merge;
- post-merge preview gate.
