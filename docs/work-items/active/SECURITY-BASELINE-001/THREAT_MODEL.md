# SECURITY-BASELINE-001 — repository-grounded threat model

**Статус:** `IN_PROGRESS / OWNER ACCEPTANCE PENDING`
**Контур:** issue #65 / Draft PR #66 / `security/security-baseline-001`
**Граница:** SAFE-CONTINUATION baseline, а не полный security programme.

## 1. Правила disposition

Для material threats используются только четыре значения:

- `PASS` — контроль и его focused evidence входят в текущий candidate;
- `ACCEPTED_PRIOR_BASELINE` — контроль уже принят владельцем в предыдущем work item и здесь не переизобретается;
- `DEFERRED` — остаточный риск явно передан в указанный named work item;
- `NOT_APPLICABLE` — контроль/сценарий не относится к фактической текущей архитектуре, с repository evidence.

`DEFERRED` не считается `PASS`.

## 2. Фактическая архитектура и assets

Защищаемые assets текущего EOD:

- оперативные записи и их зарегистрированные/исторические evidence-состояния;
- персонал, роли и предметные оперативные полномочия;
- authentication/session state;
- runtime secrets и credentials;
- PostgreSQL production data;
- deployment configuration и reverse-proxy trust contract;
- audit/evidence artifacts;
- backup/restore evidence;
- repository, dependency locks, SBOM/provenance и CI evidence.

## 3. Actors

- unauthenticated network client;
- ordinary authenticated user;
- privileged operator/admin;
- compromised legitimate account;
- accidental or malicious operator;
- repository/CI actor.

## 4. Trust boundaries

| Boundary | Repository-grounded implementation |
|---|---|
| browser ↔ reverse proxy/TLS | `compose.production.yaml`, `src/eod_config/deployment.py`, production deployment workflow |
| reverse proxy ↔ Django | trusted `X-Forwarded-Proto` only under explicit production reverse-proxy contract; forwarded Host disabled |
| Django ↔ PostgreSQL | production profile is PostgreSQL-only; DB is not host-published by production Compose |
| runtime ↔ external secrets/config | production secret/DB password/hosts/origins are external configuration and fail closed |
| GitHub Actions ↔ artifacts/evidence | Secret Hygiene redaction/verification and Dependency Provenance exact-head evidence are accepted baselines |
| future off-host backup boundary | no live off-host production storage is claimed by this work item |

## 5. Current entry points

### Network/UI

- login and session creation through the organizations authentication routes;
- POST logout;
- product HTTP routes in organizations, documents, normatives, equipment, dispatching, workplace docs, operational documents, defects and operational log;
- health endpoints `/_health/`, `/_health/live/`, `/_health/ready/`;
- Django admin `/admin/` in development/CI only after this work item.

### Import/upload/download

`src/apps/imports/urls.py` and `src/apps/imports/views.py` expose real authenticated import surfaces, including:

- generic workbook/file upload, mapping, row decisions, discard and publication;
- personnel workbook staging/publication;
- workplace-document register upload/publication;
- power-system package upload/review/publication;
- power-system canonical snapshot download.

The views are protected by `login_required` and publication paths include domain permission/re-authentication checks where implemented. Those facts do **not** establish full upload hardening.

### Operator/management paths

Standard Django `manage.py` is a privileged operator entry point. Repository search found no repository-defined `BaseCommand` implementation and no Celery/`shared_task` background-task contour in the current codebase. Privileged shell/management-command governance is therefore treated separately from network routes.

## 6. Material threat dispositions

