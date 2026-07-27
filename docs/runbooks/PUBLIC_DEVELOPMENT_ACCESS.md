# Public development access — ACCESS-001

**Status:** implementation in Draft PR #17
**Target:** `https://5.181.177.72/`
**Scope:** development only
**Preview:** must remain untouched

## 1. Purpose

ACCESS-001 opens the existing development environment through a publicly trusted
HTTPS endpoint without publishing the application port or PostgreSQL directly.
The EOD login remains the only user authentication layer.

```text
Internet client
→ TCP 443 on 5.181.177.72
→ nginx on the VPS host
→ http://127.0.0.1:8766
→ eod-development application
→ internal PostgreSQL network
```

TCP 80 is used only for HTTP-01 validation and permanent redirect to HTTPS.

## 2. Security boundary

The public boundary exposes only:

- HTTP for `/.well-known/acme-challenge/` and HTTPS redirect;
- HTTPS for the development application.

It does not publish:

- application port `8766`;
- PostgreSQL;
- Docker API;
- nginx administration endpoints;
- preview;
- `/_health/` through the external HTTPS interface.

The local endpoint `http://127.0.0.1:8766/_health/` remains available to the
trusted controller and host diagnostics. An ordinary authenticated user session
after activation is supported only through HTTPS. A plain-HTTP SSH tunnel is not
the canonical user-session path because session and CSRF cookies are secure.

## 3. TLS contract

The certificate is a publicly trusted Let's Encrypt IP address certificate for
`5.181.177.72` using the `shortlived` profile.

Required Certbot command contract:

```text
Certbot 5.4 or newer
--preferred-profile shortlived
--webroot
--ip-address 5.181.177.72
```

The first issuance is tested against Let's Encrypt staging. Production issuance
runs only after the staging request succeeds. The certificate is loaded manually
by nginx because Certbot currently obtains, but does not install, IP address
certificates into the web server.

Official references:

- <https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability.html>
- <https://letsencrypt.org/2026/03/11/shorter-certs-certbot.html>
- <https://certbot.eff.org/instructions?os=ubuntufocal&ws=nginx>

A dedicated systemd timer checks renewal twice daily. The deploy hook validates
nginx configuration and reloads nginx only after successful renewal.

## 4. Mandatory preflight inventory

The bootstrap prints the following evidence before changing the host:

1. OS and network interfaces;
2. locally assigned and externally observed public IPv4;
3. effective `sshd` ports;
4. owners of TCP 80 and 443;
5. nginx installation, state and existing virtual hosts;
6. Certbot installation method and version;
7. complete UFW status and numbered rules;
8. development and preview container identity;
9. trusted controller state.

The factual SSH port is preserved. ACCESS-001 does not create, replace, delete or
renumber an SSH rule. It adds only the required HTTP and HTTPS UFW rules and does
not reset UFW defaults or remove unrelated rules.

If nginx already exists, it is reused. If TCP 80 or 443 is owned by an unrelated
service, bootstrap aborts instead of replacing that service. An existing Certbot
installation is reused only when its version is 5.4 or newer; an older installation
causes a safe abort rather than an implicit replacement.

## 5. Exact-head activation gate

VPS activation is forbidden until all five workflows are green for the same exact
PR head:

```text
AUTO-001A Foundation CI
AUTO-001B Controller CI
EOD Development Stack
EOD Documentation Contract
EOD CI
```

Additional mandatory facts:

```text
PR: #17
branch: infra/access-001-public-development-https
Draft state: OPEN / NOT MERGED
user acceptance: PENDING
merge authorization: ABSENT
```

The one-time root action must fetch the exact PR head, verify the bootstrap
SHA-256, and pass both of these explicit gates:

```text
ACCESS001_CI_CONFIRMED=YES
ACCESS001_SCRIPT_SHA256=<reviewed SHA-256>
```

No VPS action is performed merely because the implementation commit exists.

## 6. What the bootstrap changes

After accepted inventory, the bootstrap:

1. asks the existing AUTO-001B controller to deploy and hold the exact PR head in
   a pending transaction;
