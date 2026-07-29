# AGENTS.md — обязательный контракт AI-разработчика ЭОД

Этот файл обязателен для любого AI-ассистента, агента или нового чата, работающего с репозиторием.

## 1. Перед началом работы

Сначала прочитать:

1. `README.md`;
2. `docs/INDEX.md`;
3. `docs/project/CURRENT_STATE.md`;
4. `docs/project/CURRENT_HANDOFF.md`;
5. `docs/project/DOMAIN_INVARIANTS.md`;
6. `docs/project/PRODUCT_UX_PRINCIPLES.md`;
7. `docs/process/PROJECT_OPERATING_SYSTEM.md`;
8. `docs/process/DEVELOPMENT_WORKFLOW.md`;
9. `docs/process/DEVELOPMENT_ACCELERATION.md`;
10. профильный ADR, starter и runbook для затрагиваемого контура.

Не восстанавливать состояние проекта по памяти, названию ветки или одному сообщению чата.

## 2. Роли

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

## 3. Рабочая модель

### 3.1. Основной цикл

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

Для presentation-only repairs используется:

```text
commit
→ focused checks
→ trusted hot refresh
→ health
→ пользовательская проверка
```

Manual VPS-команды пользователя не являются штатной частью functional PR.

Скачиваемые patch-файлы являются аварийным fallback, а не нормальным процессом.

### 3.2. Принцип минимально достаточного решения

- Выбирать наименьшее решение, которое достигает текущей цели и покрывает доказанные риски.
- Не создавать отдельный work item, архитектурный слой, инфраструктурный контур или полный release cycle, когда достаточно локального обратимого изменения.
- Любое усложнение должно быть обосновано конкретным требованием, угрозой или доказанным ограничением.
- Лишняя работа считается самостоятельным риском: увеличивает сроки, поверхность ошибок и стоимость проверки.
- Во время пользовательской приёмки запрещено занимать или перезапускать development параллельной работой без явной смены приоритета.
- Не запускать полный suite и все workflows по инерции после каждого малого repair.
- Новый большой аудит запрещён, если факты уже доказаны и не изменились.

### 3.3. Единый UX/UI contract

Основное правило:

> Одинаковые по назначению элементы во всех журналах выглядят и работают одинаково. Различия допускаются только там, где они обусловлены предметной функцией.

Общесистемными являются:

- shell, sidebar, topbar и page header;
- visual tokens;
- buttons, icon buttons, fields и validation;
- tabs, segmented controls, cards и panels;
- status chips, alerts и empty states;
- tables;
- hierarchy selectors;
- date/time pickers;
- dialogs, overlays и responsive behavior.

Специализированными могут быть:

- оперативный editor, ribbon, лист и разворот;
- утверждённые формы журналов;
- наряд;
- переключения;
- lifecycle конкретного документа;
- маршрут обхода;
- печатные формы.

Запрещено копировать feature-specific визуальный слой под новым префиксом и развивать его независимо.

При изменении shared UI выполняется cross-screen проверка на реальных маршрутах, desktop/mobile viewport и длинных русских данных.

### 3.4. Продуктовый benchmark

Перед новым vertical slice определяется критический пользовательский маршрут. Он сравнивается с:

- фактической бумагой/Excel/Word;
- релевантным узким продуктом;
- существующими модулями ЭОД.

Проверяются время, число действий, повторный ввод, ручной текст, риск ошибки, печать и восстановление после прерывания.

Внешний продукт является референсом, а не автоматическим requirement.

## 4. Ветки, PR и direct-to-main

Для application code, models, migrations, data, runtime, security и infrastructure обязателен отдельный branch/PR.

Один work item сохраняет одну ветку и один PR на весь repair cycle.

Допускается direct-to-main только для небольшого цельного documentation-only coordination update, если одновременно:

- пользователь явно поручил актуализировать canonical docs;
- runtime/schema/data/security не меняются;
- нет конфликтующего documentation PR;
- выполняется профильная проверка;
- изменение не используется для обхода продуктового review.

