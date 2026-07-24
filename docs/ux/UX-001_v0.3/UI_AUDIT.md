# UI_AUDIT — консолидированный аудит интерфейса ЭОД

> **Пакет:** UX-001 v0.3  
> **Дата консолидации:** 25.07.2026  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`  
> **Metadata note:** DOCS-002 — отдельный follow-up; его SHA не подменяет application baseline.  
> **Статус:** проектный контракт; production code, domain model и lifecycle этим пакетом не изменяются.

## Модель доказательности

| Маркер | Значение |
|---|---|
| `[RUNTIME]` | непосредственно наблюдалось в переданном runtime-видео |
| `[SOURCE]` | выведено из templates/CSS/JS и структуры репозитория |
| `[PRODUCT]` | прямое продуктовое решение пользователя |
| `[RECOMMENDATION]` | проектное UX/UI-предложение |
| `[INFERENCE]` | обоснованный вывод, который ещё требует runtime-проверки |
| `[OPEN]` | открытый вопрос, который нельзя закрыть в UI/UX-контуре |

Видео не считается доказательством keyboard-only, screen-reader, narrow viewport, dark theme или точного поведения клавиш, если соответствующее действие не показано.

## 1. Итоговый вывод

`[PRODUCT]` Пользователь воспринимает текущий UI как слишком технический и административный.

`[RUNTIME]` Интерфейс выполнен аккуратно: присутствуют единый shell, ровная типографика, согласованные карточки, specialised operational journal, source-bound notices и relation popovers.

`[INFERENCE]` Аккуратность реализации не равна продуктовой пригодности. Сочетание тёмного shell, множества равноправных cards, технических идентификаторов, постоянных пояснений и editor chrome формирует образ инженерно-административной системы.

`[RECOMMENDATION]` Сохраняются рабочие механики и доменные паттерны, но visual language эволюционирует в современную операционную платформу энергетического предприятия.

## 2. Проверенная архитектура UI

### 2.1 Application shell

`[SOURCE]` Общий shell содержит sticky topbar, first-level navigation, dropdown справочников, user menu и пользовательские параметры отображения.

`[RUNTIME]` Shell последователен, но уже плотен на широком экране.

`[RECOMMENDATION]` Не добавлять каждый новый журнал в top-level navigation. Основные рабочие области должны быть устойчивыми, а журналы — открываться внутри области оперативной документации.

### 2.2 Специализированный оперативный журнал

`[SOURCE]` У журнала собственная command bar, ribbon, книжная таблица, режим страницы/разворота, drawer и print route.

`[RUNTIME]` Это действительно самостоятельное рабочее пространство, а не обычная форма.

`[RECOMMENDATION]` Специализацию сохранить; облегчить editor chrome, нормализовать overlays и стабилизировать keyboard/focus behavior.

### 2.3 Structured journals core

`[SOURCE]` Реестры и карточки строятся на общей структуре records, fields, equipment, participants, relations, revisions и source-bound forms.

`[RUNTIME]` Общий core читается как технический registry framework.

`[RECOMMENDATION]` Общие механизмы сохранить, но journal-specific information architecture должна доминировать над универсальной технической моделью.

## 3. Сильные стороны, которые нельзя потерять

| ID | Тип | Наблюдение |
|---|---|---|
| GOOD-01 | `[RUNTIME]` | единый визуальный каркас и стабильная навигация |
| GOOD-02 | `[RUNTIME]` | специализированная книжная рабочая область журнала |
| GOOD-03 | `[RUNTIME]` | relation popovers дают полезный предметный контекст |
| GOOD-04 | `[RUNTIME]` | source-bound limitations показаны честно |
| GOOD-05 | `[SOURCE]` | registered records отделены от editable drafts |
| GOOD-06 | `[SOURCE]` | существуют snapshot, integrity, revisions и audit foundations |
| GOOD-07 | `[RUNTIME]` | управление и ведение представлены предметно, а не одним флагом |
| GOOD-08 | `[PRODUCT]` | русский UI и профессиональный English только внутри кода |

## 4. Системные проблемы

### SYS-01 — visual language слишком технический

**Evidence:** `[PRODUCT]`, `[RUNTIME]`  
**Severity:** HIGH

Причины:

- тёмный тяжёлый header;
- большое количество одинаковых cards;
- технические labels и IDs в обычном режиме;
- постоянные explanatory panels;
- близкий визуальный вес рабочих и audit сведений;
- формы и реестры напоминают administrative console.

**Решение:** новый самостоятельный visual direction; не palette-only restyle.

### SYS-02 — card wall заменяет смысловую иерархию

**Evidence:** `[RUNTIME]`, `[SOURCE]`  
**Severity:** HIGH

Реквизиты, содержание, участники, equipment, relations и history часто размещены в равновесных контейнерах. Пустой block может занимать почти столько же места, сколько ключевая информация.

**Решение:** typography and spacing first; cards только для самостоятельных рабочих surfaces.

### SYS-03 — technical identifiers видны вне diagnostic context

**Evidence:** `[RUNTIME]`  
**Severity:** HIGH

Наблюдались UUID-like values, `DEMO-*`, internal English codes, hashes и duplicate-group identifiers.

**Решение:** три режима раскрытия:

1. normal work — русские предметные названия;
2. provenance — source/raw identifiers по запросу;
3. diagnostic — UUID, hashes, internal codes.

### SYS-04 — lifecycle и integrity визуально конфликтуют

**Evidence:** `[RUNTIME]`  
**Severity:** CRITICAL FOR TRUST

Одновременно показаны зелёный `Зарегистрирован` и `Целостность нарушена`.

**Решение:** два независимых измерения:

```text
Состояние документа: Зарегистрирован
Состояние целостности: Нарушена — требуется проверка
```

Integrity incident должен визуально доминировать над положительной lifecycle окраской.

### SYS-05 — persistent explanation создаёт scroll tax

**Evidence:** `[RUNTIME]`, `[SOURCE]`  
**Severity:** MEDIUM/HIGH

Source-bound и technical notices часто занимают значительную область до рабочих данных.

**Решение:** compact persistent limitation для safety-critical boundary; подробности — progressive disclosure.

### SYS-06 — одна layout width не подходит всем archetypes

**Evidence:** `[RUNTIME]`, `[SOURCE]`  
**Severity:** HIGH

Registry, detail, form и journal требуют разных рабочих ширин.

**Решение:** reading/form/registry/workspace width contracts. Значения остаются candidate до runtime-проверки.

### SYS-07 — empty state похож на disabled control

**Evidence:** `[RUNTIME]`  
**Severity:** MEDIUM

Серые прямоугольники `Связей нет`, `Участники не указаны` выглядят как заблокированные поля.

**Решение:** empty state = текст, причина, допустимое следующее действие; disabled field используется только в форме и сопровождается причиной.

### SYS-08 — таблицы либо слишком технические, либо рискуют потерять плотность

**Evidence:** `[RUNTIME]`, `[PRODUCT]`  
**Severity:** HIGH

`[PRODUCT]` Нельзя запрещать horizontal scroll абсолютным правилом.

**Решение:** основные оперативные столбцы видны без обязательной horizontal scroll на target desktop; редкие колонки допускают controlled scroll; дополнительно применяются column visibility, detail disclosure и row preview; рабочая плотность важнее формального отсутствия scroll.

### SYS-09 — actions и metadata постоянно конкурируют с содержанием

**Evidence:** `[RUNTIME]`  
**Severity:** HIGH

Особенно заметно в operational journal: `Сохранено`, номер, версия и icon actions повторяются для каждой строки.

**Решение:** passive/hover/focus/active state model; полный chrome только у active entry или anomaly.

### SYS-10 — overlay behavior не имеет доказанного единого контракта

**Evidence:** `[SOURCE]`, `[RUNTIME]`, `[INFERENCE]`  
**Severity:** HIGH

Popover и drawer существуют, но видео не доказывает keyboard open, focus return, collision handling и coexistence.

**Решение:** единый overlay root, close order, focus return и regression suite.

### SYS-11 — blocking semantic marker duplication

**Evidence:** `[RUNTIME]`, известная история дефекта  
**Severity:** CRITICAL

В remarks area видны повторяющиеся красные marker icons.

**Решение:** serialization/copy-paste regression gate до признания operational journal стабильным.

### SYS-12 — print route раскрывает browser metadata

**Evidence:** `[RUNTIME]`  
**Severity:** MEDIUM

Print preview содержит локальный URL и browser header/footer.

**Решение:** отдельная print policy или generated document route; это не доказывает дефект самой HTML-формы.

## 5. Экранные выводы

### 5.1 Главная

`[RUNTIME]` Главная читается как каталог модулей.

`[RECOMMENDATION]` Главная рабочая область должна показывать активную смену, незавершённые работы, критические события, продолжение последней задачи и secondary module launcher.

### 5.2 Реестры

`[RUNTIME]` До первых данных часто расположены banners, metrics и large filters.

`[RECOMMENDATION]` Header, one-line context, compact filters, data. Metrics показываются только если поддерживают решение.

### 5.3 Detail

`[RUNTIME]` Detail pages перегружены равноправными cards.

`[RECOMMENDATION]` Порядок: identity/state → предметное содержание → next action/owner → equipment/participants/relations → timeline → provenance/audit.

### 5.4 Operational journal

`[RUNTIME]` Book workspace полезен; ribbon и row chrome перегружены.

`[RECOMMENDATION]` Документ должен быть визуально сильнее редактора.

### 5.5 Import/staging

`[RUNTIME]` Technical density здесь оправдана больше, чем в ordinary work screens.

`[RECOMMENDATION]` Raw values, hashes и conflict IDs допустимы в provenance-oriented staging, но должны быть сгруппированы и объяснены.

## 6. Accessibility evidence

### Наблюдалось

- `[RUNTIME]` текстовые labels сопровождают часть цветовых состояний;
- `[RUNTIME]` desktop hit areas в основных формах выглядят достаточными;
- `[SOURCE]` отдельные icon controls имеют labels.

### Не доказано

- keyboard-only journeys;
- native editing key precedence;
- screen-reader semantics;
- focus return;
- contrast ratios в runtime;
- 200% zoom;
- reduced motion;
- dark theme;
- narrow/mobile mode.

## 7. Противоречия v0.2, устранённые в v0.3

| v0.2 | v0.3 |
|---|---|
| visual baseline в целом достаточен | механики сохраняются, visual language эволюционирует |
| no mandatory horizontal scroll трактовался почти как запрет | controlled scroll допустим для secondary columns |
| defect journal формулировался как первый slice | остаётся кандидатом до PLAN-001 |
| concrete tokens выглядели близкими к стандарту | все concrete values — candidate |
| runtime и source findings местами смешивались | введены evidence markers |
| видео закрывало Stage 0 слишком широко | видео закрывает только показанный desktop mouse route |

## 8. Открытые вопросы

1. `[OPEN]` Утверждённый domain lifecycle дефекта.
2. `[OPEN]` Source form и обязательные поля defect record.
3. `[OPEN]` Ролевые полномочия и escalation.
4. `[OPEN]` Target desktop viewport.
5. `[OPEN]` Release gate для dark theme.
6. `[OPEN]` Обязательный набор ordinary-mode integrity indicators.
7. `[OPEN]` Название продуктовых top-level areas после PLAN-001.

## FOR_MAIN_INTEGRATION_CHAT

1. Признать visual evolution самостоятельной задачей, а не palette polish.
2. Не менять domain model из UX-документов.
3. Выбрать reference vertical slice после PLAN-001.
4. Параллельно считать marker duplication блокирующим дефектом operational journal.
5. Перед реализацией утвердить candidate tokens на трёх reference screen mockups/runtime prototypes.
