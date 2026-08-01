# PROCESS-HARDENING — быстрый и проверяемый рабочий контур

**Статус:** IMPLEMENTED
**Дата:** 01.08.2026
**Решение Chat 0:** после завершения PR #30 разрешён один контролируемый direct-to-main hardening-пакет без product/runtime/schema change.

## 1. Причина

PR #30 доказал четыре системных потери времени:

1. Малый CSS repair многократно запускал полный suite и широкую browser matrix.
2. Допустимый deployment-механизм определялся слишком поздно — после CI.
3. Наличие deployment label ошибочно принималось за факт нового trigger/run.
4. Статус сообщался до проверки правильного workflow, exact job и `LIVE_SHA`.

PROCESS-HARDENING не ослабляет final gate. Он переносит классификацию риска и выбор проверки **до публикации**, а полный gate оставляет один раз на окончательном accepted head.

## 2. Два независимых измерения

### 2.1. Change class

| Класс | Назначение | Типичный объём |
|---|---|---|
| `MICRO` | локальный обратимый repair | до 3 файлов, один низкий профиль риска, без rename/delete |
| `STANDARD` | обычный implementation slice | несколько связанных файлов и профильные проверки |
| `SYSTEM` | schema/data/security/infra либо широкий diff | отдельный rollback/failure-mode review |

### 2.2. Risk profile

Сохраняются канонические профили:

- `DOCS`;
- `PRESENTATION`;
- `APP_LOGIC`;
- `SCHEMA_DATA`;
- `SECURITY_INFRA`.

Change class отвечает на вопрос **«насколько велик и обратим diff»**.
Risk profile отвечает на вопрос **«какой максимальный риск затронут»**.

## 3. Исполняемый preflight

Скрипт:

```text
scripts/automation/work_item_preflight.py
```

Принимает JSON manifest и до публикации определяет:

- canonical base/head SHA;
- changed paths и статусы;
- выход за allowed/forbidden boundary;
- direct-to-main boundary;
- change class;
- максимальный risk profile;
- быстрые, candidate и final checks;
- `NONE / HOT_REFRESH / FULL_DEVELOPMENT`;
- targeted либо full browser evidence;
- retry и timeout policy;
- стабильный Markdown handoff для Codex/нового чата.

Пример:

```bash
python -m scripts.automation.work_item_preflight classify \
  --manifest /tmp/work-item.json \
  --json-out /tmp/preflight.json \
  --markdown-out /tmp/preflight.md \
  --handoff-out /tmp/handoff.md
```

Self-test:

```bash
python -m scripts.automation.work_item_preflight self-test
```

## 4. Manifest contract

Минимальный manifest:

```json
{
  "repository": "genrudko/electronic-operational-docs",
  "base_sha": "0123456789abcdef0123456789abcdef01234567",
  "head_sha": null,
  "purpose": "Исправить контраст одного status chip",
  "mode": "pull_request",
  "final_candidate": false,
  "changed_files": [
    {
      "path": "src/static/system/theme.css",
      "status": "modified"
    }
  ],
  "allowed_paths": [
    "src/static/**"
  ],
  "forbidden_paths": [
    ".github/**",
    "deploy/**",
    "src/**/migrations/**"
  ],
  "acceptance": [
    "Статус читаем в dark theme",
    "Светлая тема и print не изменены"
  ]
}
```

Для direct-to-main non-doc change требуется явное исключение:

```json
{
  "direct_main_exception": {
    "id": "CHAT0-PROCESS-HARDENING-2026-08-01",
    "allowed_prefixes": [
      "scripts/automation/",
      "tests/process/",
      "docs/process/"
    ]
  }
}
```

Исключение не является общей отменой branch/PR policy.

## 5. Publication protocol

Скрипт:

```text
scripts/automation/atomic_github_publish.py
```

Публикует несколько локально подготовленных файлов **одним GitHub commit**:

