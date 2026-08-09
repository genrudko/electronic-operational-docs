# DEPLOYMENT-PROFILE-001

## STATUS

`PREPARED / NOT YET CANONICALLY IN_PROGRESS`

Issue: `#59`

Branch: `deployment/deployment-profile-001`

Draft PR: `#60` against `main`.

At coordination start this contract itself changes no live runtime, and the protected Preview environment remains untouched.

## PURPOSE

Create the accepted fail-closed deployment/configuration boundary for EOD pilot and production operation without changing accepted domain behaviour or treating Preview as production.

This is a Phase 1 P0 `SAFE-CONTINUATION` work item. It closes the deployment boundary of `PSR-003`, `PSR-022` and `PSR-018` and unblocks `BACKUP-RESTORE-DRILL-001` and `SECURITY-BASELINE-001`.

## FACTUAL BASELINE

The branch starts from the post-merge `main` that contains accepted `DEPENDENCY-PROVENANCE-001`:

```text
accepted PR: #58 / CLOSED / MERGED
accepted exact head: 0f0e92522e7a2c5d43dd635ed661c65ed5021422
merge commit / main: 5b54446d632ef1839d530dc2945255b3033359fe
issue: #57 / CLOSED / COMPLETED
```

PR #58 had no live runtime or Preview impact. Live GitHub is authoritative. The repository canonical planning/state files still contain the pre-merge `DEPENDENCY-PROVENANCE-001` execution state and must be reconciled in the first atomic transition of this work item before implementation evidence is claimed.

## FIRST ATOMIC COORDINATION TRANSITION

The first implementation session must perform one consistent state transition, not a sequence of contradictory partial edits:

1. Verify current `main`, PR #58 and issue #57 from GitHub.
2. Record `DEPENDENCY-PROVENANCE-001` as `ACCEPTED` in the canonical planning owner with exact evidence.
3. Record PR #58 acceptance in applicable acceptance/baseline history without rewriting older history.
4. Set the accepted main baseline to merge commit `5b54446d632ef1839d530dc2945255b3033359fe`.
5. Transition `DEPLOYMENT-PROFILE-001` from `NOT_STARTED` to `IN_PROGRESS`.
6. Set `CURRENT_STATE.md` active issue/PR/branch to this work item.
7. Regenerate every deterministic planning/progress view from canonical owners.
8. Run the documentation/state contract and repair only factual projection drift exposed by that transition.

No product/runtime claim may be made while canonical owners disagree.

## RISKS

### PSR-003 / CRITICAL

Current settings support development/CI/Preview but there is no distinct pilot/production mode. Unsafe production-like configuration therefore cannot be rejected fail closed and Preview can accidentally become a production surrogate.

### PSR-022 / CRITICAL boundary

Production secure cookies, HSTS and reverse-proxy/TLS contract are not yet established. This work item must establish the deployment configuration boundary and negative start/preflight checks. The broader threat model and security hardening remain owned by `SECURITY-BASELINE-001`.

### PSR-018 / HIGH boundary

Current health evidence is too weak for deployment decisions. This work item establishes the minimum deployment-facing liveness/readiness semantics needed to refuse an unhealthy deployment. Metrics, dashboards, alerting and operational observability remain `OBSERVABILITY-001`.

## ARCHITECTURAL BOUNDARIES

Preserve:

- modular Django monolith;
- one deployable EOD product/version;
- PostgreSQL as the pilot/production database;
- GitHub as the canonical code/documentation source;
- Preview as a protected non-production environment;
- existing accepted domain models, legal/evidence semantics and user-visible behaviour;
- accepted immutable dependency/build provenance from PR #58.

Do not introduce Kubernetes, microservices, HA topology or external SaaS without a separately proven requirement.

## REQUIRED IMPLEMENTATION OUTCOMES

### 1. Deployment mode contract

Define explicit, validated semantics for at least:

- development;
- CI/gate;
- Preview;
- pilot/production-capable deployment.

The repository must make it impossible to obtain a production-capable posture merely by setting `DEBUG=0` or reusing Preview settings.

### 2. Fail-closed configuration

Pilot/production-capable startup or deployment preflight must reject missing or unsafe mandatory configuration, including as applicable:

