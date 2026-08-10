# SECURITY-BASELINE-001

This file is a non-canonical work-item brief. Mutable execution state remains owned by `docs/project/DEMO_RELEASE_PLAN.yaml`; volatile project state remains owned by `docs/project/CURRENT_STATE.md`.

## Purpose

Complete the final `SAFE-CONTINUATION` prerequisite by accepting a repository-grounded threat model, a small fail-closed production security baseline, focused negative tests and explicit residual-risk handoffs.

## Starting baseline

`BACKUP-RESTORE-DRILL-001` was accepted by the product owner and merged from PR #64.

- accepted exact head: `9f9b650f637af7b9bbeb2c63cb3995763b0854e0`;
- merge commit/current main at contour creation: `860e189bbb5bc05a6da4a7680acd5f719b4874af`;
- issue #63: CLOSED / COMPLETED;
- live Preview/VPS: untouched.

The first substantive change must atomically record that acceptance and move `SECURITY-BASELINE-001` from `NOT_STARTED` to `IN_PROGRESS`. After that transition, `SAFE-CONTINUATION` must show 7/8 accepted items while this work item remains in progress.

## Canonical risk scope

The industrialization program maps this work item to `PSR-022`, `PSR-023`, `PSR-024` and `PSR-033` and defines acceptance as `Threat model, hardening controls and negative tests accepted`.

The scope is intentionally bounded:

- `PSR-022`: prove and complete the production TLS/session/security-settings baseline;
- `PSR-023`: identify and hand off residual security-pipeline requirements to `SECURITY-PIPELINE-001`, without duplicating accepted provenance/secret-hygiene work;
- `PSR-024`: define the identity-assurance boundary and hand full MFA/privileged re-auth/access review/break-glass work to `AUTH-RBAC-HARDENING-001`;
- `PSR-033`: remove the unsafe assumption that globally routed Django admin is acceptable in production by default; full privileged admin assurance/audit remains `AUTH-RBAC-HARDENING-001`.

## Required first canonical transition

Before security implementation evidence:

1. verify live current main, accepted PR #64 and issue #63;
2. change `BACKUP-RESTORE-DRILL-001` from `IN_PROGRESS` to `ACCEPTED` with PR #64 exact head, merge commit, owner acceptance, final workflow IDs and restore-certificate evidence;
3. change `SECURITY-BASELINE-001` from `NOT_STARTED` to `IN_PROGRESS`;
4. update `CURRENT_STATE.md` to issue #65 / branch `security/security-baseline-001` / Draft PR for this item;
5. append immutable acceptance/baseline history;
6. regenerate deterministic project views using existing generators;
7. keep the domain queue paused and `SHIFT-HANDOVER-001` not started.

## Threat model

Build from actual EOD architecture and code, not a generic checklist. Cover protected operational/personnel/authority data, credentials/session state, PostgreSQL, deployment configuration, audit/evidence and backup/restore evidence; ordinary/privileged/unauthenticated/compromised/CI actors; browser-proxy-Django-PostgreSQL-GitHub/secrets trust boundaries; login/session, HTTP routes, admin, health/readiness, import/upload/download and management/service entry points where present.

Material threats must map to exactly one status: mitigated now, accepted prior baseline, deferred to a named work item, or not applicable with evidence.

## Existing accepted controls

Preserve rather than redesign:

- Deployment Profile production fail-closed contract;
- PostgreSQL-only production semantics;
- reverse-proxy TLS, secure cookies and HSTS baseline;
- Secret Hygiene;
- Dependency Provenance / SBOM / signing evidence;
- Backup Restore Drill.

## Required baseline behavior

### Production settings

Use `django check --deploy` plus focused tests against production-capable settings. Important unsafe production secrets/configuration, DEBUG/testing/SQLite fallback, unsafe Host/origin/proxy/TLS assumptions and security-sensitive cookie/session drift must fail closed.

Do not silently rely on framework defaults for a material project security decision.

### Django admin

`src/eod_config/urls.py` currently routes `/admin/` globally. Production-capable baseline must not expose this privileged bypass surface by default.

Use the smallest maintainable fail-closed design. Preferred invariant: production admin is disabled/unrouted by default; any future explicit enablement remains exceptional and requires later `AUTH-RBAC-HARDENING-001` assurance/audit/network controls.

