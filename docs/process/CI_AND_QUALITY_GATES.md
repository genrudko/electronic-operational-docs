# ЭОД — CI и quality gates

## Цель

Автоматические gates должны обнаруживать технические дефекты до пользовательской приёмки и не создавать ложного ощущения готовности.

## Базовый CI

Текущий основной pipeline использует:

- Ubuntu 24.04;
- Python 3.13;
- PostgreSQL 18.4.

Применимые проверки:

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

Отдельный workflow проверяет:

- shell syntax;
- Compose config;
- image build;
- startup and health;
- database identity `eod_development`;
- application bind only to `127.0.0.1:8766`;
- absence of published PostgreSQL port;
- teardown.

## Documentation contract

DOCS-001 добавляет отдельный gate:

- наличие обязательных документов;
- отсутствие пустых canonical files;
- корректность относительных Markdown links;
- одинаковый accepted baseline в current state, handoff and baseline history;
- отсутствие запрещённых legacy workflow assertions в canonical files;
- наличие PR template and AGENTS;
- отсутствие secrets-like files among tracked paths.

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
| Documentation | documentation contract and manual content review |

## Исторические gates

`gate_patch_*.py` отражают контракт конкретного исторического baseline. Они не образуют автоматически кумулятивный набор. В постоянный CI включается актуальный architecture gate, а старые сохраняются для истории и targeted diagnosis.

## Test discovery

- ноль tests — failure;
- число tests ниже явно установленного minimum — failure;
- skipped tests перечисляются и оцениваются;
- parallel runner не должен скрывать traceback;
- SQLite-only success не доказывает PostgreSQL behavior для транзакций и Unicode/locking differences.

## Evidence

Для каждого run фиксируются:

- workflow name;
- run ID;
- exact commit SHA;
- status/conclusion;
- relevant job/step failures;
- artifacts, если есть.

## Failure

При failure:

1. не объявлять change технически готовым;
2. получить logs/steps;
3. установить root cause;
4. создать repair commit;
5. дождаться повторного CI на новом head;
6. повторить VPS deployment and acceptance.

## CI не заменяет

- нормативное исследование;
- предметную проверку формы;
- оценку UX;
- проверку presentation scenario;
- разрешение merge;
- post-merge preview gate.