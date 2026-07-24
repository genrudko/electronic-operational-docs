# INTERACTION_CONTRACT — взаимодействие, keyboard и focus

> **Пакет:** UX-001 v0.3  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

## 1. Surface selection

| Задача | Surface |
|---|---|
| routeable object, long/multi-step form | page |
| inspect without losing context | drawer |
| short blocking decision | modal |
| commands | menu |
| short explanation | tooltip |
| interactive contextual detail | popover |

Nested blocking overlays prohibited.

## 2. Save model

### Autosave допустим

- active draft operational journal entry;
- personal display preferences;
- reversible local UI state.

### Explicit save обязателен

- source-bound structured record;
- evidence-bearing relation change;
- registration;
- correction/annulment;
- lifecycle transition;
- publication/configuration;
- shift handover.

Autosave never registers or publishes implicitly.

## 3. Save truth

```text
Без изменений
Изменено локально
Сохраняется…
Сохранено 23:41:18
Ошибка сохранения — повторить
Конфликт версии — открыть сравнение
```

Server acknowledgement is source of truth. Retry idempotent. Error remains visible until resolved or explicitly dismissed where safe.

## 4. Dirty state and leaving

Confirmation appears only when loss is real: unsaved structured form, failed autosave with local changes, unresolved conflict or incomplete critical transition. No confirmation for clean or server-confirmed autosaved state.

## 5. Optimistic vs confirmed

Optimistic: filter chip, expand/collapse, local view preference.

Server-confirmed: structured save, relation change, registration, transition, correction, publication, shift handover.

Final success is never shown before server confirmation.

## 6. Validation

- server authoritative;
- inline error near field;
- error summary for multiple/cross-section errors;
- focus moves to summary or first invalid control;
- collapsed section with error opens;
- values preserved;
- non-color cues;
- no expensive validation on every keystroke.

## 7. Navigation and context

List state encoded in URL where practical:

```text
?q=&status=&equipment=&date_from=&date_to=&sort=&page=&view=&columns=
```

Back restores filters, sort, page, selected row, nearest scroll anchor and user-specific column layout. Deep link works independently and explains unavailable source context.

## 8. Keyboard precedence

Priority:

1. native text editing;
2. active component;
3. active overlay;
4. workspace shortcut;
5. browser shortcut.

No single-letter global shortcuts without modifier.

## 9. Operational journal keyboard contract

| Key | Contract |
|---|---|
| `Ctrl+Enter` | finish/save active entry only when editor context defines it |
| `Escape` | close top overlay, then exit editor by explicit rule; never discard silently |
| `Ctrl+Left/Right` | native word navigation in editor |
| `Home/End` | native current-editor behavior |
| `PgUp/PgDown` | native in text control; journal navigation only outside editor or with explicit modifier |
| `Tab/Shift+Tab` | logical controls, no trap |
| `Ctrl+Z/Y` | editor undo/redo |
| `Enter` | component-specific; never global submit from multiline editor |

Exact contenteditable behavior requires runtime test and cannot be declared complete from video.

## 10. Focus

- page load does not steal focus except explicit creation or validation;
- focus-visible always rendered;
- modal traps and returns focus;
- drawer/popover returns to invoker;
- toast does not steal focus;
- inserted row receives focus only after explicit add;
- programmatic focus does not reset caret unexpectedly;
- scroll into view uses stable anchor and avoids page jump.

## 11. Overlay order

At most one blocking overlay.

Close order:

1. menu/popover;
2. drawer;
3. modal according to its own critical rule.

Outside click closes clean menu/popover, may close clean nonmodal drawer, and never silently closes dirty form or critical modal. All overlays share canonical root/top-layer strategy.

## 12. Search and picker

- typing does not block main thread;
- Enter selects/executes according to component state;
- Escape closes suggestions before clearing query;
- arrows navigate results;
- selected value announced;
- long result identity remains available;
- request race does not replace newer results with older response;
- loading/error/empty states explicit.

## 13. Data grid

Two possible models must not be mixed.

### Row navigation model

Tab reaches row actions/links; arrows may move selected row only when explicitly documented.

### Interactive grid model

ARIA grid semantics, cell focus and arrow navigation.

Default for first slices: row navigation model unless spreadsheet-like editing is truly needed.

Horizontal scroll must be keyboard accessible, show hidden-column affordance, auto-scroll focused content into view and preserve visible identity.

## 14. Selection

- checkbox separate from record link;
- selected state distinct from focus;
- bulk actions appear only with selection;
- incompatible filter change clears selection with explicit notice.

## 15. Permissions

1. not applicable — absent;
2. applicable but no permission — visible with reason when awareness matters;
3. temporarily unavailable — disabled with required condition.

Backend remains authoritative.

## 16. Registered record

- values rendered, not disabled inputs;
- immutability explained;
- correction/annulment separate;
- original remains accessible;
- new revision/event stores reason, actor and time;
- direct mutation rejected server-side.

## 17. Lifecycle transition

Review includes current → target, action verb, actor role, required fields/comment, consequences, reversibility and affected relations. Generic `Выполнить` prohibited.

## 18. Responsive interaction

### Desktop

Full capability.

### Narrow

Collapsed nav, stacked filters, one-column detail, controlled table overflow; drawer may become full-height panel.

### Smartphone auxiliary

Read/search/status/relations and separately approved safe actions. No implied support for full journal ribbon, import review or complex lifecycle configuration.

## 19. Known defect regression gates

| Defect | Pass criterion |
|---|---|
| caret position | explicit focus places caret at expected editable end without unwanted scroll |
| native Ctrl navigation | stays in active entry and follows native words |
| Home/End | current editor behavior |
| PgUp/PgDown | no unexpected whole-page jump |
| semantic target edit | target/text changed without deleting relation |
| copy/paste marker | one semantic relation produces one intended marker |
| undo/redo | relation and text restore consistently |
| blank click | no scroll or selection jump |
| overlay | correct layer, close order and focus return |
| drawer | no document reflow in accepted mode |
| autosave | truthful state after success/error/conflict |
| horizontal grid | focus and identity preserved while scrolling |

## 20. Evidence required for acceptance

Keyboard-only capture, mouse capture, network failure simulation, version conflict, 200% zoom, target desktop and narrow viewport, light theme, dark theme if in release scope, long Russian data and automated regression where feasible.