| Material threat / abuse case | Disposition | Current evidence / exact residual boundary |
|---|---|---|
| HTTP downgrade in production | `ACCEPTED_PRIOR_BASELINE` | `DEPLOYMENT-PROFILE-001`: `SECURE_SSL_REDIRECT`, HSTS and explicit reverse-proxy TLS contract. Public TLS infrastructure itself is outside repository evidence. |
| spoofed proxy protocol header / wrong TLS termination | `ACCEPTED_PRIOR_BASELINE` | production requires `reverse-proxy` termination plus explicit trusted proxy headers; negative deployment tests reject missing/wrong contract. |
| Host / forwarded-host abuse | `ACCEPTED_PRIOR_BASELINE` | explicit hosts, wildcard/leading-dot rejection, HTTPS CSRF origins, `USE_X_FORWARDED_HOST=False`. |
| weak/missing Django secret | `ACCEPTED_PRIOR_BASELINE` | Deployment Profile fails closed; Secret Hygiene is already accepted. Current focused tests additionally cover a missing key. |
| `DEBUG` or testing semantics in production | `ACCEPTED_PRIOR_BASELINE` | Deployment Profile rejects both. |
| SQLite production fallback | `ACCEPTED_PRIOR_BASELINE` | production is PostgreSQL-only; negative preflight/test evidence rejects SQLite. |
| insecure session/cookie/header default drift | `PASS` | current candidate makes HttpOnly, SameSite, secure-cookie production semantics, referrer policy, nosniff and frame denial explicit; production subprocess/runtime assertions cover them. |
| CSRF bypass on current session mutation | `PASS` | real POST logout endpoint is covered by `Client(enforce_csrf_checks=True)` negative test and rejects a missing token with HTTP 403. |
| Django admin bypass of product workflows in production | `PASS` | `EOD_DJANGO_ADMIN_ENABLED=False` is derived from the production-capable deployment contract; `/admin/` is absent from URL resolver and deployment smoke requires HTTP 404. No environment opt-in exists. |
| future exceptional production admin exposure | `DEFERRED` | `AUTH-RBAC-HARDENING-001`: privileged assurance, network restriction decision, re-authentication and privileged/admin audit. This PR does not claim such exposure pilot-safe. |
| compromised legitimate account / privileged session abuse | `DEFERRED` | `AUTH-RBAC-HARDENING-001`: MFA, privileged re-auth, rate limiting/lockout where required, access review, stale-access revocation, break-glass and pilot assurance levels. |
| SAST/dependency/container vulnerability detection and release severity policy | `DEFERRED` | `SECURITY-PIPELINE-001`: blocking scanners, severity threshold, exception/waiver expiry and release security evidence. Accepted Secret Hygiene/Dependency Provenance are reused, not duplicated. |
| secret/evidence leakage through CI artifacts | `ACCEPTED_PRIOR_BASELINE` | `SECRET-HYGIENE-001`: raw → redact → verify → publication and fail-closed sanitised evidence handling. |
| repository/dependency provenance spoofing | `ACCEPTED_PRIOR_BASELINE` | `DEPENDENCY-PROVENANCE-001`: hashed lock projections, SBOM, in-toto/SLSA provenance and Sigstore/OIDC signing identity evidence. |
| backup/restore evidence leaking raw database content | `ACCEPTED_PRIOR_BASELINE` | `BACKUP-RESTORE-DRILL-001`: raw dump not published; non-secret restore certificate accepted. |
| unsafe upload/import assumptions (MIME, size, hostile file content, AV/quarantine/storage) | `DEFERRED` | `UPLOAD-HARDENING-001`; current authentication/publication controls are not misrepresented as complete upload security. |
| hidden UI or closed route mistaken for authorization/module capability | `DEFERRED` | `MODULE-REGISTRY-001`; invariant: UI visibility and route presence are not authorization, and security decisions belong at appropriate service/capability boundaries. No universal module guard is added here. |
| privileged `manage.py`/operator path misuse | `DEFERRED` | `AUTH-RBAC-HARDENING-001` owns remaining privileged-operator assurance/audit policy; no network-accessible custom management API was found. |
| repository-owned background worker/service attack surface | `NOT_APPLICABLE` | no repository-defined `BaseCommand`, Celery or `shared_task` background contour was found in the current repository search. |
| detailed backend failure disclosure from health probes | `PASS` | `src/eod_config/health.py` returns bounded status strings and deliberately suppresses backend exception details. |
| CSP framework adoption | `NOT_APPLICABLE` | CSP is a possible hardening control, not a material threat disposition by itself. No repository-grounded SAFE blocker requiring a new CSP/third-party framework was established; this work item does not claim CSP or XSS elimination. |
| live off-host backup storage provisioning | `NOT_APPLICABLE` | this repository-only baseline neither provisions nor claims live off-host storage. Accepted DR evidence is preserved without inventing deployment state. |

