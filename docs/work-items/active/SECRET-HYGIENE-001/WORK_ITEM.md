# SECRET-HYGIENE-001

## Статус

`ACCEPTED / MERGED`.

```text
issue: #54 / CLOSED / COMPLETED
PR: #56 / CLOSED / MERGED
accepted exact head: cd7dc07a9c77a71a5b1166aa7a57ee4d3afa93da
merge commit: 95b8dd6017745886f110f052ea0950b3d48173d8
user acceptance: PASSED
merge method: ORDINARY MERGE COMMIT
squash / rebase: NOT USED
```

Runtime и Preview state принадлежат только `docs/project/CURRENT_STATE.md` и
здесь не дублируются.

## Цель

Закрыть риск `PSR-021`: исключить активные или повторно используемые credentials
из репозитория, CI logs, workflow summaries, artifacts и demo/runtime bootstrap,
сохранив воспроизводимый development/demo workflow без ручной публикации
секретов.

## Принятый contract

### Demo/development access

- supported password поступает только через local-only
  `EOD_DEMO_USER_PASSWORD`;
- значение отсутствует в Git и не публикуется в workflow output;
- при отсутствии обязательной injection demo accounts получают unusable
  password или bootstrap завершается fail closed;
- ранее опубликованный reusable credential считается скомпрометированным и
  блокируется без хранения plaintext;
- blind rotation VPS или внешних систем не выполняется без доказательства, что
  конкретное значение там фактически используется.

### Canonical scanner

Единственный canonical engine:

```text
scripts/secret_hygiene.py
```

Он владеет:

- tracked repository scan;
- Python AST assignment/keyword classification;
- bounded history inventory;
- redaction;
- post-redaction verification;
- demo-bootstrap validation;
- exact allowlist validation;
- fail-closed clean-tree verification.

Удалённые дублирующие реализации не являются частью принятого baseline:

```text
scripts/secret_hygiene_scan.py
scripts/secret_hygiene_keyword_scan.py
```

### Fail-closed правила

- test/fixture paths, class names и подстроки не дают исключений;
- fixture-каталоги сканируются как обычный tracked repository content;
- process-local generated values заменяют tracked reusable test credentials;
- allowlist требует exact path, rule, finding identifier, rationale, owner и
  expiry; wildcard и stale entries блокируются;
- raw diagnostic transport находится только в `$RUNNER_TEMP`;
- публикация разрешена только после цепочки
  `raw -> redact -> verify-sanitized -> log/summary/artifact`;
- artifact upload требует отдельного `verified=true`;
- cleanup завершается фактической проверкой `git status --porcelain`.

## Exact-head evidence

Все обязательные workflows завершились успешно на
`cd7dc07a9c77a71a5b1166aa7a57ee4d3afa93da`:

```text
EOD CI:                      31078274329 / SUCCESS
AUTO-001A Foundation CI:     31078274333 / SUCCESS
AUTO-001B Controller CI:     31078274321 / SUCCESS
EOD Documentation Contract: 31078274328 / SUCCESS
EOD Development Stack:      31078274307 / SUCCESS
EOD Secret Hygiene:          31078274346 / SUCCESS
```

Финальные проверки:

```text
full Django suite:                   720 tests / OK
focused secret-hygiene regressions: 17 / OK
tracked scan:                       854 files / 0 findings
allowlist entries:                  0
clean tree:                         CLEAN_TREE=PASS porcelain_entries=0
bounded history:                    250 commits / 18 unique findings
```

History inventory breakdown:

- `credential-output`: 1;
- `explicit-credential-assignment`: 10;
- `reusable-demo-credential`: 2;
- `secret-bearing-dsn`: 5.

AUTO-001A retained verified-sanitised artifact содержит `24 tests / OK` и не
содержит private-key marker, token-like value, secret-bearing DSN или credential
assignment matches.

## Граница принятого изменения

Изменены development/demo credential contract, CI, test/deployment tooling,
scanner и test-support fixtures. Не менялись предметные модули, пользовательский
UX, models, migrations, производственные данные и живой Preview.

## Historical limitations

- Git history не переписывалась и force push не выполнялся;
- immutable historical logs/artifacts могут сохранять факт прежней публикации до
  истечения retention или отдельного удаления;
- безопасность обеспечивается invalidation/non-reuse и блокировкой новой утечки,
  а не утверждением об исчезновении истории.

## Последующее состояние

`SECRET-HYGIENE-001` является принятой зависимостью
`DEPENDENCY-PROVENANCE-001`. Принятие этого work item не означает достижения
`SAFE-CONTINUATION`; предметная очередь остаётся paused до отдельного решения
владельца продукта.