- secret key/secret material;
- allowed hosts/origins;
- database profile and credentials;
- proxy/TLS expectations;
- secure session/CSRF cookie contract;
- HSTS/HTTPS redirect assumptions;
- trusted proxy forwarding semantics;
- other settings proven necessary by Django deploy checks or repository architecture.

Do not hard-code live credentials into repository, CI logs or fixtures.

### 3. Database contract

Pilot/production-capable mode must be PostgreSQL-only and must not silently fall back to SQLite or a development database path.

Configuration errors must produce actionable diagnostics without leaking secrets.

### 4. TLS / reverse proxy / session boundary

Document and test the application-side contract for externally terminated TLS and reverse proxy forwarding. Define what the application trusts and what must be verified externally.

Do not pretend repository tests can prove the entire external certificate/DNS/load-balancer environment. Mark those as explicit external verification steps.

### 5. Deployment-facing health

Provide a bounded health contract suitable for deployment gates:

- liveness remains minimal and must not create restart loops because an external dependency is temporarily unavailable;
- readiness must fail when the application cannot safely serve the pilot/production workload because of mandatory deployment dependencies;
- checks must avoid destructive writes and secret disclosure.

Do not expand this into full metrics, dashboards or alerting.

### 6. Operator preflight and documentation

A technical operator must be able to determine from repository documentation:

- which profile is being deployed;
- which variables/settings are mandatory;
- which unsafe combinations are rejected;
- how to run configuration/deploy checks;
- how readiness/liveness are interpreted;
- what must be verified outside the application;
- what this work item does not yet prove.

### 7. Tests and gates

Add focused positive and negative tests for configuration boundaries and failure modes. Tests must prove fail-closed behaviour, not merely check that settings exist.

Use risk-based validation during implementation. Perform one full applicable exact-head gate on the final candidate rather than repeatedly running the entire suite for every small edit.

## ACCEPTANCE CRITERIA

The work item is ready for product-owner acceptance only when all are true:

1. Unsafe pilot/production configuration refuses startup or accepted deployment preflight with actionable non-secret diagnostics.
2. Safe representative pilot/production configuration passes Django deploy/system checks and repository deployment checks.
3. PostgreSQL-only production database semantics are demonstrated; SQLite fallback is rejected.
4. Secure cookie/proxy/TLS/HSTS application-side settings and assumptions are explicit and tested.
5. External TLS/session verification boundary is documented and, where testable without touching live Preview/VPS, exercised.
6. Deployment liveness/readiness semantics are implemented and covered by positive/negative tests.
7. Existing development/CI/Preview behaviour is preserved unless a change is explicitly justified and regression-tested.
8. `DEPENDENCY-PROVENANCE-001` post-merge state and all generated planning views are reconciled.
9. `behind_by: 0` against final `main` or any divergence is explicitly resolved before final acceptance evidence.
10. Applicable exact-head workflows are successful on the final candidate.
11. PR remains Draft; no Ready for Review or merge is performed without explicit owner command.
12. Live VPS/Preview are not changed unless the owner separately authorizes a bounded runtime verification.

## REQUIRED EVIDENCE

At final acceptance report provide:

- final exact head;
- base/main and `behind_by`;
- changed-file boundary;
- canonical state/planning transition evidence;
- focused positive/negative test results;
- configuration failure matrix;
- representative safe-profile evidence;
- Django deploy/system check evidence;
- readiness/liveness evidence;
- exact-head workflow names/run IDs/results;
- explicit residual gaps handed to `BACKUP-RESTORE-DRILL-001`, `SECURITY-BASELINE-001` and `OBSERVABILITY-001`;
- confirmation that live Preview/VPS and product/domain/schema/data scope were not changed unless separately authorized.

## OUT OF SCOPE

- performing the backup/restore drill itself;
- defining RPO/RTO or issuing a restore certificate;
- full security threat model, MFA/RBAC/upload/security-pipeline implementation;
- metrics, alerting, dashboards or incident response;
- release rollback rehearsal;
- module activation/registry implementation;
- UX platform/refactor;
- `SHIFT-HANDOVER-001` or any new domain module;
- production/pilot deployment to a real facility;
- Kubernetes/microservices/HA redesign;
- Ready for Review or merge without explicit product-owner command.

## STOP CONDITION

Stop only when the Draft PR is technically ready for owner acceptance with exact-head evidence. Do not merge and do not mark Ready for Review.