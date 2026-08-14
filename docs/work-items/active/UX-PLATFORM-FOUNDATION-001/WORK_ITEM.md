# UX-PLATFORM-FOUNDATION-001

## STATUS

`REPAIR V13 / IMPLEMENTATION AND GATES`

Issue: `#69`

Branch: `ux/ux-platform-foundation-001`

Draft PR: `#70 / OPEN / DRAFT / NOT MERGED`

Owner visual acceptance: `PENDING`

Latest owner verdict: `RESPONSIVE TRANSITION / COMPACT UX = FAIL` on the Repair v12 Development candidate. Repair v12 technical evidence remains historical evidence only and is superseded for owner acceptance by Repair v13.

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

## REPAIR V7 FINAL UX PLATFORM CLOSURE

Repair v7 responds to the later owner walkthrough without adding a new design system, another repair stylesheet or route-local geometry hacks. It closes the remaining platform ownership defects surfaced by real wide-screen use:

- NORMAL/WIDE/SPECIALIST page allocation now reaches the useful inner workspace rather than stopping at the outer page container;
- Operational Rights remains SPECIALIST and Personnel remains WIDE;
- working and registered OPJ use specialist stage allocation where operational geometry requires it;
- the registered OPJ double width cap was removed so the inner journal no longer defeats the outer specialist allocation;
- Equipment hierarchy and Documents equipment relations use the existing `ux-value-stack` semantic hierarchy for human labels and technical identifiers;
- OPJ toolbar/inset geometry is owned by shared spacing/control tokens instead of route-local magic values;
- Workplace Documentation now exposes the intended `workplace-document-registry` owner class and its long counter is allowed to wrap through the existing readable-value contract, eliminating the real 390 px document overflow found by the first Repair v7 browser run;
- stale source tests were corrected only where they asserted an obsolete literal class string while the semantic `technical-only` contract remained intact.

### Owner viewport decision

Repair v7 acceptance uses the following required matrix:

- `1280×800` — desktop regression;
- `1366×768` — required baseline desktop;
- `1440×900` — desktop regression;
- `1536×864` — desktop regression;
- `1920×1080` — **PRIMARY DESKTOP**;
- `2560×1440` — **REQUIRED WIDE ADAPTIVE**, not optional and not merely a stress viewport;
- `390×844`, `412×915`, `430×932` — mobile regression and focus/overflow coverage.

Additional width is allocated according to NORMAL/WIDE/SPECIALIST semantics rather than by indiscriminately stretching readable content.

### Repair v7 automated visual evidence

Final focused browser evidence is `PASS` on runtime presentation head:

`eabd9a3281673ababc9beb7ce737ca01346a04cf`

Development Stack run:

`31648061603 / SUCCESS`

Retained artifact:

- name: `ux-platform-browser-evidence-31648061603`;
- id: `9161621583`;
- digest: `sha256:d8d98b707326b654315f0c00d4acf604a3d227bf9bc93e5679133fc1fd5207b1`;
- GitHub retention record expires `2026-08-26`.

The evidence harness covers 17 authenticated/public representative surfaces in both light and dark themes across all nine required viewport sizes. It explicitly includes Personnel (`/organization/`) and Operational Rights (`/organization/authorities/`) rather than inferring them from source tests. It also retains registered OPJ, draft/working OPJ, DEFECT, Workplace Documentation, account/public surfaces and transient interaction states.

The run verifies exact checkout, Development fixtures and real demo login, theme semantics, heading/content geometry, screen and full-page screenshots, `scrollWidth`/`innerWidth`, console/page errors, mobile `visualViewport.scale`, post-browser health, isolated database identity, private port exposure and clean repository checkout.

### Executor visual review

`EXECUTOR MANUAL VISUAL REVIEW: PASS`

The retained Repair v7 screenshots were manually inspected after the automated PASS. No new owner-visible defect was identified. In particular:

- 1920×1080 and 2560×1440 remain intentionally different adaptive compositions rather than a mechanically stretched layout;
- specialist surfaces such as Operational Rights, registered OPJ and DEFECT consume useful wide-screen space;
- readable normal registry surfaces retain bounded composition where wider text blocks would reduce usability;
- Workplace Documentation is settled without document-level overflow at 390 px after the Repair v7 responsive fix;
- mobile light/dark and transient drawer/dialog/filter/OPJ settings/reference-picker states remain coherent.

