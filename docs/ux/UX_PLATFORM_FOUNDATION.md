# UX-PLATFORM-FOUNDATION-001 — factual inventory и ownership map

**Статус:** `IN_PROGRESS / IMPLEMENTATION`

**Контур:** issue #69 / Draft PR #70 / `ux/ux-platform-foundation-001`

**Visual DNA:** Direction A, accepted DEFECT, accepted OPJ, UX-THEME-001, Onest, Consolas, first-party SVG iconography.

Этот документ фиксирует factual ownership текущего work item. Он не является `PAGE-TEMPLATE-LIBRARY-001` и не объявляет broad legacy migration выполненной.

## 1. Platform ownership после extraction

| Concern | Canonical owner | Контракт |
|---|---|---|
| Application shell | `src/templates/base.html` + `shared/direction_a/_sidebar.html` + `_topbar.html` | один sidebar/topbar/page-stage; feature shell copies запрещены |
| Responsive shell geometry | `src/static/system/ux_platform.css` | desktop/tablet/mobile без `zoom`/`transform: scale` |
| Semantic theme/tokens | `src/static/system/theme.css` | единственный owner colours/surfaces/text/borders/status/focus/spacing/radii/heights/typography/z-layers |
| Legacy geometry aliases | `src/static/system/ux_platform_compat.css` | только имена старых `--da-*`, значения всегда принадлежат `--theme-*`; временная migration boundary |
| Shared visual primitives | `src/static/system/ux_platform.css` | Direction A controls/composition; feature CSS не создаёт вторую систему |
| Shared interactions | `src/static/system/direction_a.js` | shell nav, menu, tabs, dialog, drawer, keyboard/focus return |
| Theme preference | inline first-paint resolver + `theme.js` | `light/dark/system` до первого theme-dependent stylesheet paint |
| Module-aware navigation | `system.templatetags.module_navigation` | projection of `decide_module_access(... READ, NAVIGATION_UI)`; no second activation semantics |
| Specialised OPJ workspace | `operational_log/*` | ledger/editor/command-specific geometry remains specialised |
| DEFECT domain presentation | `equipment_defects/*` | lifecycle/domain content stays specialised; shell/theme ownership promoted to platform |

## 2. Factual pattern map

| Existing pattern | Classification | Foundation decision |
|---|---|---|
| Direction A sidebar/topbar | `PROMOTE TO SHARED` | promoted into root application shell |
| historical horizontal presentation shell in `base.html` | `LEGACY / REMOVE` | removed from active authenticated shell |
| `shared/direction_a/base.html` second body/shell | `LEGACY / REMOVE` | collapsed to compatibility inheritance wrapper |
| `direction_a_shell_final.css` late shell repair | `LEGACY / REMOVE` | removed; geometry owned by `ux_platform.css` |
| `direction_a.css` raw palette + duplicate shared shell/primitives | `LEGACY / REMOVE` | accepted Direction A contracts consolidated into semantic `ux_platform.css`, old owner deleted |
| DEFECT `_direction_a_sidebar.html` / `_direction_a_topbar.html` | `LEGACY / REMOVE` | deleted; forms consume shared shell |
| DEFECT registry/detail/forms | `ADAPT` | shared shell/tokens/controls; domain lifecycle/table/form semantics retained |
| DEFECT `--ux-*` / `--defect-*` aliases | `COMPATIBILITY` | aliases resolve through `--theme-*`; broad selector cleanup deferred |
| OPJ registry | `ADAPT` | common shell/tokens/table/panel primitives |
| OPJ registered detail | `ADAPT + SPECIALIZED` | common shell/theme, registered journal/print/action behavior retained |
| OPJ shift workspace | `SPECIALIZED` | operational density, ledger/editor, drawer/context rail remain journal-owned |
| OPJ CSS/JS globally loaded from `base.html` | `LEGACY / REMOVE` | scoped to `operational_log` namespace only |
| account/settings | `KEEP / SHARED CONSUMER` | common shell/theme/controls; no new page family introduced |
| master-data/system routes | `KEEP / SHARED CONSUMER` | shared root shell available; route-by-route cleanup deferred |
| browser theme harness | `PROMOTE / EXTEND EXISTING` | remains sole browser/screenshot platform; no parallel harness |

