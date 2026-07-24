# EOD private preview — VPS runbook

> This runbook is intentionally operational and uses the real project paths for the private preview.

## Infrastructure

- Repository: `genrudko/electronic-operational-docs`
- VPS: `5.181.177.72`
- SSH user: `eodadmin`
- VPS repository: `/srv/eod/repository`
- Preview environment: `/srv/eod/secrets/preview.env`
- Preview imports: `/srv/eod/imports`
- PostgreSQL backups: `/srv/eod/backups`
- Application endpoint on VPS: `127.0.0.1:8765`
- PostgreSQL host port: not published
- Windows repository: `G:\electronic-operational-docs`
- Windows snapshot root: `G:\EOD_BACKUPS`
- Windows SSH key: `C:\Users\Gennadiy\.ssh\eod_contabo_ed25519`

## Connect to the VPS

```powershell
ssh -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" eodadmin@5.181.177.72
```

Do not paste `exit` into an interactive SSH command block.

## Open preview through an SSH tunnel

Keep this PowerShell window open:

```powershell
ssh -N `
  -L 8765:127.0.0.1:8765 `
  -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
  eodadmin@5.181.177.72
```

Open:

```text
http://127.0.0.1:8765/
```

Demo accounts:

```text
operator.demo / EodDemo!2026
supervisor.demo / EodDemo!2026
```

## Inspect current VPS state

```bash
cd /srv/eod/repository

git status --short --branch
git rev-parse HEAD

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  ps

curl --fail --silent --show-error http://127.0.0.1:8765/_health/
```

## Update the preview checkout

Use the required branch explicitly during PR acceptance:

```bash
cd /srv/eod/repository

git fetch --prune origin
git switch infra/002-container-preview
git pull --ff-only

git status --short --branch
git rev-parse HEAD
```

After merge, switch to `main` only after explicit approval:

```bash
cd /srv/eod/repository

git fetch --prune origin
git switch main
git pull --ff-only
```

## Build and start preview

```bash
cd /srv/eod/repository

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  config --quiet

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  build app

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  up --detach
```

Check:

```bash
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  ps

curl --fail --silent --show-error http://127.0.0.1:8765/_health/
```

## View logs

Application:

```bash
cd /srv/eod/repository

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  logs --no-color --tail=250 app
```

Application and PostgreSQL:

```bash
cd /srv/eod/repository

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  logs --no-color --tail=250 app db
```

## Restart application

```bash
cd /srv/eod/repository

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  restart app
```

## Create a presentation snapshot on Windows

Close the local Django server before snapshot creation.

Update the local branch first:

```powershell
Set-Location "G:\electronic-operational-docs"

git fetch --prune origin
git switch infra/002-container-preview
git pull --ff-only

git status --short --branch
git rev-parse HEAD
```

Run the repository-owned exporter:

```powershell
powershell.exe `
  -NoProfile `
  -ExecutionPolicy Bypass `
  -File "G:\electronic-operational-docs\scripts\snapshot_presentation_database.ps1"
```

The exporter:

- reads `G:\electronic-operational-docs\data\presentation.sqlite3`;
- validates source SQLite integrity;
- creates a consistent backup with the SQLite Backup API;
- exports application data as UTF-8 Django fixture;
- excludes regenerated Django metadata, sessions and admin log;
- includes `media` when it exists and is non-empty;
- writes `manifest.json` with SHA-256 and record counts;
- produces a ZIP and a separate ZIP SHA-256 file;
- never modifies the source database.

Windows can transiently deny a directory rename because of antivirus, indexing or another short-lived file handle. The exporter retries the rename and then uses a verified file-by-file copy fallback. The copied tree is checked by size and SHA-256 before the temporary directory is removed.

Expected output directory:

```text
G:\EOD_BACKUPS\presentation_YYYYMMDD_HHMMSS
```

Expected archive:

```text
G:\EOD_BACKUPS\presentation_YYYYMMDD_HHMMSS.zip
```

## Upload a snapshot to the VPS

Create the import directory:

```powershell
ssh `
  -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
  eodadmin@5.181.177.72 `
  "sudo install -d -m 0750 -o eodadmin -g eodadmin /srv/eod/imports"
