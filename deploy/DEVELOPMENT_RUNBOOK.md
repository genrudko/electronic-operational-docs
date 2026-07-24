# EOD isolated VPS development — runbook

## Purpose

This contour moves Python, Django, PostgreSQL, patch execution, tests, and visual verification to the VPS while keeping the accepted preview untouched.

| Role | Checkout | Compose project | Branch | Host port | Database |
|---|---|---|---|---:|---|
| Accepted preview | `/srv/eod/repository` | `eod-preview` | `main` only | `127.0.0.1:8765` | `eod_preview` |
| Active development | `/srv/eod/development` | `eod-development` | never `main` | `127.0.0.1:8766` | `eod_development` |

Both PostgreSQL services have separate containers, networks, users, databases, and named volumes. Neither PostgreSQL port is published to the host.

The VPS keeps its read-only GitHub deploy key. Repository writes, pull requests, and merges remain outside the VPS.

## Safety invariants

- Never apply a patch in `/srv/eod/repository`.
- Never run the development stack from `main`.
- Never use `/srv/eod/secrets/preview.env` with `compose.development.yaml`.
- Never use `/srv/eod/secrets/development.env` with `compose.preview.yaml`.
- Preview remains available on port `8765` while development uses `8766`.
- Resetting development data must never write to the preview database.

The development entrypoint verifies the exact database name, user, host, port, deployment mode, profile, and SQLite override before Django starts.

## One-time VPS checkout

Run as `eodadmin`:

```bash
sudo install -d -m 0755 -o eodadmin -g eodadmin \
  /srv/eod/development \
  /srv/eod/patches

rmdir /srv/eod/development

git clone \
  github-eod:genrudko/electronic-operational-docs.git \
  /srv/eod/development

cd /srv/eod/development

git fetch --prune origin
git switch --track origin/infra/003-isolated-vps-development

git status --short --branch
git rev-parse HEAD
```

The preview checkout at `/srv/eod/repository` is not modified by these commands.

## One-time development secrets

Generate independent development secrets and write the root-owned environment file:

```bash
DJANGO_SECRET="$(openssl rand -hex 48)"
POSTGRES_SECRET="$(openssl rand -hex 32)"

sudo install -d -m 0750 -o root -g root /srv/eod/secrets

sudo tee /srv/eod/secrets/development.env >/dev/null <<EOF
DJANGO_SECRET_KEY=${DJANGO_SECRET}
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
POSTGRES_DB=eod_development
POSTGRES_USER=eod_development
POSTGRES_PASSWORD=${POSTGRES_SECRET}
EOD_DEVELOPMENT_PORT=8766
TIME_ZONE=Europe/Moscow
EOF

unset DJANGO_SECRET POSTGRES_SECRET
sudo chown root:root /srv/eod/secrets/development.env
sudo chmod 0600 /srv/eod/secrets/development.env
sudo test -s /srv/eod/secrets/development.env
```

Do not print or commit this file.

## First development startup

```bash
cd /srv/eod/development

sudo bash scripts/development_stack.sh bootstrap
```

Expected result:

```text
Branch: infra/003-isolated-vps-development
...
eod-development-app-1 ... healthy ... 127.0.0.1:8766->8766/tcp
eod-development-db-1  ... healthy ... 5432/tcp
{"status": "ok"}
Main page: HTTP 200
```

## Seed development from accepted preview

This operation:

1. verifies that preview is on `main` and development is not;
2. backs up the current development PostgreSQL database;
3. creates a fresh dump of the accepted preview database;
4. restores that dump only into `eod_development`;
5. applies migrations from the active development branch;
6. verifies the development database name and both demo accounts;
7. restarts only the development application.

Run:

```bash
cd /srv/eod/development

sudo bash scripts/reset_development_database.sh
```

Preview containers and preview data remain intact.

## Routine patch workflow from Termux

### Prepare Termux storage and SSH

```bash
pkg install openssh
termux-setup-storage
mkdir -p ~/.ssh
chmod 700 ~/.ssh
chmod 600 ~/.ssh/eod_contabo_ed25519
```

### Upload a downloaded patch from the phone

Assuming the patch is in the Android Downloads directory:

```bash
scp \
  -i ~/.ssh/eod_contabo_ed25519 \
  ~/storage/downloads/patch_*.py \
  eodadmin@5.181.177.72:/srv/eod/patches/
```

### Apply it to the development checkout

```bash
ssh \
  -i ~/.ssh/eod_contabo_ed25519 \
  eodadmin@5.181.177.72
```

Then on the VPS:

```bash
cd /srv/eod/development

git status --short --branch
python3 /srv/eod/patches/patch_NAME.py

git status --short --branch

sudo bash scripts/development_stack.sh refresh
```

`refresh` does not rebuild Python dependencies. Source changes are bind-mounted into the container, and the Django development server reloads them.

Use `rebuild` only when a patch changes dependency declarations, the Dockerfile, or container startup files:

```bash
sudo bash scripts/development_stack.sh rebuild
```

### Checks and tests

```bash
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
sudo bash scripts/development_stack.sh logs
```

Follow live logs until `Ctrl+C`:

```bash
sudo bash scripts/development_stack.sh follow
```

## Open development in the phone browser

Keep this Termux command running in a separate session:

```bash
ssh -N \
  -L 8766:127.0.0.1:8766 \
  -i ~/.ssh/eod_contabo_ed25519 \
  eodadmin@5.181.177.72
```

Open in the ordinary Android browser:

```text
http://127.0.0.1:8766
```

The accepted preview remains independently available through a separate tunnel on local port `8765`.

## Development stack commands

```bash
cd /srv/eod/development
sudo bash scripts/development_stack.sh help
```

Available operations:

- `bootstrap` — first build and startup;
- `refresh` — recreate the app using current source files;
- `rebuild` — rebuild dependencies/image and recreate the app;
- `check` — Django check plus migration-file verification;
- `test` — full Django test suite;
- `migrate` — apply development migrations;
- `status` — repository, container, and HTTP status;
- `logs` — recent logs;
- `follow` — live logs;
- `shell` — container shell;
- `django-shell` — Django shell;
- `stop` — stop development without deleting volumes.

## Update the development checkout from GitHub

Only do this with a clean worktree:

```bash
cd /srv/eod/development

git status --short --branch
git fetch --prune origin
git pull --ff-only

sudo bash scripts/development_stack.sh refresh
```

A dirty worktree means a local test patch has not yet been reconciled with the GitHub branch. Do not reset or discard it without an explicit integration decision.

## Stop development without affecting preview

```bash
cd /srv/eod/development
sudo bash scripts/development_stack.sh stop
```

This preserves the development PostgreSQL volume.

## Destructive cleanup

Do not run `docker compose down --volumes` manually. Deleting the development volume is allowed only as an explicit reset operation after a verified backup. Preview volumes must never be referenced by development cleanup commands.
