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

## 3. Bootstrap from the accepted exact main

Run only after AUTO-001B has been reviewed, merged into `main`, and the integration chat has recorded the exact accepted merge SHA.

Replace the placeholder with that exact accepted `main` SHA:

```bash
cd /srv/eod/repository

AUTO001B_MAIN_SHA=<accepted AUTO-001B merge commit>
git fetch --prune origin main
git checkout main
git reset --hard "$AUTO001B_MAIN_SHA"
test "$(git rev-parse HEAD)" = "$AUTO001B_MAIN_SHA"
test "$(git rev-parse origin/main)" = "$AUTO001B_MAIN_SHA"

sudo bash deploy/automation/bootstrap_auto001b.sh
```

Do not run bootstrap from an old checkout, a PR branch, or an unverified `origin/main`.

The bootstrap is idempotent. A repeat run updates the installed reviewed files without creating duplicate users, keys, `authorized_keys` entries or sudo rules.

The first run prints only the public read-only GitHub Deploy Key. Add it at:

```text
Repository Settings -> Deploy keys -> Add deploy key
Allow write access: OFF
```

The private Deploy Key remains root-owned on the VPS and is never printed.
After adding the public key, run the same exact-main bootstrap command again and confirm:

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

The same rollback is used for `STALE SHA`.

After a successful VPS deploy, the controller keeps one pending transaction until GitHub confirms that the PR SHA is still current. If the workflow fails or is cancelled before confirmation, the fallback step calls `rollback-pending`. It restores the backup and previous image, moves the pending state to a completed rollback record, and therefore does not block the next deployment.

Preview is untouched.

## 8. Pending transaction recovery

Inspect controller state:

```bash
sudo /usr/local/sbin/eod-development-controller status
```

A pending transaction is reported with its workflow run ID:

```text
transaction=PENDING
pending_run_id=<run id>
```

Recover the single unfinished transaction locally:

```bash
sudo /usr/local/sbin/eod-development-controller rollback-pending
```

Successful recovery returns:

```text
ROLLBACK_PENDING_SUCCESS run=<run id>
```

This command:

1. finds the single pending transaction;
2. stops the unconfirmed new application;
3. restores the saved development database;
4. starts the previous image and verifies health;
5. removes the pending state by moving it to a rolled-back record.

If no pending transaction exists, the command stops with a clear error and changes nothing.

## 9. Manual rollback of the last confirmed release

The VPS operator can roll back the last confirmed development deployment:

```bash
sudo /usr/local/sbin/eod-development-controller rollback-last
```

`rollback-last` is separate from `rollback-pending`. If a pending transaction exists, recover it first with `rollback-pending`.

Manual rollback applies only to the development contour.

## 10. DEV-FAST-001 controller-only activation

DEV-FAST-001 does not change keys, `authorized_keys`, sudoers, Compose, Dockerfile, entrypoint, secrets or the forced-command string. After the reviewed DEV-FAST-001 code is merged and its exact accepted `main` SHA is recorded, activate only the controller:

```bash
cd /srv/eod/repository

DEV_FAST_MAIN_SHA=<accepted DEV-FAST-001 main commit>
git fetch --prune origin main
git checkout main
git reset --hard "$DEV_FAST_MAIN_SHA"
test "$(git rev-parse HEAD)" = "$DEV_FAST_MAIN_SHA"
test "$(git rev-parse origin/main)" = "$DEV_FAST_MAIN_SHA"

sudo install \
  -o root \
  -g root \
  -m 0755 \
  deploy/automation/eod-development-controller \
  /usr/local/sbin/eod-development-controller

sudo test "$(sha256sum deploy/automation/eod-development-controller | awk '{print $1}')" = \
  "$(sha256sum /usr/local/sbin/eod-development-controller | awk '{print $1}')"
sudo /usr/local/sbin/eod-development-controller status
```

This is the single authorised root activation for DEV-FAST-001 V1. Do not rerun the full bootstrap unless the unchanged key/sudoers/Compose contract is separately found damaged.

## 11. Trusted hot-refresh request

For an open same-repository PR based on `main`, containing only added or modified presentation files, publish exactly:

```text
/eod-hot-refresh <exact-lowercase-40-hex-live-pr-head>
```

The workflow from `main` validates actor write/admin authority, live PR state, same-repository head, exact SHA and GitHub changed-file policy. It invokes only:

```text
hot-refresh <pr_number> <exact_sha> <github_run_id>
```

The VPS controller independently fetches `refs/pull/<number>/head`, rechecks the SHA and inspects the full PR diff against its merge base with current `main`.

## 12. Hot-refresh V1 policy and runtime

Allowed:

```text
A or M
100644 blob
src/templates/**
src/static/**
```

Forbidden:

- deletion, rename, copy or type change;
- executable `100755` blob;
- symlink `120000`;
- submodule or non-blob entry;
- path traversal, non-canonical path or destination symlink component;
- any non-presentation path.

Runtime sequence:

```text
exact PR ref fetch
-> V1 path/blob verification
-> current full image identification
-> idempotency marker check
-> app-only force-recreate from full image
-> copy exact Git blobs to writable app layer
-> restart only app
-> host entrypoint: Django check + collectstatic
-> local development health-check
-> repeat exact PR ref fetch
-> write container-local overlay marker
```

No database backup, migration, PostgreSQL suite, image build, presentation seed or preview operation occurs.

## 13. Hot-refresh failure and rollback

After runtime mutation starts, every error triggers:

```text
force-recreate only eod-development app from current full image
-> wait for local health
-> return ERROR
```

This removes the partial overlay. If the clean full-image app also fails health, the controller returns a hard rollback failure and prints app logs. Database and preview remain untouched.

The marker is `/app/.eod-hot-refresh.env` inside the app container. It records PR, overlay SHA, workflow run and UTC apply time. It never changes `/srv/eod/automation/state/current_sha`. Repeating the same command returns `ALREADY_APPLIED` after exact-ref and health checks.

Any ordinary full trusted deployment recreates the app container, automatically removing both overlay and marker without changing the release transaction implementation.

## 14. Canary acceptance after activation

Use one separate canary PR containing one harmless added or modified `src/static/**` file.

Evidence required:

1. `SUCCESS` for the exact head;
2. `ALREADY_APPLIED` for the repeated exact command;
3. controlled invalid-template or stale-ref failure followed by clean-image recovery;
4. development `/_health/` success on port `8766`;
5. database operations `NONE`;
6. preview `UNTOUCHED`;
7. automatic merge absent.
