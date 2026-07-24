# ЭОД — сопровождение документации

## 1. Цель

Документация должна отражать фактическое состояние и позволять продолжить проект без восстановления по памяти.

## 2. Канонический слой

Канонические документы перечислены в `docs/INDEX.md`. Старые, архивные или дублирующие файлы не могут опровергать канонический слой.

## 3. Обновление вместе с изменением

В том же PR обновляются применимые файлы:

- `project/CURRENT_STATE.md`;
- `project/CURRENT_HANDOFF.md`;
- `project/MODULE_MAP.md`;
- `project/OPEN_ITEMS.md`;
- `project/DECISION_LOG.md`;
- `project/BASELINE_HISTORY.md`;
- `project/ACCEPTANCE_HISTORY.md`;
- `releases/RELEASE_NOTES.md`;
- профильные runbooks and ADR.

Не откладывать обязательное обновление состояния на неопределённый следующий patch.

Merge commit SHA, которого ещё не существует в working branch, фиксируется коротким metadata-only follow-up после успешного post-merge gate. Такой follow-up не создаёт новый application baseline только из-за собственного documentation commit.

## 4. Факты и планы

Документы обязаны различать:

- подтверждённый факт;
- inference;
- рабочую гипотезу;
- утверждённый план;
- отложенное решение;
- историческую информацию.

Функция не называется завершённой только потому, что существует model или route.

## 5. Baseline consistency

Accepted application baseline SHA должен совпадать в:

- `project/CURRENT_STATE.md`;
- `project/CURRENT_HANDOFF.md`;
- `project/BASELINE_HISTORY.md`;
- relevant release notes.

Working branch SHA и metadata-only documentation commit не подменяют accepted application baseline.

Baseline означает post-merge verified application/runtime или явно принятый operating-system milestone. Документационная фиксация уже принятого SHA остаётся обычной частью `main` history, но не запускает рекурсивную цепочку новых baseline.

## 6. Ссылки

- использовать относительные repository links;
- link target должен существовать;
- directory link допускается только когда GitHub корректно отображает каталог;
- внешние URLs используются минимально и не заменяют source attribution;
- переименование файла сопровождается обновлением всех ссылок.

## 7. История

- решения не переписываются задним числом;
- исправление оформляется новой датированной записью;
- подробные raw logs не копируются в Markdown;
- significant failure and rollback summary сохраняются;
- удалённый устаревший документ остаётся доступным в Git history.

## 8. Handoff

`CURRENT_HANDOFF.md` должен содержать:

- accepted application baseline;
- active branch and task;
- last accepted change;
- infrastructure state;
- current next step;
- critical invariants;
- exact commands only when they remain current.

## 9. Master plan and roadmap

- master plan хранит цели и крупные обязательства;
- roadmap хранит текущую последовательность;
- open items хранит дефицит и блокеры;
- module map хранит реализационный статус;
- изменение направления обновляет все четыре документа согласованно.

## 10. ADR

ADR создаётся для решения, которое:

- меняет architecture boundary;
- вводит или отменяет infrastructure invariant;
- определяет data/history/security model;
- существенно ограничивает будущую реализацию.

Принятый ADR не редактируется так, будто старого решения не было; создаётся новый superseding ADR.

## 11. Documentation gate

CI проверяет:

- required files;
- non-empty content;
- internal links;
- baseline consistency;
- forbidden legacy statements in canonical docs;
- presence of PR template and AGENTS.

Gate не оценивает предметную истинность текста, поэтому manual review остаётся обязательным.

## 12. Архивный слой

`docs/project_state/` после миграции удалён из active tree. Его история сохраняется Git. Новые документы не должны ссылаться на этот каталог как на текущий источник истины.