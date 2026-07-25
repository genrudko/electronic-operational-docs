# AUTO-000 → AUTO-001 implementation handoff

## Статус

```text
AUTO-000: accepted and merged
AUTO-000 merge commit: 937d2cd2b187c17fac3088ccfc52079fc4608306
handoff: active
AUTO-001 implementation: not started
```

Этот handoff активирован пользовательской приёмкой и merge AUTO-000. Он используется только как входной контракт отдельного AUTO-001 implementation chat и не является доказательством существующей automation implementation.

## Первый этап нового implementation chat

1. Проверить текущий `main`, exact SHA, open PR and branches.
2. Прочитать `AGENTS.md`, `docs/INDEX.md`, current state/handoff и весь `docs/automation/`.
3. Прочитать actual workflows, compose, development scripts and runbooks.
4. Проверить network route GitHub-hosted runner → VPS.
5. Сформировать gap analysis между AUTO-000 contract и фактической infrastructure.
6. Не писать workflow/gateway до завершения gap analysis.

## Цель AUTO-001

```text
current PR head
→ green required checks
→ restricted gateway
→ exact-SHA deployment to /srv/eod/development
→ explicit refresh/rebuild
→ check
→ full test apps
→ status
→ preview isolation proof
→ sanitised evidence in GitHub
```

## Запреты

- automatic merge;
- arbitrary root shell;
- ordinary self-hosted runner with sudo and Docker socket;
- Docker socket for untrusted runner;
- workflow execution from modified/untrusted PR context with VPS secrets;
- preview write;
- Git commits from VPS;
- secrets in repository or chat;
- Base64 payloads;
- temporary part-files;
- self-applying GitHub Actions workflows;
- autonomous code repair.

## Exit gate

- two successful deployments;
- one intentional negative case;
- exact-SHA and superseded proof;
- preview isolation;
- no manual VPS commands in normal cycle;
- explicit user acceptance.

После exit gate AUTO-001 merge всё равно выполняется только по отдельной явной команде пользователя. Затем работа возвращается в постоянный Chat 0 и далее к PLAN-001.
