#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
AUTOMATION_USER="eod-automation"
AUTOMATION_HOME="/var/lib/eod-automation"
CONFIG_DIR="/etc/eod-automation"
CONTROLLER="/usr/local/sbin/eod-development-controller"
DEPLOY_KEY="$CONFIG_DIR/github_deploy_key"
CLIENT_KEY="$CONFIG_DIR/github_actions_client_key"
AUTHORIZED_KEYS="$AUTOMATION_HOME/.ssh/authorized_keys"
SUDOERS_FILE="/etc/sudoers.d/eod-automation"

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

[[ "${EUID}" -eq 0 ]] || fail "run bootstrap with sudo/root"
for command in install useradd usermod gpasswd passwd ssh-keygen ssh-keyscan visudo git; do
    command -v "$command" >/dev/null 2>&1 || fail "required command is missing: $command"
done
for source_file in \
    "$SCRIPT_DIR/eod-development-controller" \
    "$SCRIPT_DIR/compose.development.yaml" \
    "$SCRIPT_DIR/Dockerfile.development" \
    "$SCRIPT_DIR/app-entrypoint.sh"; do
    [[ -f "$source_file" ]] || fail "bootstrap source file is missing: $source_file"
done

if ! id -u "$AUTOMATION_USER" >/dev/null 2>&1; then
    useradd --system --create-home --home-dir "$AUTOMATION_HOME" --shell /bin/bash "$AUTOMATION_USER"
fi
passwd --lock "$AUTOMATION_USER" >/dev/null 2>&1 || true
if id -nG "$AUTOMATION_USER" | tr ' ' '\n' | grep -Fxq docker; then
    gpasswd --delete "$AUTOMATION_USER" docker >/dev/null
fi

install -d -o root -g root -m 0700 "$CONFIG_DIR"
install -d -o root -g root -m 0700 \
    /srv/eod/automation \
    /srv/eod/automation/releases \
    /srv/eod/automation/backups \
    /srv/eod/automation/state
install -d -o "$AUTOMATION_USER" -g "$AUTOMATION_USER" -m 0700 "$AUTOMATION_HOME/.ssh"

install -o root -g root -m 0755 "$SCRIPT_DIR/eod-development-controller" "$CONTROLLER"
install -o root -g root -m 0600 "$SCRIPT_DIR/compose.development.yaml" "$CONFIG_DIR/compose.development.yaml"
install -o root -g root -m 0600 "$SCRIPT_DIR/Dockerfile.development" "$CONFIG_DIR/Dockerfile.development"
install -o root -g root -m 0755 "$SCRIPT_DIR/app-entrypoint.sh" "$CONFIG_DIR/app-entrypoint.sh"

if [[ ! -f "$CONFIG_DIR/controller.env" ]]; then
    cat >"$CONFIG_DIR/controller.env" <<'CONFIG'
EOD_REPOSITORY_SSH_URL=git@github.com:genrudko/electronic-operational-docs.git
EOD_REPOSITORY_CACHE=/srv/eod/automation/repository.git
EOD_RELEASES_DIR=/srv/eod/automation/releases
EOD_BACKUPS_DIR=/srv/eod/automation/backups
EOD_STATE_DIR=/srv/eod/automation/state
EOD_DEVELOPMENT_ENV=/srv/eod/secrets/development.env
EOD_DEVELOPMENT_PORT=8766
CONFIG
    chmod 0600 "$CONFIG_DIR/controller.env"
fi

if [[ ! -f "$DEPLOY_KEY" ]]; then
    ssh-keygen -q -t ed25519 -N '' -C 'eod-vps-readonly-deploy-key' -f "$DEPLOY_KEY"
fi
chmod 0600 "$DEPLOY_KEY"
chmod 0644 "$DEPLOY_KEY.pub"

if [[ ! -f "$CLIENT_KEY" ]]; then
    ssh-keygen -q -t ed25519 -N '' -C 'eod-github-actions-vps-client' -f "$CLIENT_KEY"
fi
chmod 0600 "$CLIENT_KEY"
chmod 0644 "$CLIENT_KEY.pub"

ssh-keyscan -t ed25519 github.com 2>/dev/null | sort -u >"$CONFIG_DIR/github_known_hosts.tmp"
if [[ -s "$CONFIG_DIR/github_known_hosts.tmp" ]]; then
    install -o root -g root -m 0644 "$CONFIG_DIR/github_known_hosts.tmp" "$CONFIG_DIR/github_known_hosts"
fi
rm -f "$CONFIG_DIR/github_known_hosts.tmp"
[[ -s "$CONFIG_DIR/github_known_hosts" ]] || fail "could not create GitHub known_hosts"

forced_line="restrict,command=\"sudo -n $CONTROLLER ssh-gateway\" $(cat "$CLIENT_KEY.pub")"
touch "$AUTHORIZED_KEYS"
chown "$AUTOMATION_USER:$AUTOMATION_USER" "$AUTHORIZED_KEYS"
chmod 0600 "$AUTHORIZED_KEYS"
if ! grep -Fqx "$forced_line" "$AUTHORIZED_KEYS"; then
    printf '%s\n' "$forced_line" >>"$AUTHORIZED_KEYS"
fi

cat >"$SUDOERS_FILE" <<EOF_SUDOERS
Defaults:$AUTOMATION_USER env_keep += "SSH_ORIGINAL_COMMAND"
$AUTOMATION_USER ALL=(root) NOPASSWD: $CONTROLLER ssh-gateway
EOF_SUDOERS
chmod 0440 "$SUDOERS_FILE"
visudo -cf "$SUDOERS_FILE" >/dev/null

printf '\n===== READ-ONLY GITHUB DEPLOY KEY =====\n'
cat "$DEPLOY_KEY.pub"
printf '\nAdd this public key in GitHub:\n'
printf 'Repository Settings -> Deploy keys -> Add deploy key\n'
printf 'Title: EOD development VPS read-only\n'
printf 'Allow write access: OFF\n'
printf '\nThe private deploy key remains only at %s and was not printed.\n' "$DEPLOY_KEY"

printf '\n===== GITHUB ACTIONS VPS ACCESS =====\n'
printf 'Create repository Actions secrets:\n'
printf 'EOD_VPS_HOST              = VPS hostname or IP\n'
printf 'EOD_VPS_PORT              = SSH port, normally 22\n'
printf 'EOD_VPS_SSH_PRIVATE_KEY   = securely import from root-owned file %s; value not printed\n' "$CLIENT_KEY"
printf 'EOD_VPS_HOST_KEY          = output of: ssh-keyscan -p <port> <host>\n'
printf '\nDo not send either private key to chat.\n'

ssh_command="ssh -i $DEPLOY_KEY -o IdentitiesOnly=yes -o UserKnownHostsFile=$CONFIG_DIR/github_known_hosts -o StrictHostKeyChecking=yes"
if GIT_SSH_COMMAND="$ssh_command" git ls-remote git@github.com:genrudko/electronic-operational-docs.git HEAD >/dev/null 2>&1; then
    printf '\nDeploy Key access test: SUCCESS\n'
else
    printf '\nDeploy Key access test: PENDING\n'
    printf 'Add the public Deploy Key in GitHub, then run this same bootstrap command again.\n'
fi

printf '\nBootstrap state: OK and safe to run again.\n'
