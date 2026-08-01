# AGENTS.md — обязательный контракт AI-разработчика ЭОД

Этот файл обязателен для любого AI-ассистента, агента или нового чата, работающего с репозиторием.

## 1. Перед началом работы

Сначала прочитать:

1. `README.md`;
2. `docs/INDEX.md`;
3. `docs/project/CURRENT_STATE.md`;
4. `docs/project/DEMO_RELEASE_PLAN.yaml`;
5. `docs/project/CURRENT_HANDOFF.md`;
6. `docs/project/DOMAIN_INVARIANTS.md`;
7. `docs/project/PRODUCT_UX_PRINCIPLES.md`;
8. `docs/ux/UX_UI_CONTRACT_V1.md`;
9. `docs/process/PROJECT_OPERATING_SYSTEM.md`;
10. `docs/process/DEVELOPMENT_WORKFLOW.md`;
11. `docs/process/DEVELOPMENT_ACCELERATION.md`;
12. профильный module contract, ADR, work-item contract и runbook.

Не восстанавливать состояние проекта по памяти, названию ветки или одному сообщению чата.

Если текущий разговор не содержит истории work item, сначала самостоятельно восстановить факты из GitHub. Нормальная стартовая команда пользователя:

```text
Продолжай EOD по фактическому состоянию GitHub.
```

## 2. Источники истины

- `docs/project/CURRENT_STATE.md` — единственный владелец accepted main SHA, active work item/PR и runtime state.
- `docs/project/DEMO_RELEASE_PLAN.yaml` — единственный machine-readable владелец release/module/capability/work-item status, depth, dependencies, source IDs и acceptance.
- `docs/project/CURRENT_HANDOFF.md` — навигатор без независимого volatile state.
- `docs/product/MODULE_MAP.md`, `docs/product/IMPLEMENTATION_SEQUENCE.md` и `docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md` — проверяемые human-readable views плана.
- `docs/project/ROADMAP.md`, `docs/project/OPEN_ITEMS.md` и `docs/project/MODULE_MAP.md` — compatibility pointers, а не владельцы статусов.
- GitHub state сильнее любого описания в чате или документации.

После утверждения baseline изменение release scope, module map, implementation sequence, shared UX contract или presentation scenarios требует явного решения пользователя, decision/ADR, version bump плана и повторной проверки производных представлений.

## 3. Роли

Пользователь:

- владелец продукта и предметный эксперт энергетики;
- не обязан читать, писать или исправлять код;
- формулирует цель, предметные правила и приоритет;
- проверяет реальный workflow, UX и результат;
- единственный разрешает merge принятого результата в `main`.

AI-разработчик:

- самостоятельно исследует репозиторий и источники;
- проектирует минимально достаточное изменение;
- создаёт code, migrations, tests, docs, commits и PR;
- анализирует CI, VPS-логи, видео и результаты приёмки;
- не перекладывает программирование и штатные технические операции на пользователя;
- критически оспаривает рискованные или недоказанные предположения.

## 3.1. Единый пользовательский контур

Один активный пользовательский чат ведёт один work item через весь цикл:

```text
factual preflight
→ issue / branch / Draft PR
→ implementation
→ CI и diagnosis
→ development candidate
→ пользовательская приёмка
→ repairs в том же PR
→ final exact-head gate
→ явное разрешение merge
→ merge
→ post-merge coordination
```

Разделение на отдельные coordination-, implementation-, review- и repair-чаты не является штатной моделью. Новый чат создаётся только при техническом переполнении или деградации текущего разговора и продолжает тот же work item по фактическому состоянию GitHub.

При доступном GitHub запрещено просить пользователя:

- переносить handoff-файлы, SHA, CI-отчёты или команды между чатами;
- выступать посредником между AI-исполнителями, GitHub, Codex или VPS;
- повторно пересказывать уже опубликованный в GitHub contract и фактическое состояние.

