# AUTO-001 — модель безопасности

## 1. Активы

- private GitHub repository и история;
- GitHub Actions secrets;
- deploy credential;
- VPS host;
- accepted preview;
- development checkout и database;
- backups;
- sanitised evidence;
- presentation data.

## 2. Trust boundaries

```text
ChatGPT / GitHub API
→ private repository and PR
→ trusted GitHub workflow from main
→ GitHub-hosted runner
→ restricted authenticated gateway
→ development-only orchestrator
```

Accepted preview является отдельной защищённой границей.

## 3. Запрещённая архитектура

Не используется обычный self-hosted runner на VPS, который одновременно:

- запускает PR code;
- имеет `sudo`;
- имеет Docker socket;
- видит development или preview secrets.

Такой runner фактически предоставляет PR root-equivalent доступ к VPS.

## 4. Предпочтительная архитектура

```text
GitHub-hosted runner
→ отдельный deploy credential
→ forced command / fixed gateway
→ allowlisted development operations
```

Gateway не предоставляет interactive shell.

## 5. GitHub permissions

Минимальный предполагаемый набор:

- `contents: read`;
- `pull-requests: write` только для status/comment/labels;
- `checks/actions: read`;
- `deployments: write`, только если используется GitHub Environment.

Запрещены:

- `contents: write`;
- `workflows: write`;
- repository administration;
- secrets management;
- merge permission для automation token.

## 6. Gateway requirements

Gateway обязан:

- использовать fixed absolute paths;
- очищать неподтверждённое environment;
- валидировать exact repository;
- валидировать PR number;
- валидировать 40-hex SHA;
- разрешать только `refresh` или `rebuild`;
- не использовать `eval`;
- отклонять неизвестные arguments;
- иметь timeout;
- устанавливать безопасный `PATH` и `umask`;
- писать audit record;
- редактировать secrets из stdout/stderr.

## 7. OS privilege model

Отдельный account `eod-deploy` или эквивалент:

- не имеет интерактивного login;
- не имеет общего `sudo`;
- может вызвать только gateway;
- не читает preview secrets;
- не меняет system users, SSH config или GitHub.

Root-owned orchestrator получает только права, необходимые для development checkout, development Compose и development env.

## 8. Preview isolation

До и после запуска фиксируются:

- preview branch и HEAD;
- preview health;
- preview database identity;
- container state.

Предпочтительно технически исключить write-доступ orchestrator к preview paths и credentials. Post-check не заменяет минимальные права.

## 9. Главные угрозы

| Угроза | Обязательная защита |
|---|---|
| workflow tampering | исполнять trusted workflow из `main` |
| command injection | strict parser и allowlist |
| SHA substitution | end-to-end exact-SHA verification |
| concurrent branch switch | GitHub + VPS lock |
| secret leakage | redaction, no `set -x`, marker test |
| preview modification | separate permissions and before/after proof |
| fork PR secret access | same-repository restriction |
| stale result | `SUPERSEDED` on head change |
| failed migration/state | stop and documented recovery |
| stolen key | separate credential, rotation and revoke procedure |

## 10. Audit

Каждый run фиксирует:

- timestamp;
- actor;
- GitHub run ID;
- PR;
- requested and deployed SHA;
- profile;
- gateway credential fingerprint;
- exit state;
- preview before/after;
- artifact checksum.

## 11. Incident conditions

- preview state изменился;
- deployed SHA не совпал;
- development database identity неверна;
- secret marker найден в логах;
- gateway принял неизвестный argument;
- обнаружена попытка interactive shell;
- lock обойдён;
- использован неизвестный deploy credential.

При incident automation останавливается и не выполняет автоматический repair.
