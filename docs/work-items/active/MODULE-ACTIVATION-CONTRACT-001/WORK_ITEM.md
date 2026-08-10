# MODULE-ACTIVATION-CONTRACT-001

## STATUS

`PREPARED / NOT YET CANONICALLY IN_PROGRESS`

Issue: `#61`

Branch: `architecture/module-activation-contract-001`

Draft PR: to be created against `main`.

## WORK ITEM ID

`MODULE-ACTIVATION-CONTRACT-001`

## PARENT RELEASE

Industrialization Phase 1 / `SAFE-CONTINUATION`.

## PARENT MODULE

Platform architecture / cross-module activation contract.

This work item does not create a new end-user module.

## CAPABILITY IDS

Architecture capabilities to be defined by this work item:

- stable module manifest identity;
- scoped activation semantics;
- module lifecycle semantics;
- dependency/integration semantics;
- universal guard decision contract;
- history-preserving deactivation/reactivation semantics;
- activation audit semantics.

Final canonical capability identifiers may be normalised in the accepted ADR/contract.

## EXACT BASELINE SHA

At contour creation:

`1f3296bcf3d0f57bd088241c81691c7f54b2ac25`

Live GitHub remains authoritative. The implementation session must re-check current `main` before relying on this SHA.

## GOAL

Accept one deterministic architecture contract for optional EOD modules before implementing `MODULE-REGISTRY-001`.

EOD remains one modular Django monolith, one deployable application version and one database. Different organization / energy-site / workplace scopes may have different effective module sets without separate builds, forks or loss of historical data.

## USER SCENARIO

A product owner or administrator must eventually be able to activate an approved module for one operational scope while leaving another scope unchanged, then disable or retire that module later without deleting its historical records or making the system inconsistent.

The future implementation must be able to answer deterministically:

- whether a module/capability is available at a given scope;
- whether reads are allowed;
- whether new writes/transitions are allowed;
- why access is allowed or denied;
- whether required dependencies are satisfied;
- what happens to historical data after deactivation;
- whether reactivation is valid.

## BUSINESS RESULT

New journals and functional contours can be added to one EOD product and enabled gradually per object/workplace instead of creating separate product variants. Historical data remains durable when functionality is disabled.

## IN SCOPE

1. Canonical module manifest semantics.
2. Stable module identity.
3. Supported activation scopes.
4. Lifecycle states and state transitions.
5. Deterministic scope inheritance/precedence/override rules.
6. Required dependencies versus optional integrations.
7. Guard decision model for all future runtime entry points.
8. Read/write/history/export behaviour by effective lifecycle state.
9. Historical-data retention and reactivation semantics.
10. Migration boundary for inactive modules.
11. Activation/configuration audit semantics.
12. Current-system gap mapping to future `MODULE-REGISTRY-001`.
13. Negative architecture examples and acceptance tests/checkers appropriate for an architecture work item.
14. Canonical post-merge transition from accepted `DEPLOYMENT-PROFILE-001` to this work item.

## OUT OF SCOPE

- runtime module registry/control-plane implementation;
- module-registry database schema unless strictly necessary to express a deterministic contract and explicitly justified;
- wiring universal route/service/API/admin/task/command guards into the application;
- product/domain migrations;
- executable mixed-module migration matrix;
- UX platform or page-template work;
- new journals/modules;
- `SHIFT-HANDOVER-001`;
- live Preview/VPS changes;
- Ready for Review or merge without explicit owner command.

## DEPENDENCIES

Canonical program dependency:

- `PROJECT-STATE-RECONCILIATION-001` — accepted.

Downstream consumers include:

- `MODULE-REGISTRY-001`;
- `MODULE-BOUNDARY-GATES-001`;
- `UX-PLATFORM-FOUNDATION-001`;
- later `MODULE-MIGRATION-COMPATIBILITY-001`.

## DOMAIN CONTRACT

This work item is platform architecture and must not invent new domain rules for OPJ, DEFECT, SHIFT or future journals.

Cross-module links do not automatically create hard dependencies. A dependency is required only when the dependent module cannot preserve its own domain invariants without the provider module.

For example, availability of an OPJ link from another module is not sufficient evidence that OPJ must be active for that module unless a canonical domain contract explicitly requires it.

## LEGAL MODE / VERIFY OWNER

No new legal mode is introduced here.

The architecture must preserve existing evidence/history/legal semantics when a module becomes inactive or retired. Any module-specific legal requirement that changes lifecycle behaviour remains owned by that module's canonical domain/evidence contract and must be represented as an explicit restriction, not guessed globally.

## SOURCE IDS

Primary repository evidence:

- `docs/project/INDUSTRIALIZATION_PROGRAM.yaml` / generated human view;
- `docs/audits/PROJECT_SUSTAINABILITY_RISK_REGISTER_20260805.csv` (`PSR-004`, `PSR-005`, `PSR-014`);
- `docs/project/SYSTEM_ARCHITECTURE.md`;
- `docs/product/MODULE_MAP.md`;
- existing module contracts under `docs/modules/<MODULE_ID>/MODULE_CONTRACT.md`;
- current route/service/middleware wiring inspected from exact head.

No external web research is required unless a material architecture uncertainty cannot be resolved from accepted repository decisions.

## COMPETITOR BENCHMARK

Not required for the core activation contract. Do not broaden this architecture work into market research.

## UX REFERENCES / LOCATORS

No UI redesign is in scope.

The contract must nevertheless state that future navigation visibility is only one presentation of activation state; hiding navigation is never an authorization/enforcement mechanism.

## VIEWPORTS / STATES

No viewport acceptance.

Lifecycle/effective access states are the relevant state space.

The ADR must define a minimal complete lifecycle model. Candidate conceptual distinctions that must be preserved even if renamed:

