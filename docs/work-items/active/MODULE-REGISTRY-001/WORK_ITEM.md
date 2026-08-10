# MODULE-REGISTRY-001

## STATUS

`IN_PROGRESS / REPRESENTATIVE INTEGRATION UNDER EXACT-HEAD VALIDATION`

Issue: `#67`

Branch: `platform/module-registry-001`

Draft PR: `#68 / OPEN / DRAFT / NOT MERGED`

## EXACT BASELINE SHA

Accepted main at contour creation:

`862b682ba19b6747ea6f4d41fd31322808140b82`

Accepted SECURITY-BASELINE-001 exact head:

`b59a9485187dbd588c7b9f35bfd634c89344ea9d`

## FACTUAL GATE STATE

`SECURITY-BASELINE-001` is accepted and merged in PR #66; issue #65 is CLOSED / COMPLETED.

Canonical `SAFE-CONTINUATION = 8/8 ACCEPTED` and `MODULE-REGISTRY-001 = IN_PROGRESS` are now recorded in the release plan, current-state owner, immutable histories and deterministic planning views.

No separate reconciliation work item was created.

## APPROVED PRODUCT ROUTE AFTER SAFE

1. canonical SAFE closure;
2. `MODULE-REGISTRY-001`;
3. `UX-PLATFORM-FOUNDATION-001` + `PAGE-TEMPLATE-LIBRARY-001` with controlled migration of existing UI where required;
4. new product/module development on the shared module and UX platforms;
5. remaining `PILOT-READY` hardening in risk-based portions as real pilot approaches.

Do not automatically start unrelated industrialization work.

## GOAL

Implement the accepted `MODULE-ACTIVATION-CONTRACT-001` as the runtime module control plane for the single modular Django monolith.

One deployable EOD product and one compatible database must support different effective module sets across Organization / EnergySite / Workplace scopes without per-site builds, forks, dynamic Django app loading or data loss.

Canonical program acceptance:

- mixed module sets work across Organizations, EnergySites and Workplaces;
- deactivation blocks new actions and preserves readable history.

## ACCEPTED ARCHITECTURE — DO NOT REDESIGN

Source: `docs/project/SYSTEM_ARCHITECTURE.md`, ADR `MODULE-ACTIVATION-CONTRACT-001`, accepted in PR #62.

Preserve:

- module code installed with the product; activation is runtime capability state;
- manifest with stable ID, policy, scopes, dependencies/integrations, capabilities, prerequisites, history and migration policy;
- lifecycle states `AVAILABLE`, `CONFIGURED`, `ACTIVE`, `READ_ONLY`, `INACTIVE`, `RETIRED` and accepted transition graph;
- v1 scopes exactly `ORGANIZATION`, `ENERGY_SITE`, `WORKPLACE`;
- precedence `WORKPLACE > ENERGY_SITE > ORGANIZATION`;
- no rule for `SCOPED_OPTIONAL` means `AVAILABLE`, not implicit `ACTIVE`;
- exact duplicate scoped rule fails closed;
- `READ_ONLY`/`RETIRED` restrictive caps, with `RETIRED` strongest;
- broader `INACTIVE` may be overridden by a valid more-specific `ACTIVE` for phased rollout;
- required dependencies fail closed; optional integrations do not become hard dependencies without evidence;
- hidden UI and route-only guards are not authorization;
- mutation enforcement belongs at service/capability boundary;
- admin/commands/jobs have no implicit activation bypass;
- final permission is module ALLOW AND identity/RBAC/authority ALLOW AND domain invariants ALLOW;
- migrations are product-version-wide and inactive modules still migrate;
- activation/deactivation never deletes historical records;
- lifecycle attempts produce append-only audit evidence.

## REQUIRED IMPLEMENTATION OUTCOME

Start with factual repository inventory and map existing product apps/routes/services to canonical module IDs/capabilities. Do not invent a second taxonomy.

Implement the smallest coherent runtime control plane proving the accepted contract end-to-end:

1. deterministic manifest registry;
2. persistent scoped activation records with exact uniqueness and scope membership validation;
3. lifecycle transition service with fail-closed prerequisites/dependencies;
4. append-only activation audit;
5. normalized Organization/Site/Workplace context resolver;
6. deterministic effective-state resolver;
7. `ModuleAccessDecision` / equivalent central access decision API covering capability, operation and entry-point class;
8. service-boundary mutation enforcement;
9. representative HTTP/navigation integration;
10. retained read/history/export behavior for non-active states as accepted;
11. mixed-scope tests;
12. reactivation using the same stable module identity/history;
13. dependency versus optional-integration tests;
14. audit tests for accepted and denied lifecycle transitions;
15. migrations that do not auto-activate modules.

If wiring every existing endpoint would become a risky big-bang rewrite, implement a central fail-closed seam plus representative existing modules and document the exact remaining module-by-module migration boundary. Do not claim universal coverage unless it is actually wired/tested.