```

Upload the archive and hash file:

```powershell
$Archive = "G:\EOD_BACKUPS\presentation_YYYYMMDD_HHMMSS.zip"
$HashFile = "$Archive.sha256.txt"

scp `
  -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
  $Archive `
  $HashFile `
  eodadmin@5.181.177.72:/srv/eod/imports/
```

## Import presentation snapshot into PostgreSQL

The repository-owned importer must be run from the expected VPS layout:

```bash
sudo bash \
  /srv/eod/repository/scripts/import_presentation_snapshot.sh \
  /srv/eod/imports/presentation_YYYYMMDD_HHMMSS.zip
```

The importer performs the following sequence:

1. verifies Git worktree cleanliness;
2. validates ZIP paths, required files, SHA-256 values and manifest counts;
3. validates Compose configuration;
4. builds the current application image;
5. waits for PostgreSQL health;
6. creates a custom-format `pg_dump` in `/srv/eod/backups`;
7. stops the application;
8. flushes application data through a one-off administrative container;
9. loads the fixture into PostgreSQL;
10. compares all model counts against the manifest;
11. checks both demo logins;
12. recreates the current application container;
13. waits for health and checks `/` and `/_health/`.

Administrative one-off containers bypass the normal entrypoint and therefore do not repeat migrations or `collectstatic`.

If import fails after backup creation, the script attempts an automatic `pg_restore` and starts the application again. The backup path is always printed.

## Create a manual PostgreSQL backup

```bash
sudo install -d -m 0750 -o root -g root /srv/eod/backups

cd /srv/eod/repository
set -a
source /srv/eod/secrets/preview.env
set +a

DB_CONTAINER="$(sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  ps -q db)"

BACKUP="/srv/eod/backups/eod_preview_$(date +%Y%m%d_%H%M%S).dump"
BACKUP_IN_CONTAINER="/tmp/$(basename "$BACKUP")"

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  exec -T db \
  pg_dump \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --format custom \
  --file "$BACKUP_IN_CONTAINER"

sudo docker cp "$DB_CONTAINER:$BACKUP_IN_CONTAINER" "$BACKUP"
sudo chmod 0600 "$BACKUP"
ls -lh "$BACKUP"
```

## Restore a PostgreSQL backup manually

Stop the application first:

```bash
cd /srv/eod/repository
set -a
source /srv/eod/secrets/preview.env
set +a

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  stop app
```

Copy and restore the selected dump:

```bash
BACKUP="/srv/eod/backups/SELECTED_BACKUP.dump"
DB_CONTAINER="$(sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  ps -q db)"
BACKUP_IN_CONTAINER="/tmp/$(basename "$BACKUP")"

sudo docker cp "$BACKUP" "$DB_CONTAINER:$BACKUP_IN_CONTAINER"

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  exec -T db \
  pg_restore \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --clean \
  --if-exists \
  --no-owner \
  --exit-on-error \
  "$BACKUP_IN_CONTAINER"
```

Start and check the application:

```bash
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  up --detach --force-recreate app

curl --fail --silent --show-error http://127.0.0.1:8765/_health/
```

## Stop preview without deleting data

```bash
cd /srv/eod/repository

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  down
```

Do not add `--volumes` on the VPS unless the PostgreSQL data volume is intentionally being destroyed.

## Inspect disk and memory

```bash
df -h
free -h
sudo docker system df
```

## Important boundaries

- Preview is private and must remain bound to `127.0.0.1`.
- PostgreSQL must not publish a host port.
- `/srv/eod/secrets/preview.env` is not committed.
- The application container runs as the unprivileged `eod` user.
- One-off import containers may run as root only for the bind-mounted snapshot and terminate immediately.
- PR branches are never merged or switched to `main` on VPS without explicit approval.
- A successful CI run does not replace VPS and visual acceptance.