- module code/product capability is available;
- module is configured/ready for a scope;
- module is active for normal operation;
- module is read-only for historical access;
- module is retired/inactive with history preserved.

Do not collapse `inactive` into data deletion.

## ALLOWED FILES

Expected architecture/documentation boundary:

- `docs/decisions/**` or the repository's accepted ADR location;
- `docs/project/**` canonical state/history/planning projections as required by generators;
- `docs/work-items/active/MODULE-ACTIVATION-CONTRACT-001/**`;
- architecture contract/checker/test fixtures strictly needed to make the decision deterministic and regression-protected;
- existing documentation generators/checkers only where necessary to support the accepted contract.

Any source-code change outside an architecture/checking contract requires explicit justification in the PR body.

## PROTECTED FILES

Unless an exact requirement proves otherwise, do not change:

- product/domain models;
- migrations;
- production/preview runtime configuration;
- UX templates/static assets;
- accepted OPJ/DEFECT domain behaviour;
- deployment profile semantics;
- dependency provenance architecture.

## FORBIDDEN CHANGES

- microservices or separate module deployments;
- separate product versions/builds per object;
- database-per-module design;
- deletion of module history on disable/retire;
- optional integration silently promoted to required dependency;
- UI-only activation enforcement;
- route-only enforcement presented as complete;
- skipping product migrations because a module is inactive;
- automatic activation caused merely by a migration or software upgrade;
- physical removal of historical data as a lifecycle transition;
- weakening existing guards/checkers to make the architecture fit current code.

## DATA / FIXTURES

No live data changes.

Architecture examples/fixtures should include at least:

1. two organizations/sites/workplaces with different module sets;
2. parent scope active + child override scenario;
3. explicit deny/inactive override scenario;
4. required dependency unavailable scenario;
5. optional integration unavailable scenario;
6. read-only/retired historical record access;
7. attempted write while inactive/read-only;
8. reactivation after retained history;
9. software migration while module inactive;
10. conflicting or ambiguous scope records rejected fail closed.

## ACCEPTANCE IDS

Architecture acceptance must prove:

- `AC-MODULE-ACTIVATION-MANIFEST`;
- `AC-MODULE-ACTIVATION-LIFECYCLE`;
- `AC-MODULE-ACTIVATION-SCOPE`;
- `AC-MODULE-ACTIVATION-DEPENDENCIES`;
- `AC-MODULE-ACTIVATION-GUARDS`;
- `AC-MODULE-ACTIVATION-HISTORY`;
- `AC-MODULE-ACTIVATION-MIGRATION-BOUNDARY`;
- `AC-MODULE-ACTIVATION-AUDIT`.

Identifiers may be normalised by the final ADR only if traceability remains explicit.

## REQUIRED CHECKS

During architecture work use focused checks.

Final candidate requires:

- deterministic documentation/state contract;
- any architecture checker/negative fixtures added by this work item;
- relevant existing architectural gates;
- one final applicable exact-head workflow set;
- `behind_by: 0` or an explicitly resolved main divergence before final acceptance.

Do not repeatedly run the full heavy suite after every documentation edit.

## DELIVERY PROFILE

Architecture-only acceptance candidate. No runtime deployment.

## COMMIT / PR RULES

- work only in issue #61 / `architecture/module-activation-contract-001` / its Draft PR;
- no additional issue/branch/PR;
- no Ready for Review or merge without explicit owner command;
- preserve exact-head evidence;
- keep canonical state owners singular;
- generated views must be regenerated, not hand-edited.

## FIRST ATOMIC COORDINATION TRANSITION

Before claiming architecture execution evidence, reconcile the post-merge state in one consistent transition:

1. Verify current GitHub `main`, merged PR #60 and closed issue #59.
2. Record `DEPLOYMENT-PROFILE-001` as `ACCEPTED` in the canonical plan with accepted exact head `323f4fb9162e84ca25a49556340078de81af2424`, merge commit `1f3296bcf3d0f57bd088241c81691c7f54b2ac25`, applicable final workflow evidence and owner acceptance.
3. Append immutable Deployment Profile acceptance/baseline history without rewriting older history.
4. Transition `MODULE-ACTIVATION-CONTRACT-001` from `NOT_STARTED` to `IN_PROGRESS`.
5. Update the volatile current-state owner to issue #61 / this Draft PR / `architecture/module-activation-contract-001`.
6. Regenerate all deterministic planning/progress views.
7. Verify `SAFE-CONTINUATION` becomes `5/8 ACCEPTED` with this work item active.
8. Keep the product/domain queue paused; do not start `SHIFT-HANDOVER-001`.

## REPORT FORMAT

Final acceptance report must include:

- exact head and current `main`;
- compare/`behind_by`;
- changed-file boundary;
- canonical transition evidence;
- final lifecycle model;
- scope resolution/preference algorithm with examples;
- manifest schema/required metadata;
- required-dependency vs optional-integration rules;
- entry-point guard matrix;
- read/write/history/export matrix by lifecycle state;
- migration and reactivation semantics;
- audit requirements;
- mapping of current gaps to `MODULE-REGISTRY-001`;
- negative architecture fixtures/check results;
- applicable exact-head workflow IDs/results;
- explicit confirmation that runtime/Preview/domain/schema/data/UX were not changed unless separately justified.

## STOP CONDITIONS

Stop only when:

- the architecture contract is internally complete and implementable by `MODULE-REGISTRY-001` without reopening fundamental lifecycle/scope/dependency decisions;
- current code gaps are described honestly rather than misrepresented as already implemented;
- canonical state and generated views are consistent;
- applicable exact-head gates are green;
- PR remains Draft for product-owner acceptance.