1. читает live branch ref;
2. сравнивает его с `--expected-head`;
3. получает base tree exact commit;
4. создаёт blobs;
5. создаёт один tree;
6. создаёт один commit с expected head как единственным parent;
7. обновляет ref с `force=false`;
8. повторно проверяет final ref.

При сдвиге branch publication останавливается до создания видимого commit/ref update.

Dry-run:

```bash
python -m scripts.automation.atomic_github_publish publish \
  --repository genrudko/electronic-operational-docs \
  --branch main \
  --expected-head 0123456789abcdef0123456789abcdef01234567 \
  --message "PROCESS: harden publication preflight" \
  --file docs/process/PROCESS_HARDENING.md=/tmp/PROCESS_HARDENING.md \
  --dry-run
```

Реальная публикация читает token только из `GITHUB_TOKEN` либо указанной `--token-env`. Token не выводится в отчёт.

Self-test:

```bash
python -m scripts.automation.atomic_github_publish self-test
```

## 6. Proportional checks

### MICRO / PRESENTATION

```text
diff/path guard
→ CSS/JS/template syntax
→ focused source-contract
→ trusted hot refresh
→ health
→ targeted affected states
→ user feedback
```

Не запускаются после каждого repair:

- полный PostgreSQL suite;
- пять workflow;
- full browser matrix;
- full image rebuild.

Full matrix и final gate выполняются один раз на окончательном accepted head.

### STANDARD

Профильные tests/checks и один candidate delivery. Full gate откладывается до final head.

### SYSTEM

Dedicated security/schema/infra checks, rollback review и controlled evidence. Для product/runtime работы сохраняется отдельный PR.

## 7. Deployment selection

Preflight выбирает delivery до публикации:

| Условие | Delivery |
|---|---|
| docs-only | `NONE` |
| только added/modified `src/templates/**`, `src/static/**` | `HOT_REFRESH` |
| application/schema/infra либо mixed paths | `FULL_DEVELOPMENT` |
| direct-to-main hardening exception | `NONE` |

Hot refresh запрещён при delete, rename, migration, workflow/controller или любом path вне presentation allowlist.

## 8. Browser evidence reuse

- MICRO repair: только затронутые routes/states.
- STANDARD presentation candidate: targeted routes, затем full matrix на final head.
- Shared visual system: full stable matrix один раз перед merge.
- Повтор полной матрицы нужен только после изменения runtime visual files либо самого browser contract.
- CI success не заменяет пользовательскую визуальную приёмку.

## 9. Retry and stall rules

| Этап | Граница |
|---|---|
| preflight | 2 минуты |
| focused checks | 10 минут до stall diagnosis |
| trusted hot refresh | 20 минут |
| trusted full development | 35 минут |

Правила:

1. Code/test failure не перезапускается до извлечения primary cause.
2. Доказанный infrastructure timeout допускает один retry только failed job.
3. Второй одинаковый timeout — blocker.
4. Deployment label всегда сначала снимается, затем устанавливается заново.
5. Наличие label не является evidence запуска.
6. Success объявляется только после exact run/job conclusion и `LIVE_SHA = HEAD_SHA`.
7. Новый commit инвалидирует старые exact-head gates и runtime evidence.

## 10. Stable handoff

Generated handoff всегда содержит:

- repository;
- exact starting SHA;
- current/requested head;
- class/profile;
- allowed/forbidden paths;
- required checks;
- delivery type;
- acceptance;
- обязательный итоговый report;
- запрет необоснованного нового issue/branch/PR;
- запрет success claim без evidence.

Пользователь не переносит задания, patches или GitHub-команды между ChatGPT, Codex и CI.

## 11. Граница hardening-пакета

Этот пакет:

- не меняет application/runtime/schema/data;
- не запускает deployment;
- не меняет preview;
- не вводит automatic merge;
- не меняет required final gate;
- не создаёт новый issue/branch/PR по явному решению Chat 0.

Минимальная проверка пакета:

```text
Python compile
self-test двух scripts
manifest dry-run
optimistic-lock failure self-test
path/protected-boundary self-test
```

После этого проект возвращается к `PROJECT-BASELINE-001`.
