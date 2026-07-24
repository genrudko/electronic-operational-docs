#!/usr/bin/env bash
set -Eeuo pipefail

PREVIEW_REPO="${EOD_PREVIEW_REPO:-/srv/eod/repository}"
DEVELOPMENT_REPO="${EOD_DEVELOPMENT_REPO:-/srv/eod/development}"
PREVIEW_ENV="${EOD_PREVIEW_ENV:-/srv/eod/secrets/preview.env}"
DEVELOPMENT_ENV="${EOD_DEVELOPMENT_ENV:-/srv/eod/secrets/development.env}"
BACKUP_ROOT="${EOD_BACKUP_ROOT:-/srv/eod/backups}"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

read_env_value() {
    local file="$1"
    local name="$2"
    (
        set -a
        # shellcheck disable=SC1090
        source "$file"
        set +a
        printf '%s' "${!name:-}"
    )
}

if [[ "${EUID}" -ne 0 ]]; then
    fail "run this script through sudo."
fi

[[ -d "$PREVIEW_REPO/.git" ]] || fail "preview repository not found: $PREVIEW_REPO"
[[ -d "$DEVELOPMENT_REPO/.git" ]] || fail "development repository not found: $DEVELOPMENT_REPO"
[[ -f "$PREVIEW_ENV" ]] || fail "preview environment file not found: $PREVIEW_ENV"
[[ -f "$DEVELOPMENT_ENV" ]] || fail "development environment file not found: $DEVELOPMENT_ENV"
[[ -f "$PREVIEW_REPO/compose.preview.yaml" ]] || fail "preview Compose file is missing."
[[ -f "$DEVELOPMENT_REPO/compose.development.yaml" ]] || fail "development Compose file is missing."

PREVIEW_DB="$(read_env_value "$PREVIEW_ENV" POSTGRES_DB)"
PREVIEW_USER="$(read_env_value "$PREVIEW_ENV" POSTGRES_USER)"
DEVELOPMENT_DB="$(read_env_value "$DEVELOPMENT_ENV" POSTGRES_DB)"
DEVELOPMENT_USER="$(read_env_value "$DEVELOPMENT_ENV" POSTGRES_USER)"
DEVELOPMENT_PORT="$(read_env_value "$DEVELOPMENT_ENV" EOD_DEVELOPMENT_PORT)"

[[ "$PREVIEW_DB" == "eod_preview" ]] || fail "preview database must be eod_preview, got '$PREVIEW_DB'."
[[ "$DEVELOPMENT_DB" == "eod_development" ]] || fail "development database must be eod_development, got '$DEVELOPMENT_DB'."
[[ "$DEVELOPMENT_USER" == "eod_development" ]] || fail "development user must be eod_development."
[[ "$DEVELOPMENT_PORT" == "8766" ]] || fail "development port must be 8766."
[[ "$PREVIEW_DB" != "$DEVELOPMENT_DB" ]] || fail "preview and development database names must differ."

PREVIEW_COMPOSE=(
    docker compose
    --env-file "$PREVIEW_ENV"
    -f "$PREVIEW_REPO/compose.preview.yaml"
)
DEVELOPMENT_COMPOSE=(
    docker compose
    --env-file "$DEVELOPMENT_ENV"
    -f "$DEVELOPMENT_REPO/compose.development.yaml"
)

"${PREVIEW_COMPOSE[@]}" config --quiet
"${DEVELOPMENT_COMPOSE[@]}" config --quiet

install -d -m 0750 -o root -g root "$BACKUP_ROOT"
STAMP="$(date +%Y%m%d_%H%M%S)"
PREVIEW_SEED="$BACKUP_ROOT/preview_seed_for_development_$STAMP.dump"
DEVELOPMENT_BACKUP="$BACKUP_ROOT/development_before_reset_$STAMP.dump"

wait_for_database() {
    local compose_name="$1"
    local container="$2"

    for attempt in $(seq 1 30); do
        local state
        state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container")"
        printf '%s database attempt %02d/30: %s\n' "$compose_name" "$attempt" "$state"
        [[ "$state" == "healthy" ]] && return 0
        [[ "$attempt" -eq 30 ]] && fail "$compose_name PostgreSQL did not become healthy."
        sleep 2
    done
}

echo "===== VERIFY REPOSITORY ROLES ====="
printf 'Preview:     %s / %s / %s\n' "$PREVIEW_REPO" "$(git -C "$PREVIEW_REPO" branch --show-current)" "$(git -C "$PREVIEW_REPO" rev-parse HEAD)"
printf 'Development: %s / %s / %s\n' "$DEVELOPMENT_REPO" "$(git -C "$DEVELOPMENT_REPO" branch --show-current)" "$(git -C "$DEVELOPMENT_REPO" rev-parse HEAD)"
[[ "$(git -C "$PREVIEW_REPO" branch --show-current)" == "main" ]] || fail "preview checkout must remain on main."
[[ "$(git -C "$DEVELOPMENT_REPO" branch --show-current)" != "main" ]] || fail "development checkout must not use main."

echo
echo "===== START DATABASE CONTAINERS ====="
cd "$PREVIEW_REPO"
"${PREVIEW_COMPOSE[@]}" up --detach db
PREVIEW_CONTAINER="$("${PREVIEW_COMPOSE[@]}" ps -q db)"
[[ -n "$PREVIEW_CONTAINER" ]] || fail "preview database container was not created."
wait_for_database Preview "$PREVIEW_CONTAINER"

