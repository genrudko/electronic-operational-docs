# UX-PLATFORM-FOUNDATION-001 — factual inventory и ownership map

**Статус:** `IN_PROGRESS / FINAL REPAIR EVIDENCE`

**Контур:** issue #69 / Draft PR #70 / `ux/ux-platform-foundation-001`

**Visual DNA:** Direction A, accepted DEFECT, accepted OPJ, UX-THEME-001, Onest, Consolas, first-party SVG iconography.

Этот документ фиксирует factual ownership текущего work item. Он не является `PAGE-TEMPLATE-LIBRARY-001` и не объявляет broad historical CSS cleanup завершённым.

## 1. Repair v3 supersession

Первоначальная граница Foundation разрешала оставить route-by-route cleanup на будущий `LEGACY-UX-MIGRATION-001`. После owner review эта граница была уточнена.

Внутри **этого** work item обязательны:

- platform-native presentation ownership для обычных owner-visible core routes;
- platform-native login/account и обычных list/detail/create/edit/form surfaces;
- отсутствие legacy generic presentation classes во всех owner-visible template roots;
- сохранение OPJ и DEFECT как специализированных consumers общего shell/theme/primitives;
- полный factual route/template inventory;
- exact browser evidence на установленной viewport matrix;
- trusted Development deployment exact SHA до owner visual acceptance.

На будущий `LEGACY-UX-MIGRATION-001` остаётся только broad cleanup исторических CSS selectors/aliases/dead compatibility, а не миграция обычных core pages.

## 2. Platform ownership после extraction

| Concern | Canonical owner | Контракт |
|---|---|---|
| Application shell | `src/templates/base.html` + `shared/direction_a/_sidebar.html` + `_topbar.html` | один sidebar/topbar/page-stage; feature shell copies запрещены |
| Responsive shell geometry | `src/static/system/ux_platform.css` | desktop/mobile без viewport lock, `zoom` или layout `transform: scale` hacks |
| Semantic theme/tokens | `src/static/system/theme.css` | единственный owner colours/surfaces/text/borders/status/focus/spacing/radii/heights/typography/z-layers |
| Legacy geometry aliases | `src/static/system/ux_platform_compat.css` | только migration aliases; значения принадлежат platform/theme tokens |
| Shared visual primitives | `src/static/system/ux_platform.css` + `ux_platform_compositions.css` | Direction A controls/compositions; feature CSS не создаёт вторую generic system |
| Public/auth composition | `src/static/system/ux_platform_public.css` | login surface + source-level mobile focus safety |
| Shared interactions | `src/static/system/direction_a.js` | shell nav, menu, tabs, dialog, drawer, keyboard/focus return |
| Theme preference | inline first-paint resolver + `theme.js` | `light/dark/system` до первого theme-dependent stylesheet paint |
| Module-aware navigation | `system.templatetags.module_navigation` | projection of module access; no second activation semantics |
| Specialised OPJ workspace | `operational_log/*` | ledger/editor/command geometry remains specialised while shell/theme are shared |
| DEFECT domain presentation | `equipment_defects/*` | lifecycle/domain content stays specialised; shell/theme/generic controls belong to platform |

## 3. Source-level migration guard

`src/apps/system/tests/test_ux_platform_migration_contract.py` recursively audits these owner-visible roots:

`system`, `organizations`, `documents`, `equipment`, `dispatching`, `normatives`, `imports`, `workplace_docs`, `operational_documents`, `equipment_defects`, `operational_log`.

Except specialised `print.html`, none may use legacy generic presentation tokens including `page-heading`, generic `button`, `profile-card`, `profile-grid`, `metric`, `summary-grid`, `table-wrap`, legacy auth shell/card/form, generic status/error/empty-state ownership.

Feature/domain classes are allowed only when they describe real feature semantics rather than a second generic design system.

The same gate rejects `user-scalable=no`, `maximum-scale=1`, `zoom:` and unexpected `transform: scale(...)` declarations. The five pre-existing OPJ micro-animation declarations in `app.css` are explicitly bounded by exact declaration/count and are not viewport/layout scaling.

## 4. Complete active template inventory

Factual count at Repair v3: **87 HTML templates** under active `src/templates`.

### 4.1 PLATFORM-NATIVE

These surfaces use the shared application shell/theme and no legacy generic presentation ownership.

