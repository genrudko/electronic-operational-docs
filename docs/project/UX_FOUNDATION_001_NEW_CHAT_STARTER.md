# UX-FOUNDATION-001 — NEW CHAT STARTER

## Цель

Создать минимальный переиспользуемый UX/UI foundation для ЭОД на основе принятого журнала дефектов, не меняя без необходимости предметную модель DEFECT-001.

Утверждённое визуальное направление:

```text
Direction A — спокойное светлое документно-операционное
```

Это отдельный implementation work item. Финальная пользовательская приёмка и разрешение на merge выполняются в Chat 0.

---

## Источник истины

GitHub — единственный источник кода и canonical documentation. VPS используется только для runtime/test evidence.

В начале работы:

1. проверь фактический `main`;
2. прочитай `AGENTS.md`;
3. прочитай `docs/project/CURRENT_HANDOFF.md`;
4. прочитай `docs/project/ROADMAP.md` и `docs/project/OPEN_ITEMS.md`;
5. изучи фактические templates, static assets, routes и tests журнала дефектов;
6. не полагайся на старые описания структуры файлов.

Baseline на момент создания starter:

```text
main:
228b8cb9b1d73e05b676ba3231d626bcea0f4218

previous runtime/application main:
6959b9767ce411e74fc4788d5da8dac97f41018f
```

Если `main` изменился, использовать фактическое текущее состояние GitHub.

---

## Рабочий процесс

```text
один work item
→ одна ветка
→ один Draft PR
→ несколько implementation chats при необходимости
→ focused checks
→ trusted hot refresh для template/static repairs
→ пользовательская проверка
→ один final exact-head gate
→ возврат в Chat 0 за merge-разрешением
```

Пользователь не редактирует код и не выполняет штатные VPS-команды для функционального PR.

Preview не используется и не изменяется.

Automatic merge запрещён.

Не создавать новый PR для каждого визуального замечания.

---

## Первый ответ нового чата

После проверки GitHub и фактических файлов выдать только:

```text
FACT
IMPLEMENTATION CONTRACT
FIRST DELIVERY SLICE
READY TO IMPLEMENT / BLOCKED
```

Не проводить большой повторный аудит DEFECT-001, DEV-FAST-001 и всей архитектуры приложения.

Если фактических блокеров нет, после этого самостоятельно создать:

```text
work item: UX-FOUNDATION-001
branch: ux/ux-foundation-001
Draft PR: один на весь цикл
```

---

## Reference screen

Первый reference screen:

```text
Журнал дефектов оборудования
```

Сохранять принятые предметные правила DEFECT-001:

- source-bound форма;
- шесть утверждённых граф;
- equipment snapshot;
- lifecycle `REGISTERED → IN_PROGRESS → RESOLVED → CLOSED`;
- versioned продление срока;
- immutable action evidence;
- explicit operational-log link;
- dedicated registry/card/actions/print;
- существующие роли и permissions.

Не менять модели, migrations, services, lifecycle или evidence только ради визуального слоя.

---

## Утверждённое визуальное направление A

Обязательные свойства:

- светлая нейтральная основа;
- спокойный синий акцент;
- компактная шапка;
- понятная постоянная навигация;
- высокая рабочая плотность без ощущения admin-panel;
- полноценная desktop-таблица;
- отдельная рабочая карточка записи;
- понятный боковой блок связей и файлов;
- чёткая status/action hierarchy;
- минимум декоративных бабблов;
- профессиональный русский интерфейс;
- полноценная мобильная читаемость.

Не превращать интерфейс в SCADA, BI-dashboard, generic Django admin или маркетинговый landing page.

Не копировать концепт буквально: использовать реальные поля и данные DEFECT-001.

---

## Первый scope UX-FOUNDATION-001

### Application shell

- компактная верхняя зона;
- навигация без лишнего вертикального расхода;
- единый page header;
- согласованные primary/secondary/destructive actions.

### Registry pattern

- центрированные заголовки таблицы;
- сквозная пользовательская нумерация строк;
- нормальная сортировка;
- компактные понятные фильтры;
- поиск без технической терминологии;
- визуально явные статусы;
- понятный row-click contract;
- desktop density без потери читаемости.

### Mobile pattern

- не пытаться сжимать desktop-таблицу до нечитаемого состояния;
- использовать карточки/строки с ясной информационной иерархией;
- сохранять ключевые статусы, оборудование, дату, описание и действия.

### Card/form pattern

- сделать карточку менее технической;
- отделить основные данные, lifecycle, связи, файлы и evidence;
- понятная связь с оперативной записью;
- нормальные date/time controls;
- единые validation и notification patterns;
- без избыточных modal/dialog flows.

### Foundation tokens

- typography;
- spacing;
- density;
- borders/radii/shadows;
- status colors;
- focus/hover/selected/disabled states;
- responsive breakpoints.

---

## Накопленные пользовательские замечания

Обязательно закрыть в рамках reference screen:

1. заголовки таблицы должны быть отцентрированы;
2. шапка и служебные блоки занимают слишком много полезного пространства;
3. карточки дефектов выглядят слишком техническими;
4. нужен первый столбец со сквозной нумерацией дефектов, не кодом;
5. связывание с оперативной записью должно быть понятно оператору;
6. нужны нормальные сортировка, поиск и фильтры;
7. date/time pickers требуют переработки;
8. статусы «устранён», «закрыт», «в работе» должны быть заметнее;
9. мобильная версия журнала должна стать реально читаемой.

---

## DEV-FAST-001

Trusted hot refresh завершён и принят.

Для промежуточных repairs разрешены только added/modified regular `100644` files:

```text
src/templates/**
src/static/**
```

После каждого достаточного presentation repair implementation-чат самостоятельно:

1. проверяет diff;
2. запускает focused/profile checks;
3. публикует `/eod-hot-refresh <exact-head-sha>` в активном PR;
4. отслеживает workflow;
5. сообщает пользователю URL проверки.

При ошибке самостоятельно извлекать diagnostics artifact и устанавливать точную причину. Не передавать пользователю штатные VPS-команды.

Полный CI и full deployment не выполнять после каждой визуальной мелочи.

---

## Development acceptance

Проверочный URL reference screen:

```text
http://5.181.177.72:8766/operations/defects/
```

Пользователь при необходимости самостоятельно включает доступ:

```text
sudo dev-on
```

Не просить повторно выполнять controller activation, bootstrap, deploy key или другие инфраструктурные действия.

---

## Final gate

После сообщения пользователя, что новых замечаний нет:

1. зафиксировать final exact head;
2. выполнить focused UX/template/static tests;
3. выполнить один полный required exact-head gate;
4. доставить final head в development обычным trusted механизмом, если hot refresh недостаточен;
5. получить финальную пользовательскую приёмку;
6. вернуть работу в Chat 0;
7. не сливать без отдельной команды пользователя.

---

## После UX-FOUNDATION-001

Следующий product vertical slice:

```text
PRODUCT-D2 — Журнал заявок
```

Он должен переиспользовать принятый UX foundation, а не копировать legacy UI журнала дефектов.
