# COMPONENT_CONTRACT — компоненты интерфейса ЭОД

> **Пакет:** UX-001 v0.3  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`  
> **Статус:** component contract; конкретные visual values остаются candidate.

## 1. Общие требования

Каждый компонент обязан иметь:

- semantic role;
- visual anatomy;
- normal/hover/focus/active/disabled/loading/error/read-only states;
- keyboard contract;
- long Russian text behavior;
- light/dark candidate validation;
- permission behavior;
- accessible name;
- ownership и reuse boundary.

## 2. Application shell

### Anatomy

```text
product identity
current area
primary navigation
workplace/shift context
global search or launcher
user/session controls
```

### Contract

- не более устойчивого набора top-level areas;
- journals не добавляются бесконечно в header;
- active area выражен text + shape/color;
- admin/import/configuration отделены от everyday work;
- keyboard navigation предсказуема;
- long labels не ломают shell;
- narrow mode переходит в menu/drawer без потери current context.

## 3. Page header

Содержит context path, type, title/number, concise state, primary action и secondary actions menu.

Не содержит полный audit block, длинные instructions или все lifecycle actions одновременно.

## 4. Buttons

Variants: primary, secondary, quiet, destructive, icon, split/menu only when behavior truly split.

Rules:

- one primary per local task level;
- label — конкретный глагол;
- loading prevents duplicate submit;
- destructive action не маскируется под primary;
- icon-only requires accessible label and tooltip;
- disabled explains condition where awareness matters.

## 5. Fields

### Text/input/textarea

- visible label;
- optional/required semantics explicit;
- hint distinct from value;
- inline error;
- values preserved after server validation;
- read-only document rendered as text, not disabled form.

### Date/time

- locale `ru-RU`;
- event time and registration time remain distinct;
- keyboard manual entry supported;
- timezone/context shown where ambiguity matters.

### Checkbox/radio/switch

Switch используется только для immediate reversible setting, не для publication/lifecycle/permission.

## 6. Searchable picker

Types: equipment, personnel, document, organizational unit, source form.

Contract:

- async search for large datasets;
- scope/workplace context visible;
- full long identity accessible;
- selected value represented by text + relation chip;
- clear/change action explicit;
- permission/eligibility shown;
- native select допустим только для короткого стабильного списка;
- no mouse-only interception that breaks keyboard.

## 7. Status indicator

Status has label, semantic icon/shape where needed and optional short explanation. Lifecycle, integrity, source validity and sync/save are separate status domains. Не отображать множество насыщенных pills в одной строке.

## 8. Banner

Variants: critical incident, warning/limitation, information, source/provenance compact line.

Rules:

- persistent only when state changes user decision;
- long explanation collapses;
- action placed inside when clear;
- critical integrity warning dominates positive lifecycle color.

## 9. Section and card

### Section

Default grouping mechanism: title, optional description, content, divider/spacing.

### Card

Use only when block has independent action set, distinct state, separate background/context, selectable identity or own scroll/lifecycle. Equal card wall is prohibited on detail pages.

## 10. Data grid

### Anatomy

```text
column headers
primary identity column
operational columns
optional columns
row actions
selection
pagination/virtualization
horizontal overflow affordance
```

### Contract

- primary operational columns visible on target desktop;
- optional columns may use controlled horizontal scroll;
- identity column may be sticky after runtime validation;
- row focus, selection and hover are distinct;
- entire-row click does not conflict with controls;
- no mandatory tiny font to fit all columns;
- column visibility may be saved;
- full long value accessible by wrap, disclosure or preview;
- scroll shadow/indicator shows hidden columns;
- keyboard cell/row model explicitly chosen per grid complexity.

## 11. Filter bar

- common filters visible;
- advanced filters disclosure;
- active filter chips;
- result count server-confirmed;
- Apply for expensive registries;
- Reset returns canonical view;
- state encoded in URL;
- saved view stores filters/sort/columns, not result snapshot.

## 12. Pagination

- current range and total;
- previous/next always labelled;
- page size belongs to view control, not unrelated settings drawer;
- restoring list context returns same page;
- infinite scroll not default for audit-heavy registers.

## 13. Empty/loading/error/read-only states

### Empty

Explains why empty and whether action is possible. Не стилизуется как disabled field.

### Loading

Preserves existing context. Skeleton only where geometry known. Long process shows phase/progress.

### Error

Identifies object and next action; input is preserved; diagnostic reference disclosed separately.

### Read-only

Rendered information, reason and allowed next action. Correction/revision path separated.

## 14. Modal

Only for short confirmation, critical transition review or small focused input.

- focus enters/traps/returns;
- no nested modal;
- Escape behavior explicit;
- dirty/critical modal not closed silently by outside click;
- action labels name consequence.

## 15. Drawer

Use for quick preview, context inspection и limited adjustment without leaving workspace.

Not for unrelated settings bundle, long multi-step form, replacement navigation tree or content that changes document geometry unexpectedly.

Journal drawer must overlay or use stable split mode with frozen page geometry.

## 16. Menu, tooltip, popover

### Menu

Commands only; keyboard arrows, Enter, Escape.

### Tooltip

Short noninteractive explanation; never sole source of critical information.

### Popover

Interactive contextual detail. Relation popover includes human identity, type/status, relation meaning, open full and change relation when permitted. Focus and collision behavior are shared across relation types.

## 17. Notification

- save success subtle;
- actionable error persistent;
- identifies object;
- toast never steals focus;
- critical integrity incident not reduced to transient toast.

## 18. Relation chip

Displays relation type, object identity, state where relevant and remove/change control by permission. Semantic target remains editable. Copy/paste must not duplicate technical marker.

## 19. Timeline item

Contains event time, registration time when different, event type, actor, subject, relation/evidence link and correction/annulment state. Generic `Связано` is insufficient when domain relation is known.

## 20. Provenance/audit disclosure

Normal mode shows concise source and integrity summary.

Expanded mode may show source document/revision, snapshot, actor, revision, hash, internal identifier and raw import value. Technical detail must not compete with work content.

## 21. Operational journal entry chrome

### Passive

Timestamp, content and essential anomaly only.

### Hover/focus

Compact actions, relation affordances and row identity.

### Active editing

Truthful save state, necessary formatting/insert actions and explicit finish/cancel according to actual behavior.

### Registered/clean copy

No editor chrome; correction history available separately.

## 22. Component priorities

### P0

Shell/navigation, page header, buttons, fields/errors, statuses/banners, focus, searchable picker, filter bar, data grid, overlay root, relation chip/popover, journal entry chrome.

### P1

Saved views, preview drawer, timeline, audit disclosure, column personalization, shortcut help, skeleton/progress.

### P2 evidence-triggered

Bulk operations, split view, real-time conflict comparison, offline/mobile editing.
