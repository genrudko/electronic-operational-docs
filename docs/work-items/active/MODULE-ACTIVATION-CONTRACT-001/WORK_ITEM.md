# MODULE-ACTIVATION-CONTRACT-001

## STATUS

`IN_PROGRESS / TECHNICAL CANDIDATE UNDER EXACT-HEAD VALIDATION`

Issue: `#61`

Branch: `architecture/module-activation-contract-001`

Draft PR: `#62 / OPEN / DRAFT / NOT MERGED`

Runtime impact: `NONE`

Preview: `UNTOUCHED`

## EXACT BASELINE SHA

Accepted-main baseline at contour start:

`1f3296bcf3d0f57bd088241c81691c7f54b2ac25`

Final acceptance report must re-check live `main`, exact head and `behind_by`.

## GOAL

Accept one deterministic architecture contract for optional EOD modules before implementation of `MODULE-REGISTRY-001`.

EOD remains one modular Django monolith, one deployable application version and one shared compatible database. Different Organization / EnergySite / Workplace contexts may have different effective module sets without separate builds, forks, deployments or loss of historical data.

## IN SCOPE

1. Canonical module manifest and stable identity.
2. Lifecycle states and transitions.
3. Activation scopes, inheritance, precedence and explicit overrides.
4. Required dependencies versus optional integrations.
5. Universal access-decision semantics across UI/HTTP/service/API/admin/commands/exports/jobs/cross-module actions.
6. Read/write/history/export/background behaviour matrix.
7. Historical retention and reactivation.
8. Product-version migration boundary for inactive modules.
9. Activation audit requirements.
10. Current implementation-gap mapping.
11. Machine-readable architecture representation and fail-closed negative fixtures.
12. Canonical transition from accepted `DEPLOYMENT-PROFILE-001` to this active work item.

## OUT OF SCOPE

- runtime `MODULE-REGISTRY-001` implementation;
- registry/control-plane DB tables;
- universal runtime guard wiring;
- product/domain models or migrations;
- executable `active/inactive × N-1/N` module migration matrix;
- UX/page templates;
- new journals/modules;
- `SHIFT-HANDOVER-001`;
- live Preview/VPS;
- Ready for Review or merge.

## COMPLETED CANONICAL TRANSITION

GitHub factual state was independently verified before transition:

- PR #60: `CLOSED / MERGED`;
- issue #59: `CLOSED / COMPLETED`;
- accepted Deployment Profile exact head: `323f4fb9162e84ca25a49556340078de81af2424`;
- merge/current accepted baseline: `1f3296bcf3d0f57bd088241c81691c7f54b2ac25`;
- all eight applicable final exact-head PR #60 workflows: `SUCCESS`.

Canonical state is now:

```text
DEPLOYMENT-PROFILE-001:       ACCEPTED
MODULE-ACTIVATION-CONTRACT:   IN_PROGRESS
SAFE-CONTINUATION:            5/8 ACCEPTED
domain queue:                 PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION
SHIFT-HANDOVER-001:           NOT STARTED
```

`CURRENT_STATE.md`, `DEMO_RELEASE_PLAN.yaml`, immutable acceptance/baseline history and deterministic progress/planning views were updated. No second runtime/Preview state owner was created.

## CANONICAL ARCHITECTURE DECISION

The ADR and its machine-readable fenced JSON block are stored in the existing architecture owner:

`docs/project/SYSTEM_ARCHITECTURE.md` section `13. ADR: MODULE-ACTIVATION-CONTRACT-001`.

The existing permanent Documentation Contract entry point parses and validates this block fail closed:

`scripts/check_documentation_contract.py`.

Negative module-activation mutations are stored in the existing process-fixture catalog:

`tests/process/fixtures/industrialization_execution_cases.json` under `module_activation_cases`.

No additional executable checker/workflow or second architecture/status owner is introduced.

## MANIFEST CONTRACT

