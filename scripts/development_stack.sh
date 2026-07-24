#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="${EOD_DEVELOPMENT_REPO:-/srv/eod/development}"
ENV_FILE="${EOD_DEVELOPMENT_ENV:-/srv/eod/secrets/development.env}"
COMPOSE_FILE="$REPO_DIR/compose.development.yaml"

usage() {
    cat <<'EOF'
Usage:
  sudo bash scripts/development_stack.sh bootstrap
  sudo bash scripts/development_stack.sh refresh
  sudo bash scripts/development_stack.sh rebuild
  sudo bash scripts/development_stack.sh check
  sudo bash scripts/development_stack.sh test
  sudo bash scripts/development_stack.sh migrate
  sudo bash scripts/development_stack.sh status
  sudo bash scripts/development_stack.sh logs
  sudo bash scripts/development_stack.sh follow
  sudo bash scripts/development_stack.sh shell
  sudo bash scripts/development_stack.sh django-shell
  sudo bash scripts/development_stack.sh stop

bootstrap     Build the image and start the isolated development stack.
refresh       Recreate the app from the current working tree without rebuilding dependencies.
rebuild       Rebuild the image, then recreate the app.
check         Run Django check and verify that migration files are current.
test          Run the full Django test suite against the development PostgreSQL database.
migrate       Apply migrations to the development PostgreSQL database.
status        Show repository, containers, health endpoint, and main-page status.
logs          Show the last 250 app/database log lines.
follow        Follow app/database logs until Ctrl+C.
shell         Open a shell in the running app container.
django-shell  Open Django shell in the running app container.
stop          Stop development containers without deleting their volumes.
EOF
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

require_equal() {
    local name="$1"
    local expected="$2"
    local actual="${!name:-}"
    [[ "$actual" == "$expected" ]] || fail "$name must be '$expected', got '$actual'."
}

if [[ "${EUID}" -ne 0 ]]; then
    fail "run this script through sudo."
fi

COMMAND="${1:-}"
[[ -n "$COMMAND" ]] || { usage; exit 1; }

[[ -d "$REPO_DIR/.git" ]] || fail "development repository not found: $REPO_DIR"
[[ -f "$COMPOSE_FILE" ]] || fail "development Compose file not found: $COMPOSE_FILE"
[[ -f "$ENV_FILE" ]] || fail "development secret file not found: $ENV_FILE"

cd "$REPO_DIR"
BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || fail "development checkout must be on a named branch."
[[ "$BRANCH" != "main" ]] || fail "development stack refuses to run from main."

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

require_equal POSTGRES_DB eod_development
require_equal POSTGRES_USER eod_development
require_equal EOD_DEVELOPMENT_PORT 8766
[[ -n "${POSTGRES_PASSWORD:-}" ]] || fail "POSTGRES_PASSWORD is missing in development.env."
[[ -n "${DJANGO_SECRET_KEY:-}" ]] || fail "DJANGO_SECRET_KEY is missing in development.env."
[[ "$POSTGRES_PASSWORD" != "replace-with-a-long-random-development-password" ]] || fail "replace the example PostgreSQL password."
[[ "$DJANGO_SECRET_KEY" != "replace-with-a-long-random-development-secret" ]] || fail "replace the example Django secret key."

COMPOSE=(
    docker compose
    --env-file "$ENV_FILE"
    -f "$COMPOSE_FILE"
)

"${COMPOSE[@]}" config --quiet

wait_for_database() {
    local container
    container="$("${COMPOSE[@]}" ps -q db)"
    [[ -n "$container" ]] || fail "development database container was not created."

    for attempt in $(seq 1 30); do
        local state
        state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container")"
        printf 'Database attempt %02d/30: %s\n' "$attempt" "$state"
        [[ "$state" == "healthy" ]] && return 0
        [[ "$attempt" -eq 30 ]] && fail "development PostgreSQL did not become healthy."
        sleep 2
    done
}

wait_for_application() {
    local container
    container="$("${COMPOSE[@]}" ps -q app)"
    [[ -n "$container" ]] || fail "development application container was not created."

    for attempt in $(seq 1 36); do
        local state
        state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container")"
        printf 'Application attempt %02d/36: %s\n' "$attempt" "$state"
        if curl --fail --silent --show-error --max-time 5 \
            "http://127.0.0.1:${EOD_DEVELOPMENT_PORT}/_health/" >/dev/null; then
            return 0
        fi
        if [[ "$attempt" -eq 36 ]]; then
            "${COMPOSE[@]}" logs --no-color --tail=250 app db
            fail "development application did not become healthy."
        fi
        sleep 5
    done
}

start_database() {
    "${COMPOSE[@]}" up --detach db
    wait_for_database
}

recreate_application() {
    "${COMPOSE[@]}" up --detach --force-recreate app
    wait_for_application
}

run_manage() {
    start_database
    "${COMPOSE[@]}" run --rm --no-deps \
        --entrypoint python \
        app manage.py "$@"
}

show_status() {
    echo "===== DEVELOPMENT REPOSITORY ====="
    printf 'Path:   %s\n' "$REPO_DIR"
    printf 'Branch: %s\n' "$BRANCH"
    printf 'HEAD:   %s\n' "$(git rev-parse HEAD)"
    git status --short --branch

    echo
    echo "===== DEVELOPMENT CONTAINERS ====="
    "${COMPOSE[@]}" ps

    echo
    echo "===== DEVELOPMENT HTTP ====="
    curl --fail --silent --show-error \
        "http://127.0.0.1:${EOD_DEVELOPMENT_PORT}/_health/"
    echo
    curl --fail --silent --show-error --output /dev/null \
        --write-out 'Main page: HTTP %{http_code}; content-type=%{content_type}; bytes=%{size_download}\n' \
        "http://127.0.0.1:${EOD_DEVELOPMENT_PORT}/"
}

case "$COMMAND" in
    bootstrap)
        echo "===== BUILD DEVELOPMENT IMAGE ====="
        "${COMPOSE[@]}" build app
        start_database
        recreate_application
        show_status
        ;;
    refresh)
        start_database
        recreate_application
        show_status
        ;;
    rebuild)
        echo "===== REBUILD DEVELOPMENT IMAGE ====="
        "${COMPOSE[@]}" build app
        start_database
        recreate_application
        show_status
        ;;
    check)
        run_manage check
        run_manage makemigrations --check --dry-run
        ;;
    test)
        run_manage test --verbosity 2
        ;;
    migrate)
        run_manage migrate --noinput
        ;;
    status)
        show_status
        ;;
    logs)
        "${COMPOSE[@]}" logs --no-color --tail=250 app db
        ;;
    follow)
        "${COMPOSE[@]}" logs --follow app db
        ;;
    shell)
        "${COMPOSE[@]}" exec app /bin/sh
        ;;
    django-shell)
        "${COMPOSE[@]}" exec app python manage.py shell
        ;;
    stop)
        "${COMPOSE[@]}" stop app db
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        usage
        fail "unknown command: $COMMAND"
        ;;
esac