## EXISTING SPECIALIZED GUARDS

Repository inventory confirmed that `EquipmentDefectRouteGuardMiddleware` is a specialized canonical-route redirect helper, not an activation or security authorization layer. It is not rebranded as the registry.

Current models also confirm that `Workplace` and `EnergySite` each belong independently to `Organization`; no `Workplace -> EnergySite` hierarchy is invented.

Current DEFECT <-> OPJ remains an optional integration unless factual domain evidence proves a hard dependency.

## COMPLETED CANONICAL TRANSITION

The first transition is complete:

1. live accepted main remained `862b682ba19b6747ea6f4d41fd31322808140b82`;
2. `SECURITY-BASELINE-001` is `ACCEPTED` with PR #66, exact head `b59a9485187dbd588c7b9f35bfd634c89344ea9d`, merge `862b682ba19b6747ea6f4d41fd31322808140b82`, issue #65 CLOSED/COMPLETED and owner acceptance PASSED;
3. `SAFE-CONTINUATION = 8/8 ACCEPTED`;
4. the explicit approved post-SAFE route above is recorded;
5. `MODULE-REGISTRY-001 = IN_PROGRESS`;
6. `CURRENT_STATE.md` owns issue #67 / branch `platform/module-registry-001` / Draft PR #68;
7. acceptance/baseline histories and deterministic planning views were updated;
8. post-SAFE generators and queue validation were corrected so completed SAFE and the explicit owner route are represented fail closed rather than by stale pre-SAFE constants;
9. UX implementation was not started;
10. live Preview/VPS remains untouched.

## CURRENT IMPLEMENTATION EVIDENCE

The branch now contains the first coherent runtime control-plane slice in existing `apps.system` rather than a new infrastructure Django app:

- deterministic manifests for current repository-backed canonical module IDs;
- persistent exact-scope activation rules;
- append-only lifecycle audit events;
- Organization / EnergySite / Workplace context membership validation;
- accepted lifecycle transition graph;
- same-scope hard-dependency validation;
- optional-integration semantics (`DEFECT -> OPJ` remains optional);
- precedence and restrictive caps;
- central `ModuleAccessDecision` and `require_module_access` service seam;
- product-version migration with no activation-data seeding;
- focused mixed-scope, fail-closed, history-preservation and audit tests.

## REPRESENTATIVE REAL PRODUCT INTEGRATION

The first migrated real product seam is the existing registered-OPJ-entry -> DEFECT creation action:

- `CAP-DEFECT-OPJ-LINK` remains an optional integration; inactive DEFECT does not block OPJ itself;
- navigation generation omits the new-action row/button when DEFECT is unavailable for that Organization/Workplace;
- an existing historical OPJ<->DEFECT link remains visible while DEFECT is inactive;
- the direct `create_from_operational_log` HTTP entry point is guarded and returns a permission denial when the module decision denies creation;
- the public `register_defect(... operational_log_entry=...)` service boundary independently enforces the same module capability, so bypassing navigation/HTTP does not permit the mutation;
- defect test fixtures explicitly configure and activate DEFECT as test data; no product migration auto-activates it.

This is intentionally representative, not a false claim of universal endpoint coverage. Existing OPJ and DEFECT route/service surfaces outside this cross-module creation seam remain under their current accepted domain controls until controlled module-by-module migration. Broad migration is deferred rather than hidden inside this PR.

## NEGATIVE / FAIL-CLOSED EVIDENCE

Focused evidence covers unknown module/capability/operation/entry point, unsupported or foreign scope, duplicate rule, missing hard dependency, forbidden lifecycle transition, activation without readiness, precedence/restrictive caps, navigation-hidden/direct-HTTP/direct-service mutation, READ_ONLY mutation denial, INACTIVE new-action denial, deactivation preserving history, migration not auto-activating, optional integration absent, reactivation identity preservation, and append-only activation audit.

Prefer table-driven/mutation tests over repetitive one-off tests.

## RISK-BASED TEST POLICY

Use focused registry tests during implementation. Do not manually rerun every heavy workflow after each edit. Existing workflows stay enabled.

Final candidate requires one common exact head, clean tree, `behind_by: 0` and all applicable workflows green. Diagnose exact failed job/step/log; do not weaken gates blindly.

## OUT OF SCOPE

- UX platform/page-template implementation or broad UI redesign;
- new journals/product modules;
- `SHIFT-HANDOVER-001` implementation;
- full AUTH-RBAC / security pipeline / upload hardening;
- full N-1/N/N-2 module migration compatibility matrix;
- microservices, dynamic Django app loading or per-site builds;
- live Preview/VPS changes without separate authorisation;
- Ready for Review or merge before explicit owner acceptance.

## STOP CONDITION

Stop at a technically complete Draft PR ready for owner acceptance with mixed-scope activation evidence, preserved history, fail-closed service-boundary decisions, exact-head green workflows and `behind_by: 0`.
