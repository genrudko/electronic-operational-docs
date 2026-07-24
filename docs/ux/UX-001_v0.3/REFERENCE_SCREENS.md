# REFERENCE_SCREENS — согласованные reference contracts

> **Пакет:** UX-001 v0.3  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`  
> **Статус:** textual contracts; изображение без этого контракта результатом не считается.

## 0. Общие правила

Три families проверяют одну visual system, но не должны выглядеть одинаковыми:

1. shell — лёгкий, устойчивый, навигационный;
2. structured journal — предметный, системный, controlled-density;
3. operational journal — specialised, document-first, high-density.

Все concrete tokens остаются candidate до runtime acceptance.

---

# R-01. Application shell и главная рабочая навигация

## 1. Цель

Дать оператору за несколько секунд:

- identity текущего рабочего места;
- active shift;
- critical/unresolved work;
- путь к оперативной документации;
- продолжение последней задачи;
- безопасный доступ к справочникам и настройкам.

## 2. Information architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│ ЭОД | Рабочее место | Оперативная документация | Документы      │
│      | Справочники                    Поиск | Смена | Пользователь│
├─────────────────────────────────────────────────────────────────┤
│ Кочубеевская ВЭС · Смена принята 24.07.2026 20:00               │
│                                                                 │
│ Требует внимания                                                │
│ 2 незавершённых события · 1 нарушение целостности                │
│                                                                 │
│ Продолжить работу                                               │
│ Оперативный журнал · последняя запись 23:41                     │
│                                                                 │
│ Быстрый доступ                                                  │
│ Журналы · Реестр документов · Оборудование · Персонал           │
└─────────────────────────────────────────────────────────────────┘
```

Названия top-level areas — candidate и требуют product confirmation.

## 3. Visual hierarchy

1. shell and current area;
2. workplace/shift context;
3. critical attention;
4. continue task;
5. secondary launchers;
6. admin/diagnostic areas.

No equal grid of all modules as primary home content.

## 4. Actions

### Primary

Depends on current state: `Принять смену`, `Открыть оперативный журнал` или `Продолжить запись`. Only one dominant action.

### Secondary

Open unresolved items, global search, document registry, directories, user/settings. Admin/import actions reside separately.

## 5. States

- no active shift;
- active shift;
- handover pending;
- critical integrity incident;
- partial permissions;
- loading;
- no unresolved work;
- connection/server error;
- maintenance/read-only mode.

Critical state must not be a transient toast only.

## 6. Focus and keyboard

- skip link to main content;
- logical top navigation;
- menu arrows/Enter/Escape;
- no focus stealing on refresh;
- critical alert announced without moving focus;
- global shortcut cannot override native editor;
- active nav focus differs from active state.

## 7. Overlays

Navigation menu, user menu, compact shift popover, optional global search palette. No nested menu inside modal. Shift work opens page/drawer with focus return.

## 8. Responsive

### Wide desktop

Full nav labels and context.

### 960–1279 candidate range

Less-used areas collapse under `Ещё`; current area and shift remain visible.

### Mobile auxiliary

Menu button, current workplace, critical count and continue action. No promise of full journal editing.

## 9. Long Russian data

Workplace name wraps or truncates with full accessible value. Navigation does not shrink below usable hit targets.

## 10. Empty/error/read-only

- empty: `Незавершённых задач нет`;
- loading preserves geometry;
- error keeps cached context and offers retry;
- maintenance banner names unavailable actions;
- permission behavior follows awareness rule.

## 11. Сохраняется из current UI

Persistent shell, clear active section, user/session entry, directories and Russian labels.

## 12. Изменяется

Lighter visual weight, stable work areas instead of module accumulation, work state before module cards, technical/admin demotion, pointwise color and coherent shift context.

## 13. Acceptance criteria

- current area and next action identified in ≤5 seconds;
- no third-party branding resemblance;
- long labels survive;
- keyboard route reaches all primary areas;
- no duplicate primary actions;
- critical integrity dominates normal success;
- 1440 px and 960 px pass without overlap;
- mobile auxiliary boundary is honest.

---

# R-02. Журнал дефектов — list + form + detail family

## 1. Статус family

`[PRODUCT]` Strong candidate for first structured reference vertical slice.

`[OPEN]` Not finally selected until PLAN-001.

The contract may be reused for another structured journal if PLAN-001 chooses differently, but labels, fields and lifecycle remain domain-specific.

## 2. Shared identity

All three screens share journal name, source form/revision, record number format, state vocabulary, equipment/personnel pickers, relation to operational entry, context-preserving navigation and common visual system.