## 3. Shared primitive vocabulary implemented now

Foundation owns primitive contracts for:

- page header / breadcrumbs / toolbar / action group;
- primary / secondary / tertiary / danger / compact action;
- icon button;
- text input / textarea / select / checkbox / switch / search;
- card / section / panel;
- table/register and selected/hover row states;
- status chip / badge / counter;
- tabs;
- dropdown/action menu;
- native dialog and drawer surfaces;
- toast/system message;
- empty / loading / error / read-only / disabled states;
- shared focus-visible, touch/control heights and reduced-motion baseline.

Это не component framework и не page template library. Примитивы используют существующие `da-*` contracts или нейтральные `ux-*` contracts и не вводят новый frontend framework.

## 4. Theme and first-paint contract

1. `data-theme-preference` приходит из accepted UI preferences.
2. Inline resolver в `<head>` выбирает `light/dark` до первого stylesheet.
3. `theme.css` владеет semantic values для обеих тем.
4. Feature/specialised CSS может владеть geometry, но не альтернативной theme architecture.
5. Print остаётся deterministic light presentation; screen shell скрывается.

## 5. Responsive/accessibility baseline

Canonical baseline:

- desktop: `1440×900`;
- tablet: `1024×768`;
- mobile: `390×844`;
- sidebar становится drawer-like navigation без масштабирования desktop UI;
- critical actions remain reachable;
- tables remain horizontally scrollable rather than scaled;
- visible `:focus-visible` is system-wide;
- Escape closes shared nav/menu/drawer;
- tablist supports arrow/Home/End focus navigation;
- dialog/drawer/menu interactions return focus to the invoking control;
- icon-only system controls retain accessible text;
- new motion obeys `prefers-reduced-motion`.

## 6. DEFECT stress test boundary

DEFECT is the reference business UI. In this work item:

- registry/detail already consuming Direction A remain consumers of shared shell/tokens;
- registration and lifecycle action forms no longer render their own shell copies;
- shared action contracts are added without changing defect lifecycle or form semantics;
- historical repair selectors remain where removal would become broad route migration.

The remaining repair files are **not** declared clean or eliminated. Their broad selector consolidation, dead selector deletion and route-by-route markup normalization belong to `LEGACY-UX-MIGRATION-001` after the foundation is accepted.

## 7. OPJ stress test boundary

OPJ proves the platform is not only CRUD-oriented:

- shared shell/theme/navigation/control baseline applies to OPJ;
- OPJ specialised assets are no longer global application assets;
- registered ledger geometry, draft editor, command ribbon, context rail/drawers, keyboard-oriented journal behavior, autosave, revisions, locking, immutable registration and print semantics remain OPJ-owned.

A shared primitive is not forced into the ledger/editor when it would weaken the accepted operational workspace.

## 8. Explicitly deferred to PAGE-TEMPLATE-LIBRARY-001

Not implemented here:

- registry/list family contract;
- detail/card family contract;
- create/edit form family contract;
- complex journal family contract;
- specialist workspace family contract;
- master-detail, timeline/history, settings/reference and dashboard/home family compositions.

Current compositions exist only as real consumers used to prove primitive stability.

## 9. Explicitly deferred to LEGACY-UX-MIGRATION-001

- broad route-by-route conversion of old markup;
- full collapse/removal of historical DEFECT repair selector files;
- removal of every old compatibility class/alias;
- cleanup of unrelated old `app.css`/feature selectors;
- representative legacy routes not needed to prove this foundation.

This is a migration boundary, not hidden debt removal by another override layer.

## 10. Acceptance evidence contract

Final evidence must be produced on one exact PR head and include the existing browser harness for representative DEFECT + OPJ routes in light/dark and desktop/tablet/mobile, applicable transient states and existing print contract. Final exact-head repository gates and trusted Development delivery must use that same SHA where applicable.