## 7. Production security decisions

The production-capable profile retains the accepted Deployment Profile and adds only bounded explicit decisions:

- secure cookies remain mandatory in production;
- session and CSRF cookies are `HttpOnly` and `SameSite=Lax` as explicit project settings;
- `SECURE_CONTENT_TYPE_NOSNIFF=True`;
- `X_FRAME_OPTIONS=DENY`;
- `SECURE_REFERRER_POLICY=same-origin`;
- HSTS remains contract-controlled with a minimum accepted production value of 3600 seconds;
- trusted proxy protocol remains `X-Forwarded-Proto=https` under the explicit reverse-proxy contract;
- forwarded Host trust remains disabled;
- production Django admin is unrouted by construction;
- no production admin environment toggle is introduced.

The production deployment gate continues to execute `python manage.py check --deploy` under the isolated production-capable PostgreSQL profile.

## 8. Negative-test matrix

| Scenario | Evidence source | Expected result |
|---|---|---|
| missing production secret | `test_deployment_profile.py` | rejected |
| weak production secret | existing Deployment Profile test | rejected without echoing secret |
| production `DEBUG` | existing Deployment Profile test | rejected |
| production testing flag | existing Deployment Profile test | rejected |
| production SQLite | existing test + deployment workflow negative preflight | rejected |
| wildcard/subdomain-wildcard host | existing Deployment Profile tests | rejected |
| non-HTTPS / credentialed CSRF origin | existing Deployment Profile tests | rejected |
| missing/wrong TLS termination | deployment tests | rejected |
| untrusted proxy configuration | existing Deployment Profile test | rejected |
| forwarded Host trust | existing Deployment Profile test | rejected |
| insufficient HSTS | existing Deployment Profile test | rejected |
| insecure session/cookie/header drift | `test_security_baseline.py` + deployment runtime assertions | rejected by exact-value assertions |
| production admin exposed by default | production resolver test + deployment HTTP smoke | `/admin/` does not resolve / HTTP 404 |
| stray `EOD_DJANGO_ADMIN_ENABLED=1` environment value | production subprocess test | ignored; admin remains disabled |
| CSRF-less real logout mutation | `test_security_baseline.py` | HTTP 403 |
| invalid machine-readable security evidence claim | no artifact introduced | `NOT_APPLICABLE` |

## 9. Explicit residual handoff

This work item does **not** implement or claim:

- MFA or full privileged-session assurance — `AUTH-RBAC-HARDENING-001`;
- SAST, dependency vulnerability scanning, container scanning, severity/waiver lifecycle — `SECURITY-PIPELINE-001`;
- MIME/AV/quarantine/storage redesign or a complete download-authorization framework — `UPLOAD-HARDENING-001`;
- universal module/capability authorization guards or specialised defect-route guard replacement — `MODULE-REGISTRY-001`;
- live off-host production backup storage;
- WAF/IDS, Kubernetes, HA, production network redesign, observability or incident-response framework.

`EquipmentDefectRouteGuardMiddleware` is not generalised in this PR. The baseline records only the invariant that route/UI closure is not an authorization substitute.

## 10. Acceptance boundary

Until explicit owner acceptance and merge:

- `SECURITY-BASELINE-001` remains `IN_PROGRESS`;
- `SAFE-CONTINUATION` remains `7/8`;
- domain queue remains `PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION`;
- `SHIFT-HANDOVER-001` is not started;
- live Preview/VPS remains untouched.
