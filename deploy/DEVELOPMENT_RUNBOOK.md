# EOD isolated VPS development — runbook

## Purpose

This contour moves Python, Django, PostgreSQL, tests, and visual verification to the VPS while keeping the accepted preview untouched.

The primary development workflow is GitHub-first:

1. changes are committed to the active working branch in GitHub;
2. the VPS development checkout receives them with `git pull --ff-only`;
3. the isolated development stack is refreshed, checked, and tested;
4. the user verifies the result through an SSH tunnel in any browser.

Downloading, uploading, and executing patch files is not part of the normal workflow. It remains only an emergency fallback for changes that cannot be committed directly to GitHub.

| Role | Checkout | Compose project | Branch | Host port | Database |
|---|---|---|---|---:|---|
| Accepted preview | `/srv/eod/repository` | `eod-preview` | `main` only | `127.0.0.1:8765` | `eod_preview` |
| Active development | `/srv/eod/development` | `eod-development` | never `main` | `127.0.0.1:8766` | `eod_development` |

Both PostgreSQL services have separate containers, networks, users, databases, and named volumes. Neither PostgreSQL port is published to the host.

The VPS keeps its read-only GitHub deploy key. Repository writes, commits, pull requests, and merges are performed through GitHub, not from the VPS.

## Safety invariants

- Never edit or test code in `/srv/eod/repository`.
- Never run the development stack from `main`.
- Never use `/srv/eod/secrets/preview.env` with `compose.development.yaml`.
- Never use `/srv/eod/secrets/development.env` with `compose.preview.yaml`.
- Preview remains available on port `8765` while development uses `8766`.
- Resetting development data must never write to the preview database.
- The VPS deploy key remains read-only.

The development entrypoint verifies the exact database name, user, host, port, deployment mode, profile, and SQLite override before Django starts.

## One-time VPS checkout

Run as `eodadmin`:

```bash
sudo install -d -m 0755 -o eodadmin -g eodadmin /srv/eod/development
rmdir /srv/eod/development

git clone \
  --branch infra/003-isolated-vps-development \
  --single-branch \
  github-eod:genrudko/electronic-operational-docs.git \
  /srv/eod/development

cd /srv/eod/development

git status --short --branch
git rev-parse HEAD
```

The preview checkout at `/srv/eod/repository` is not modified by these commands.

## One-time development secrets

Generate independent development secrets and write a root-owned environment file without printing the secret values:

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

Expected ownership and mode:

```text
root:root 600 /srv/eod/secrets/development.env
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
{"status":"ok"}
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

## Primary GitHub-first development cycle

### 1. Changes are committed to GitHub

The assistant prepares complete changes directly in the active GitHub branch. The VPS does not create commits and does not need a writable GitHub key.

### 2. Pull the branch on the VPS

From Termux or any SSH client:

```bash
ssh -i ~/.ssh/eod_contabo_ed25519 eodadmin@5.181.177.72
```

Then on the VPS:

```bash
cd /srv/eod/development

git status --short --branch
git fetch --prune origin
git pull --ff-only
```

The working tree must be clean before `git pull --ff-only`.

### 3. Refresh the development application

For normal Python, template, CSS, and JavaScript changes:

```bash
sudo bash scripts/development_stack.sh refresh
```

The application source is bind-mounted into the container, so a dependency image rebuild is not required.

Use `rebuild` only when the commit changes dependency declarations, the Dockerfile, or container startup files:

```bash
sudo bash scripts/development_stack.sh rebuild
```

### 4. Run checks and tests

```bash
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

Recent logs:

```bash
sudo bash scripts/development_stack.sh logs
```

Live logs until `Ctrl+C`:

```bash
sudo bash scripts/development_stack.sh follow
```

### 5. Verify in a browser

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

## Emergency local patch fallback

This path is not used for normal work. Use it only when a complete change cannot be committed through GitHub first.

A fallback patch must be applied only in `/srv/eod/development`, never in `/srv/eod/repository`. A dirty development worktree must be reviewed and reconciled before any later `git pull`; do not discard it automatically.

## Stop development without affecting preview

```bash
cd /srv/eod/development
sudo bash scripts/development_stack.sh stop
```

This preserves the development PostgreSQL volume.

## Destructive cleanup

Do not run `docker compose down --volumes` manually. Deleting the development volume is allowed only as an explicit reset operation after a verified backup. Preview volumes must never be referenced by development cleanup commands.
