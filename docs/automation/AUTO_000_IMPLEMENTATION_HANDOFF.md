# AUTO-000 → AUTO-001 implementation handoff

## Условие использования

Этот handoff становится рабочим только после пользовательской приёмки и merge AUTO-000.

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
→ evidence in GitHub
```

## Запреты

- automatic merge;
- arbitrary root shell;
- Docker socket for untrusted runner;
- workflow execution from modified PR context with secrets;
- preview write;
- Git commits from VPS;
- secrets in repository or chat;
- Base64/self-applying bootstrap.

## Exit gate

- two successful deployments;
- one negative case;
- exact-SHA and superseded proof;
- preview isolation;
- no manual VPS commands in normal cycle;
- user acceptance.
