# MODULE-ACTIVATION-CONTRACT-001

## STATUS

`IN_PROGRESS / TECHNICAL CANDIDATE UNDER EXACT-HEAD VALIDATION`

Issue: `#61`

Branch: `architecture/module-activation-contract-001`

Draft PR: `#62 / OPEN / DRAFT / NOT MERGED`

Runtime impact: `NONE`

Preview: `UNTOUCHED`

## WORK ITEM ID

`MODULE-ACTIVATION-CONTRACT-001`

## PARENT RELEASE

Industrialization Phase 1 / `SAFE-CONTINUATION`.

## PARENT MODULE

Platform architecture / cross-module activation contract. This work item does not create a new end-user module.

## CAPABILITY IDS

- `AC-MODULE-ACTIVATION-MANIFEST`;
- `AC-MODULE-ACTIVATION-LIFECYCLE`;
- `AC-MODULE-ACTIVATION-SCOPE`;
- `AC-MODULE-ACTIVATION-DEPENDENCIES`;
- `AC-MODULE-ACTIVATION-GUARDS`;
- `AC-MODULE-ACTIVATION-HISTORY`;
- `AC-MODULE-ACTIVATION-MIGRATION-BOUNDARY`;
- `AC-MODULE-ACTIVATION-AUDIT`.

## EXACT BASELINE SHA

Contour creation and accepted-main baseline:

`1f3296bcf3d0f57bd088241c81691c7f54b2ac25`

Live GitHub remains authoritative; final acceptance report records final exact head and re-checks `main` / `behind_by`.

## GOAL

Accept one deterministic architecture contract for optional EOD modules before implementing `MODULE-REGISTRY-001`.

EOD remains one modular Django monolith, one deployable application version and one shared database. Different Organization / EnergySite / Workplace contexts may have different effective module sets without separate builds, forks or loss of historical data.

## USER SCENARIO

A product owner/administrator can eventually activate an approved module for one operational scope, keep another scope inactive, freeze or retire it later, and reactivate it without deleting history or creating a new module identity.

Every future entry point must deterministically resolve module/capability, effective lifecycle state, configuration readiness, hard-dependency result, requested operation access and an audit-safe denial reason.

## BUSINESS RESULT

New journals and functional contours can be added to one EOD product and enabled gradually per organization/object/workplace instead of creating separate product variants. Deactivation remains reversible and history-preserving.

## IN SCOPE

1. Canonical module manifest semantics and stable identity.
2. Supported activation scopes and deterministic precedence/override.
3. Lifecycle states and transitions.
4. Required dependencies versus optional integrations.
5. Universal access-decision contract across UI/HTTP/service/API/admin/commands/exports/jobs/cross-module actions.
6. Read/write/history/export/background behaviour by lifecycle state.
7. Historical-data retention and reactivation.
8. Product-version migration boundary for inactive modules.
9. Activation audit semantics.
10. Current implementation-gap mapping.
11. Machine-readable contract, fail-closed validation and negative fixtures.
12. Canonical post-merge transition from accepted `DEPLOYMENT-PROFILE-001`.

## OUT OF SCOPE

- `MODULE-REGISTRY-001` runtime implementation;
- registry/control-plane DB tables;
- universal runtime guard wiring;
- product/domain models and migrations;
- mixed-module N-1/N migration matrix;
- UX/page templates;
- new journals/modules;
- `SHIFT-HANDOVER-001`;
- live Preview/VPS;
- Ready for Review or merge.

## DEPENDENCIES

Canonical program dependency:

- `PROJECT-STATE-RECONCILIATION-001` — `ACCEPTED`.

Downstream consumers:

- `MODULE-REGISTRY-001`;
- `MODULE-BOUNDARY-GATES-001`;
- `UX-PLATFORM-FOUNDATION-001`;
- `MODULE-MIGRATION-COMPATIBILITY-001`.

## DOMAIN CONTRACT

This is platform architecture and does not invent new OPJ/DEFECT/SHIFT domain rules.