2. preserves the current development database backup and rollback boundary;
3. installs nginx only when absent, otherwise reuses it;
4. installs Certbot through the official snap only when Certbot is absent;
5. installs an HTTP-only ACME virtual host;
6. adds the HTTP UFW rule when missing;
7. obtains staging and production IP certificates;
8. updates the host-owned development Compose file and only the required
   non-secret environment keys;
9. recreates the development application with `DJANGO_DEBUG=0` and the public
   HTTPS security contract;
10. installs the TLS virtual host and adds the HTTPS UFW rule when missing;
11. verifies renewal with a dry run;
12. verifies local health, HTTPS login page, HTTP redirect, certificate SAN,
    external health closure, listeners, UFW, timer and preview identity;
13. confirms the AUTO-001B transaction only after all evidence succeeds.

The bootstrap never prints `development.env` or application secrets.

## 7. Django public-mode contract

The host-owned development Compose file supplies:

```text
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,5.181.177.72
DJANGO_CSRF_TRUSTED_ORIGINS=https://5.181.177.72
DJANGO_TRUST_PROXY_HTTPS=1
DJANGO_SECURE_COOKIES=1
EOD_PUBLIC_HTTPS=1
EOD_PUBLIC_HTTPS_ORIGIN=https://5.181.177.72
```

Django fails closed when public mode is combined with debug mode, insecure
cookies, missing proxy trust, missing host/origin, SQLite, the default secret, or
a deployment mode other than development.

`SECURE_SSL_REDIRECT` is intentionally not enabled inside Django because nginx
owns the public redirect and the controller must retain direct loopback health.

## 8. nginx behavior

The final virtual host:

- redirects ordinary HTTP requests to HTTPS;
- serves the ACME webroot on HTTP and HTTPS;
- forwards only to `127.0.0.1:8766`;
- preserves `Host`, real client address and forwarding headers;
- sets `X-Forwarded-Proto: https` only in the TLS virtual host;
- returns `404` for the external `/_health/` path;
- limits login requests conservatively;
- limits request bodies to 16 MiB;
- enforces secure, HttpOnly, SameSite=Lax flags on proxied cookies as a
  defense-in-depth boundary.

## 9. Rollback

Any failure before controller confirmation triggers automatic rollback:

- host Compose and `development.env` are restored;
- the previous nginx configuration and service state are restored;
- UFW rules added by this run are removed;
- renewal units and hook are restored;
- the pending AUTO-001B transaction restores the previous application image and
  database backup;
- preview identity is compared before and after.

Packages installed during a failed attempt are retained but are stopped or left
unused. This avoids destructive package removal during incident recovery.

Evidence is written under:

```text
/srv/eod/audits/ACCESS-001_<run-id>_<head-prefix>/
```

## 10. Manual acceptance after activation

The user acceptance gate requires:

1. open `https://5.181.177.72/` from a network outside the VPS;
2. confirm a publicly trusted certificate for the IP address;
3. log in with the existing EOD account;
4. submit a normal form and confirm CSRF success;
5. repeat the login and navigation check over a mobile network;
6. confirm that `https://5.181.177.72/_health/` is unavailable;
7. confirm that direct external access to `8766` and PostgreSQL fails;
8. confirm preview was not changed.

User acceptance does not authorize merge automatically.

## 11. Parallel PR #16 boundary

ACCESS-001 does not modify PR #16. The current DEFECT-001 head does not contain
the new Django public HTTPS settings. Therefore the safe integration sequence is:

```text
ACCESS-001 accepted and merged
→ PR #16 synchronised with updated main
→ five green exact-head workflows for PR #16
→ trusted development redeployment
```

Deploying the current unsynchronised PR #16 head after ACCESS-001 activation is
not an accepted operating state. It may break HTTPS form submission and must not
be used as a substitute for synchronisation.

## 12. Merge boundary

```text
implementation complete
→ five green exact-head workflows
→ one-time VPS activation
→ technical evidence
→ external and mobile user acceptance
→ separate explicit merge command
```

Automatic merge remains forbidden.