Новый чат самостоятельно определяет current `main`, active issue/PR/branch, exact head, changed-file boundary, CI, runtime state, blocker и следующий action. Изменчивое состояние конкретного PR хранится в PR body или одном machine-owned PR comment; чат является временным интерфейсом, а не единственным хранилищем памяти.

## 4. Рабочая модель

```text
цель и factual preflight
→ одна issue / branch / Draft PR
→ implementation slice
→ focused/profile checks
→ trusted development delivery
→ пользовательская проверка
→ repairs в том же PR
→ один full final gate на final exact head
→ явная команда пользователя
→ merge
→ post-merge baseline/docs
```

Для presentation-only repairs:

```text
commit
→ focused checks
→ trusted hot refresh
→ health
→ пользовательская проверка
```

Manual VPS-команды пользователя не являются штатной частью functional PR. Скачиваемые patch-файлы — аварийный fallback, а не нормальный процесс.

## 5. Принцип минимально достаточного решения

- Выбирать наименьшее решение, которое достигает текущей цели и покрывает доказанные риски.
- Не создавать отдельный work item, архитектурный слой, инфраструктурный контур или полный release cycle, когда достаточно локального обратимого изменения.
- Любое усложнение обосновывать конкретным требованием, угрозой или доказанным ограничением.
- Не запускать полный suite и все workflows по инерции после каждого малого repair.
- Новый широкий аудит запрещён, если факты уже доказаны и не изменились.
- Во время пользовательской приёмки не занимать development параллельной работой без явной смены приоритета.

## 6. Единый UX/UI contract

Одинаковые по назначению элементы во всех журналах выглядят и работают одинаково. Различия допускаются только там, где они обусловлены предметной функцией.

Общесистемными являются shell, sidebar, topbar, page header, visual tokens, controls, validation, status chips, tables, hierarchy selectors, date/time pickers, dialogs, overlays и responsive behavior.

Специализированными могут быть оперативный editor/ribbon/лист, утверждённые формы, наряд, переключения, lifecycle конкретного документа, маршрут обхода и печатные формы.

Запрещено копировать feature-specific визуальный слой под новым префиксом и развивать его независимо. При изменении shared UI обязательна cross-screen проверка на реальных маршрутах, desktop/mobile viewport и длинных русских данных.

## 7. Продуктовый benchmark

Перед новым vertical slice определяется критический пользовательский маршрут. Он сравнивается с фактической бумагой/Excel/Word, релевантным узким продуктом и существующими модулями ЭОД.

Проверяются время, число действий, повторный ввод, ручной текст, риск ошибки, печать и восстановление после прерывания. Внешний продукт является референсом, а не автоматическим requirement.

## 8. Ветки, PR и merge

Для application code, models, migrations, data, runtime, security и infrastructure обязателен отдельный branch/PR. Один work item сохраняет одну ветку и один PR на весь repair cycle.

Direct-to-main допустим только для небольшого цельного documentation-only coordination update, если пользователь явно поручил актуализацию canonical docs, runtime/schema/data/security не меняются, отсутствует конфликтующий documentation PR, выполняется профильная проверка и изменение не обходит product review.

Automatic merge запрещён.

## 9. Инфраструктурные инварианты

- accepted preview: `/srv/eod/repository`, только `main`, Compose project `eod-preview`, база `eod_preview`, порт `127.0.0.1:8765`;
- active development: изолированный `eod-development`, никогда не `main`, база `eod_development`, порт `127.0.0.1:8766`;
- PostgreSQL не публикуется на host port;
- secrets preview и development не смешиваются;
- VPS deploy key остаётся read-only;
- код не редактируется непосредственно на VPS как источник истины;
- development reset не имеет права записывать в preview;
- exact PR head и live-head re-check обязательны для trusted delivery;
- preview write и automatic merge отсутствуют в product PR.

## 10. Предметные инварианты

Полный контракт: `docs/project/DOMAIN_INVARIANTS.md`. Ключевые правила:

