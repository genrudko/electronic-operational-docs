#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="/srv/eod/repository"
ENV_FILE="/srv/eod/secrets/preview.env"
IMPORT_ROOT="/srv/eod/imports"
BACKUP_ROOT="/srv/eod/backups"

if [[ "${EUID}" -ne 0 ]]; then
    echo "ОШИБКА: запустите скрипт через sudo." >&2
    exit 1
fi

if [[ "$#" -ne 1 ]]; then
    echo "Использование: sudo bash scripts/import_presentation_snapshot.sh /путь/к/snapshot.zip" >&2
    exit 1
fi

ARCHIVE_PATH="$(readlink -f "$1")"
[[ -f "$ARCHIVE_PATH" ]] || { echo "ОШИБКА: архив не найден: $ARCHIVE_PATH" >&2; exit 1; }
[[ -d "$REPO_DIR/.git" ]] || { echo "ОШИБКА: репозиторий не найден: $REPO_DIR" >&2; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "ОШИБКА: secret-файл не найден: $ENV_FILE" >&2; exit 1; }

install -d -m 0750 -o root -g root "$IMPORT_ROOT" "$BACKUP_ROOT"

STAMP="$(date +%Y%m%d_%H%M%S)"
SNAPSHOT_DIR="$IMPORT_ROOT/presentation_$STAMP"
POSTGRES_BACKUP="$BACKUP_ROOT/postgres_before_presentation_$STAMP.dump"
BACKUP_READY=0
COMPOSE_READY=0
DB_CONTAINER=""

cleanup_on_failure() {
    local exit_code=$?
    trap - EXIT

    if [[ "$exit_code" -eq 0 ]]; then
        exit 0
    fi

    echo
    echo "===== IMPORT FAILED =====" >&2
    cd "$REPO_DIR" || true

    if [[ "$COMPOSE_READY" -ne 1 ]]; then
        echo "Import failed before Docker Compose initialization." >&2
        exit "$exit_code"
    fi

    if [[ "$BACKUP_READY" -eq 1 && -s "$POSTGRES_BACKUP" && -n "$DB_CONTAINER" ]]; then
        echo "Attempting automatic PostgreSQL rollback..." >&2
        local restore_name="/tmp/$(basename "$POSTGRES_BACKUP")"
        if docker cp "$POSTGRES_BACKUP" "$DB_CONTAINER:$restore_name" \
            && "${COMPOSE[@]}" exec -T db \
                pg_restore \
                --username "$POSTGRES_USER" \
                --dbname "$POSTGRES_DB" \
                --clean \
                --if-exists \
                --no-owner \
                --exit-on-error \
                "$restore_name"
        then
            echo "Automatic PostgreSQL rollback completed." >&2
        else
            echo "Automatic PostgreSQL rollback FAILED." >&2
            echo "Manual backup: $POSTGRES_BACKUP" >&2
        fi
    fi

    "${COMPOSE[@]}" up --detach --force-recreate app >/dev/null 2>&1 || true
    "${COMPOSE[@]}" ps || true
    exit "$exit_code"
}

trap cleanup_on_failure EXIT

cd "$REPO_DIR"

echo "===== REPOSITORY STATE ====="
printf 'Branch: %s\n' "$(git branch --show-current)"
printf 'HEAD:   %s\n' "$(git rev-parse HEAD)"

WORKTREE_STATUS="$(git status --porcelain=v1 --untracked-files=all)"
if [[ -n "$WORKTREE_STATUS" ]]; then
    echo "ОШИБКА: рабочее дерево репозитория не чистое." >&2
    printf '%s\n' "$WORKTREE_STATUS" >&2
    exit 1
fi

echo
echo "===== VALIDATE AND EXTRACT SNAPSHOT ====="
python3 - "$ARCHIVE_PATH" "$SNAPSHOT_DIR" <<'PY'
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

archive_path = Path(sys.argv[1])
snapshot_dir = Path(sys.argv[2])


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


