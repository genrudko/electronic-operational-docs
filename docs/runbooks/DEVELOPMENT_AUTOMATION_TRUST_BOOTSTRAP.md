# Runbook — trusted development automation

## 1. Baseline

```text
repository: genrudko/electronic-operational-docs
accepted AUTO-001A baseline: b9fe794955af33843aee9b553ae73c06352e0929
accepted application baseline: 937d2cd2b187c17fac3088ccfc52079fc4608306
AUTO-001B merge: requires a separate explicit user decision
```

AUTO-001A supplies the trusted `pull_request_target:labeled` entry point from `main`.
AUTO-001B adds a restricted VPS controller for the isolated development contour only.
Preview is never a target of this controller.

## 2. Files installed on the VPS

The reviewed bootstrap copies fixed host-owned files to:

```text
/usr/local/sbin/eod-development-controller
/etc/eod-automation/controller.env
/etc/eod-automation/compose.development.yaml
/etc/eod-automation/Dockerfile.development
/etc/eod-automation/app-entrypoint.sh
```

Runtime data is stored under:

```text
/srv/eod/automation/repository.git
/srv/eod/automation/releases/
/srv/eod/automation/backups/
/srv/eod/automation/state/
```

The restricted account is `eod-automation`. It is not a member of the `docker` group.
Its SSH key is forced to run only:

```text
sudo -n /usr/local/sbin/eod-development-controller ssh-gateway
```

## 3. Bootstrap

Run only after AUTO-001B has been reviewed and merged into `main`:

```bash
cd /srv/eod/repository
sudo bash deploy/automation/bootstrap_auto001b.sh
```

The bootstrap is idempotent. A repeat run updates the installed reviewed files without creating duplicate users, keys, `authorized_keys` entries or sudo rules.

The first run prints only the public read-only GitHub Deploy Key. Add it at:

```text
Repository Settings -> Deploy keys -> Add deploy key
Allow write access: OFF
```

The private Deploy Key remains root-owned on the VPS and is never printed.
After adding the public key, run the same bootstrap command again and confirm:

```text
Deploy Key access test: SUCCESS
```

Create GitHub Actions secrets exactly as printed by bootstrap:

```text
EOD_VPS_HOST
EOD_VPS_PORT
EOD_VPS_SSH_PRIVATE_KEY
EOD_VPS_HOST_KEY
```

Do not send either private key to chat.

## 4. Normal PR verification

For an open same-repository PR with all required exact-SHA CI checks green, the repository owner adds one label:

```text
vps-development-refresh
vps-development-rebuild
```

The trusted workflow from `main` validates the current PR SHA and invokes the installed controller with only:

```text
profile
PR number
exact 40-hex SHA
GitHub workflow run ID
```

The controller fetches `refs/pull/<number>/head` using the read-only Deploy Key and rejects it if the fetched SHA differs.

## 5. Execution order

Before changing the working development database:

1. build the exact-SHA image with the fixed host Dockerfile;
2. start a temporary PostgreSQL container with ephemeral storage;
3. run `manage.py check`;
4. run `makemigrations --check --dry-run`;
5. run the full `manage.py test apps --verbosity 2` suite;
6. remove the temporary test database and network.

Only after all tests succeed:

```text
stop development application
-> pg_dump eod_development
-> apply migrations with the new exact-SHA image
-> start the new release
-> verify health and Django check
```

The fixed controller accepts only development identifiers:

```text
Compose project: eod-development
PostgreSQL database/user: eod_development
PostgreSQL volume: eod_development_postgres_data
HTTP port: 8766
Environment file: /srv/eod/secrets/development.env
```

No preview path, port, database, volume or command is present in the controller.

## 6. Results

The workflow reports one practical result:

```text
SUCCESS
ERROR
STALE SHA
```

- `SUCCESS`: exact SHA remains current after VPS verification and the transaction is confirmed.
- `ERROR`: build, isolated tests, backup, migration, start or health verification failed.
- `STALE SHA`: the PR head changed during verification; the workflow calls development rollback.

The workflow never approves or merges a PR.

## 7. Automatic rollback

If migrations or the new application start fails, the controller performs:

```text
stop failed new application
-> recreate eod_development
-> restore the transaction pg_dump
-> start the previous application image
-> verify health
-> return ERROR
```

The same rollback is used for `STALE SHA` before the new release is confirmed.
Preview is untouched.

## 8. Manual rollback

The VPS operator can roll back the last confirmed development deployment:

```bash
sudo /usr/local/sbin/eod-development-controller rollback-last
```

Inspect the current controller state with:

```bash
sudo /usr/local/sbin/eod-development-controller status
```

Manual rollback applies only to the development contour.

## 9. Acceptance gate

Before merging AUTO-001B, record:

```text
exact PR head
AUTO-001A Foundation CI: success
AUTO-001B Controller CI: success
EOD CI: success
EOD Development Stack: success
EOD Documentation Contract: success
VPS changes before merge: none
```

After merge, run bootstrap and one safe canary on a non-protected test PR. The canary must remain unmerged and must confirm `SUCCESS`, exact SHA, development-only targeting and no preview change.
