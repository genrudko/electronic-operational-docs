# UX-PLATFORM-FOUNDATION-001

## STATUS

`IN_PROGRESS / IMPLEMENTATION`

Issue: `#69`

Branch: `ux/ux-platform-foundation-001`

Draft PR: `#70 / OPEN / DRAFT / NOT MERGED`

## EXACT BASELINE SHA

Live `main` at contour creation:

`1befcb73a8a6f7cc03c2e18d292cbb2c85ef6594`

Accepted `MODULE-REGISTRY-001` exact head:

`f00d99b6434477c7bcefceff5253d6ccbe4a5fca`

## GOAL

Turn the accepted Direction A / DEFECT / OPJ / UX-THEME visual language into one shared EOD UX platform: shared application shell, semantic design tokens, reusable visual/interaction primitives and stable UX contracts, proven on both DEFECT and OPJ without a big-bang rewrite.

## CANONICAL TRANSITION

Started with the bounded post-merge transition:

1. `MODULE-REGISTRY-001 = ACCEPTED` with PR #68, accepted exact head `f00d99b6434477c7bcefceff5253d6ccbe4a5fca`, merge commit `1befcb73a8a6f7cc03c2e18d292cbb2c85ef6594`, issue #67 CLOSED / COMPLETED and owner acceptance PASSED;
2. `UX-PLATFORM-FOUNDATION-001 = IN_PROGRESS`;
3. active contour moved to issue #69 / branch `ux/ux-platform-foundation-001` / Draft PR #70;
4. immutable acceptance/baseline history and deterministic planning views remain part of the same canonical transition boundary.

No separate reconciliation work item is created.

## REQUIRED IMPLEMENTATION

- one shared application shell and module-aware navigation owner;
- one semantic token owner for colour, surface, typography, spacing, geometry, interaction states and layer ordering;
- shared controls/primitives only where system purpose or real consumers justify them;
- shared JS ownership for shell/dropdown/dialog/drawer/tabs/notification/keyboard interactions where applicable;
- DEFECT reference integration without a second local design system;
- OPJ shared shell/tokens/controls integration while preserving specialised operational ledger/editor geometry;
- light / dark / system first-paint stability;
- desktop / tablet / mobile behavior;
- keyboard/focus/accessibility engineering baseline;
- deterministic print isolation where existing print contracts apply;
- focused browser/visual evidence during implementation and one coherent final matrix on the final exact head;
- final exact-head applicable CI and trusted Development candidate if repository delivery supports it.

## HARD BOUNDARIES

Do not implement `PAGE-TEMPLATE-LIBRARY-001`, `LEGACY-UX-MIGRATION-001`, new product modules, broad route-by-route migration, Module Registry redesign, domain/lifecycle/security redesign, Preview/pilot/production deployment, Ready for Review or merge.

Existing domain models, migrations, lifecycle semantics, OPJ autosave/revisions/locking/registration/correction/print semantics, DEFECT lifecycle and stored business data are protected.

## STOP CONDITION

Stop only at a technically and visually complete Draft PR ready for direct owner visual acceptance: one final exact head, `behind_by: 0`, clean repository state, applicable exact-head gates green, coherent DEFECT+OPJ visual evidence and Development deployed at that same SHA if the trusted delivery path is applicable.