cd "$DEVELOPMENT_REPO"
"${DEVELOPMENT_COMPOSE[@]}" up --detach db
DEVELOPMENT_CONTAINER="$("${DEVELOPMENT_COMPOSE[@]}" ps -q db)"
[[ -n "$DEVELOPMENT_CONTAINER" ]] || fail "development database container was not created."
wait_for_database Development "$DEVELOPMENT_CONTAINER"

echo
echo "===== BACK UP CURRENT DEVELOPMENT DATABASE ====="
DEVELOPMENT_BACKUP_IN_CONTAINER="/tmp/$(basename "$DEVELOPMENT_BACKUP")"
"${DEVELOPMENT_COMPOSE[@]}" exec -T db pg_dump \
    --username "$DEVELOPMENT_USER" \
    --dbname "$DEVELOPMENT_DB" \
    --format custom \
    --file "$DEVELOPMENT_BACKUP_IN_CONTAINER"
docker cp "$DEVELOPMENT_CONTAINER:$DEVELOPMENT_BACKUP_IN_CONTAINER" "$DEVELOPMENT_BACKUP"
chmod 0600 "$DEVELOPMENT_BACKUP"
[[ -s "$DEVELOPMENT_BACKUP" ]] || fail "development backup is empty."
printf 'Development backup: %s bytes\n' "$(stat -c '%s' "$DEVELOPMENT_BACKUP")"

echo
echo "===== CREATE PREVIEW SEED DUMP ====="
PREVIEW_SEED_IN_CONTAINER="/tmp/$(basename "$PREVIEW_SEED")"
"${PREVIEW_COMPOSE[@]}" exec -T db pg_dump \
    --username "$PREVIEW_USER" \
    --dbname "$PREVIEW_DB" \
    --format custom \
    --file "$PREVIEW_SEED_IN_CONTAINER"
docker cp "$PREVIEW_CONTAINER:$PREVIEW_SEED_IN_CONTAINER" "$PREVIEW_SEED"
chmod 0600 "$PREVIEW_SEED"
[[ -s "$PREVIEW_SEED" ]] || fail "preview seed dump is empty."
printf 'Preview seed: %s bytes\n' "$(stat -c '%s' "$PREVIEW_SEED")"

echo
echo "===== STOP DEVELOPMENT APPLICATION ====="
"${DEVELOPMENT_COMPOSE[@]}" stop app || true

echo
echo "===== RESTORE PREVIEW DATA INTO DEVELOPMENT ====="
DEVELOPMENT_SEED_IN_CONTAINER="/tmp/$(basename "$PREVIEW_SEED")"
docker cp "$PREVIEW_SEED" "$DEVELOPMENT_CONTAINER:$DEVELOPMENT_SEED_IN_CONTAINER"
"${DEVELOPMENT_COMPOSE[@]}" exec -T db pg_restore \
    --username "$DEVELOPMENT_USER" \
    --dbname "$DEVELOPMENT_DB" \
    --clean \
    --if-exists \
    --no-owner \
    --exit-on-error \
    "$DEVELOPMENT_SEED_IN_CONTAINER"

echo
echo "===== APPLY CURRENT DEVELOPMENT MIGRATIONS ====="
"${DEVELOPMENT_COMPOSE[@]}" run --rm --no-deps \
    --entrypoint python \
    app manage.py migrate --noinput

echo
echo "===== VERIFY DEVELOPMENT DATABASE ====="
"${DEVELOPMENT_COMPOSE[@]}" run --rm --no-deps \
    --entrypoint python \
    app manage.py shell -c \
    'from django.contrib.auth import authenticate; from django.db import connection; assert connection.settings_dict["NAME"] == "eod_development"; assert authenticate(username="operator.demo", password="EodDemo!2026") is not None; assert authenticate(username="supervisor.demo", password="EodDemo!2026") is not None; print("Development database and demo authentication: ok")'

echo
echo "===== START DEVELOPMENT APPLICATION ====="
"${DEVELOPMENT_COMPOSE[@]}" up --detach --force-recreate app

for attempt in $(seq 1 36); do
    APP_CONTAINER="$("${DEVELOPMENT_COMPOSE[@]}" ps -q app)"
    [[ -n "$APP_CONTAINER" ]] || fail "development app container was not created."
    APP_STATE="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$APP_CONTAINER")"
    printf 'Application attempt %02d/36: %s\n' "$attempt" "$APP_STATE"
    if curl --fail --silent --show-error --max-time 5 \
        "http://127.0.0.1:${DEVELOPMENT_PORT}/_health/" >/dev/null; then
        break
    fi
    if [[ "$attempt" -eq 36 ]]; then
        "${DEVELOPMENT_COMPOSE[@]}" logs --no-color --tail=250 app db
        fail "development application did not become healthy after database reset."
    fi
    sleep 5
done

echo
echo "===== DEVELOPMENT DATABASE RESET COMPLETE ====="
"${DEVELOPMENT_COMPOSE[@]}" ps
curl --fail --silent --show-error "http://127.0.0.1:${DEVELOPMENT_PORT}/_health/"
echo
printf 'Development backup: %s\n' "$DEVELOPMENT_BACKUP"
printf 'Preview seed dump:  %s\n' "$PREVIEW_SEED"
