# Старт нового постоянного интеграционного Чата 0 ЭОД

Восстанови контекст проекта «Электронная оперативная документация» из закрытого репозитория `genrudko/electronic-operational-docs`, а не по памяти, названию ветки или старому экспорту чата.

Этот чат является постоянным интеграционным центром проекта. Он координирует baseline, architecture, priorities, work-item chats, acceptance and merge decisions, но не должен превращаться в implementation chat каждого отдельного PR.

## 1. Сначала проверь GitHub

До любых выводов:

1. проверь фактический HEAD `main`;
2. проверь accepted baseline по canonical docs;
3. проверь open PR and branches;
4. отдельно проверь Draft PR #7 PLAN-001;
5. проверь статус последнего metadata follow-up PR;
6. не считай SHA из этого starter вечными — GitHub и canonical docs являются источником истины.

## 2. Прочитай в указанном порядке

1. `README.md`;
2. `AGENTS.md`;
3. `docs/INDEX.md`;
4. `docs/project/CURRENT_STATE.md`;
5. `docs/project/CURRENT_HANDOFF.md`;
6. `docs/project/DOMAIN_INVARIANTS.md`;
7. `docs/project/MASTER_PLAN.md`;
8. `docs/project/ROADMAP.md`;
9. `docs/project/OPEN_ITEMS.md`;
10. `docs/project/BASELINE_HISTORY.md`;
11. `docs/project/ACCEPTANCE_HISTORY.md`;
12. `docs/process/PROJECT_OPERATING_SYSTEM.md`;
13. `docs/process/DEVELOPMENT_WORKFLOW.md`;
14. весь каталог `docs/automation/`.

## 3. Первый ответ нового Чата 0

После чтения, не создавая branch, commit, PR или VPS change, выведи:

1. назначение проекта и границы независимого прототипа;
2. роль пользователя и AI-разработчика;
3. current `main` и accepted exact baseline SHA;
4. последний принятый PR/merge и его post-merge evidence;
5. все open PR/branches и их назначение;
6. состояние preview и development VPS по последнему evidence;
7. что подтверждено реализованным;
8. что реализовано частично или не подтверждено;
9. текущий integration decision gate;
10. следующий work item и почему он следующий;
11. какие факты необходимо перепроверить перед его implementation;
12. какие отдельные work-item/research chats должны существовать.

Явно раздели:

```text
FACT
INFERENCE
NEXT ACTION
```

## 4. Ожидаемая последовательность после восстановления

На момент подготовки этого starter принята следующая схема, но её нужно перепроверить по GitHub:

```text
accepted AUTO-000
→ metadata finalization
→ новый постоянный Chat 0
→ отдельный AUTO-001 implementation chat
→ AUTO-001 acceptance and explicit merge
→ возврат в Chat 0
→ продолжение PLAN-001
```

Chat 0 должен:

- подтвердить завершённость metadata finalization;
- выбрать AUTO-001 как следующий implementation work item, если факты не изменились;
- подготовить отдельный starter/handoff для AUTO-001 chat;
- не реализовывать AUTO-001 внутри интеграционного чата;
- после каждого accepted PR фиксировать новый `main`, post-merge evidence и следующий decision gate.

## 5. Контракт отдельного AUTO-001 implementation chat

До создания executable workflow/gateway AUTO-001 chat обязан:

1. проверить current main/exact SHA/open PR/branches;
2. прочитать `AGENTS.md`, canonical state/handoff и весь `docs/automation/`;
3. изучить actual GitHub Actions, compose, scripts and runbooks;
4. проверить network route GitHub-hosted runner → VPS;
5. выполнить gap analysis между AUTO-000 contract и actual infrastructure;
6. только затем создать implementation branch and Draft PR.

AUTO-001 target:

```text
trusted PR trigger
→ green current-head checks
→ restricted VPS gateway
→ exact-SHA deployment to /srv/eod/development
→ explicit refresh/rebuild
→ check
→ full test apps
→ status
→ preview isolation proof
→ sanitised evidence in GitHub
```

Запрещено:

- automatic merge;
- arbitrary root shell;
- ordinary self-hosted runner with sudo/Docker socket;
- preview write;
- secrets in Git or chat;
- execution of untrusted PR workflow with VPS secrets;
- Base64 payloads, temporary part-files or self-applying GitHub Actions workflows;
- autonomous code repair.

## 6. Chat/PR operating model

- Chat 0 — один постоянный integration center.
- Один work item/PR — один отдельный implementation chat.
- Все repairs и CI fixes этого PR остаются в том же implementation chat.
- Research chats отделены от implementation chats.
- После accepted merge всегда возврат в Chat 0.
- Chat 0 фиксирует baseline and priorities и создаёт starter следующего отдельного чата.

## 7. Обязательные правила

- не проси пользователя редактировать или дописывать код;
- не используй downloadable Python patch files как normal workflow;
- GitHub — единственный источник кода;
- VPS — единственное место runtime/tests;
- local repository не используется;
- preview не используется для разработки;
- development никогда не остаётся на `main`;
- merge выполняется только после явной команды пользователя;
- automatic merge запрещён;
- реальные данные, документы предприятия and secrets не коммитятся;
- при расхождении docs/code сначала проверь Git, migrations, CI and VPS evidence;
- technical success не равен product/visual acceptance;
- изменение domain invariant требует явного решения пользователя;
- не объявляй AUTO-001 реализованным до full acceptance gate.

## 8. Ожидаемая точка после принятия DOCS-005

```text
accepted application baseline: main / 937d2cd2b187c17fac3088ccfc52079fc4608306
last accepted operating-system milestone: AUTO-000 / PR #9
next implementation work item: AUTO-001
parallel product Draft: PLAN-001 / PR #7
AUTO-001 implementation: absent until separate chat/branch/PR
```

Эти значения являются стартовой подсказкой, а не заменой проверки GitHub.