A hard dependency exists only when a module cannot preserve its own invariants without the provider. Cross-module links do not automatically create hard dependencies. The accepted DEFECT contract names `MASTER-DATA` as dependency; the accepted OPJ link therefore remains optional integration unless future domain evidence proves otherwise.

## LEGAL MODE / VERIFY OWNER

No new legal mode. Module-specific legal/evidence rules remain owned by canonical module contracts. Activation state may restrict access but must never erase legally/operationally significant records, snapshots, relations or audit evidence.

## SOURCE IDS

Primary repository evidence:

- `docs/project/INDUSTRIALIZATION_PROGRAM.yaml` and `.md`;
- `docs/audits/PROJECT_SUSTAINABILITY_RISK_REGISTER_20260805.csv`;
- `docs/project/SYSTEM_ARCHITECTURE.md`;
- `docs/product/MODULE_MAP.md`;
- relevant `docs/modules/*/MODULE_CONTRACT.md`;
- current `INSTALLED_APPS`, URL wiring and middleware;
- `EquipmentDefectRouteGuardMiddleware`;
- current Organization / EnergySite / Workplace models;
- current DEFECT service layer;
- existing architecture/process gates.

No external research was required.

## COMPETITOR BENCHMARK

Not required. This architecture contract derives from accepted EOD architecture and factual current-code gaps, not market-product behaviour.

## UX REFERENCES / LOCATORS

No UI redesign. Future navigation visibility is presentation/defence in depth only; hidden UI is never a substitute for HTTP/service/API/admin/command/task enforcement.

## VIEWPORTS / STATES

No viewport acceptance.

Canonical lifecycle:

```text
AVAILABLE
CONFIGURED
ACTIVE
READ_ONLY
INACTIVE
RETIRED
```

`INACTIVE` is intentionally distinct from `CONFIGURED` and `RETIRED`.

## ALLOWED FILES

- `docs/decisions/**`;
- canonical `docs/project/**` transition/history/generated views;
- this work-item directory;
- existing Documentation Contract entry point;
- focused architecture test/fixture files.

## PROTECTED FILES

No changes to product/domain models, migrations, runtime configuration, UX templates/static, accepted OPJ/DEFECT lifecycle behaviour, accepted Deployment Profile semantics or accepted Dependency Provenance architecture.

## FORBIDDEN CHANGES

- microservices/separate module deployments;
- separate product versions/builds per object;
- DB-per-module;
- history deletion on disable/retire;
- optional integration silently promoted to required dependency;
- UI-only or route-only enforcement presented as complete;
- inactive-module migration skipping;
- upgrade-triggered automatic activation;
- random first-match scope conflict resolution;
- new module identity on reactivation;
- weakening existing gates.

## DATA / FIXTURES

No live data changes.

Machine-readable positive contract:

`docs/work-items/active/MODULE-ACTIVATION-CONTRACT-001/MODULE_ACTIVATION_CONTRACT.json`

Fail-closed validation is integrated into the existing Documentation Contract entry point:

`scripts/check_documentation_contract.py`

Negative fixtures:

`tests/process/fixtures/module_activation_contract_cases.json`

Focused regressions:

`tests/process/test_module_activation_contract.py`

The catalog contains all ten required negative architecture scenarios plus focused manifest/entry-point/reactivation/precedence drift cases. No separate executable checker was retained, avoiding unnecessary expansion of the accepted Dependency Provenance source contour.

## ACCEPTANCE IDS

- `AC-MODULE-ACTIVATION-MANIFEST`
- `AC-MODULE-ACTIVATION-LIFECYCLE`
- `AC-MODULE-ACTIVATION-SCOPE`
- `AC-MODULE-ACTIVATION-DEPENDENCIES`
- `AC-MODULE-ACTIVATION-GUARDS`
- `AC-MODULE-ACTIVATION-HISTORY`
- `AC-MODULE-ACTIVATION-MIGRATION-BOUNDARY`
- `AC-MODULE-ACTIVATION-AUDIT`

## REQUIRED CHECKS

Focused contract checks are covered by:

```text
python scripts/check_documentation_contract.py
python -m unittest -v tests.process.test_module_activation_contract
```

