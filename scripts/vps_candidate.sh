#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
DEFAULT_PORT="18766"
HOST="${EOD_VPS_CANDIDATE_HOST:-127.0.0.1}"
PORT="${EOD_VPS_CANDIDATE_PORT:-$DEFAULT_PORT}"
BASE_URL="http://${HOST}:${PORT}"
LOCK_FILE="$ROOT/requirements/locks/browser.txt"
USER_HOME="${HOME:-}"
if [[ -z "$USER_HOME" ]]; then
    USER_HOME="$(getent passwd "$(id -u)" | cut -d: -f6)"
fi
[[ -n "$USER_HOME" ]] || { printf 'VPS CANDIDATE BLOCKED: cannot resolve user home\n' >&2; exit 2; }
CACHE_BASE="${XDG_CACHE_HOME:-$USER_HOME/.cache}"
CACHE_ROOT="${EOD_VPS_CANDIDATE_CACHE:-$CACHE_BASE/eod-vps-candidate}"
PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$USER_HOME/.cache/ms-playwright}"
export PLAYWRIGHT_BROWSERS_PATH

usage() {
    cat <<'EOF'
Usage:
  bash scripts/vps_candidate.sh prepare
  bash scripts/vps_candidate.sh verify [django_test_label ...]
  bash scripts/vps_candidate.sh browser-smoke
  bash scripts/vps_candidate.sh with-server -- <command> [args ...]

The candidate is unprivileged and ephemeral. It uses the hashed browser lock,
an isolated SQLite database and localhost port 18766 by default. `with-server`
exports EOD_CANDIDATE_BASE_URL and EOD_CANDIDATE_PYTHON to the child command.
EOF
}

fail() {
    printf 'VPS CANDIDATE BLOCKED: %s\n' "$*" >&2
    exit 2
}

command_name="${1:-}"
case "$command_name" in
    -h|--help|help|"")
        usage
        exit 0
        ;;
esac

PATH="$USER_HOME/.local/bin:${PATH:-/usr/local/bin:/usr/bin:/bin}"
export PATH
command -v uv >/dev/null 2>&1 || fail "uv is required"
command -v flock >/dev/null 2>&1 || fail "flock is required"
[[ -f "$LOCK_FILE" ]] || fail "missing browser lock: $LOCK_FILE"
[[ "$HOST" == "127.0.0.1" ]] || fail "candidate host must remain 127.0.0.1"
[[ "$PORT" =~ ^[0-9]+$ ]] || fail "candidate port must be numeric"

LOCK_SHA="$(sha256sum "$LOCK_FILE" | awk '{print $1}')"
VENV_DIR="$CACHE_ROOT/venvs/$LOCK_SHA"
PYTHON="$VENV_DIR/bin/python"
PREPARE_LOCK="$CACHE_ROOT/prepare.lock"

ensure_environment() {
    mkdir -p "$CACHE_ROOT/venvs"
    exec 9>"$PREPARE_LOCK"
    flock 9
    if [[ ! -x "$PYTHON" || ! -f "$VENV_DIR/.ready-$LOCK_SHA" ]]; then
        rm -rf "$VENV_DIR"
        uv venv --python 3.13 "$VENV_DIR"
        # Keep dependency resolution deterministic and integrity checked.
        uv pip sync --python "$PYTHON" --require-hashes "$LOCK_FILE"
        "$PYTHON" -c 'import django; import playwright.sync_api'
        : >"$VENV_DIR/.ready-$LOCK_SHA"
    fi
    flock -u 9
    exec 9>&-
    export EOD_CANDIDATE_PYTHON="$PYTHON"
}

new_runtime() {
    DB_PATH="$(mktemp "${TMPDIR:-/tmp}/eod-vps-candidate.XXXXXX.sqlite3")"
    export DB_ENGINE=sqlite
    export EOD_ALLOW_SQLITE_PATH_OVERRIDE=1
    export SQLITE_PATH="$DB_PATH"
    export EOD_DATABASE_PROFILE=development
    export DJANGO_DEBUG=1
    export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
    export DJANGO_SECRET_KEY="$("$PYTHON" -c 'import secrets; print(secrets.token_urlsafe(48))')"
    export EOD_DEMO_USER_PASSWORD="$("$PYTHON" -c 'import secrets; print("Candidate-Aa1!" + secrets.token_urlsafe(24))')"
    export EOD_CANDIDATE_BASE_URL="$BASE_URL"
}

SERVER_PID=""
DB_PATH=""
cleanup() {
    if [[ -n "$SERVER_PID" ]]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    if [[ -n "$DB_PATH" ]]; then
        rm -f "$DB_PATH"
    fi
}
trap cleanup EXIT

prepare_database() {
    cd "$ROOT"
    "$PYTHON" manage.py check
    "$PYTHON" manage.py migrate --noinput
}

port_is_free() {
    "$PYTHON" - "$HOST" "$PORT" <<'PY'
import socket
import sys
host = sys.argv[1]
port = int(sys.argv[2])
with socket.socket() as sock:
    try:
        sock.bind((host, port))
    except OSError as exc:
        raise SystemExit(f"candidate port unavailable: {host}:{port}: {exc}")
PY
}

