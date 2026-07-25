# AUTO-001 — модель безопасности

## 1. Активы

- private GitHub repository и история;
- GitHub Actions credentials and permissions;
- deploy credential;
- VPS host;
- accepted preview;
- development checkout, containers and database;
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
→ development containers running current PR code
```

Accepted preview является отдельной защищённой границей.

Код текущего PR до пользовательской приёмки считается недоверенным относительно VPS host и accepted preview, даже если branch находится в том же private repository. Он может выполняться только внутри development-контейнеров с минимальным development runtime environment.

## 3. Запрещённая архитектура

Не используется обычный self-hosted runner на VPS, который одновременно:

- запускает PR code;
- имеет `sudo`;
- имеет Docker socket;
- видит development или preview secrets.

Такой runner фактически предоставляет PR root-equivalent доступ к VPS.

Также запрещено передавать PR-коду:

- preview credentials;
- host SSH keys;
- Docker socket;
- privileged container mode;
- writable mounts к preview checkout, preview data или host configuration;
- repository write token;
- merge-capable automation credential.

## 4. Предпочтительная архитектура

```text
GitHub-hosted runner
→ отдельный deploy credential
→ forced command / fixed gateway
→ allowlisted development operations
→ isolated development containers
```

Gateway не предоставляет interactive shell. GitHub-hosted runner не получает Docker socket или произвольный shell на VPS.

## 5. GitHub permissions

Permissions выбираются по фактическому reporting mechanism и фиксируются в implementation PR.

Базовый минимум:

- `contents: read`;
- `pull-requests: read`;
- `actions: read` для проверки required runs;
- `checks: write` только если создаётся отдельный check run;
- `issues: write` только если automation обновляет один PR conversation comment или automation labels;
- `deployments: write` только если используется GitHub Environment.

Не следует выдавать `pull-requests: write` только ради комментария или labels, если достаточно `issues: write`/`checks: write`.

Запрещены:

- `contents: write`;
- `workflows: write`;
- repository administration;
- secrets management;
- merge-capable credential;
- approval/review submission от имени automation.

Если выбранный GitHub permission технически позволяет merge, reporting должен быть перенесён на отдельный credential или механизм с меньшими полномочиями. Документальный запрет merge не заменяет техническое исключение полномочия.

## 6. Gateway requirements

Gateway обязан:

- использовать fixed absolute paths;
- очищать неподтверждённое environment;
- валидировать exact repository;
- валидировать PR number;
- валидировать 40-hex SHA;
- разрешать только утверждённые profiles and operations;
- не использовать `eval`;
- отклонять неизвестные arguments;
- иметь timeout;
- устанавливать безопасный `PATH` и `umask`;
- писать audit record;
- маскировать или удалять secrets из stdout/stderr;
- не принимать произвольные paths, URLs, shell fragments или environment variables;
- не выполнять Git write operations и не обращаться к preview с write-доступом.

## 7. OS privilege model

Отдельный account `eod-deploy` или эквивалент:

- не имеет интерактивного login;
- не имеет общего `sudo`;
- может вызвать только gateway;
- не читает preview secrets;
- не меняет system users, SSH config или GitHub.

Root-owned orchestrator получает только права, необходимые для development checkout, development Compose и development env.

Development application containers:

- получают только development runtime secrets;
- не получают Docker socket;
- не запускаются privileged;
- не получают writable mounts к preview или host configuration;
- не получают host SSH keys или GitHub write credentials;
- используют отдельные development network, volumes and database.

Необходимость ограничения outbound network access оценивается в implementation audit и фиксируется отдельно; она не может молча игнорироваться, если development secrets имеют ценность вне VPS.

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
| untrusted PR code attacks host | isolated non-privileged development container without Docker socket/host keys/preview mounts |
| untrusted PR code exfiltrates development secrets | минимальный development env и отдельное решение по outbound network policy |
| stale result | `SUPERSEDED` on head change |
| failed migration/state | stop and documented recovery |
| stolen deploy credential | separate credential, rotation and revoke procedure |
| overpowered GitHub token | permission audit and technical absence of merge/repository-write capability |

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
- artifact checksum;
- effective GitHub permission contract version;
- orchestrator/gateway version.

## 11. Incident conditions

- preview state изменился;
- deployed SHA не совпал;
- development database identity неверна;
- secret marker найден в логах;
- gateway принял неизвестный argument;
- обнаружена попытка interactive shell;
- lock обойдён;
- использован неизвестный deploy credential;
- PR-код получил Docker socket, privileged mode, host key или preview credential;
- automation credential оказался способен выполнять merge или repository write вопреки контракту.

При incident automation останавливается и не выполняет автоматический repair.
