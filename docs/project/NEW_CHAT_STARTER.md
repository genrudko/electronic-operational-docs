# Старт нового интеграционного чата ЭОД

Восстанови контекст проекта «Электронная оперативная документация» из закрытого репозитория `genrudko/electronic-operational-docs`, а не по памяти или старому экспорту чата.

Сначала прочитай в указанном порядке:

1. `README.md`;
2. `AGENTS.md`;
3. `docs/INDEX.md`;
4. `docs/project/CURRENT_STATE.md`;
5. `docs/project/CURRENT_HANDOFF.md`;
6. `docs/project/DOMAIN_INVARIANTS.md`;
7. `docs/project/MASTER_PLAN.md`;
8. `docs/project/ROADMAP.md`;
9. `docs/process/PROJECT_OPERATING_SYSTEM.md`;
10. `docs/process/DEVELOPMENT_WORKFLOW.md`.

После чтения, не создавая изменение, выведи:

1. назначение проекта и границы независимого прототипа;
2. роль пользователя и роль AI-разработчика;
3. accepted branch и exact baseline SHA;
4. active working branch и её цель;
5. состояние preview и development VPS;
6. что подтверждено реализованным;
7. что реализовано частично или не подтверждено;
8. последний принятый PR/merge;
9. текущий этап и следующий decision gate;
10. данные или проверки, которых не хватает для безопасного продолжения.

Обязательные правила:

- не проси пользователя редактировать код;
- не используй скачиваемые Python patch-файлы как основной workflow;
- commits, PR и merge выполняются через GitHub;
- VPS development получает branch через `git pull --ff-only`;
- preview не используется для разработки;
- merge выполняется только после явного разрешения пользователя;
- реальные данные, документы и secrets не коммитятся;
- при расхождении документа и кода сначала проверь Git, migrations, CI и VPS evidence;
- изменение предметного инварианта требует явного решения.

Текущая ожидаемая точка при создании этого файла:

```text
accepted main: abd6066885b060e3e3d2c39098fcaf640bb70416
working branch: docs/001-project-operating-system
current task: DOCS-001
next task: PLAN-001 evidence-based plan review
```

Не считай эти значения вечными: проверь их по `CURRENT_STATE.md` и GitHub перед началом работы.