### Repair v7 trusted-controller boundary

The Repair v7 browser harness was temporarily wired into `.github/workflows/development-stack.yml` solely to produce focused evidence. That temporary workflow content is not part of the deliverable and must be removed before the final privileged controller run.

The final controller-compatible candidate restores `.github/workflows/development-stack.yml` byte-for-byte to the trusted `main` blob:

`7e74a4f8ca85b631b49b303d6eb118e64ab72e2f`

No application/runtime presentation file may change after `eabd9a32...` without invalidating the Repair v7 visual evidence. Source-neutral closure is limited to restoring the trusted workflow boundary, canonical evidence documentation and deterministic generated dependency projections if required by the repository generator.

This Repair v7 evidence is technical/executor evidence only. It does **not** claim owner visual acceptance. `OWNER VISUAL ACCEPTANCE` remains `PENDING` until the owner inspects the final persistent Development candidate.

## REPAIR V13 RESPONSIVE-STATE CLOSURE

Repair v13 removes the fragmented interval where the shell had already compacted but content still rendered as squeezed desktop panes, tables and ribbons. It uses the existing canonical owners and introduces no repair-specific stylesheet or third design system.

The implementation contract is:

- **FULL DESKTOP** above `61.25rem`: accepted desktop shell, specialist matrices, dense tables and OPJ ribbon remain unchanged;
- **COMPACT** from `48rem` through `61.25rem`: shell and data surfaces change together; Personnel hierarchy releases employee width before the shell boundary; nested Personnel panels stack; Rights uses the existing employee-first grouped composition; dense Rights/OPJ/DEFECT/Documentation/Import surfaces adapt before pathological wrapping; OPJ secondary formatting remains behind the existing `Формат` disclosure; controls retain mouse-oriented platform height;
- **PHONE** below `48rem`: 44px-class touch targets, stacked card metadata and existing phone composition remain active;
- normal human text keeps word boundaries; `overflow-wrap:anywhere` is limited to technical identifiers;
- ordinary surfaces cannot create document-level horizontal overflow; the DEFECT normative register remains the explicit local-scroll exception.

The canonical browser harness now performs the mandatory same-page continuous resize down and back up at widths `1440, 1280, 1180, 1100, 1024, 976, 950, 900, 832, 768, 600, 440, 412, 390` in both themes for Personnel, Rights, Imports, Workplace Documentation, DEFECT, OPJ registry and OPJ draft workspace. It blocks document overflow, human-word shredding, stale desktop compositions below the shared boundary and OPJ toolbar overflow.

Repair v13 technical evidence, exact-head workflow results, trusted persistent Development deployment and executor visual verdict must be recorded here after they exist. Until then, and until a new owner walkthrough occurs, `OWNER VISUAL ACCEPTANCE` remains `PENDING`; Draft PR `#70` must remain Draft and unmerged.

## HARD BOUNDARIES

Do **not** implement `PAGE-TEMPLATE-LIBRARY-001`, full historical `LEGACY-UX-MIGRATION-001`, new product modules, Module Registry redesign, domain/lifecycle/security redesign, Preview/pilot/production deployment, Ready for Review or merge.

The prohibition on full `LEGACY-UX-MIGRATION-001` does **not** permit ordinary owner-visible core routes to retain legacy generic presentation ownership; those routes are part of Repair v3 and must be platform-native now.

Existing domain models, migrations, lifecycle semantics, OPJ autosave/revisions/locking/registration/correction/print semantics, DEFECT lifecycle and stored business data are protected.

## STOP CONDITION

Stop only at a technically and visually complete Draft PR ready for direct owner visual acceptance:

- one final exact head;
- source contract, full Django suite and all applicable repository gates green;
- Repair v7 automated browser evidence and mobile/wide proof green on runtime presentation head `eabd9a3281673ababc9beb7ce737ca01346a04cf`;
- executor manual review of the retained Repair v7 artifact = `PASS`;
- no application/runtime presentation change after that evidence head;
- trusted Development workflow restored byte-for-byte to the trusted main blob before privileged deployment;
- deterministic dependency inventory exact for the final head;
- trusted persistent Development deployed at the final exact SHA and verified;
- `behind_by: 0`;
- Preview untouched;
- `OWNER VISUAL ACCEPTANCE = PENDING` until actual owner review.

Ready for Review and merge remain prohibited until explicit owner instruction.
