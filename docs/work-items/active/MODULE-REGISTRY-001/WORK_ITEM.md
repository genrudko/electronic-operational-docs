# MODULE-REGISTRY-001

## STATUS

`STARTED / CANONICAL TRANSITION PENDING`

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

Therefore factual `SAFE-CONTINUATION = 8/8 ACCEPTED`.

The first substantive commit in this contour must atomically record that acceptance in canonical planning/history, record the explicit product-owner strategy decision, and move `MODULE-REGISTRY-001` to `IN_PROGRESS`.

No separate reconciliation work item is required.

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

Inventory `EquipmentDefectRouteGuardMiddleware` and other current permission/route mechanisms. They are not the module registry. Adapt only as required to avoid contradictory semantics and preserve accepted domain authority behavior.

Current DEFECT <-> OPJ remains an optional integration unless factual domain evidence proves a hard dependency.

## FIRST ATOMIC CANONICAL TRANSITION

Before implementation evidence:

1. re-check live main, merged PR #66 and closed issue #65;
2. record `SECURITY-BASELINE-001: ACCEPTED` with exact head `b59a9485187dbd588c7b9f35bfd634c89344ea9d`, merge `862b682ba19b6747ea6f4d41fd31322808140b82`, issue #65 CLOSED/COMPLETED and owner acceptance PASSED;
3. record `SAFE-CONTINUATION = 8/8 ACCEPTED`;
4. record the explicit approved post-SAFE route above;
5. set `MODULE-REGISTRY-001 = IN_PROGRESS`;
6. update `CURRENT_STATE.md` to issue #67 / this branch / Draft PR #68;
7. append immutable histories and regenerate existing deterministic planning views/checks;
8. do not start UX implementation in this PR.

## NEGATIVE / FAIL-CLOSED EVIDENCE

Cover material cases such as unknown module/capability/operation/entry point, unsupported or foreign scope, duplicate rule, missing hard dependency, forbidden lifecycle transition, activation without readiness, precedence/restrictive caps, hidden UI with direct mutation, route denial with direct service mutation, READ_ONLY/INACTIVE/RETIRED new mutation, deactivation preserving history, migration not auto-activating, optional integration absent, and activation audit on allowed/denied attempts.

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
