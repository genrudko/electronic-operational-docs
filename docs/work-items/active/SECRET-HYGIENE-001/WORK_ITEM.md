# SECRET-HYGIENE-001

## Статус

`IN_PROGRESS` после открытия issue #54 и отдельного Draft PR. Финальная приёмка и merge требуют отдельной явной команды владельца продукта.

## Цель

Закрыть риск `PSR-021`: исключить активные или повторно используемые credentials из репозитория, CI logs, workflow summaries, artifacts и demo/runtime bootstrap, сохранив воспроизводимый development/demo workflow без ручной публикации секретов.

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
- этот файл задаёт scope и acceptance work item, но не создаёт второго planning-state owner;
- GitHub exact-head evidence сильнее текстовых отчётов.

## Scope

1. Провести доказательный credential inventory в:
   - tracked repository content;
   - Git history в обоснованной глубине;
   - workflows, logs, summaries и artifacts;
   - Docker/Compose env и bootstrap paths;
   - development/demo fixtures, seed commands и operator instructions.
2. Удалить вывод паролей, tokens, secret-bearing DSN и generated credentials из CI/logging paths.
3. Заменить постоянные demo credentials безопасным contract:
   - generated ephemeral credentials, либо
   - explicit local-only injection с masking, либо
   - иной принятый fail-closed механизм без публичного повторно используемого пароля.
4. Зафиксировать rotation/invalidation decision для ранее опубликованных значений и ограничения очистки неизменяемых исторических logs/artifacts.
5. Добавить постоянный secret-hygiene gate и fail-closed fixtures.
6. Обновить operator/development documentation без публикации действующих значений.

## Обязательные проверки

Validator и tests должны обнаруживать как минимум:

- tracked plaintext credential;
- reusable demo password;
- credential, напечатанный в workflow log или summary;
- secret-bearing artifact;
- unmasked generated credential;
- secret-bearing DSN;
- небезопасный fallback/default password;
- чрезмерный или wildcard allowlist;
- allowlist entry без rationale/owner/expiry;
- bootstrap, который продолжает работу без обязательной secret injection;
- stale documentation с опубликованным действующим значением.

Диагностика должна содержать file, identifier, rule, expected и actual, не раскрывая само значение секрета.

## Rotation и historical evidence

- все ранее публично выведенные credentials считаются скомпрометированными;
- запрещено подтверждать безопасность только удалением строки из текущего head;
- должны быть определены rotation/invalidation action, affected environments и limitations;
- immutable GitHub history/logs не переписываются без отдельного решения владельца и доказанной необходимости;
- historical evidence может сохранять факт утечки, но не должно повторно публиковать действующее значение.

## Out of scope

Запрещено в этом work item:

- реализовывать общий threat model `SECURITY-BASELINE-001`;
- выполнять dependency/SBOM/image provenance;
- создавать production deployment profile;
- реализовывать MFA/RBAC/admin hardening;
- реализовывать module activation/registry;
- начинать UX refactor;
- начинать `SHIFT-HANDOVER-001` или другие предметные модули;
- менять модели, migrations или предметные данные без доказанной необходимости для безопасного demo/bootstrap contract;
- трогать пользовательский Preview или VPS без явной runtime-классификации и отдельной необходимости;
- переводить PR в Ready for Review или выполнять merge без отдельной команды владельца.

## Acceptance criteria

- reusable credentials отсутствуют в актуальном repository/CI/artifact контуре;
- ранее опубликованные значения признаны скомпрометированными и не используются повторно;
- demo/development access создаётся безопасно, воспроизводимо и без публикации пароля;
- secret scan и log-leak fixtures fail closed;
- allowlist минимален, поимёнен, обоснован и ограничен сроком;
- все applicable workflows зелёные на final exact head;
- runtime/Preview impact доказательно классифицирован;
- canonical planning state и generated views согласованы;
- PR остаётся Draft до отдельной пользовательской команды.

## Stop condition

После реализации, focused tests и полного exact-head gate остановиться на пользовательской приёмке. Merge не выполнять. `SAFE-CONTINUATION` после этого work item всё ещё не будет достигнут автоматически.