The canonical positive and negative machine contract is executed by the existing `EOD Documentation Contract` entry point; full exact-head workflows remain unchanged.

Final candidate additionally requires deterministic project-state/planning views exact, one applicable final exact-head workflow set, current `main` re-check and `behind_by: 0`.

## DELIVERY PROFILE

Architecture-only acceptance candidate. No runtime deployment.

## COMMIT / PR RULES

- issue #61 / existing branch / Draft PR #62 only;
- no new issue/branch/PR;
- no Ready for Review or merge;
- exact-head evidence only;
- canonical owners remain singular;
- generated views must match generators.

## COMPLETED CANONICAL TRANSITION

GitHub factual state was re-verified before transition:

- PR #60: `CLOSED / MERGED`;
- issue #59: `CLOSED / COMPLETED`;
- accepted Deployment Profile exact head: `323f4fb9162e84ca25a49556340078de81af2424`;
- merge/current accepted baseline: `1f3296bcf3d0f57bd088241c81691c7f54b2ac25`;
- all eight applicable final exact-head PR #60 workflows: `SUCCESS`.

Canonical transition performed:

```text
DEPLOYMENT-PROFILE-001:       IN_PROGRESS -> ACCEPTED
MODULE-ACTIVATION-CONTRACT:   NOT_STARTED -> IN_PROGRESS
SAFE-CONTINUATION:            5/8 ACCEPTED
domain queue:                 PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION
SHIFT-HANDOVER-001:           NOT STARTED
```

`CURRENT_STATE.md`, `DEMO_RELEASE_PLAN.yaml`, acceptance/baseline history and deterministic progress/planning views were updated. No second runtime/Preview state owner was created.

## ARCHITECTURE OUTPUTS

Canonical decision:

`docs/decisions/MODULE_ACTIVATION_CONTRACT_001_DECISION.md`

Machine contract:

`docs/work-items/active/MODULE-ACTIVATION-CONTRACT-001/MODULE_ACTIVATION_CONTRACT.json`

### Final scope decision

Activation v1 supports `ORGANIZATION`, `ENERGY_SITE`, `WORKPLACE`.

`Workplace` is not modelled as a child of `EnergySite`, because the current Django model contains no such relation. Requested context requires Organization and may contain Site/Workplace if each belongs to the same Organization.

Ordinary precedence:

```text
WORKPLACE > ENERGY_SITE > ORGANIZATION
```

`READ_ONLY` and `RETIRED` are restrictive caps. `INACTIVE` is not an ancestor cap: a more-specific scope may explicitly become `ACTIVE` when configuration and hard dependencies validate. This enables staged activation.

### Final lifecycle decision

```text
AVAILABLE -> CONFIGURED -> ACTIVE
                       \-> INACTIVE
                       \-> RETIRED

ACTIVE -> READ_ONLY / INACTIVE / RETIRED
READ_ONLY -> ACTIVE / INACTIVE / RETIRED
INACTIVE -> CONFIGURED -> ACTIVE
RETIRED  -> CONFIGURED -> ACTIVE
```

Direct `AVAILABLE|INACTIVE|RETIRED -> ACTIVE` is forbidden where defined by the machine contract; stale configuration/dependencies must be revalidated.

### Final migration decision

Django/software migrations are a property of the product version, never of activation state. Inactive-module migrations apply and retained data migrate; upgrade never auto-activates the module.

## REPORT FORMAT

Final report records exact head, current main / `behind_by`, changed files, canonical transition, SAFE status, manifest/lifecycle/scope/dependency/guard/behaviour/migration/reactivation/audit contracts, current-gap mapping, negative evidence, exact-head workflow IDs/results, residual work handed to `MODULE-REGISTRY-001`, and confirmation of no runtime/Preview/domain/schema/data/UX changes.

## STOP CONDITIONS

Stop only when future `MODULE-REGISTRY-001` has no fundamental lifecycle/scope/dependency question left to invent, current implementation gaps are described as gaps, canonical state/views are consistent, applicable exact-head gates are green, and PR #62 remains `OPEN / DRAFT / NOT MERGED`.
