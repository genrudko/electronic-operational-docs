# UX-PLATFORM-FOUNDATION-001 — Repair v5 geometry inventory

**Статус:** `IN_PROGRESS / IMPLEMENTATION INPUT`

**Контур:** issue #69 / branch `ux/ux-platform-foundation-001` / Draft PR #70.

Repair v5 не создаёт `PAGE-TEMPLATE-LIBRARY-001`. Таблица фиксирует только владельца геометрии существующих primitives и текущих owner-visible consumers.

| Recurring component | Current variants / defect | Canonical contract owner | Consumers to migrate / verify |
|---|---|---|---|
| Page header | generic `da-page-header`, compact, Import balanced, DEFECT nested heading-row, OPJ specialised header | `system/ux_platform.css` + `ux_platform_compositions.css`: stable left title anchor, optional context/kicker/subtitle, actions in predictable end zone, controlled stack | Home, Documents, Equipment, Dispatching, Imports, Normatives, Operational Documents, Workplace Docs, DEFECT, OPJ |
| Section header | `da-panel-heading`, generic `.section-heading`, feature headers with incompatible insets | shared section/card heading rhythm | Home rules block, Imports, Documents, Account, Equipment, DEFECT |
| Card / panel | `da-card`, `da-panel`, feature cards with arbitrary 5–24 px inset | shared regular / compact / dense geometry based on existing spacing scale | generic routes; specialised DEFECT/OPJ/Personnel consume density levels |
| Button | `da-button`, DEFECT `defect-button`, Personnel row actions, OPJ local controls | shared regular/compact/icon geometry; semantic state owns text/fill; enabled button cannot be blank | all core routes; DEFECT action panel; Personnel row actions; OPJ toolbar/row actions |
| Icon button | `da-icon-button` plus feature controls | square platform control, canonical SVG icon, shared focus/hover/disabled state | shell, OPJ, dialogs |
| Form action | `ux-form-actions`, feature footers and lone filter submit buttons | shared action row; desktop end alignment, narrow controlled stack/full-width | generic forms, Personnel Import, Dispatching filters |
| Field grid | `ux-form-grid`, Personnel feature grid, arbitrary half-width leftovers | 12-column semantic spans exposed as full/half/third/two-thirds, one-column collapse | Documents/forms, Personnel Import, other generic forms |
| Metric grid | fixed 4-column and feature-specific grids causing 3+1 / 4+1 | auto-fit responsive grid with one readable minimum card width | Home, Structured Journals, Imports, Equipment, Documents, Personnel summary |
| Table | `da-table`, Personnel custom table, DEFECT/OPJ dense tables | shared regular/compact cell rhythm; feature dense profile only where workflow requires it | generic registers; Personnel; DEFECT/OPJ as specialised dense consumers |
| Table actions | flex implementations without minimum geometry | shared compact action group; no clipping/collision; controlled wrap | Personnel `Карточка` / `Изменить`, future row actions |
| Primary / secondary / technical text | inline spans/codes and feature stacks | shared `ux-value-stack` / primary / secondary / technical; explicit gap and wrapping | Workplace Docs, Equipment relations, Imports, Operational Documents, Personnel tree |
| Human label + technical code | Workplace Docs repaired, Equipment still inline `code · label` | same value-stack contract; human label primary, internal ID monospace secondary | Workplace Docs, Equipment relations/parents/children, applicable imports/docs |
| Status / lifecycle | shared chips plus DEFECT feature lifecycle | shared chip geometry; DEFECT owns lifecycle semantics only; terminal current stage visually reached | generic status chips, DEFECT detail |
| Tree row | Personnel directory and Operational Rights use different geometry | reusable tree-row rhythm: indent lane, icon, text stack, optional count/status | Personnel main tree; Operational Rights regression/reference |
| Sidebar identity | one-line ellipsis with full value only in `title`/hover | two-line readable identity with role secondary and bounded height | shared sidebar |
| Workspace width | one generic max-width; feature overrides | Normal / Wide / Specialist-Full profiles without stretching every route | normal CRUD, Personnel/authority wide, OPJ full/specialist |
| OPJ toolbar | local small controls, pale enabled state | specialised consumer of platform control size/state tokens; minimum click target and explicit enabled/disabled/current states | OPJ workspace toolbar, row actions, spread/full views |

## Positive references to preserve

- Account/settings: spacing, 2×2 card composition and hierarchy.
- Workplace Documentation: human label / technical code / applicability stack.
- Operational Rights: cleaner tree rhythm than the current Personnel main tree.
- Repair v4 login, Import header repair, DEFECT dark-link/status repair and OPJ SVG disclosure icon are not to be reverted.

## Ownership boundary

Generic geometry is owned only by shared platform CSS. Feature styles may define domain composition (DEFECT lifecycle layout, OPJ ledger/editor, Personnel master-detail workspace), but do not redefine generic button, card, field, status or table-action contracts.