with zipfile.ZipFile(archive_path, "r") as archive:
    names = archive.namelist()
    required = {"manifest.json", "presentation.sqlite3", "presentation_fixture.json"}
    missing = sorted(required.difference(names))
    if missing:
        raise SystemExit("Snapshot archive is incomplete: " + ", ".join(missing))

    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"Unsafe archive path: {name}")

    manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    if manifest.get("snapshot_format") != "eod.presentation.snapshot.v1":
        raise SystemExit("Unsupported snapshot format.")

    database_data = archive.read("presentation.sqlite3")
    fixture_data = archive.read("presentation_fixture.json")

    if len(database_data) != manifest["database"]["size_bytes"]:
        raise SystemExit("Database size does not match manifest.")
    if len(fixture_data) != manifest["fixture"]["size_bytes"]:
        raise SystemExit("Fixture size does not match manifest.")
    if digest(database_data) != manifest["database"]["sha256"]:
        raise SystemExit("Database SHA-256 does not match manifest.")
    if digest(fixture_data) != manifest["fixture"]["sha256"]:
        raise SystemExit("Fixture SHA-256 does not match manifest.")

    objects = json.loads(fixture_data.decode("utf-8"))
    counts = Counter(item["model"] for item in objects)
    if len(objects) != manifest["fixture"]["object_count"]:
        raise SystemExit("Fixture object count does not match manifest.")
    if dict(sorted(counts.items())) != manifest["model_counts"]:
        raise SystemExit("Fixture model counts do not match manifest.")

    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    snapshot_dir.mkdir(parents=True, mode=0o750)
    archive.extractall(snapshot_dir)

print(f"Snapshot objects: {len(objects)}")
print(f"Snapshot models:  {len(counts)}")
print(f"Database SHA-256: {manifest['database']['sha256']}")
print(f"Fixture SHA-256:  {manifest['fixture']['sha256']}")
PY

cat > "$SNAPSHOT_DIR/verify_import.py" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import django
from django.apps import apps
from django.contrib.auth import authenticate
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
django.setup()

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
errors: list[str] = []
actual_counts: dict[str, int] = {}

for model_label, expected_count in manifest["model_counts"].items():
    model = apps.get_model(model_label)
    if model is None:
        errors.append(f"{model_label}: model not found")
        continue
    actual = model._default_manager.count()
    actual_counts[model_label] = actual
    if actual != expected_count:
        errors.append(f"{model_label}: expected {expected_count}, got {actual}")

for username in ("operator.demo", "supervisor.demo"):
    if authenticate(username=username, password="EodDemo!2026") is None:
        errors.append(f"{username}: authentication failed")

with connection.cursor() as cursor:
    cursor.execute("SELECT current_database(), version()")
    database_name, database_version = cursor.fetchone()

print(f"Database: {database_name}")
print(f"Backend:  {database_version}")
print(f"Models checked: {len(actual_counts)}")
print(f"Objects checked: {sum(actual_counts.values())}")

for label in (
    "auth.user",
    "organizations.employee",
    "equipment.equipmentasset",
    "imports.powersystemassetoccurrence",
    "imports.powersystemauthorityoccurrence",
    "operational_log.operationaldraftentry",
    "operational_log.operationaldraftrevision",
    "operational_documents.operationaldocumentrecord",
    "workplace_docs.workplacedocumententry",
):
    if label in actual_counts:
        print(f"{label}: {actual_counts[label]}")

if errors:
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print("All model counts match the snapshot manifest.")
print("Demo authentication: ok")
PY

