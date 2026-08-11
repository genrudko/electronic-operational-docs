# UX-PLATFORM-FOUNDATION-001

## STATUS

`IN_PROGRESS / FINAL REPAIR EVIDENCE`

Issue: `#69`

Branch: `ux/ux-platform-foundation-001`

Draft PR: `#70 / OPEN / DRAFT / NOT MERGED`

Owner visual acceptance: `PENDING`

## EXACT BASELINE SHA

Live `main` at contour creation:

`1befcb73a8a6f7cc03c2e18d292cbb2c85ef6594`

Accepted `MODULE-REGISTRY-001` exact head:

`f00d99b6434477c7bcefceff5253d6ccbe4a5fca`

## GOAL

Turn the accepted Direction A / DEFECT / OPJ / UX-THEME visual language into one shared EOD UX platform: shared application shell, semantic design tokens, reusable visual/interaction primitives and stable UX contracts, proven across ordinary core routes and specialised DEFECT/OPJ surfaces.

## OWNER REPAIR V3 SCOPE OVERRIDE

The initial Foundation brief prohibited broad route-by-route migration. Owner review found that boundary too narrow because ordinary core navigation and form/detail surfaces still exposed a second generic presentation system.

The accepted Repair v3 boundary supersedes that narrow interpretation:

- ordinary owner-visible core routes, including list/detail/create/edit/form surfaces, **must** be platform-native inside this work item;
- the public login/account surfaces **must** be platform-native and mobile-focus safe;
- DEFECT and OPJ remain specialised only for domain/workspace geometry while consuming shared shell/theme/generic controls;
- all active owner-visible template roots are covered by a blocking source contract;
- a complete route/template inventory must classify `PLATFORM-NATIVE`, `SPECIALIZED-INTENTIONAL` and any real `DEFERRED` surfaces with reason;
- broad dead-selector/compatibility cleanup remains future `LEGACY-UX-MIGRATION-001` work and must not be confused with current route migration.

## REQUIRED IMPLEMENTATION

- one shared application shell and module-aware navigation owner;
- one semantic token owner for colour, surface, typography, spacing, geometry, interaction states and layer ordering;
- shared controls/primitives only where system purpose or real consumers justify them;
- shared JS ownership for shell/dropdown/dialog/drawer/tabs/notification/keyboard interactions where applicable;
- platform-native ordinary core route presentation;
- DEFECT reference integration without a second local generic design system;
- OPJ shared shell/tokens/controls integration while preserving specialised operational ledger/editor geometry;
- light / dark / system first-paint stability;
- keyboard/focus/accessibility engineering baseline;
- deterministic print isolation where existing print contracts apply;
- Development demo accounts `operator.demo` and `supervisor.demo` bootstrapped safely against Development PostgreSQL with real server-side authentication;
- source-level prohibition of viewport zoom locks/layout scaling hacks;
- final browser matrix on desktop `1280×800`, `1366×768`, `1536×864`, `1920×1080` and mobile `390×844`, `412×915`, `430×932`;
- screen + fullpage screenshots, runtime console/page errors, width/heading/content geometry and mobile `visualViewport.scale` focus evidence;
- deterministic dependency inventory regeneration;
- one final exact-head applicable CI cycle;
- trusted persistent Development deployment of that exact SHA with credential-safe auth/health verification;
- `behind_by: 0`, Preview untouched and clean repository state.

## HARD BOUNDARIES

Do **not** implement `PAGE-TEMPLATE-LIBRARY-001`, full historical `LEGACY-UX-MIGRATION-001`, new product modules, Module Registry redesign, domain/lifecycle/security redesign, Preview/pilot/production deployment, Ready for Review or merge.

The prohibition on full `LEGACY-UX-MIGRATION-001` does **not** permit ordinary owner-visible core routes to retain legacy generic presentation ownership; those routes are part of Repair v3 and must be platform-native now.

Existing domain models, migrations, lifecycle semantics, OPJ autosave/revisions/locking/registration/correction/print semantics, DEFECT lifecycle and stored business data are protected.

## STOP CONDITION

Stop only at a technically and visually complete Draft PR ready for direct owner visual acceptance:

- one final exact head;
- source contract, full Django suite and applicable project gates green;
- complete seven-viewport browser evidence and mobile focus proof green;
- deterministic dependency inventory exact on the same head;
- trusted persistent Development deployed at that same SHA and verified;
- `behind_by: 0`;
- Preview untouched;
- `OWNER VISUAL ACCEPTANCE = PENDING` until actual owner review.

Ready for Review and merge remain prohibited until explicit owner instruction.
