# ЭОД — работа параллельных чатов

## 1. Главный принцип

Основной интеграционный чат — единственное место, где принимаются решения о:

- architecture;
- accepted baseline;
- active development branch;
- commits and PR;
- migrations;
- repair after logs/video;
- merge;
- синхронизации preview.

Вспомогательные чаты исследуют и готовят материалы, но не изменяют архитектуру самостоятельно.

## 2. Разделение контуров

### Основной интеграционный чат

- repository and infrastructure;
- code implementation;
- integration decisions;
- acceptance and repair;
- documentation state;
- final reconciliation.

### Оборудование и объекты диспетчеризации

- source analysis;
- taxonomy;
- aliases;
- dispatching names;
- technical equipment families;
- import conflicts.

### Персонал, права и документация

- organization/personnel sources;
- roles and rights;
- workplace documentation;
- applicability and editions;
- data normalization.

### Нормативный контур и электронные наряды

- current legal sources;
- permit/disposition lifecycle;
- journals;
- briefings/admissions/transfers/completion;
- signatures and storage;
- evidence matrix.

### Демонстрационные сценарии, UX и приёмка

- end-to-end scenarios;
- acceptance criteria;
- demo data requirements;
- blocking defects;
- presentation route.

## 3. Что вспомогательный чат должен вернуть

Результат оформляется как доказательный пакет:

- цель и scope;
- использованные sources;
- facts from sources;
- assumptions/inferences separately;
- decisions requested from integration chat;
- proposed data model or acceptance criteria;
- unresolved questions;
- files suitable for repository, если применимо.

## 4. Что запрещено

Вспомогательный чат не должен:

- объявлять новый baseline;
- создавать несовместимую branch strategy;
- merge changes;
- менять domain invariant без решения main chat;
- считать исследование implementation acceptance;
- дублировать master plan в собственной версии как новый источник истины.

## 5. Интеграция результата

Основной чат:

1. проверяет freshness and source quality;
2. сопоставляет с current code and docs;
3. выявляет conflicts;
4. принимает/отклоняет выводы;
5. обновляет canonical decision log/master plan/domain docs;
6. создаёт work item branch, если требуется implementation.

## 6. Передача файлов

- длинные задания и отчёты оформляются `.md` files;
- реальные source documents не коммитятся в code repository;
- repository получает summary, traceability and derived safe data;
- sensitive archives хранятся вне Git.

## 7. Восстановление контекста

Новый чат начинает с `project/NEW_CHAT_STARTER.md` и current repository docs. Экспорт старого чата используется только как secondary evidence.

## 8. Согласованность

После принятия результата вспомогательного чата обновляются применимые:

- `DECISION_LOG.md`;
- `OPEN_ITEMS.md`;
- `MASTER_PLAN.md` or `ROADMAP.md`;
- `DOMAIN_INVARIANTS.md`;
- acceptance documents;
- profile ADR.

Без этой интеграции вывод остаётся исследовательским и не считается решением проекта.