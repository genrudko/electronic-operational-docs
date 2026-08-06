# SECRET-HYGIENE-001

## Статус

`IN_PROGRESS` в issue #54, ветке `security/secret-hygiene-001` и Draft PR #56.
Финальная пользовательская приёмка и merge требуют отдельной явной команды
владельца продукта.

## Цель

Закрыть риск `PSR-021`: исключить активные или повторно используемые credentials
из репозитория, CI logs, workflow summaries, artifacts и demo/runtime bootstrap,
сохранив воспроизводимый development/demo workflow без ручной публикации
секретов.

## Основание

- `PROJECT-SUSTAINABILITY-001` — ACCEPTED / MERGED;
- `PROJECT-STATE-RECONCILIATION-001` — ACCEPTED / MERGED;
- `INDUSTRIALIZATION-PROGRAM-EXECUTION-001` — ACCEPTED / MERGED;
- Phase 0 — COMPLETE;
- `PSR-021` — HIGH;
- обязательный элемент `SAFE-CONTINUATION` и `PILOT-READY`;
- зависимость `DEPENDENCY-PROVENANCE-001`.

## Canonical ownership

- `docs/project/CURRENT_STATE.md` владеет volatile active state;
- `docs/project/DEMO_RELEASE_PLAN.yaml` владеет mutable status и acceptance evidence;
- `docs/project/INDUSTRIALIZATION_PROGRAM.yaml` владеет phase/dependency/risk/gate contract;
- этот файл задаёт scope, implementation contract и acceptance work item, но не
  создаёт второго planning-state owner;
- GitHub exact-head evidence сильнее текстовых отчётов.

## Scope

1. Провести доказательный credential inventory в:
   - tracked repository content;
   - Git history в обоснованной глубине;
   - workflows, logs, summaries и artifacts;
   - Docker/Compose env и bootstrap paths;
   - development/demo fixtures, seed commands и operator instructions.
2. Удалить вывод паролей, tokens, secret-bearing DSN и generated credentials из
   CI/logging paths.
3. Заменить постоянные demo credentials безопасным fail-closed contract.
4. Зафиксировать rotation/invalidation decision для ранее опубликованных
   значений и ограничения очистки неизменяемых исторических logs/artifacts.
5. Добавить постоянный secret-hygiene gate и fail-closed fixtures.
6. Обновить operator/development documentation без публикации действующих
   значений.

## Реализованный contract

### Demo/development access

- единственный supported вход — local-only `EOD_DEMO_USER_PASSWORD`;
- значение отсутствует в Git и вводится локально через скрытый prompt;
- локальное значение хранится только в root-owned env;
- при отсутствии injection demo accounts получают unusable password;
- обязательный bootstrap завершается понятным fail-closed отказом;
- ранее опубликованный reusable credential считается скомпрометированным и
  блокируется сравнением SHA-256 без хранения plaintext;
- seed/reset и historical gates используют только injected value и не выводят
  его;
- usernames могут оставаться демонстрационными идентификаторами, но не образуют
  пригодную credential pair без локального секрета.

### CI и diagnostics

- CI Django key и применимые container credentials генерируются заново для
  каждого run и немедленно маскируются;
- isolated PostgreSQL test service не требует tracked reusable password;
- raw Django/Compose/VPS-controller output записывается только во временный файл;
- перед log, summary или artifact применяется обязательная redaction;
- raw temporary output удаляется независимо от результата;
- trusted full-development controller и hot-refresh не публикуют raw SSH output;
- private key bootstrap instruction не предлагает печатать key value.

### Permanent gate

- blocking workflow: `.github/workflows/secret-hygiene.yml`;
- tracked-content scanner: `scripts/secret_hygiene_scan.py`;
- redaction/bootstrap/allowlist contract: `scripts/secret_hygiene.py`;
- сканируются все tracked text files, workflows, Compose/env templates,
  bootstrap/seed paths, tests и документация;