Minimum canonical fields:

- stable `module_id`;
- human name;
- manifest contract version;
- activation policy (`ALWAYS_ON` / `SCOPED_OPTIONAL`);
- supported scopes;
- required dependencies;
- optional integrations;
- capabilities / operations;
- activation prerequisites/configuration readiness;
- history policy (`PRESERVE` for optional modules);
- migration policy (`ALWAYS_WITH_PRODUCT`);
- lifecycle contract version.

Manifest must not own release/work-item status, current main, active PR or accepted SHA.

No explicit rule for a `SCOPED_OPTIONAL` module means fail-closed `AVAILABLE`, not implicit `ACTIVE`.

## LIFECYCLE CONTRACT

Canonical states:

```text
AVAILABLE
CONFIGURED
ACTIVE
READ_ONLY
INACTIVE
RETIRED
```

Allowed transitions:

```text
AVAILABLE  -> CONFIGURED
CONFIGURED -> ACTIVE | INACTIVE | RETIRED
ACTIVE     -> READ_ONLY | INACTIVE | RETIRED
READ_ONLY  -> ACTIVE | INACTIVE | RETIRED
INACTIVE   -> CONFIGURED | RETIRED
RETIRED    -> CONFIGURED
```

Direct `AVAILABLE -> ACTIVE`, `INACTIVE -> ACTIVE` and `RETIRED -> ACTIVE` are forbidden.

Reactivation:

```text
INACTIVE -> CONFIGURED -> ACTIVE
RETIRED  -> CONFIGURED -> ACTIVE
```

Configuration and hard dependencies are revalidated before `ACTIVE`.

`disable`, `READ_ONLY` and `retire` never mean delete.

## ACTIVATION SCOPE CONTRACT

Supported v1 scopes:

```text
ORGANIZATION
ENERGY_SITE
WORKPLACE
```

`DIVISION` and `OPERATIONAL_AREA` are not v1 activation scopes.

Factual current models do **not** contain `Workplace -> EnergySite`; the contract does not invent such a hierarchy. Requested Organization is mandatory; optional Site/Workplace must each belong to that Organization.

Ordinary decision precedence:

```text
WORKPLACE > ENERGY_SITE > ORGANIZATION
```

Rules:

- exact `(module_id, scope_type, scope_id)` uniqueness; duplicate = `DENY`;
- no rule = `AVAILABLE`;
- `READ_ONLY` and `RETIRED` are restrictive caps; `RETIRED` dominates `READ_ONLY`;
- broader `INACTIVE` is not an ancestor safety cap and may be explicitly overridden by a more-specific `ACTIVE` after config/dependency validation, enabling phased rollout;
- invalid organization membership or unsupported scope fails closed;
- rules bind stable IDs, not mutable names/path strings.

## DEPENDENCIES AND INTEGRATIONS

### Required dependency

Hard dependency exists only when the consumer cannot preserve its own invariants without the provider.

It is:

- declared in manifest;
- checked before activation and guarded operations;
- fail closed;
- evaluated in the requested context by default;
- impossible to bypass via direct route/service/API/admin/command;
- acyclic.

Historical reads are not erased when the provider becomes unavailable.

### Optional integration

Missing/inactive provider does not block primary-module activation. It disables/degrades only the integration capability and preserves historical links/snapshots.

Current `DEFECT ↔ OPJ` classification remains optional integration unless future domain evidence proves a hard invariant dependency. The accepted DEFECT contract names `MASTER-DATA` as dependency; the existence of an OPJ link capability alone is insufficient evidence for a hard OPJ dependency.

## UNIVERSAL ACCESS DECISION

Future canonical predicate:

```text
decide_module_access(
    normalized_context,
    module_id,
    capability_id,
    operation,
    entry_point_class,
) -> ModuleAccessDecision
```

Mandatory entry-point classes:

