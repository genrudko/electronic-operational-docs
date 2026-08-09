# Pilot / production-capable deployment profile

**Work item:** `DEPLOYMENT-PROFILE-001`

This runbook defines the repository-owned deployment contract. It does **not** claim that a real facility is production-ready and does not replace external TLS/DNS/reverse-proxy, backup/restore, security-baseline or observability acceptance.

## Deployment modes

| Mode | Purpose | Production-capable |
|---|---|---:|
| `development` | local/isolated development | no |
| `ci` | automated gates/tests | no |
| `preview` | protected non-production Preview | no |
| `production` | hardened profile used for pilot/production-capable operation | yes |

`DEBUG=0` is not a production switch. Only `EOD_DEPLOYMENT_MODE=production` activates the production-capable contract, and that mode refuses unsafe configuration.

## Mandatory production environment

The operator must supply all values below. Secret values must come from the deployment secret store/environment and must never be committed.

```text
EOD_DEPLOYMENT_MODE=production
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<strong unique value, >= 50 characters>
DJANGO_ALLOWED_HOSTS=<explicit host list; no wildcard>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<public-origin>[,https://...]
DJANGO_SECURE_HSTS_SECONDS=3600
EOD_TLS_TERMINATION=reverse-proxy
EOD_TRUST_PROXY_HEADERS=1
EOD_TRUST_X_FORWARDED_HOST=0
DB_ENGINE=postgresql
POSTGRES_DB=<database>
POSTGRES_USER=<database user>
POSTGRES_PASSWORD=<non-development password>
POSTGRES_HOST=<database host>
POSTGRES_PORT=5432
EOD_DATABASE_PROFILE=production
EOD_ALLOW_SQLITE_PATH_OVERRIDE=0
```

`DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` and `DJANGO_SECURE_HSTS_PRELOAD` default to `0`. Enable them only after the DNS/certificate scope is explicitly verified; this work item does not infer that every subdomain is ready for HSTS.

## Fail-closed negative matrix

Production startup/preflight rejects at least these states:

| Unsafe state | Result |
|---|---|
| missing/short/default Django secret | reject |
| `DJANGO_DEBUG=1` | reject |
| empty or wildcard `DJANGO_ALLOWED_HOSTS` | reject |
| missing, HTTP or wildcard CSRF trusted origin | reject |
| SQLite / unknown database engine | reject |
| missing PostgreSQL DB/user/password/host/port | reject |
| local development PostgreSQL password | reject |
| SQLite path override enabled | reject |
| TLS termination not declared as `reverse-proxy` | reject |
| trusted proxy protocol contract not explicitly enabled | reject |
| `X-Forwarded-Host` trust enabled | reject |
| HSTS below the minimum repository contract | reject |

Diagnostics name the invalid setting/contract but do not echo secret values.

## Application-side TLS and reverse-proxy contract

TLS terminates at an external reverse proxy. The Django application must not be exposed directly to untrusted networks.

The proxy must:

1. terminate valid HTTPS for the intended public name;
2. preserve the canonical `Host` header used by `ALLOWED_HOSTS`;
3. remove/overwrite client-supplied forwarding headers;
4. set `X-Forwarded-Proto: https` for trusted HTTPS requests;
5. forward only to the loopback-bound EOD application port.

Django trusts only `X-Forwarded-Proto=https` through `SECURE_PROXY_SSL_HEADER`; `USE_X_FORWARDED_HOST` remains disabled. Production enables HTTPS redirect, secure session/CSRF cookies and HSTS.

Repository tests can prove those application settings and the loopback/private-port Compose contract. They **cannot** prove the real certificate chain, DNS, firewall rules, proxy sanitisation or external network path. Those remain mandatory external verification before any real pilot/production deployment.

## PostgreSQL-only rule

`compose.production.yaml` has an internal PostgreSQL service with no published host database port. Production settings reject SQLite even if a SQLite path is present, so there is no silent development-database fallback.

## Preflight

From an exact repository release candidate with the required environment exported:

```bash
python scripts/deployment_preflight.py
```

The command first validates the repository deployment contract and then runs:

```bash
python manage.py check --deploy --fail-level WARNING
```

A production container performs the same preflight before migrations and static collection. Any contract or Django deployment warning therefore prevents startup.

For the Compose profile:

```bash
docker compose -f compose.production.yaml config --quiet
docker compose -f compose.production.yaml up --build --detach
```

Do not run this against the live VPS/Preview merely to satisfy repository acceptance. Real deployment requires a separate owner-authorised action.

## Liveness and readiness

| Endpoint | Meaning | Dependency behaviour |
|---|---|---|
| `/_health/live/` | process is serving HTTP | does not touch the database |
| `/_health/ready/` | application can safely serve the bounded deployment | checks DB connectivity and pending Django migrations; returns 503 on failure |
| `/_health/` | backward-compatible alias | remains readiness semantics |

Liveness is intentionally minimal so a temporary database outage does not create application restart loops. Readiness is intentionally fail-closed. Response bodies are generic and do not expose backend exceptions or credentials.

Metrics, dashboards, alerts, SLOs and dependency-specific observability are not part of this work item and remain `OBSERVABILITY-001`.

## Representative repository verification

A safe representative profile must pass all of:

```bash
python scripts/deployment_preflight.py
docker compose -f compose.production.yaml config --quiet
curl --fail http://127.0.0.1:8767/_health/live/
curl --fail http://127.0.0.1:8767/_health/ready/
```

The repository gate also verifies that the app port is bound to loopback and PostgreSQL publishes no host port.

## Explicit residual boundaries

- `BACKUP-RESTORE-DRILL-001`: actual backup, restore rehearsal, restore certificate, RPO/RTO and recovery evidence.
- `SECURITY-BASELINE-001`: full threat model and broader application/security hardening beyond this deployment boundary.
- `OBSERVABILITY-001`: metrics, dashboards, alerting, operational monitoring and drills.

This work item does not change domain models, migrations, product data, modules or UX, and it does not touch the live Preview/VPS.
