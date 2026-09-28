#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONTROLLER_SRC="$SCRIPT_DIR/eod-development-controller"
CONTROLLER_BIN="/usr/local/sbin/eod-development-controller"
HELPER_DIR="/usr/local/lib/eod"
VALIDATOR_SRC="$(cd -- "$SCRIPT_DIR/../../scripts/automation" && pwd)/local_overlay.py"
VALIDATOR_BIN="/usr/local/lib/eod/local_overlay.py"
INBOX_DIR="/home/eodadmin/.local/state/development-bridge/eod-overlay"
SUDOERS_FILE="/etc/sudoers.d/eodadmin-local-overlay"
TARGET_USER="eodadmin"

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

[[ "${EUID}" -eq 0 ]] || fail "run bootstrap with sudo/root"

for command in install visudo python3 cp; do
    command -v "$command" >/dev/null 2>&1 || fail "required command is missing: $command"
done

[[ -f "$CONTROLLER_SRC" ]] || fail "controller source is missing: $CONTROLLER_SRC"
[[ -f "$VALIDATOR_SRC" ]] || fail "validator source is missing: $VALIDATOR_SRC"

# 1. Preserve/backup currently installed controller if present
if [[ -f "$CONTROLLER_BIN" ]]; then
    cp -p "$CONTROLLER_BIN" "${CONTROLLER_BIN}.bak"
fi

# 2. Install validator helper to system lib (root-owned, non-writable by eodadmin)
install -d -o root -g root -m 0755 "$HELPER_DIR"
install -o root -g root -m 0755 "$VALIDATOR_SRC" "$VALIDATOR_BIN"

# 3. Install controller to system sbin
install -o root -g root -m 0755 "$CONTROLLER_SRC" "$CONTROLLER_BIN"

# 4. Ensure isolated fixed inbox exists for eodadmin (0700)
if id -u "$TARGET_USER" >/dev/null 2>&1; then
    install -d -o "$TARGET_USER" -g "$TARGET_USER" -m 0700 \
        "/home/eodadmin/.local" \
        "/home/eodadmin/.local/state" \
        "/home/eodadmin/.local/state/development-bridge" \
        "$INBOX_DIR"
else
    install -d -m 0700 "$INBOX_DIR"
fi

# 5. Configure narrow sudoers granting NOPASSWD only for local overlay commands
cat >"$SUDOERS_FILE" <<EOF_SUDOERS
$TARGET_USER ALL=(root) NOPASSWD: $CONTROLLER_BIN local-hot-refresh *, $CONTROLLER_BIN local-hot-refresh-clear
EOF_SUDOERS

chmod 0440 "$SUDOERS_FILE"
visudo -cf "$SUDOERS_FILE" >/dev/null

printf 'Local overlay bootstrap: SUCCESS (eodadmin granted narrow local-hot-refresh NOPASSWD)\n'
