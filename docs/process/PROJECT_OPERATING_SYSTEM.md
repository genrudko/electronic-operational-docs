# Операционная система проекта ЭОД

**Актуализировано:** 29.07.2026

## 1. Цель

Организовать разработку так, чтобы:

- пользователь не выполнял механические операции программирования;
- product/domain/UX control оставался у пользователя;
- GitHub сохранял source of truth и историю;
- runtime проверялся в изолированном development;
- скорость достигалась удалением повторной работы, а не ослаблением качества.

| Область | Ответственный |
|---|---|
| Цели, предметные правила, приоритеты | пользователь |
| Product architecture, code, tests, docs, repair | AI-разработчик |
| Branches, PR, history, CI | GitHub |
| Runtime/PostgreSQL execution | isolated VPS development |
| Предметная и визуальная приёмка | пользователь |
| Merge permission | только пользователь |

## 2. Инварианты процесса

1. `main` содержит accepted application changes и canonical coordination docs.
2. Application/runtime work выполняется в отдельной branch/PR.
3. Один work item сохраняет одну issue, branch и PR на весь repair cycle.
4. Development никогда не запускается из `main`.
5. Preview не используется для разработки.
6. GitHub является source code authority; VPS не является автором кода.
7. VPS deploy key остаётся read-only.
8. Preview и development имеют разные checkout, Compose, database, users, volumes, networks, ports и secrets.
9. Green CI не заменяет user acceptance.
10. Automatic merge запрещён.
11. Final gate выполняется один раз на окончательном exact head.
12. Micro-repair получает proportional checks и быстрый delivery.
13. Одинаковые UI elements используют единый shared contract.
14. Исследовательский факт не становится requirement автоматически.

## 3. Контуры

| Контур | Назначение | Branch | Compose | App | Database |
|---|---|---|---|---|---|
| Accepted preview | принятый baseline | только `main` | `eod-preview` | `127.0.0.1:8765` | `eod_preview` |
| Active development | текущий PR exact head | не `main` | `eod-development` | `127.0.0.1:8766` | `eod_development` |

PostgreSQL ports не публикуются.

## 4. Типы единиц работы

- `feature` — новая пользовательская возможность;
- `fix` — исправление дефекта;
- `repair` — корректировка в текущем PR после проверки;
- `infra` — CI, VPS, deployment, backup;
- `docs` — canonical documentation;
- `research` — доказательное исследование;
- `ux` — shared UX contract или module workspace.

Рабочая branch:

```text
<type>/<work-item-short-name>
```

Имена не заменяют issue/PR evidence.

## 5. Жизненный цикл work item

```text
goal
→ factual preflight
→ issue / branch / Draft PR
→ implementation slices
→ focused/profile checks
→ trusted development delivery
→ user acceptance
→ repairs
→ final exact-head gate
→ explicit merge permission
→ merge
→ post-merge baseline/docs
```

## 6. Product planning

Перед реализацией:

- проверить current state и active PR;
- прочитать domain и product/UX principles;
- установить критический пользовательский маршрут;
- определить primary object и derived views;
- отделить authoring от lifecycle;
- отделить shared UI от specialized workspace;
- выбрать evidence status `ADOPT/ADAPT/REJECT/DEFER/VERIFY`;
- не добавлять недоказанный lifecycle декоративными кнопками.

## 7. UX/UI system

Direction A является общесистемным visual language.

Shared:

- shell/navigation;
- tokens;
- page hierarchy;
- buttons/fields/tabs/cards/statuses;
- selectors/pickers/overlays;
- responsive and state behavior.

Specialized:

- operational editor and book geometry;
- source-bound journal forms;
- permit;
- switching;
- defect lifecycle;
- rounds;
- print contracts.

Cross-screen acceptance обязательна для shared changes.

## 8. Risk-based quality

| Профиль | Быстрый цикл | Final gate |
|---|---|---|
| `DOCS` | documentation checks | documentation gate |
| `PRESENTATION` | focused tests + hot refresh | full gate once |
| `APP_LOGIC` | profile tests + trusted deploy | full gate |
| `SCHEMA_DATA` | PostgreSQL/migration/data checks | full gate + rollback evidence |
| `SECURITY_INFRA` | dedicated gates | controlled full profile |

Тесты выбираются по максимальному риску diff.

## 9. Trusted presentation hot refresh

Разрешены только added/modified regular files:

```text
src/templates/**
src/static/**
```

Hot refresh:

- проверяет PR и exact head;
- применяет overlay только в development app;
- перезапускает app;
- выполняет health;
- сохраняет marker;
- при ошибке clean-recreate app;
- не затрагивает DB, migrations, preview и automatic merge.

## 10. Trusted full development deployment

Используется для application/runtime candidate.

Обязательны:

- exact PR ref fetch;
- SHA verification;
- serialized transaction;
- allowed actor and same-repo PR;
- build/recreate по профилю;
- migrations/check/smoke;
- live-head re-check;
- confirm/rollback;
- evidence summary.

Полный PostgreSQL suite не должен бессмысленно повторяться на GitHub и VPS. Источник доверия и эквивалентность exact head должны быть явными.

## 11. Пользовательская приёмка

Проверяются:

- предметная корректность;
- критический маршрут;
- отсутствие повторного ввода;
- понятность следующего действия;
- единообразие shared UI;
- specialized domain geometry;
- desktop/mobile;
- keyboard/focus;
- печать;
- ограничения и честная терминология.

Результаты:

- `accepted`;
- `accepted with follow-up`;
- `repair required`;
- `rejected`.

## 12. Merge gate

Перед merge:

- PR не draft, если таково решение;
- exact current head известен;
- required checks green;
- development подтверждён на этом head;
- user acceptance зафиксирована;
- blockers отсутствуют;
- пользователь явно разрешил merge.

## 13. Post-merge

1. получить merge commit;
2. закрыть issue;
3. удалить branch по решению;
4. выполнить актуальный release/deployment action;
5. проверить preview health/database identity;
6. обновить canonical docs и histories;
7. зафиксировать новый baseline;
8. выбрать следующий work item.

## 14. Documentation-only exception

Small coherent canonical update может быть direct-to-main только без runtime/schema/data/security change и по явному поручению пользователя.

Такое обновление:

- не является application baseline;
- не должно создавать параллельный product PR;
- проходит documentation checks;
- не отменяет update соответствующего application PR после merge.

## 15. Метрики процесса

Отслеживаются:

- commit-to-acceptance time;
- full suite count per accepted PR;
- CI/VPS minutes;
- manual user commands;
- repair cycles;
- diagnosis time;
- flaky retries;
- rollback count;
- UX consistency defects.

Automation вводится только при измеримой выгоде.

## 16. Запрещено

- automatic merge;
- product development в preview;
- direct code change на VPS;
- common secrets/database volumes;
- host-published PostgreSQL;
- secrets/real data/unauthorized materials in Git;
- отдельная UI-system для каждого журнала;
- claim of success without evidence;
- full-gate repetition по инерции;
- large automation project без доказанного bottleneck.

## 17. Связанные документы

- `../project/PRODUCT_UX_PRINCIPLES.md`;
- `DEVELOPMENT_WORKFLOW.md`;
- `DEVELOPMENT_ACCELERATION.md`;
- `CI_AND_QUALITY_GATES.md`;
- `DEFINITION_OF_DONE.md`;
- `BRANCH_AND_PR_POLICY.md`;
- `../project/DOMAIN_INVARIANTS.md`;
- `../project/CURRENT_HANDOFF.md`.
