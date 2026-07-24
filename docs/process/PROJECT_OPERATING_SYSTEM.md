# Операционная система проекта ЭОД

## 1. Цель

Организовать разработку так, чтобы человек не выполнял механические операции программирования, но сохранял контроль над продуктом и стабильным baseline.

| Область | Ответственный |
|---|---|
| Цели, предметные правила, приоритеты | пользователь — владелец продукта и доменный эксперт |
| Архитектура, код, migrations, tests, docs, repair | AI-разработчик |
| Ветки, PR, история и CI | GitHub |
| Django/PostgreSQL execution | isolated VPS development |
| Предметная и визуальная приёмка | пользователь |
| Разрешение merge | только пользователь |

## 2. Инварианты процесса

1. `main` содержит только принятые изменения.
2. Каждый work item выполняется в отдельной ветке и PR.
3. Development никогда не запускается из `main`.
4. Preview не используется для разработки.
5. VPS deploy key остаётся read-only.
6. Нормальный цикл не использует скачиваемые patch-файлы.
7. Preview и development имеют разные checkout, Compose projects, databases, users, volumes, networks, ports and secrets.
8. Зелёный CI не заменяет предметную приёмку.
9. Merge выполняется только после явной команды пользователя.
10. Новый baseline фиксируется только после post-merge preview gate.

## 3. Контуры

| Контур | Checkout | Branch | Compose | App | Database |
|---|---|---|---|---|---|
| Accepted preview | `/srv/eod/repository` | только `main` | `eod-preview` | `127.0.0.1:8765` | `eod_preview` |
| Active development | `/srv/eod/development` | любая active branch, кроме `main` | `eod-development` | `127.0.0.1:8766` | `eod_development` |

PostgreSQL ports не публикуются. Доступ через SSH tunnel.

## 4. Единица работы

Типы:

- `feature` — новая пользовательская возможность;
- `fix` — исправление дефекта;
- `repair` — корректировка после проверки;
- `infra` — CI, VPS, backup, deployment;
- `docs` — документы и регламенты;
- `research` — доказательное исследование без runtime change.

Branch name:

```text
<type>/<number>-<short-name>
```

## 5. Жизненный цикл

```text
цель и критерии
→ branch
→ implementation commits
→ PR
→ CI
→ VPS development
→ technical gate
→ user acceptance
→ explicit merge permission
→ merge
→ preview sync
→ post-merge gate
→ accepted baseline
```

## 6. Постановка

AI-разработчик обязан:

- восстановить current accepted baseline;
- прочитать canonical docs и профильный ADR;
- выявить риски и противоречия;
- определить acceptance criteria;
- не подменять предметное решение догадкой;
- не начинать реализацию по устаревшему plan item без сверки состояния.

## 7. Реализация

Изменения создаются непосредственно в GitHub active branch. VPS не является автором кода.

```text
AI → GitHub commit → CI → VPS git pull --ff-only
```

Ручное редактирование пользователем или на accepted preview запрещено.

## 8. Quality gates

По риску применяются:

- diff and secret scan;
- Ruff and compileall;
- Django system checks;
- migration consistency;
- PostgreSQL migrations/tests;
- profile gates;
- full current test suite;
- container smoke;
- isolation and database identity checks;
- documentation contract;
- functional and visual acceptance.

Ноль обнаруженных тестов не является успехом.

## 9. Development deployment

```bash
cd /srv/eod/development
git status --short --branch
git fetch --prune origin
git pull --ff-only
sudo bash scripts/development_stack.sh refresh
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

`rebuild` используется для dependency/Docker/startup changes. Reset development data выполняется отдельным safe script.

## 10. Пользовательская приёмка

Проверяются:

- предметная корректность;
- полнота сценария;
- понятность UI;
- отсутствие регрессии;
- пригодность для внутреннего показа;
- фактическое выполнение acceptance criteria.

Результаты:

- `accepted`;
- `accepted with follow-up`;
- `repair required`;
- `rejected`.

## 11. Merge gate

Перед merge:

- PR не draft;
- exact current head известен;
- обязательный CI green;
- development работает на этом head;
- review threads закрыты или приняты;
- acceptance evidence зафиксирован;
- пользователь явно разрешил merge.

Expected head SHA используется для защиты от подмены ветки между приёмкой и merge.

## 12. Post-merge

1. получить merge commit SHA;
2. синхронизировать `/srv/eod/repository` fast-forward;
3. выполнить backup/migrations/rebuild по необходимости;
4. проверить health, HTTP and database identity;
5. обновить current state, handoff, baseline and acceptance histories;
6. только после этого объявить новый baseline принятым.

## 13. Repair

```text
CI/log/video/acceptance failure
→ root cause analysis
→ repair commit in same branch/PR
→ repeated CI
→ repeated VPS deployment
→ repeated acceptance
```

Пользователь не исправляет код вручную.

## 14. Аварийный fallback

Ручной patch или копирование допускаются только при технической невозможности direct GitHub commit. Результат обязан быть немедленно воспроизведён normal commit и не может быть принят, пока GitHub branch не соответствует проверенному состоянию.

## 15. Запрещено

- direct push/commit to `main`;
- force-push to `main`;
- development in preview checkout;
- common secrets or PostgreSQL volume;
- host-published PostgreSQL;
- secrets, real data, backups or databases in Git;
- merge without explicit permission;
- claim of success without evidence.

## 16. Связанные документы

- `DEVELOPMENT_WORKFLOW.md`;
- `BRANCH_AND_PR_POLICY.md`;
- `CI_AND_QUALITY_GATES.md`;
- `DEFINITION_OF_DONE.md`;
- `RELEASE_PROCESS.md`;
- `../project/DOMAIN_INVARIANTS.md`;
- `../project/CURRENT_HANDOFF.md`.