chmod 0750 "$SNAPSHOT_DIR"
chmod 0640 "$SNAPSHOT_DIR"/*

echo
echo "===== LOAD PREVIEW ENVIRONMENT ====="
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${POSTGRES_DB:?POSTGRES_DB is missing in preview.env}"
: "${POSTGRES_USER:?POSTGRES_USER is missing in preview.env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is missing in preview.env}"

PREVIEW_PORT="${EOD_PREVIEW_PORT:-8765}"
COMPOSE=(
    docker compose
    --env-file "$ENV_FILE"
    -f compose.preview.yaml
)
COMPOSE_READY=1

echo
echo "===== VALIDATE COMPOSE CONFIGURATION ====="
"${COMPOSE[@]}" config --quiet

echo
echo "===== BUILD CURRENT APPLICATION IMAGE ====="
"${COMPOSE[@]}" build app

echo
echo "===== VERIFY RUNNING DATABASE ====="
"${COMPOSE[@]}" up --detach db
DB_CONTAINER="$("${COMPOSE[@]}" ps -q db)"

for attempt in $(seq 1 30); do
    DB_HEALTH="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$DB_CONTAINER")"
    printf 'Database attempt %02d/30: %s\n' "$attempt" "$DB_HEALTH"
    [[ "$DB_HEALTH" == "healthy" ]] && break
    [[ "$attempt" -eq 30 ]] && { echo "ОШИБКА: PostgreSQL не стал healthy." >&2; exit 1; }
    sleep 2
done

echo
echo "===== BACK UP CURRENT POSTGRESQL ====="
BACKUP_IN_CONTAINER="/tmp/$(basename "$POSTGRES_BACKUP")"
"${COMPOSE[@]}" exec -T db pg_dump \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --format custom \
    --file "$BACKUP_IN_CONTAINER"
docker cp "$DB_CONTAINER:$BACKUP_IN_CONTAINER" "$POSTGRES_BACKUP"
chmod 0600 "$POSTGRES_BACKUP"
[[ -s "$POSTGRES_BACKUP" ]] || { echo "ОШИБКА: PostgreSQL backup пуст." >&2; exit 1; }
BACKUP_READY=1
printf 'PostgreSQL backup: %s bytes\n' "$(stat -c '%s' "$POSTGRES_BACKUP")"

echo
echo "===== STOP APPLICATION ====="
"${COMPOSE[@]}" stop app

echo
echo "===== FLUSH PREVIEW APPLICATION DATA ====="
"${COMPOSE[@]}" run --rm --no-deps \
    --user 0:0 \
    --entrypoint python \
    app manage.py flush --noinput

echo
echo "===== LOAD PRESENTATION FIXTURE ====="
"${COMPOSE[@]}" run --rm --no-deps \
    --user 0:0 \
    --entrypoint python \
    --volume "$SNAPSHOT_DIR:/snapshot:ro" \
    app manage.py loaddata /snapshot/presentation_fixture.json

echo
echo "===== VERIFY IMPORT AGAINST MANIFEST ====="
"${COMPOSE[@]}" run --rm --no-deps \
    --user 0:0 \
    --entrypoint python \
    --volume "$SNAPSHOT_DIR:/snapshot:ro" \
    app /snapshot/verify_import.py /snapshot/manifest.json

echo
echo "===== START CURRENT APPLICATION IMAGE ====="
"${COMPOSE[@]}" up --detach --force-recreate app
APP_CONTAINER="$("${COMPOSE[@]}" ps -q app)"

for attempt in $(seq 1 36); do
    APP_HEALTH="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$APP_CONTAINER")"
    printf 'Application attempt %02d/36: %s\n' "$attempt" "$APP_HEALTH"
    if curl --fail --silent --show-error --max-time 5 "http://127.0.0.1:${PREVIEW_PORT}/_health/" >/dev/null; then
        break
    fi
    if [[ "$attempt" -eq 36 ]]; then
        "${COMPOSE[@]}" logs --no-color --tail=250 app db
        exit 1
    fi
    sleep 5
done

echo
echo "===== FINAL STATUS ====="
"${COMPOSE[@]}" ps

echo
echo "===== FINAL HTTP CHECK ====="
curl --fail --silent --show-error "http://127.0.0.1:${PREVIEW_PORT}/_health/"
echo
curl --fail --silent --show-error --output /dev/null \
    --write-out 'Main page: HTTP %{http_code}; content-type=%{content_type}; bytes=%{size_download}\n' \
    "http://127.0.0.1:${PREVIEW_PORT}/"

echo
echo "===== PRESENTATION SNAPSHOT IMPORTED ====="
echo "Snapshot directory: $SNAPSHOT_DIR"
echo "PostgreSQL backup:  $POSTGRES_BACKUP"
echo "Imported archive:   $ARCHIVE_PATH"

trap - EXIT
