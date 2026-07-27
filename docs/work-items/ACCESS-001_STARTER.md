# ACCESS-001 — Public HTTPS access to development

## Status

```text
work item: ACCESS-001
branch: infra/access-001-public-development-https
base: main
implementation: NOT STARTED
merge authorization: ABSENT
preview changes: FORBIDDEN
```

## User goal

Open the current development environment from a work laptop or phone without starting an SSH tunnel each time.

Target address:

```text
https://5.181.177.72/
```

No domain purchase. No second authentication layer. Existing EOD login remains the only application login.

## Existing facts

- VPS: Ubuntu Server 24.04 LTS Minimal.
- UFW is enabled with default deny incoming; SSH remains allowed.
- Development app currently publishes only:

```text
127.0.0.1:8766 -> app:8766
```

- PostgreSQL is internal and must remain unpublished.
- Preview must remain untouched.
- Current development Compose hardcodes `DJANGO_DEBUG: "1"` and `DJANGO_ALLOWED_HOSTS` defaults to `127.0.0.1,localhost`.
- Existing trusted deployment controller uses the fixed host Compose file from `/etc/eod-automation/compose.development.yaml`.

## Minimal accepted architecture

```text
Internet client
    -> HTTPS 443 on 5.181.177.72
    -> nginx reverse proxy on VPS host
    -> http://127.0.0.1:8766
    -> existing development container
```

HTTP 80 is used only for ACME validation and redirect to HTTPS.

The app port `8766` stays bound to loopback and is never opened directly to the Internet.

## TLS contract

Use a publicly trusted Let's Encrypt IP address certificate.

IP certificates are short-lived. The implementation must use Certbot 5.4 or newer with automated renewal:

```text
--preferred-profile shortlived
--ip-address 5.181.177.72
--webroot
```

Official references:

- https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability.html
- https://letsencrypt.org/2026/03/11/shorter-certs-certbot.html

## Required application changes

1. Development must run with `DJANGO_DEBUG=0` when publicly reachable.
2. `DJANGO_ALLOWED_HOSTS` must include `5.181.177.72`.
3. Django must trust the reverse-proxy HTTPS signal only from the local proxy path:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

4. Add environment-driven trusted CSRF origins, including:

```text
https://5.181.177.72
```

5. Public mode must use secure session and CSRF cookies.
6. Existing local SSH-tunnel access to `127.0.0.1:8766` must continue working.

## Required nginx behavior

- Listen on public ports 80 and 443 only.
- Proxy to `127.0.0.1:8766`.
- Preserve host and client forwarding headers.
- Set `X-Forwarded-Proto https` on the TLS virtual host.
- Redirect ordinary HTTP traffic to HTTPS.
- Serve `/.well-known/acme-challenge/` from a dedicated webroot.
- Return a non-public response for `/_health/` through the external interface.
- Apply a conservative request-body limit and login rate limit without changing application behavior.
- Reload automatically after certificate renewal.

## Firewall contract

UFW must expose only:

```text
22/tcp   SSH
80/tcp   ACME + HTTPS redirect
443/tcp  HTTPS development access
```

Do not expose:

- 8766/tcp;
- PostgreSQL;
- Docker API;
- Caddy/nginx admin endpoints;
- any preview port.

## Repository deliverables

Expected narrow scope:

```text
deploy/access/bootstrap_access001.sh
deploy/access/nginx/eod-development.conf
src/eod_config/settings.py
deploy/automation/compose.development.yaml
docs/runbooks/PUBLIC_DEVELOPMENT_ACCESS.md
tests for security settings and bootstrap contract
```

The bootstrap script must be autonomous, idempotent, auditable, and abort safely when:

- the public IP does not match the expected server IP;
- ports 80 or 443 are already owned by an unrelated service;
- Certbot is too old;
- certificate issuance fails;
- nginx configuration validation fails;
- UFW is unavailable or not active;
- the development application health check fails.

No Base64 payloads, temporary part-files, or self-applying GitHub Actions workflows.

## Deployment boundary

This is a host infrastructure change. Existing AUTO-001B application deployment cannot install the first version of the new host proxy because the current restricted controller does not yet own that capability.

Therefore the first activation may require exactly one reviewed root command block on the VPS after the PR exact head is green. That block must:

1. fetch the exact accepted commit from GitHub;
2. verify the fetched script checksum;
3. execute the repository bootstrap;
4. print complete preflight, TLS, firewall, nginx, Django and rollback evidence.

After initial bootstrap, normal DEFECT-001 and later application deployments must continue without manual VPS commands.

## Acceptance gates

```text
GitHub exact head
-> all required CI green
-> one-time VPS bootstrap
-> nginx config test
-> publicly trusted TLS certificate for 5.181.177.72
-> HTTPS login from external network
-> form POST/CSRF check
-> mobile-network check
-> local 127.0.0.1:8766 health check
-> PostgreSQL not externally reachable
-> port 8766 not externally reachable
-> preview untouched
-> user acceptance
-> separate explicit merge command
```

## Explicit non-goals

- domain registration;
- Cloudflare Tunnel;
- Tailscale;
- second Basic Auth prompt;
- public preview access;
- changes to DEFECT-001 business logic;
- automatic merge;
- opening development directly over plain HTTP;
- exposing `0.0.0.0:8766`.

## First response of the implementation chat

Before changing code, verify the actual repository state and return:

```text
FACT
GAP MATRIX
IMPLEMENTATION PLAN
ONE-TIME VPS ACTION
SECURITY BOUNDARY
READY TO IMPLEMENT or BLOCKED
```

Do not create another branch or PR. Continue only in this branch and its Draft PR.