| Area | Route surface | Templates |
|---|---|---|
| Root/shared shell | all authenticated consumers | `base.html`; `shared/direction_a/base.html`; `shared/direction_a/_sidebar.html`; `shared/direction_a/_topbar.html` |
| Home | `/` | `system/home.html` |
| Documents | `/documents/`; `/documents/new/`; detail/edit/register; link action | `documents/list.html`; `documents/form.html`; `documents/detail.html`; `documents/register_confirm.html` |
| Equipment | `/equipment/`; site detail; item detail; selector endpoint supports forms | `equipment/registry.html`; `equipment/site_detail.html`; `equipment/detail.html` |
| Dispatching | `/dispatching/`; `/dispatching/subjects/`; equipment detail | `dispatching/registry.html`; `dispatching/subjects.html`; `dispatching/equipment_detail.html` |
| Normatives | registry; evidence registry; legal-mode/event details; document/revision details | `normatives/registry.html`; `normatives/evidence_registry.html`; `normatives/legal_mode_decision_detail.html`; `normatives/evidence_event_detail.html`; `normatives/document_detail.html`; `normatives/revision_detail.html` |
| Imports | `/imports/` workflows for generic, personnel, power-system and workplace-document imports; upload/detail/mapping/edit/publication/results | `imports/data_profiles.html`; `imports/detail.html`; `imports/list.html`; `imports/mapping.html`; `imports/personnel_detail.html`; `imports/personnel_list.html`; `imports/personnel_publication.html`; `imports/personnel_publication_result.html`; `imports/personnel_upload.html`; `imports/power_system_detail.html`; `imports/power_system_list.html`; `imports/power_system_publication.html`; `imports/power_system_publication_result.html`; `imports/power_system_upload.html`; `imports/publication.html`; `imports/publication_result.html`; `imports/row_edit.html`; `imports/upload.html`; `imports/workplace_document_detail.html`; `imports/workplace_document_list.html`; `imports/workplace_document_publication.html`; `imports/workplace_document_publication_result.html`; `imports/workplace_document_upload.html` |
| Workplace documentation | registry, current/revision detail | `workplace_docs/registry.html`; `workplace_docs/detail.html` |
| Structured operational documents | registry; type registry/create/detail; record choose/create/detail/edit/transition | `operational_documents/registry.html`; `operational_documents/type_registry.html`; `operational_documents/type_form.html`; `operational_documents/type_detail.html`; `operational_documents/choose_type.html`; `operational_documents/record_form.html`; `operational_documents/record_detail.html` |
| Public/account + ordinary personnel forms | login/logout/account; organization create/edit; personnel import; qualification/right/contact form routes use shared presentation ownership | `organizations/login.html`; `organizations/account.html`; `organizations/organization_form.html`; `organizations/personnel_import_upload.html`; `organizations/personnel_import_detail.html`; `organizations/personnel_record_form.html` |

`/health/`, selector/decision/download/transition endpoints and other action-only URLs do not own separate HTML presentation and therefore are not missing route templates.

### 4.2 SPECIALIZED-INTENTIONAL

These surfaces consume the common platform shell/theme but retain domain-specific geometry or interaction semantics that generic primitives must not erase.

| Area | Why specialised | Templates |
|---|---|---|
| Personnel / authority workspace | organization tree, employee editor/detail, authority registry/evaluation and external operational contact semantics | `organizations/directory.html`; `organizations/employee_detail.html`; `organizations/employee_editor.html`; `organizations/authority_registry.html`; `organizations/authority_evaluation_detail.html`; `organizations/_external_operational_contacts.html` |
| DEFECT | dense defect worklist/journal, lifecycle actions, hierarchy pickers, time-trust controls, approved print form | `equipment_defects/registry.html`; `equipment_defects/detail.html`; `equipment_defects/registration_form.html`; `equipment_defects/action_form.html`; `equipment_defects/print.html`; `equipment_defects/_detail_repair2_aside.html`; `equipment_defects/_detail_repair2_header.html`; `equipment_defects/_detail_repair2_main.html`; `equipment_defects/_registry_repair2_header.html`; `equipment_defects/_registry_repair2_journal.html`; `equipment_defects/_registry_repair2_worklist.html`; `equipment_defects/_time_trust.html` |
| OPJ | registered journal ledger, shift workspace/editor, draft lifecycle, contextual drawer/overlays, normative markers and deterministic print | `operational_log/registry.html`; `operational_log/detail.html`; `operational_log/shift_workspace.html`; `operational_log/print.html`; `operational_log/_normative_markers.html`; `operational_log/_shift_workspace_drawer.html`; `operational_log/_shift_workspace_overlays.html`; `operational_log/_shift_workspace_registered_row.html`; `operational_log/_shift_workspace_rows.html`; `operational_log/_shift_workspace_toolbar.html` |

Specialised does **not** mean separate shell/theme/design system. It means only feature-specific geometry and workflow semantics remain feature-owned.

### 4.3 DEFERRED

**No active owner-visible core route template is deferred by Repair v3.**