- `NAVIGATION_UI`;
- `HTTP_ROUTE`;
- `SERVICE`;
- `API`;
- `ADMIN`;
- `MANAGEMENT_COMMAND`;
- `EXPORT`;
- `BACKGROUND_JOB`;
- `CROSS_MODULE_ACTION`.

Hidden UI is not protection. Route-only protection is incomplete. Mutation enforcement belongs at the service/capability boundary. Admin, management commands and background jobs have no implicit module-activation bypass.

Final permission is:

```text
module decision ALLOW
AND identity/RBAC/authority ALLOW
AND domain invariants ALLOW
```

## BEHAVIOUR SUMMARY

| State | Read/history | Create/edit/transition | Delete | Export | Background mutation |
|---|---|---|---|---|---|
| `ACTIVE` | ALLOW | ALLOW subject to normal policy | capability/domain only | ALLOW | declared operations only |
| `READ_ONLY` | ALLOW | DENY | DENY | read-only ALLOW | DENY |
| `INACTIVE` | retained history | DENY | DENY | retained-history ALLOW | DENY |
| `RETIRED` | retained history | DENY | DENY | retained-history ALLOW | DENY |
| `CONFIGURED` | retained history | DENY | DENY | retained-history ALLOW | DENY |
| `AVAILABLE` | retained history if supported | DENY | DENY | retained export if supported | DENY |

Historical operational/legal records, snapshots, audit and relations are preserved.

## MIGRATION CONTRACT

Software/database migrations belong to product version, never activation state.

Inactive-module migrations are applied; retained inactive data migrate safely; upgrade never auto-activates a module and preserves explicit activation state. One product version must not produce different DB schemas because of module set.

Full executable `active/inactive × N-1/N` compatibility belongs to `MODULE-MIGRATION-COMPATIBILITY-001`.

## ACTIVATION AUDIT

Every attempted activation-state transition requires append-only evidence containing module ID, scope, Organization, previous explicit/effective state, requested/resulting state, actor, timestamp, reason, configuration/dependency validation, result, denial reason, correlation identity and manifest contract version.

## CURRENT IMPLEMENTATION GAP

Current code is intentionally **not** presented as a registry implementation:

- Django apps and URL namespaces are globally wired;
- `EquipmentDefectRouteGuardMiddleware` is only a specialized redirect guard;
- current service paths do not have a universal module predicate;
- universal UI/HTTP/service/API/admin/command/export/job guards do not exist;
- scoped activation records and activation audit do not exist.

These are explicit deliverables for `MODULE-REGISTRY-001`.

## NEGATIVE ARCHITECTURE EVIDENCE

The machine contract and mutations reject all required scenarios:

1. UI hidden, direct URL operationally works.
2. Route denied, direct service write works.
3. Optional integration becomes hard dependency without evidence.
4. Required dependency missing, activation succeeds.
5. Disable deletes records/history.
6. `READ_ONLY` allows write/transition.
7. Upgrade auto-activates inactive module.
8. Inactive module skips schema migrations.
9. Scope conflict/duplicates use random/first-match resolution.
10. Reactivation creates a new module identity.

Additional mutations protect manifest minimum, mandatory `SERVICE` entry-point coverage, no direct `RETIRED -> ACTIVE` and exact scope precedence.

## REQUIRED CHECKS

Focused architecture validation is executed by the existing Documentation Contract:

```text
python scripts/check_documentation_contract.py
```

Final candidate additionally requires the full applicable exact-head workflow set, deterministic planning views, live current-main re-check and `behind_by: 0`.

## DELIVERY / PROTECTED BOUNDARY

No changes to:

- product/domain models;
- migrations;
- working data;
- runtime configuration;
- live VPS/Preview;
- UX/templates/static;
- new journals/modules;
- `SHIFT-HANDOVER-001`;
- runtime `MODULE-REGISTRY-001`.

PR #62 stays `OPEN / DRAFT / NOT MERGED` until an explicit product-owner decision.