They do not expose generic `OperationalRecord` terminology.

## 3. List — information architecture

```text
Оперативная документация / Журнал дефектов

Журнал дефектов                         [+ Зарегистрировать дефект]
Форма: <источник · редакция>                         [Подробнее]

[Поиск] [Состояние] [Приоритет] [Оборудование] [Ответственный] [Ещё]
[Открыт ×] [Кочубеевская ВЭС ×]                      14 результатов

┌ Дата/№ ┬ Дефект и оборудование ┬ Приоритет ┬ Ответственный ┬ Состояние ┐
│ ...                                                                │
└─────────────────────────────────────────────────────────────────────┘
```

Candidate primary columns: event date/record number; defect summary + equipment; priority if domain-approved; responsible; state.

Secondary optional columns: source operational entry, registration time, creator, source form revision, technical/demo flag. They may use controlled horizontal scroll or column visibility.

## 4. List visual hierarchy

```text
ДФ-2026-0042 · 24.07.2026 22:48
Периодическое срабатывание сигнализации перегрева силового модуля
ВЭУ № 07 › Щит управления преобразователя частоты, секция 690 В
Высокий · Инженер по эксплуатации · Открыт
```

Subject and equipment dominate; number/time support identity; metadata lower.

## 5. List actions

Primary: `Зарегистрировать дефект` only if role and lifecycle allow.

Secondary: search/filter, saved view, export when available, open record, optional preview drawer. No permanent row of equal icon actions.

## 6. List states

No records, no filter results, loading, retained-filter error, permission-limited, technical/demo, stale data, optional-column overflow and long equipment names.

## 7. Form — information architecture

Final order follows accepted source form. Candidate structure:

```text
Новый дефект
Форма: <source/revision>

[Error summary]

Что обнаружено
- event date/time
- defect description
- equipment
- condition/priority (only if domain-approved)

Организация работы
- detected by
- responsible
- source operational entry
- related documents

Дополнительные сведения
- attachments/comment
- provenance disclosure

[Отменить] [Сохранить/Зарегистрировать]
```

Whether draft exists and exact action labels are `[OPEN]` domain decisions.

## 8. Form behavior

- equipment picker async and workplace-scoped;
- personnel picker shows eligibility/role;
- source operational entry can be linked without losing form;
- validation preserves values;
- source-required fields cannot be hidden;
- explicit save;
- dirty warning only with real loss;
- registration/transition never optimistic.

## 9. Form states

Create, editable draft if permitted, validation error, source form unavailable, equipment inactive/renamed, person ineligible, relation conflict, version conflict, permission read-only and registered immutable.

## 10. Detail — information architecture

```text
ДФ-2026-0042     Открыт
Периодическое срабатывание сигнализации перегрева...

Где
ВЭУ № 07 › Щит управления преобразователя частоты...

Текущее состояние
Ответственный · приоритет · следующее допустимое действие

Основание
Создано из оперативной записи 24.07.2026 22:41

Хронология
...

Связанные документы и работы
...

Источник и аудит [раскрыть]
```

## 11. Detail actions

Primary action is state/permission-specific and requires accepted lifecycle. Illustrative, not approved: `Назначить ответственного`, `Передать в работу`, `Закрыть дефект`.

Secondary: create related application, open source entry, add relation, correction/revision, print/export and provenance. Generic `Изменить` for registered object prohibited.

## 12. Lifecycle and integrity

Display separately: record state, editability, integrity, source validity and technical/demo nature. Registered with integrity incident cannot look like normal success.

## 13. Keyboard/focus

### List

Tab through filters, row links and actions; Enter applies search; Escape closes suggestions; preview returns focus; horizontal focused content scrolls into view.

### Form

Logical source order, error-summary links, keyboard-complete picker, modal focus return and no mouse-only multi-picker.

### Detail

Heading first, keyboard actions menu, timeline links, provenance disclosure and correction path.

## 14. Overlays

Picker popovers, relation preview, lifecycle review modal and optional row preview drawer. No long form in modal and no simultaneous blocking overlays.

## 15. Responsive

Desktop full list/form; narrow collapses filters and optional columns; detail/form become one column. Mobile supports read/search/detail and only approved safe actions.

## 16. Long Russian data

Use package fixture plus a defect description of at least 300 characters. Primary identity remains visible; row may grow; full equipment path accessible; actions do not overlap.

## 17. Empty/loading/error/read-only

Empty list offers action only if permitted; loading keeps filters; error preserves input; read-only renders content; missing source explains boundary; technical/demo marked at record level.

## 18. Сохраняется