Negative tests must prove production default cannot reach admin.

### CSRF / HTTP / headers

Prove the actual accepted deployment boundary with focused negative tests. Use a stable existing write route for CSRF behavior if one exists; do not create fake product endpoints solely for tests. Inventory material response-security headers/settings and make necessary project decisions explicit without introducing heavyweight security middleware only to satisfy a checklist.

## Explicit residual handoffs

- `SECURITY-PIPELINE-001`: blocking SAST/dependency/container scanning, vulnerability severity/exception policy and release security evidence.
- `AUTH-RBAC-HARDENING-001`: MFA, privileged re-auth, rate/lockout policy where appropriate, access review, break-glass and full privileged/admin audit.
- `UPLOAD-HARDENING-001`: full MIME/size/AV/quarantine/storage/download hardening if pilot scope enables relevant surfaces.
- `MODULE-REGISTRY-001`: universal module/capability guards; security baseline states the invariant but does not implement registry control plane.

Never mark those deferred controls as PASS unless actually implemented and tested.

## Evidence semantics

If machine-readable evidence is useful, keep it small and deterministic. Allowed semantic states:

- `PASS` — executable current control proven;
- `ACCEPTED_PRIOR_BASELINE` — already proven by a named accepted work item;
- `DEFERRED` — named later work item with explicit residual requirement;
- `NOT_APPLICABLE` — supported by repository/scope evidence.

Do not create another governance framework.

## Risk-based test policy

During implementation run focused security/deployment tests. Do not manually run the full heavy suite after every small edit. Existing workflows stay enabled. Final acceptance requires one common exact head, `behind_by: 0`, and all applicable workflows green.

## Out of scope

- full `SECURITY-PIPELINE-001`;
- full `AUTH-RBAC-HARDENING-001`;
- `UPLOAD-HARDENING-001` implementation;
- `MODULE-REGISTRY-001` implementation;
- product/domain features, new journals or UX refactor;
- observability/incident response;
- migration safety/release rollback;
- WAF/IDS/HA/Kubernetes or production network redesign;
- live Preview/VPS mutation without explicit owner authorization;
- Ready for Review or merge before owner acceptance.

## Implemented candidate boundary

The current Draft candidate remains `IN_PROGRESS` and intentionally stops at the SAFE baseline boundary:

- the required DR acceptance / Security start transition is recorded canonically, with `SAFE-CONTINUATION` at 7/8 and the domain queue still paused;
- `THREAT_MODEL.md` records repository-grounded assets, actors, trust boundaries, entry points and material threat dispositions;
- production-capable settings explicitly pin material cookie/session/header decisions instead of relying on framework defaults;
- production derives `EOD_DJANGO_ADMIN_ENABLED=False` from the deployment contract, and the URL configuration omits the privileged `/admin/` route when disabled;
- development/CI keep Django admin available;
- a real POST logout route supplies focused CSRF-negative evidence without creating a synthetic product endpoint;
- the production deployment workflow deliberately supplies a stray `EOD_DJANGO_ADMIN_ENABLED=1` environment value but still requires the loaded production setting to remain false and `/admin/` to return HTTP 404;
- the production deployment workflow retains PostgreSQL-only identity checks and `python manage.py check --deploy`;
- existing Secret Hygiene and Dependency Provenance gates were kept fail closed; detected test credential/process-provenance violations were repaired at source rather than allowlisted or excluded;
- generated dependency inventory views were regenerated with the accepted repository generator after source stabilization;
- no machine-readable security governance platform was introduced.

Residual MFA/privileged assurance, SAST/dependency/container vulnerability scanning and severity policy, full upload hardening, and universal module/capability authorization remain explicitly deferred to their named future work items. They are not claimed as implemented by this candidate.

## Acceptance boundary

Stop at a technically complete Draft PR with a repository-grounded threat model, focused fail-closed security controls, production-safe admin default, executable negative tests, explicit residual handoffs, `SAFE-CONTINUATION` still 7/8 while this item is IN_PROGRESS, `behind_by: 0`, all applicable exact-head workflows green and live Preview/VPS untouched.