start_server() {
    port_is_free
    cd "$ROOT"
    "$PYTHON" manage.py runserver "$HOST:$PORT" --noreload >"${TMPDIR:-/tmp}/eod-vps-candidate-server.log" 2>&1 &
    SERVER_PID=$!
    local ready=0
    for _ in $(seq 1 80); do
        if "$PYTHON" - "$BASE_URL/_health/" "${TMPDIR:-/tmp}/eod-vps-candidate-health.json" <<'PY' 2>/dev/null
import sys
import urllib.request

url, output_path = sys.argv[1:]
with urllib.request.urlopen(url, timeout=1) as response:
    if response.status != 200:
        raise SystemExit(1)
    payload = response.read(8192)
with open(output_path, "wb") as target:
    target.write(payload)
PY
        then
            ready=1
            break
        fi
        if ! kill -0 "$SERVER_PID" 2>/dev/null; then
            cat "${TMPDIR:-/tmp}/eod-vps-candidate-server.log" >&2 || true
            fail "candidate server exited before health became ready"
        fi
        sleep 0.25
    done
    [[ "$ready" == "1" ]] || fail "candidate health timeout at $BASE_URL"
    printf 'CANDIDATE_HEALTH=PASS url=%s\n' "$BASE_URL"
}

resolve_browser_executable() {
    local configured="${EOD_VPS_CANDIDATE_CHROMIUM:-}"
    local candidate
    if [[ -n "$configured" ]]; then
        [[ -x "$configured" ]] || fail "configured Chromium is not executable: $configured"
        printf '%s\n' "$configured"
        return 0
    fi

    candidate="$USER_HOME/.local/chrome-cft/chrome-linux64/chrome"
    if [[ -x "$candidate" ]]; then
        printf '%s\n' "$candidate"
        return 0
    fi

    for candidate in "$PLAYWRIGHT_BROWSERS_PATH"/chromium-*/chrome-linux64/chrome; do
        if [[ -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    fail "no existing Chromium executable found; set EOD_VPS_CANDIDATE_CHROMIUM"
}

resolve_browser_runtime_libs() {
    local browser_executable="$1"
    local configured="${EOD_VPS_CANDIDATE_CHROMIUM_LIBS:-}"
    local candidate="$USER_HOME/.local/chrome-cft/runtime-libs/usr/lib/x86_64-linux-gnu"

    if [[ -n "$configured" ]]; then
        [[ -d "$configured" ]] || fail "configured Chromium runtime libs directory is missing: $configured"
        printf '%s\n' "$configured"
        return 0
    fi

    if [[ -d "$candidate" ]]; then
        printf '%s\n' "$candidate"
        return 0
    fi

    if ! ldd "$browser_executable" 2>/dev/null | grep -q 'not found'; then
        printf '\n'
        return 0
    fi

    fail "Chromium has unresolved shared libraries; set EOD_VPS_CANDIDATE_CHROMIUM_LIBS"
}

browser_smoke_live() {
    local browser_executable
    local browser_libs
    local browser_ld_library_path
    browser_executable="$(resolve_browser_executable)"
    browser_libs="$(resolve_browser_runtime_libs "$browser_executable")"
    browser_ld_library_path="${LD_LIBRARY_PATH:-}"
    if [[ -n "$browser_libs" ]]; then
        browser_ld_library_path="$browser_libs${browser_ld_library_path:+:$browser_ld_library_path}"
    fi
    EOD_CANDIDATE_CHROMIUM_RESOLVED="$browser_executable" LD_LIBRARY_PATH="$browser_ld_library_path" "$PYTHON" - <<'PY'
import os
from playwright.sync_api import sync_playwright

url = os.environ["EOD_CANDIDATE_BASE_URL"]
executable_path = os.environ["EOD_CANDIDATE_CHROMIUM_RESOLVED"]
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True, executable_path=executable_path)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    response = page.goto(url, wait_until="networkidle", timeout=30_000)
    if response is None or not response.ok:
        raise SystemExit(f"candidate browser response failed: {response}")
    body = page.locator("body").inner_text().strip()
    if not body:
        raise SystemExit("candidate browser rendered an empty body")
    print(f"CANDIDATE_BROWSER=PASS url={url} body_chars={len(body)} browser={executable_path}")
    browser.close()
PY
}

run_with_server() {
    [[ "$#" -gt 0 ]] || fail "with-server requires a command after --"
    ensure_environment
    new_runtime
    prepare_database
    start_server
    "$@"
}

command_name="${1:-}"
case "$command_name" in
    prepare)
        ensure_environment
        printf 'CANDIDATE_ENV=READY python=%s lock_sha=%s\n' "$PYTHON" "$LOCK_SHA"
        ;;
    verify)
        shift
        ensure_environment
        new_runtime
        prepare_database
        if [[ "$#" -gt 0 ]]; then
            "$PYTHON" manage.py test "$@" --verbosity 2
        fi
        start_server
        browser_smoke_live
        printf 'VPS_LOCAL_CANDIDATE=PASS tests=%s\n' "$#"
        ;;
    browser-smoke)
        shift
        ensure_environment
        new_runtime
        prepare_database
        start_server
        browser_smoke_live
        ;;
    with-server)
        shift
        [[ "${1:-}" == "--" ]] || fail "with-server syntax requires -- before the child command"
        shift
        run_with_server "$@"
        ;;
    -h|--help|help|"")
        usage
        ;;
    *)
        usage >&2
        fail "unknown command: $command_name"
        ;;
esac