- bounded history inventory проверяет последние 250 commits report-only;
- diagnostics содержат file, line, safe identifier, rule, expected и actual
  class, но не найденное значение;
- текущий allowlist пуст;
- wildcard/path-wide исключения запрещены;
- exact exception требует path, rule, finding identifier, rationale, named owner
  и expiry; изменившееся или stale значение снова блокирует gate.

## Inventory classification

Текущий work item различает:

- подтверждённый активный секрет;
- ранее опубликованный и недоверенный credential;
- безопасный placeholder/runtime expression;
- специально именованный test fixture;
- false positive с regression fixture и семантическим rationale.

В актуальном tracked head активные/reusable credentials отсутствуют. Исторический
bounded inventory сохраняет только количества и безопасные identifiers. Найденные
значения не копируются в этот файл, PR body, issue, commit messages или отчёты.

## Rotation и historical evidence

- ранее опубликованный reusable demo credential признан скомпрометированным;
- повторное использование блокируется application policy;
- существующие demo account hashes инвалидируются при отсутствии новой injection;
- tracked bootstrap/reset/gate paths больше не используют прежнее значение;
- blind rotation внешних систем или действующего VPS не выполнялась: work item не
  доказал наличие этого значения во внешней credential store;
- Git history не переписывается, force push не выполняется;
- уже существующие immutable GitHub logs/artifacts могут физически сохранять
  исторический факт публикации до истечения retention или ручного удаления;
- безопасность обеспечивается invalidation/non-reuse и отсутствием действующего
  значения в текущем execution contour, а не утверждением, что история исчезла.

## Fixtures

Positive/negative coverage включает:

- committed password;
- bare workflow password;
- token-like value;
- private-key marker;
- secret-bearing database URL;
- reusable demo credential;
- password printed by shell;
- secret exposed through `set -x`;
- workflow summary leak;
- artifact leak;
- missing mandatory injection;
- overly broad allowlist;
- exact allowlist, который не скрывает изменившееся значение;
- safe runtime/generated placeholders;
- named test fixture;
- sanitised artifact path;
- отсутствие полного fixture secret в diagnostics и redacted output.

## Runtime impact

`DEVELOPMENT`:

- изменён development/demo bootstrap и local credential-injection contract;
- действующий VPS автоматически не изменялся;
- Preview не разворачивался, не обновлялся и не сбрасывался;
- product/domain modules, UX, models, migrations и предметные данные не
  изменялись.

## Out of scope

Запрещено в этом work item:

- реализовывать общий threat model `SECURITY-BASELINE-001`;
- выполнять dependency/SBOM/image provenance;
- создавать production deployment profile;
- реализовывать MFA/RBAC/admin hardening;
- реализовывать module activation/registry;
- начинать UX refactor;
- начинать `SHIFT-HANDOVER-001` или другие предметные модули;
- менять models, migrations или предметные данные;
- трогать пользовательский Preview;
- переводить PR в Ready for Review или выполнять merge без отдельной команды
  владельца.

## Acceptance criteria

- reusable credentials отсутствуют в актуальном repository/CI/artifact контуре;
- ранее опубликованные значения признаны скомпрометированными и не используются
  повторно;
- demo/development access создаётся безопасно, воспроизводимо и без публикации
  пароля;
- secret scan и log-leak fixtures fail closed;
- allowlist минимален, поимёнен и не скрывает новое значение;
- все applicable workflows зелёные на final exact head;
- logs, summaries и retained artifacts финального кандидата не раскрывают test
  credentials;
- runtime/Preview impact доказательно классифицирован;
- canonical planning state и generated views согласованы;
- PR остаётся Draft до отдельной пользовательской команды.

## Stop condition

После реализации, focused tests и полного exact-head gate остановиться на
пользовательской приёмке. Merge не выполнять. `SAFE-CONTINUATION` после этого
work item всё ещё не будет достигнут автоматически.
