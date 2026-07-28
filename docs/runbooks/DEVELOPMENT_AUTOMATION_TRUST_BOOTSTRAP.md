# Runbook — trusted development automation

## 1. Accepted boundary

The restricted account is `eod-automation`. It is not a member of the Docker group. Its SSH key is forced to run only:

```text
sudo -n /usr/local/sbin/eod-development-controller ssh-gateway
```

Host-owned files remain:

```text
/usr/local/sbin/eod-development-controller
/etc/eod-automation/controller.env
/etc/eod-automation/compose.development.yaml
/etc/eod-automation/Dockerfile.development
/etc/eod-automation/app-entrypoint.sh
```

Runtime data remains under `/srv/eod/automation/`. Preview is never a controller target.

## 2. Full AUTO-001B bootstrap from accepted main

This is the established full bootstrap and remains available only when the complete trusted boundary must be installed or repaired.

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

It installs the fixed controller, Compose, Dockerfile and entrypoint and manages the restricted keys/sudoers contract. Do not run it from a PR branch or an unverified checkout.

## 3. DEV-FAST-001 controller-only activation

DEV-FAST-001 does not change keys, authorized_keys, sudoers, Compose, Dockerfile, entrypoint, secrets or the forced-command string. After the reviewed DEV-FAST-001 code is merged and its exact accepted `main` SHA is recorded, activate only the controller:

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

## 4. Trusted hot-refresh request

For an open same-repository PR based on `main`, containing only added or modified presentation files, publish exactly:

```text
/eod-hot-refresh <exact-lowercase-40-hex-live-pr-head>
```

The workflow from `main` validates actor write/admin authority, live PR state, same-repository head, exact SHA and GitHub changed-file policy. It invokes only:

```text
hot-refresh <pr_number> <exact_sha> <github_run_id>
```

The VPS controller independently fetches `refs/pull/<number>/head`, rechecks the SHA and inspects the full PR diff against its merge base with current `main`.

## 5. V1 file policy

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

## 6. Runtime sequence

```text
exact PR ref fetch
→ V1 path/blob verification
→ current full image identification
→ idempotency marker check
→ app-only force-recreate from full image
→ copy exact Git blobs to writable app layer
→ restart only app
→ host entrypoint: Django check + collectstatic
→ local development health-check
→ repeat exact PR ref fetch
→ write container-local overlay marker
```

No database backup, migration, PostgreSQL suite, image build, presentation seed or preview operation occurs.

## 7. Failure and rollback

After the runtime mutation starts, every error triggers:

```text
force-recreate only eod-development app from current full image
→ wait for local health
→ return ERROR
```

This removes the partial overlay. If the clean full-image app also fails health, the controller returns a hard rollback failure and prints app logs. Database and preview remain untouched.

The marker is `/app/.eod-hot-refresh.env` inside the app container. It records PR, overlay SHA, workflow run and UTC apply time. It never changes `/srv/eod/automation/state/current_sha`. Repeating the same command returns `ALREADY_APPLIED` after exact-ref and health checks.

Any ordinary full trusted deployment recreates the app container, automatically removing both overlay and marker without changing the release transaction implementation.

## 8. Canary acceptance after activation

Use one separate canary PR containing one harmless added or modified `src/static/**` file.

Evidence required:

1. `SUCCESS` for the exact head;
2. `ALREADY_APPLIED` for the repeated exact command;
3. controlled invalid-template or stale-ref failure followed by clean-image recovery;
4. development `/_health/` success on port `8766`;
5. database operations `NONE`;
6. preview `UNTOUCHED`;
7. automatic merge absent.