- end-user UI только русский;
- внутренние идентификаторы — профессиональный английский;
- оперативный журнал остаётся специализированным модулем;
- остальные журналы используют общие механизмы, но формы и lifecycle определяются утверждёнными источниками;
- оператор не конструирует произвольные журналы;
- опубликованные редакции, зарегистрированные документы и исторические снимки не переписываются;
- управление и ведение моделируются раздельно;
- информационное ведение — характеристика ведения;
- ЩПТ и ШОТ относятся к общей технической группе оборудования системы оперативного постоянного тока;
- paper, hybrid и electronic modes не объявляются юридически эквивалентными без доказанного основания;
- product target и proven legal mode хранятся раздельно;
- SCADA является интеграцией, а не обязательной основой ЭОД;
- research observation не становится requirement без canonical decision.

## 11. Качество изменения

Проверки соразмерны фактическому риску.

### `DOCS`

- documentation contract;
- links/format/consistency;
- release-plan validation;
- без полного application suite, если runtime не затронут.

### `PRESENTATION`

- diff/path validation;
- focused template/static/source-contract tests;
- trusted hot refresh;
- browser acceptance;
- один full final gate перед merge.

### `APP_LOGIC`

- Ruff, compile, Django check;
- focused/profile tests;
- migration check;
- trusted development deployment;
- full final gate.

### `SCHEMA_DATA`

- migration consistency;
- PostgreSQL migrations/tests;
- backup/rollback/data identity;
- full final gate.

### `SECURITY_INFRA`

- профильные security/controller/workflow gates;
- controlled runtime evidence;
- full профильный final gate.

Ноль обнаруженных тестов не является успехом. Техническая готовность не равна пользовательской приёмке.

## 12. Документационный контракт

Каждое принятое изменение обновляет применимые владельцы и представления:

- `docs/project/CURRENT_STATE.md` — только volatile state;
- `docs/project/DEMO_RELEASE_PLAN.yaml` — release/module/capability/work-item state;
- `docs/project/CURRENT_HANDOFF.md` — navigation only;
- `docs/product/MODULE_MAP.md` и `docs/product/IMPLEMENTATION_SEQUENCE.md`;
- `docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md`;
- профильный `docs/modules/<MODULE_ID>/MODULE_CONTRACT.md`;
- `docs/project/DECISION_LOG.md` либо профильный decision record;
- `docs/project/BASELINE_HISTORY.md` и `docs/project/ACCEPTANCE_HISTORY.md` после принятия;
- `docs/releases/RELEASE_NOTES.md` для значимого изменения;
- `docs/project/PRODUCT_UX_PRINCIPLES.md` и `docs/ux/UX_UI_CONTRACT_V1.md`, если меняется общий UX contract.

Не дублировать одну истину в несовместимых вариантах. Compatibility pointers не получают самостоятельные статусы.

## 13. Безопасность данных и материалов

Запрещено коммитить passwords, private keys, tokens, `.env`, реальные персональные данные, фактические оперативные записи, внутренние инструкции, исходные PDF/XLSX/CSV и архивы предприятия, databases/dumps/backups, чувствительные логи и сторонние материалы без подтверждённого права публикации.

Для исследования допускаются собственные аналитические тексты, source catalog, ссылки, атрибуция и hashes исходных материалов.

## 14. Правила ответа пользователю

- русский язык;
- факт, вывод и план разделяются;
- один ручной этап за раз, когда он действительно нужен;
- не просить пользователя собирать файлы или исправлять код;
- не просить пользователя переносить технический контекст между чатами;
- не объявлять успех без проверяемой опоры;
- возвращать acceptance route и ожидаемый результат;
- при ошибке извлекать точную первичную причину;
- не превращать краткий запрос в необоснованно большой процесс.

## 15. Merge

Никогда не выполнять merge по собственной инициативе.

Перед merge проверить current PR state, exact current head, актуальный final gate, acceptance evidence, отсутствие blocking defects и явное разрешение пользователя.

Формулировки «сливай», «мёрджим», «принимаю» или однозначный эквивалент являются разрешением только в соответствующем контексте.
