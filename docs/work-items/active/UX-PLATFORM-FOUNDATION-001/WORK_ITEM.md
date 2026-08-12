# UX-PLATFORM-FOUNDATION-001

## STATUS

`ACCEPTANCE_CANDIDATE / FINAL GATES`

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
- final browser evidence covering representative wide/desktop/tablet/mobile owner states, including mobile focus/layout proof;
- deterministic dependency inventory regeneration;
- one final exact-head applicable CI cycle;
- trusted persistent Development deployment of that exact SHA with credential-safe auth/health verification;
- `behind_by: 0`, Preview untouched and clean repository state.

## REPAIR V4 ACCEPTANCE-CANDIDATE EVIDENCE

The owner-rejected Development candidate was repaired against the concrete `UX-VIS-01 ... UX-VIS-23` walkthrough findings rather than by route-local cosmetic overrides.

The final focused Repair v4 browser evidence was repeated on exact UI/evidence head `02f1508de5bf8ca73d2531781ad1b4750cedbc1b` and is `PASS` with `failures=[]` and 33 retained screenshots. That exact-head Development Stack also passed readiness, real demo login, canonical organization/dispatching/workplace/OPJ fixtures, canonical DEFECT Module Registry activation, guarded DEFECT presentation seeding, post-browser health, database identity, private-port isolation and clean-tree verification.

Representative Repair v4 evidence includes:

- dark OPJ normative-marker tooltip with platform-owned surface/text semantics, viewport containment and measured contrast `12.35:1`;
- OPJ wide/spread workspace and mobile page-level overflow containment;
- canonical OPJ drawer disclosure iconography and enabled/disabled toolbar states;
- DEFECT lifecycle states without whole-component opacity fading and with measured future-state text contrast about `4.57:1`;
- one DEFECT status presentation mapping across dedicated DEFECT and generic Operational Documents views through canonical domain/schema metadata rather than translated labels or ad-hoc status strings;
- DEFECT dark links/disclosures, long status chips and approved-journal presentation in both themes;
- Workplace Documentation label/code/applicability hierarchy on desktop and a settled mobile-entry shell at `390×844` with `scrollWidth == innerWidth == 390`, navigation closed and sidebar `aria-hidden=true`;
- Import, Organization/current-user identity, Equipment relations, Dispatching semantic differentiation, Structured Journals metric geometry, public wide composition, Development credential presentation and account/mobile regression evidence.

The earlier apparent Workplace mobile sidebar overlap was traced to a transient desktop-to-mobile resize frame in the evidence runner. The acceptance evidence now re-enters the route at the mobile viewport and explicitly verifies the settled shell state; the resulting PNG was visually reviewed and is clean.

### Trusted-controller boundary

The focused browser evidence was temporarily wired into `.github/workflows/development-stack.yml` while Repair v4 defects were being isolated. That workflow change is **not** part of the product/runtime deliverable and cannot remain in a PR that must deploy itself through AUTO-001B: trusted policy intentionally blocks PRs changing `.github/workflows/**` from invoking the privileged Development controller.

Before the final deployable candidate, `.github/workflows/development-stack.yml` was restored byte-for-byte to the trusted `main` version (`7e74a4f8ca85b631b49b303d6eb118e64ab72e2f`). The temporary self-deleting inventory-sync workflow is also absent from the resulting tree. Therefore the final PR diff contains no `.github/workflows/**` change and does not weaken or bypass the AUTO-001A/AUTO-001B security boundary.

No application/runtime presentation file changed after the `02f1508...` browser evidence. Subsequent changes are limited to restoration of the trusted workflow boundary, generator-owned dependency inventory projections and this work-item evidence record. Thus `02f1508...` remains the runtime-identical automated visual predecessor, while the final persistent Development deployment and the owner's walkthrough are performed on the final controller-compatible exact SHA.

The canonical dependency inventory was regenerated from the repository generator after both addition of the focused browser runner and restoration of the trusted Development workflow. Temporary write-capable sync workflows removed themselves before generation and are absent from the resulting repository tree; generated inventory content was not manually edited.

This section records technical candidate evidence only. It does **not** claim owner visual acceptance. Owner acceptance remains `PENDING` until the owner performs the new persistent Development walkthrough.

## HARD BOUNDARIES

Do **not** implement `PAGE-TEMPLATE-LIBRARY-001`, full historical `LEGACY-UX-MIGRATION-001`, new product modules, Module Registry redesign, domain/lifecycle/security redesign, Preview/pilot/production deployment, Ready for Review or merge.

The prohibition on full `LEGACY-UX-MIGRATION-001` does **not** permit ordinary owner-visible core routes to retain legacy generic presentation ownership; those routes are part of Repair v3 and must be platform-native now.

Existing domain models, migrations, lifecycle semantics, OPJ autosave/revisions/locking/registration/correction/print semantics, DEFECT lifecycle and stored business data are protected.

## STOP CONDITION

Stop only at a technically and visually complete Draft PR ready for direct owner visual acceptance:

- one final exact head;
- source contract, full Django suite and applicable project gates green;
- focused Repair v4 browser evidence and mobile proof green on the runtime-identical visual predecessor;
- deterministic dependency inventory exact for the final head;
- trusted persistent Development deployed at the final exact SHA and verified;
- `behind_by: 0`;
- Preview untouched;
- `OWNER VISUAL ACCEPTANCE = PENDING` until actual owner review.

Ready for Review and merge remain prohibited until explicit owner instruction.
