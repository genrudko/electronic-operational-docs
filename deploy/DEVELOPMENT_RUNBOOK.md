# EOD isolated VPS development — technical runbook

This file documents the infrastructure created by INFRA-003. The canonical operator-facing workflow is maintained in:

- `docs/runbooks/DEVELOPMENT_RUNBOOK.md`;
- `docs/runbooks/BRANCH_SWITCHING.md`;
- `docs/runbooks/PRESENTATION_DATA_RESET.md`;
- `docs/runbooks/SSH_TUNNEL_ACCESS.md`.

## Contour contract

| Role | Checkout | Compose project | Branch | Host port | Database |
|---|---|---|---|---:|---|
| Accepted preview | `/srv/eod/repository` | `eod-preview` | `main` only | `127.0.0.1:8765` | `eod_preview` |
| Active development | `/srv/eod/development` | `eod-development` | never `main` | `127.0.0.1:8766` | `eod_development` |

Both PostgreSQL services use separate containers, networks, users, databases and named volumes. Neither PostgreSQL port is published to the host.

The VPS deploy key is read-only. Commits, pull requests and merges are performed through GitHub, not from the VPS.

## Safety invariants

- never edit or test code in `/srv/eod/repository`;
- never run development from `main`;
- never mix preview and development env files;
- keep preview on `8765` and development on `8766`;
- resetting development data must not write to preview;
- do not publish PostgreSQL;
- do not create commits on the VPS.

The development entrypoint verifies exact deployment mode, database name/user/host/port, profile and SQLite override before Django starts.

## One-time checkout

Use the current active non-main branch supplied by the integration workflow:

```bash
ACTIVE_BRANCH='<active-non-main-branch>'

sudo install -d -m 0755 -o eodadmin -g eodadmin /srv/eod/development
rmdir /srv/eod/development

git clone \
  --branch "$ACTIVE_BRANCH" \
  github-eod:genrudko/electronic-operational-docs.git \
  /srv/eod/development

cd /srv/eod/development

git config remote.origin.fetch \
  '+refs/heads/*:refs/remotes/origin/*'

git fetch --prune origin
git status --short --branch
git rev-parse HEAD
```

Do not use `--single-branch`; the development checkout must be able to switch between future work-item branches.

## One-time development secrets

```bash
umask 077
DEV_ENV_TMP="$(mktemp)"
DJANGO_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(64))')"
POSTGRES_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

cat > "$DEV_ENV_TMP" <<EOF
DJANGO_SECRET_KEY=${DJANGO_SECRET}
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
POSTGRES_DB=eod_development
POSTGRES_USER=eod_development
POSTGRES_PASSWORD=${POSTGRES_SECRET}
EOD_DEVELOPMENT_PORT=8766
TIME_ZONE=Europe/Moscow
EOF

sudo install -d -m 0750 -o root -g root /srv/eod/secrets
sudo install -m 0600 -o root -g root \
  "$DEV_ENV_TMP" \
  /srv/eod/secrets/development.env

rm -f "$DEV_ENV_TMP"
unset DEV_ENV_TMP DJANGO_SECRET POSTGRES_SECRET

sudo test -s /srv/eod/secrets/development.env
sudo stat -c '%U:%G %a %n' /srv/eod/secrets/development.env
```

Expected:

```text
root:root 600 /srv/eod/secrets/development.env
```

Never print or commit the secret values.

## First startup

```bash
cd /srv/eod/development
sudo bash scripts/development_stack.sh bootstrap
```

Expected characteristics:

```text
active branch: non-main
eod-development-app-1 ... healthy ... 127.0.0.1:8766->8766/tcp
eod-development-db-1  ... healthy ... 5432/tcp
{"status": "ok"}
Main page: HTTP 200
```

## Seed from accepted preview

```bash
cd /srv/eod/development
sudo bash scripts/reset_development_database.sh
```

The script:

1. verifies preview `main` and development non-main roles;
2. backs up current development PostgreSQL;
3. creates a fresh accepted preview dump;
4. restores only into `eod_development`;
5. applies active branch migrations;
6. verifies database identity and demo accounts;
7. restarts only the development application.

## Primary GitHub-first cycle

Changes are committed to the active GitHub branch by the AI developer.

On the VPS:

```bash
cd /srv/eod/development

git status --short --branch
git fetch --prune origin
git pull --ff-only

sudo bash scripts/development_stack.sh refresh
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

Use `rebuild` instead of `refresh` for dependencies, Dockerfile, Compose or startup changes.

## Branch switching

```bash
cd /srv/eod/development

git status --short --branch
git fetch --prune origin

git switch <branch> 2>/dev/null || \
git switch --track origin/<branch>

git pull --ff-only
```

Do not merge, rebase or force-reset branch history on the VPS.

## Browser access

```bash
ssh -N -T \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -L 8766:127.0.0.1:8766 \
  -i ~/.ssh/eod_contabo_ed25519 \
  eodadmin@5.181.177.72
```

Open `http://127.0.0.1:8766`.

## Stack commands

```text
bootstrap  first build/start
refresh    recreate app using current source
rebuild    rebuild image and recreate app
check      Django check and migration-file verification
test       full Django test suite
migrate    apply development migrations
status     repository/container/HTTP status
logs       recent logs
follow     live logs
shell      container shell
django-shell Django shell
stop       stop development without deleting volumes
```

## Emergency fallback

Manual patching is not part of normal work. A fallback may be applied only in `/srv/eod/development` when GitHub writes are unavailable. The exact result must then be reproduced as a normal GitHub commit before CI, acceptance or merge.

## Destructive cleanup

Do not run `docker compose down --volumes` manually. Volume deletion requires an explicit reset plan and verified backup. Preview volumes must never be referenced by development cleanup commands.