Deferred with explicit reason:

- page-family abstraction (`PAGE-TEMPLATE-LIBRARY-001`) — future reusable family contracts, not required to make current real routes platform-native;
- broad historical DEFECT/OPJ selector consolidation and dead selector deletion (`LEGACY-UX-MIGRATION-001`) — cleanup of implementation history after owner acceptance;
- removal of every compatibility alias in old feature/app CSS — only after no consumer remains; changing them now would increase regression risk without adding route coverage.

## 5. Route contract cross-check

Factual URL owners used for the inventory:

- `system`: `/` + non-HTML `/health/`;
- `documents`: list/create/detail/edit/register/link action;
- `equipment`: registry/site/item detail + selector endpoint;
- `dispatching`: registry/subjects/equipment detail;
- `normatives`: registry/evidence/legal-mode/event/document/revision details;
- `imports`: generic/personnel/power-system/workplace-document import lifecycles including publication and decision actions;
- `workplace_docs`: registry/current/revision detail;
- `operational_documents`: type and record registries/forms/details/transitions;
- `organizations`: auth/account, organization/personnel management, personnel import and authority evaluation;
- `equipment_defects`: registry/create/create-from-OPJ/print/detail/deadline/resolution/acknowledge/close;
- `operational_log`: registry/detail/shift workspace/open/draft lifecycle/entry lifecycle/correction/cancel/display/print.

## 6. Shared primitive vocabulary implemented now

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

This is not a component framework or page template library.

## 7. Responsive/accessibility acceptance matrix

Required browser viewport matrix:

### Desktop

- `1280×800`;
- `1366×768`;
- `1536×864`;
- `1920×1080`.

### Mobile

- `390×844`;
- `412×915`;
- `430×932`.

For each representative baseline state the harness records:

- light/dark theme;
- viewport screen screenshot;
- full-page screenshot;
- `scrollWidth` and `innerWidth`;
- rendered heading and content-region geometry;
- console errors and page errors;
- semantic surface/background contract.

Mobile login additionally uses Chromium mobile emulation and records `visualViewport.scale` before focus, after username focus and after password focus, computed font size for both inputs, unfocused/focused screenshots and overflow state. Input focus must remain at scale `1.0` and computed font size must be at least `16px` without disabling user zoom.

## 8. DEFECT stress-test boundary

DEFECT remains the reference specialised business UI:

- registry/detail/forms consume shared shell/theme/generic controls;
- domain lifecycle/table/hierarchy/time-trust semantics remain feature-owned;
- registered print view retains its specialised deterministic print layout;
- old repair files may remain only as feature implementation layers, not alternative generic design ownership.

## 9. OPJ stress-test boundary

OPJ proves the platform is not only CRUD-oriented:

- shared shell/theme/navigation/control baseline applies to OPJ;
- registered ledger geometry, draft editor, command ribbon, context rail/drawers, keyboard-oriented journal behavior, autosave, revisions, locking, immutable registration and print semantics remain OPJ-owned;
- no generic page primitive may flatten the accepted operational workspace.

## 10. Explicitly deferred work items

### PAGE-TEMPLATE-LIBRARY-001

May formalise reusable registry/detail/form/journal/specialist-workspace/master-detail/timeline/settings/dashboard family contracts after this Foundation is owner-accepted. Current real routes do not depend on that abstraction to be platform-native.

### LEGACY-UX-MIGRATION-001

May remove dead selectors, collapse historical repair files and retire remaining compatibility aliases. It must not be used later as justification for leaving an ordinary current route on a second generic presentation system.

## 11. Acceptance evidence contract

Final evidence must be produced on one exact PR head and include:

1. source-level generic presentation ownership guard;
2. Ruff, compile/system/migration/architecture/collectstatic and full Django suite;
3. Development bootstrap + real server-side demo login smoke;
4. representative browser matrix across the seven required viewport sizes, light/dark, screen/fullpage, runtime errors and rendered geometry;
5. mobile login focus proof using `visualViewport.scale`;
6. DEFECT + OPJ transient/regression surfaces and OPJ print isolation;
7. deterministic dependency inventory views for that exact head;
8. trusted persistent Development controller deployment of the same exact SHA;
9. `behind_by: 0` and Preview untouched.

Final report terminology remains separate:

- `AUTOMATED VISUAL EVIDENCE: PASS/FAIL`;
- `DEVELOPMENT AUTHENTICATION SMOKE: PASS/FAIL`;
- `OWNER VISUAL ACCEPTANCE: PENDING/PASS`.

`OWNER VISUAL ACCEPTANCE` can become `PASS` only after actual owner review. Draft PR must not be marked Ready or merged without explicit owner instruction.