Automatic merge запрещён.

## 5. Инфраструктурные инварианты

- accepted preview: `/srv/eod/repository`, только `main`, Compose project `eod-preview`, база `eod_preview`, порт `127.0.0.1:8765`;
- active development: изолированный `eod-development`, никогда не `main`, база `eod_development`, порт `127.0.0.1:8766`;
- PostgreSQL не публикуется на host port;
- secrets preview и development не смешиваются;
- VPS deploy key остаётся read-only;
- код не редактируется непосредственно на VPS как источник истины;
- development reset не имеет права записывать в preview;
- exact PR head и live-head re-check обязательны для trusted delivery;
- preview write и automatic merge отсутствуют в product PR.

## 6. Предметные инварианты

Обязателен полный документ `docs/project/DOMAIN_INVARIANTS.md`. Ключевые правила:

- end-user UI только русский;
- внутренние идентификаторы — профессиональный английский;
- оперативный журнал остаётся специализированным модулем;
- остальные журналы используют общие механизмы, но формы и lifecycle определяются утверждёнными источниками;
- оператор не конструирует произвольные журналы;
- опубликованные редакции, зарегистрированные документы и исторические снимки не переписываются;
- управление и ведение моделируются раздельно;
- информационное ведение — характеристика ведения;
- ЩПТ и ШОТ относятся к общей технической группе оборудования системы оперативного постоянного тока;
- бумажный, гибридный и электронный режимы не объявляются юридически эквивалентными без доказанного основания;
- SCADA является интеграцией, а не обязательной основой ЭОД;
- исследовательские наблюдения не становятся requirements без отдельного решения.

## 7. Качество изменения

Проверки соразмерны фактическому риску.

### `DOCS`

- documentation contract;
- links/format/consistency;
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

## 8. Документационный контракт

Каждое принятое изменение обновляет применимые документы:

- `docs/project/CURRENT_STATE.md`;
- `docs/project/CURRENT_HANDOFF.md`;
- `docs/project/OPEN_ITEMS.md`;
- `docs/project/DECISION_LOG.md` для архитектурного/предметного решения;
- `docs/project/BASELINE_HISTORY.md` и `ACCEPTANCE_HISTORY.md` после принятия;
- `docs/releases/RELEASE_NOTES.md` для значимого изменения;
- `docs/project/MODULE_MAP.md`, если изменился статус модуля;
- `docs/project/PRODUCT_UX_PRINCIPLES.md`, если меняется общий продуктовый или UX contract.

Не дублировать одну истину в несовместимых вариантах.

## 9. Безопасность данных и материалов

Запрещено коммитить:

- passwords, private keys, tokens и `.env`;
- реальные персональные данные;
- фактические оперативные записи;
- внутренние инструкции, исходные PDF/XLSX/CSV и архивы предприятия;
- databases, dumps, backups и чувствительные логи;
- сторонние изображения и документы, право на публикацию которых не подтверждено.

Для исследования допускаются собственные аналитические тексты, source catalog, ссылки, атрибуция и hashes исходных материалов.

## 10. Правила ответа пользователю

- русский язык;
- факт, вывод и план разделяются;
- один ручной этап за раз, когда он действительно нужен;
- не просить пользователя собирать файлы или исправлять код;
- не объявлять успех без проверяемой опоры;
- возвращать acceptance route и ожидаемый результат;
- при ошибке извлекать точную первичную причину;
- не превращать краткий запрос в необоснованно большой процесс.

## 11. Merge

Никогда не выполнять merge по собственной инициативе.

Перед merge проверить:

- current PR state;
- exact current head;
- актуальный final gate;
- acceptance evidence;
- отсутствие blocking defects;
- явное разрешение пользователя.

Формулировки «сливай», «мёрджим», «принимаю» или однозначный эквивалент являются разрешением только в соответствующем контексте.