Structured core, source-bound form, participants/equipment/relations/revisions foundations, server pagination/filtering and read-only registered records.

## 19. Изменяется

Defect-specific language/hierarchy, compact pre-data area, searchable pickers, technical metadata disclosure, lifecycle/integrity separation, controlled overflow, contextual actions and domain-specific relation labels.

## 20. Acceptance criteria

- source form and lifecycle approved;
- list/form/detail use one vocabulary;
- no generic internal model labels;
- primary columns visible at target desktop;
- optional horizontal scroll explicit and usable;
- keyboard-only create/find/open passes;
- registered record immutable;
- technical/demo unmistakable;
- long-data fixture passes;
- source relation has domain wording;
- no final approval before PLAN-001 chooses slice.

---

# R-03. Operational journal — облегчённая книжная область

## 1. Цель

Создавать, читать, связывать и завершать записи с минимальной потерей focus и контекста, сохраняя документальный характер журнала.

## 2. Information architecture

```text
Оперативный журнал · Смена 24.07.2026 20:00–08:00
Сохранено 23:41:18 · 1 незавершённое событие

[Вид] [Поиск] [Фильтр] [Страница 3/8]       [+ Запись] [Смена] [Чистовик]

[Compact active-entry toolbar appears only when needed]

┌────────────── stable page/spread geometry ──────────────────────┐
│ Время │ Содержание                                  │ Отметки   │
│ 22:41 │ ...                                         │ ...       │
│ 22:48 │ active entry                                │ ...       │
└──────────────────────────────────────────────────────────────────┘
```

## 3. Visual hierarchy

Page/spread and entry content → active entry → anomaly/save error → commands → metadata/version → settings/audit.

Inactive rows do not show permanent `Сохранено`, version and full action set.

## 4. Actions

Idle primary: `+ Запись`.

Active primary exact label depends on save model; candidate: `Завершить запись`.

Secondary: insert relation, template/abbreviation, search/filter, page/spread, shift panel, clean copy, history/corrections. Formatting commands compact and expandable.

## 5. Entry states

Passive saved draft, active editing, saving, saved, save error, conflict, registered/read-only, corrected/annulled, relation issue, removed draft, search match and focused. Save state local to active entry or anomaly.

## 6. Focus and keyboard

Required regression:

1. explicit add focuses intended editable location;
2. blank-area click does not jump page;
3. `Ctrl+Left/Right` native word movement;
4. `Home/End` current editor;
5. `PgUp/PgDown` no unexpected whole-page movement;
6. `Ctrl+Z/Y` relation-safe undo/redo;
7. Escape closes top overlay first;
8. relation popover returns focus/caret;
9. Tab order predictable;
10. search does not destroy draft context.

Video does not prove these; runtime keyboard capture required.

## 7. Relation overlay

Common component for equipment, person, document and structured record. It shows human-readable target, relation meaning, open fully, change and remove if permitted.

Serialization rule:

```text
one semantic relation
→ one data representation
→ one intended visual marker
```

Copy/paste cannot multiply technical icons.

## 8. Shift/settings panel

Split responsibilities:

- Shift panel: members, handover/current state, unfinished work.
- Quick view: density, page/spread, theme/preset.
- Advanced preferences: typography details and persistent settings.
- History: removed entries, revisions/audit.

Opening panel must not change journal page geometry in accepted mode.

## 9. Responsive

Wide desktop supports stable spread/page. Narrow desktop/tablet uses single page and collapsed commands. Mobile read/search/status may be supported; full rich editing is not promised.

## 10. Long Russian data

Test 500-character record, multiple equipment relations, long personnel/title, document title, abbreviation expansion and paste from external plain-text editor. No duplicate marker, row collapse or caret loss.

## 11. Empty/loading/error/read-only

No active shift, empty journal, loading pages, offline/server error, save conflict, registered read-only, integrity incident, permission-limited and print route unavailable.

## 12. Сохраняется

Specialised book metaphor, page/spread, templates/relations foundation, autosave draft concept, clean copy, context drawer idea and Russian workflow.

## 13. Изменяется

Lighter shell integration, on-demand editor chrome, truthful compact save state, drawer decomposition, stable geometry, unified overlay/focus, marker serialization, command hierarchy and technical metadata disclosure.

## 14. Acceptance criteria

- all known keyboard/editor defects pass;
- no duplicate relation markers after copy/paste/save/reload;
- inactive entries read as document, not form;
- panel does not reflow accepted geometry;
- one primary action per state;
- long records readable;
- print/clean copy has no editor chrome;
- browser URL/header policy handled;
- light theme accepted;
- dark behavior tested only if in scope.
