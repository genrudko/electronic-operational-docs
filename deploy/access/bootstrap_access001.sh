#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_IP="5.181.177.72"
EXPECTED_PR_NUMBER="17"
EXPECTED_BRANCH="infra/access-001-public-development-https"
MIN_CERTBOT_VERSION="5.4"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HTTP_NGINX_TEMPLATE="$SCRIPT_DIR/nginx/eod-development-http.conf"
TLS_NGINX_TEMPLATE="$SCRIPT_DIR/nginx/eod-development.conf"
HOST_COMPOSE_SOURCE="$SCRIPT_DIR/../automation/compose.development.yaml"
HOST_COMPOSE_TARGET="/etc/eod-automation/compose.development.yaml"
DEVELOPMENT_ENV="/srv/eod/secrets/development.env"
CONTROLLER="/usr/local/sbin/eod-development-controller"
ACME_ROOT="/var/lib/eod-access001/acme"
CERT_LIVE_DIR="/etc/letsencrypt/live/$EXPECTED_IP"
CERTBOT_HOOK="/etc/letsencrypt/renewal-hooks/deploy/eod-access001-nginx-reload"
RENEW_SERVICE="/etc/systemd/system/eod-access001-certbot-renew.service"
RENEW_TIMER="/etc/systemd/system/eod-access001-certbot-renew.timer"

PR_NUMBER=""
HEAD_SHA=""
RUN_ID=""
CERTBOT_EMAIL="${ACCESS001_CERTBOT_EMAIL:-}"

SUCCESS=0
ROLLBACK_STARTED=0
CONTROLLER_PENDING=0
CERT_CREATED=0
CERT_WAS_PRESENT=0
UFW_ADDED_80=0
UFW_ADDED_443=0
NGINX_INSTALLED_BY_SCRIPT=0
CERTBOT_INSTALLED_BY_SCRIPT=0
SNAPD_INSTALLED_BY_SCRIPT=0
NGINX_WAS_ACTIVE=0
NGINX_WAS_ENABLED=0
TIMER_WAS_ACTIVE=0
TIMER_WAS_ENABLED=0
HOST_BACKUPS_READY=0
NGINX_BACKUPS_READY=0
RENEW_BACKUPS_READY=0

AUDIT_ROOT=""
BACKUP_ROOT=""
LOG_FILE=""
NGINX_TARGET=""
NGINX_LINK=""
CERTBOT_BIN=""
NGINX_BIN=""
CURRENT_IMAGE=""
PREVIEW_BEFORE=""

usage() {
    cat <<'EOF'
Usage:
  sudo ACCESS001_CI_CONFIRMED=YES \
    ACCESS001_SCRIPT_SHA256=<sha256> \
    bash deploy/access/bootstrap_access001.sh \
      --pr-number 17 \
      --head-sha <40-hex-sha> \
      [--run-id <digits>] \
      [--certbot-email <address>]
EOF
}

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

log() {
    printf '[ACCESS-001] %s\n' "$*"
}

section() {
    printf '\n===== %s =====\n' "$*"
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "required command is missing: $1"
}

require_root() {
    [[ "${EUID}" -eq 0 ]] || fail "bootstrap must run as root"
}

parse_args() {
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --pr-number)
                [[ "$#" -ge 2 ]] || fail "--pr-number requires a value"
                PR_NUMBER="$2"
                shift 2
                ;;
            --head-sha)
                [[ "$#" -ge 2 ]] || fail "--head-sha requires a value"
                HEAD_SHA="$2"
                shift 2
                ;;
            --run-id)
                [[ "$#" -ge 2 ]] || fail "--run-id requires a value"
                RUN_ID="$2"
                shift 2
                ;;
            --certbot-email)
                [[ "$#" -ge 2 ]] || fail "--certbot-email requires a value"
                CERTBOT_EMAIL="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                fail "unknown argument: $1"
                ;;
        esac
    done

    [[ "$PR_NUMBER" == "$EXPECTED_PR_NUMBER" ]] || \
        fail "ACCESS-001 must use Draft PR #$EXPECTED_PR_NUMBER"
    [[ "$HEAD_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "--head-sha must be an exact 40-hex SHA"
    if [[ -z "$RUN_ID" ]]; then
        RUN_ID="$(date -u +%Y%m%d%H%M%S)"
    fi
    [[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "--run-id must contain digits only"
}

verify_operator_gate() {
    [[ "${ACCESS001_CI_CONFIRMED:-}" == "YES" ]] || \
        fail "five green exact-head workflows were not explicitly confirmed"
    local expected_script_sha actual_script_sha
    expected_script_sha="${ACCESS001_SCRIPT_SHA256:-}"
    [[ "$expected_script_sha" =~ ^[0-9a-f]{64}$ ]] || \
        fail "ACCESS001_SCRIPT_SHA256 must contain the reviewed bootstrap checksum"
    actual_script_sha="$(sha256sum "$0" | awk '{print $1}')"
    [[ "$actual_script_sha" == "$expected_script_sha" ]] || \
        fail "bootstrap checksum mismatch: expected $expected_script_sha, got $actual_script_sha"
}

prepare_audit() {
    AUDIT_ROOT="/srv/eod/audits/ACCESS-001_${RUN_ID}_${HEAD_SHA:0:12}"
    BACKUP_ROOT="$AUDIT_ROOT/rollback"
    LOG_FILE="$AUDIT_ROOT/bootstrap.log"
    install -d -o root -g root -m 0700 "$BACKUP_ROOT"
    touch "$LOG_FILE"
    chmod 0600 "$LOG_FILE"
    exec > >(tee -a "$LOG_FILE") 2>&1
}

backup_item() {
    local source="$1" label="$2"
    if [[ -e "$source" || -L "$source" ]]; then
        cp -a -- "$source" "$BACKUP_ROOT/$label"
        printf 'PRESENT\n' >"$BACKUP_ROOT/$label.state"
    else
        printf 'ABSENT\n' >"$BACKUP_ROOT/$label.state"
    fi
}

restore_item() {
    local target="$1" label="$2" state
    state="$(cat "$BACKUP_ROOT/$label.state" 2>/dev/null || printf 'ABSENT')"
    rm -rf -- "$target"
    if [[ "$state" == "PRESENT" ]]; then
        cp -a -- "$BACKUP_ROOT/$label" "$target"
    fi
}

controller_command() {
    local original="$1"
    SSH_ORIGINAL_COMMAND="$original" "$CONTROLLER" ssh-gateway
}

capture_preview_state() {
    docker ps --all \
        --filter label=com.docker.compose.project=eod-preview \
        --format '{{.ID}}|{{.Image}}|{{.State}}|{{.Names}}' \
        | sort
}

rollback() {
    local original_rc="$1"
    [[ "$ROLLBACK_STARTED" -eq 0 ]] || return 0
    ROLLBACK_STARTED=1
    trap - ERR EXIT
    set +e

    section "ROLLBACK"
    log "activation failed with rc=$original_rc; restoring host state"

    systemctl disable --now eod-access001-certbot-renew.timer >/dev/null 2>&1 || true
    if [[ -n "$BACKUP_ROOT" && -d "$BACKUP_ROOT" ]]; then
        if [[ "$RENEW_BACKUPS_READY" -eq 1 ]]; then
            restore_item "$RENEW_SERVICE" renew-service
            restore_item "$RENEW_TIMER" renew-timer
            restore_item "$CERTBOT_HOOK" certbot-hook
            systemctl daemon-reload >/dev/null 2>&1 || true
            if [[ "$TIMER_WAS_ENABLED" -eq 1 ]]; then
                systemctl enable eod-access001-certbot-renew.timer >/dev/null 2>&1 || true
            fi
            if [[ "$TIMER_WAS_ACTIVE" -eq 1 ]]; then
                systemctl start eod-access001-certbot-renew.timer >/dev/null 2>&1 || true
            fi
        fi

        if [[ "$NGINX_BACKUPS_READY" -eq 1 ]]; then
            [[ -n "$NGINX_TARGET" ]] && restore_item "$NGINX_TARGET" nginx-target
            [[ -n "$NGINX_LINK" ]] && restore_item "$NGINX_LINK" nginx-link
        fi
        if [[ "$HOST_BACKUPS_READY" -eq 1 ]]; then
            restore_item "$HOST_COMPOSE_TARGET" host-compose
            restore_item "$DEVELOPMENT_ENV" development-env
        fi
    fi

    if command -v nginx >/dev/null 2>&1 && nginx -t >/dev/null 2>&1; then
        if [[ "$NGINX_WAS_ACTIVE" -eq 1 ]]; then
            systemctl reload nginx >/dev/null 2>&1 || systemctl restart nginx >/dev/null 2>&1 || true
        else
            systemctl stop nginx >/dev/null 2>&1 || true
        fi
    fi
    if [[ "$NGINX_WAS_ENABLED" -eq 0 ]]; then
        systemctl disable nginx >/dev/null 2>&1 || true
    fi

    if [[ "$CONTROLLER_PENDING" -eq 1 ]]; then
        log "rolling back pending development deployment through AUTO-001B controller"
        controller_command "rollback $RUN_ID" || true
        CONTROLLER_PENDING=0
    fi

    if [[ "$UFW_ADDED_443" -eq 1 ]]; then
        ufw --force delete allow 443/tcp >/dev/null 2>&1 || true
    fi
    if [[ "$UFW_ADDED_80" -eq 1 ]]; then
        ufw --force delete allow 80/tcp >/dev/null 2>&1 || true
    fi

    if [[ "$CERT_CREATED" -eq 1 && "$CERT_WAS_PRESENT" -eq 0 && -n "$CERTBOT_BIN" ]]; then
        "$CERTBOT_BIN" delete --non-interactive --cert-name "$EXPECTED_IP" >/dev/null 2>&1 || true
    fi

    local preview_after
    preview_after="$(capture_preview_state 2>/dev/null || true)"
    if [[ "$preview_after" == "$PREVIEW_BEFORE" ]]; then
        log "preview rollback evidence: UNTOUCHED"
    else
        log "preview evidence changed unexpectedly; manual inspection required"
        printf 'BEFORE:\n%s\nAFTER:\n%s\n' "$PREVIEW_BEFORE" "$preview_after"
    fi

    log "rollback completed; packages installed during bootstrap were retained but not used"
    log "audit log: $LOG_FILE"
    exit "$original_rc"
}

on_exit() {
    local rc="$?"
    if [[ "$SUCCESS" -ne 1 ]]; then
        rollback "$rc"
    fi
}

print_inventory() {
    section "HOST INVENTORY — NO MUTATIONS YET"
    printf 'expected_branch=%s\n' "$EXPECTED_BRANCH"
    printf 'pr_number=%s\n' "$PR_NUMBER"
    printf 'head_sha=%s\n' "$HEAD_SHA"
    printf 'expected_public_ip=%s\n' "$EXPECTED_IP"
    printf 'kernel=%s\n' "$(uname -srmo)"
    printf 'os_release=%s\n' "$(. /etc/os-release && printf '%s %s' "$ID" "$VERSION_ID")"

    printf '\n-- interface addresses --\n'
    ip -brief address

    printf '\n-- observed public IPv4 --\n'
    local observed_ip=""
    observed_ip="$(curl -4 --fail --silent --show-error --max-time 10 https://api.ipify.org || true)"
    if [[ -z "$observed_ip" ]]; then
        observed_ip="$(curl -4 --fail --silent --show-error --max-time 10 https://ifconfig.co/ip || true)"
        observed_ip="${observed_ip//$'\n'/}"
    fi
    printf '%s\n' "${observed_ip:-UNAVAILABLE}"

    printf '\n-- sshd effective ports --\n'
    if command -v sshd >/dev/null 2>&1; then
        sshd -T 2>/dev/null | awk '$1 == "port" {print}' || true
    else
        printf 'sshd command unavailable\n'
    fi

    printf '\n-- listeners on 80/443 --\n'
    ss -H -ltnp | awk '$4 ~ /:80$/ || $4 ~ /:443$/ {print}' || true

    printf '\n-- nginx inventory --\n'
    if command -v nginx >/dev/null 2>&1; then
        nginx -v 2>&1
        systemctl is-active nginx || true
        systemctl is-enabled nginx || true
    else
        printf 'nginx=ABSENT\n'
    fi

    printf '\n-- Certbot inventory --\n'
    if command -v certbot >/dev/null 2>&1; then
        certbot --version
    else
        printf 'certbot=ABSENT\n'
    fi
    if command -v snap >/dev/null 2>&1; then
        snap list certbot 2>/dev/null || true
    fi

    printf '\n-- UFW inventory --\n'
    ufw status verbose
    ufw status numbered

    printf '\n-- Docker development/preview inventory --\n'
    docker ps --all \
        --filter label=com.docker.compose.project=eod-development \
        --format 'development|{{.ID}}|{{.Image}}|{{.Status}}|{{.Names}}' \
        | sort
    docker ps --all \
        --filter label=com.docker.compose.project=eod-preview \
        --format 'preview|{{.ID}}|{{.Image}}|{{.Status}}|{{.Names}}' \
        | sort

    printf '\n-- controller status --\n'
    "$CONTROLLER" status

    OBSERVED_PUBLIC_IP="$observed_ip"
}

validate_inventory() {
    section "INVENTORY VALIDATION"
    [[ "${OBSERVED_PUBLIC_IP:-}" == "$EXPECTED_IP" ]] || \
        fail "observed public IPv4 does not match $EXPECTED_IP"

    ip -o -4 address show scope global | \
        awk -v expected="$EXPECTED_IP" \
            '{split($4, parts, "/"); if (parts[1] == expected) found=1} END {exit !found}' || \
        fail "expected public IPv4 is not assigned to this host"

    [[ "$(ufw status | sed -n '1p')" == "Status: active" ]] || \
        fail "UFW must already be installed and active"

    local listener
    while IFS= read -r listener; do
        [[ -z "$listener" ]] && continue
        if [[ "$listener" != *nginx* ]]; then
            fail "port 80/443 is owned by an unrelated listener: $listener"
        fi
    done < <(ss -H -ltnp | awk '$4 ~ /:80$/ || $4 ~ /:443$/ {print}')

    if command -v nginx >/dev/null 2>&1; then
        nginx -T >"$AUDIT_ROOT/nginx-before.txt" 2>&1
        if grep -Eq 'server_name[[:space:]]+5\.181\.177\.72([[:space:];]|$)' \
            "$AUDIT_ROOT/nginx-before.txt"; then
            if ! grep -Rqs 'ACCESS-001' /etc/nginx/sites-enabled /etc/nginx/conf.d 2>/dev/null; then
                fail "an existing nginx virtual host already owns $EXPECTED_IP"
            fi
        fi
    fi

    [[ -f "$HTTP_NGINX_TEMPLATE" ]] || fail "missing HTTP nginx template"
    [[ -f "$TLS_NGINX_TEMPLATE" ]] || fail "missing TLS nginx template"
    [[ -f "$HOST_COMPOSE_SOURCE" ]] || fail "missing exact-head host Compose source"
    [[ -f "$HOST_COMPOSE_TARGET" ]] || fail "current host Compose file is missing"
    [[ -f "$DEVELOPMENT_ENV" ]] || fail "development environment file is missing"
    [[ -x "$CONTROLLER" ]] || fail "trusted development controller is missing"

    PREVIEW_BEFORE="$(capture_preview_state)"
    log "inventory accepted; no SSH port or existing UFW rule will be replaced"
}

deploy_exact_head() {
    section "EXACT-HEAD DEVELOPMENT DEPLOYMENT"
    log "delegating application backup, tests, migration and rollback boundary to AUTO-001B"
    controller_command "deploy refresh $PR_NUMBER $HEAD_SHA $RUN_ID"
    CONTROLLER_PENDING=1
}

ensure_nginx() {
    section "NGINX PREPARATION"
    if command -v nginx >/dev/null 2>&1; then
        systemctl is-active --quiet nginx && NGINX_WAS_ACTIVE=1 || true
        systemctl is-enabled --quiet nginx && NGINX_WAS_ENABLED=1 || true
        log "reusing existing nginx installation"
    else
        require_command apt-get
        log "nginx is absent; installing without replacing another listener"
        apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
        NGINX_INSTALLED_BY_SCRIPT=1
    fi
    NGINX_BIN="$(command -v nginx)"

    if [[ -d /etc/nginx/sites-available && -d /etc/nginx/sites-enabled ]]; then
        NGINX_TARGET="/etc/nginx/sites-available/eod-development-access001.conf"
        NGINX_LINK="/etc/nginx/sites-enabled/eod-development-access001.conf"
    else
        install -d -o root -g root -m 0755 /etc/nginx/conf.d
        NGINX_TARGET="/etc/nginx/conf.d/eod-development-access001.conf"
        NGINX_LINK=""
    fi

    backup_item "$NGINX_TARGET" nginx-target
    if [[ -n "$NGINX_LINK" ]]; then
        backup_item "$NGINX_LINK" nginx-link
    else
        printf 'ABSENT\n' >"$BACKUP_ROOT/nginx-link.state"
    fi
    NGINX_BACKUPS_READY=1

    backup_item "$HOST_COMPOSE_TARGET" host-compose
    backup_item "$DEVELOPMENT_ENV" development-env
    HOST_BACKUPS_READY=1

    backup_item "$RENEW_SERVICE" renew-service
    backup_item "$RENEW_TIMER" renew-timer
    backup_item "$CERTBOT_HOOK" certbot-hook
    RENEW_BACKUPS_READY=1
    systemctl is-active --quiet eod-access001-certbot-renew.timer && TIMER_WAS_ACTIVE=1 || true
    systemctl is-enabled --quiet eod-access001-certbot-renew.timer && TIMER_WAS_ENABLED=1 || true

    install -d -o root -g root -m 0755 "$ACME_ROOT/.well-known/acme-challenge"
    install -o root -g root -m 0644 "$HTTP_NGINX_TEMPLATE" "$NGINX_TARGET"
    if [[ -n "$NGINX_LINK" ]]; then
        ln -sfn "$NGINX_TARGET" "$NGINX_LINK"
    fi

    nginx -t
    systemctl enable --now nginx

    local token="access001-${RUN_ID}-${HEAD_SHA:0:12}"
    printf '%s\n' "$token" >"$ACME_ROOT/.well-known/acme-challenge/$token"
    local response
    response="$(curl --fail --silent --show-error --max-time 10 \
        --resolve "$EXPECTED_IP:80:127.0.0.1" \
        "http://$EXPECTED_IP/.well-known/acme-challenge/$token")"
    rm -f "$ACME_ROOT/.well-known/acme-challenge/$token"
    [[ "$response" == "$token" ]] || fail "nginx ACME webroot self-test failed"
}

ufw_rule_exists() {
    local port="$1"
    ufw status | awk -v target="$port/tcp" '$1 == target && $2 == "ALLOW" {found=1} END {exit !found}'
}

open_required_firewall_ports() {
    section "UFW NARROW EXPOSURE"
    if ufw_rule_exists 80; then
        log "existing allow rule for 80/tcp retained"
    else
        ufw allow 80/tcp comment 'ACCESS-001 ACME and HTTPS redirect'
        UFW_ADDED_80=1
    fi
}

ensure_certbot() {
    section "CERTBOT PREPARATION"
    if command -v certbot >/dev/null 2>&1; then
        CERTBOT_BIN="$(command -v certbot)"
        log "reusing existing Certbot at $CERTBOT_BIN"
    else
        require_command apt-get
        if ! command -v snap >/dev/null 2>&1; then
            log "snapd is absent; installing it for the official Certbot snap"
            apt-get update
            DEBIAN_FRONTEND=noninteractive apt-get install -y snapd
            SNAPD_INSTALLED_BY_SCRIPT=1
        fi
        snap install --classic certbot
        CERTBOT_INSTALLED_BY_SCRIPT=1
        CERTBOT_BIN="/snap/bin/certbot"
        if [[ ! -e /usr/local/bin/certbot ]]; then
            ln -s "$CERTBOT_BIN" /usr/local/bin/certbot
        fi
    fi

    local version
    version="$($CERTBOT_BIN --version | sed -nE 's/^certbot[[:space:]]+([^[:space:]]+).*/\1/p')"
    [[ -n "$version" ]] || fail "could not determine Certbot version"
    dpkg --compare-versions "$version" ge "$MIN_CERTBOT_VERSION" || \
        fail "Certbot $version is too old; version $MIN_CERTBOT_VERSION or newer is required"
    printf 'certbot_path=%s\ncertbot_version=%s\n' "$CERTBOT_BIN" "$version"
}

certificate_has_expected_ip() {
    [[ -f "$CERT_LIVE_DIR/fullchain.pem" && -f "$CERT_LIVE_DIR/privkey.pem" ]] || return 1
    openssl x509 -in "$CERT_LIVE_DIR/fullchain.pem" -noout -ext subjectAltName 2>/dev/null | \
        grep -Fq "IP Address:$EXPECTED_IP"
}

certificate_is_fresh() {
    certificate_has_expected_ip || return 1
    openssl x509 -checkend 86400 -noout -in "$CERT_LIVE_DIR/fullchain.pem" >/dev/null 2>&1
}

certbot_identity_args() {
    if [[ -n "$CERTBOT_EMAIL" ]]; then
        printf '%s\n' "--email" "$CERTBOT_EMAIL"
    else
        printf '%s\n' "--register-unsafely-without-email"
    fi
}

issue_certificate() {
    section "LET'S ENCRYPT IP CERTIFICATE"
    local identity_args=()
    mapfile -t identity_args < <(certbot_identity_args)

    if [[ -d "$CERT_LIVE_DIR" ]]; then
        CERT_WAS_PRESENT=1
    fi
    if [[ "$CERT_WAS_PRESENT" -eq 1 ]] && ! certificate_has_expected_ip; then
        fail "existing certificate name $EXPECTED_IP does not contain the expected IP SAN"
    fi

    if certificate_is_fresh; then
        log "existing publicly configured IP certificate is still fresh; issuance skipped"
        return 0
    fi

    local staging_name="${EXPECTED_IP}-access001-staging"
    log "requesting a staging short-lived IP certificate first"
    "$CERTBOT_BIN" certonly \
        --staging \
        --non-interactive \
        --agree-tos \
        "${identity_args[@]}" \
        --preferred-profile shortlived \
        --webroot \
        --webroot-path "$ACME_ROOT" \
        --ip-address "$EXPECTED_IP" \
        --cert-name "$staging_name" \
        --force-renewal
    "$CERTBOT_BIN" delete --non-interactive --cert-name "$staging_name" >/dev/null 2>&1 || true

    log "requesting the publicly trusted short-lived IP certificate"
    local force_args=()
    [[ -d "$CERT_LIVE_DIR" ]] && force_args+=(--force-renewal)
    "$CERTBOT_BIN" certonly \
        --non-interactive \
        --agree-tos \
        "${identity_args[@]}" \
        --preferred-profile shortlived \
        --webroot \
        --webroot-path "$ACME_ROOT" \
        --ip-address "$EXPECTED_IP" \
        --cert-name "$EXPECTED_IP" \
        "${force_args[@]}"
    CERT_CREATED=1

    certificate_has_expected_ip || fail "issued certificate does not contain $EXPECTED_IP as an IP SAN"
}

update_development_environment() {
    section "DJANGO PUBLIC HTTPS CONTRACT"
    install -o root -g root -m 0600 "$HOST_COMPOSE_SOURCE" "$HOST_COMPOSE_TARGET"

    python3 - "$DEVELOPMENT_ENV" <<'PY'
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
updates = {
    "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost,5.181.177.72",
    "DJANGO_CSRF_TRUSTED_ORIGINS": "https://5.181.177.72",
    "DJANGO_TRUST_PROXY_HTTPS": "1",
    "DJANGO_SECURE_COOKIES": "1",
    "EOD_PUBLIC_HTTPS": "1",
    "EOD_PUBLIC_HTTPS_ORIGIN": "https://5.181.177.72",
}
stat = path.stat()
lines = path.read_text(encoding="utf-8").splitlines()
kept = []
for line in lines:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        kept.append(line)
        continue
    key = stripped.split("=", 1)[0].strip()
    if key not in updates:
        kept.append(line)

if kept and kept[-1] != "":
    kept.append("")
kept.append("# ACCESS-001 public HTTPS development contract")
kept.extend(f"{key}={value}" for key, value in updates.items())
content = "\n".join(kept) + "\n"

with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    dir=path.parent,
    prefix=".access001-env-",
    delete=False,
) as handle:
    handle.write(content)
    temp_name = handle.name
os.chmod(temp_name, stat.st_mode & 0o777)
os.chown(temp_name, stat.st_uid, stat.st_gid)
os.replace(temp_name, path)
PY

    local container
    container="$(docker ps \
        --filter label=com.docker.compose.project=eod-development \
        --filter label=com.docker.compose.service=app \
        --format '{{.ID}}' | head -n 1)"
    [[ -n "$container" ]] || fail "development app container is not running after exact-head deployment"
    CURRENT_IMAGE="$(docker inspect --format '{{.Config.Image}}' "$container")"
    [[ "$CURRENT_IMAGE" == "eod-development-app:$HEAD_SHA" ]] || \
        fail "development image mismatch: expected exact SHA image, got $CURRENT_IMAGE"

    EOD_RELEASE_IMAGE="$CURRENT_IMAGE" docker compose \
        --project-name eod-development \
        --env-file "$DEVELOPMENT_ENV" \
        --file "$HOST_COMPOSE_TARGET" \
        up --detach --force-recreate app

    for attempt in $(seq 1 36); do
        if curl --fail --silent --show-error --max-time 5 \
            http://127.0.0.1:8766/_health/ >/dev/null; then
            break
        fi
        [[ "$attempt" -eq 36 ]] && fail "development health failed after public HTTPS settings activation"
        sleep 5
    done

    EOD_RELEASE_IMAGE="$CURRENT_IMAGE" docker compose \
        --project-name eod-development \
        --env-file "$DEVELOPMENT_ENV" \
        --file "$HOST_COMPOSE_TARGET" \
        exec -T app python - <<'PY'
from django.conf import settings

assert settings.DEBUG is False
assert settings.EOD_PUBLIC_HTTPS is True
assert settings.SESSION_COOKIE_SECURE is True
assert settings.CSRF_COOKIE_SECURE is True
assert settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
assert "5.181.177.72" in settings.ALLOWED_HOSTS
assert "https://5.181.177.72" in settings.CSRF_TRUSTED_ORIGINS
print("DJANGO_PUBLIC_HTTPS_SETTINGS=PASSED")
PY
}

activate_tls_nginx() {
    section "NGINX TLS ACTIVATION"
    install -o root -g root -m 0644 "$TLS_NGINX_TEMPLATE" "$NGINX_TARGET"
    nginx -t
    systemctl reload nginx

    if ufw_rule_exists 443; then
        log "existing allow rule for 443/tcp retained"
    else
        ufw allow 443/tcp comment 'ACCESS-001 HTTPS development'
        UFW_ADDED_443=1
    fi
}

install_renewal_contract() {
    section "SHORT-LIVED CERTIFICATE RENEWAL"
    install -d -o root -g root -m 0755 "$(dirname "$CERTBOT_HOOK")"
    cat >"$CERTBOT_HOOK" <<HOOK
#!/bin/sh
set -eu
$NGINX_BIN -t
/bin/systemctl reload nginx
HOOK
    chmod 0755 "$CERTBOT_HOOK"

    cat >"$RENEW_SERVICE" <<EOF
[Unit]
Description=Renew ACCESS-001 short-lived IP certificate
After=network-online.target nginx.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$CERTBOT_BIN renew --quiet --cert-name $EXPECTED_IP
EOF

    cat >"$RENEW_TIMER" <<'EOF'
[Unit]
Description=Twice-daily ACCESS-001 certificate renewal check

[Timer]
OnCalendar=*-*-* 00,12:17:00
RandomizedDelaySec=1800
Persistent=true
Unit=eod-access001-certbot-renew.service

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable --now eod-access001-certbot-renew.timer

    "$CERTBOT_BIN" renew \
        --dry-run \
        --cert-name "$EXPECTED_IP" \
        --run-deploy-hooks
}

verify_final_state() {
    section "FINAL EVIDENCE"
    nginx -t

    curl --fail --silent --show-error --max-time 10 \
        http://127.0.0.1:8766/_health/ >/tmp/access001-local-health.json
    cat /tmp/access001-local-health.json
    rm -f /tmp/access001-local-health.json

    local redirect_headers login_status health_status
    redirect_headers="$(curl --silent --show-error --max-time 10 \
        --resolve "$EXPECTED_IP:80:127.0.0.1" \
        --head "http://$EXPECTED_IP/")"
    printf '%s\n' "$redirect_headers"
    grep -Eq '^HTTP/.* 308' <<<"$redirect_headers" || fail "HTTP does not redirect with 308"
    grep -Fiq "location: https://$EXPECTED_IP/" <<<"$redirect_headers" || \
        fail "HTTP redirect target is incorrect"

    login_status="$(curl --silent --show-error --max-time 15 \
        --resolve "$EXPECTED_IP:443:127.0.0.1" \
        --output /dev/null --write-out '%{http_code}' \
        "https://$EXPECTED_IP/accounts/login/")"
    [[ "$login_status" == "200" ]] || fail "HTTPS login page returned $login_status"

    health_status="$(curl --silent --show-error --max-time 15 \
        --resolve "$EXPECTED_IP:443:127.0.0.1" \
        --output /dev/null --write-out '%{http_code}' \
        "https://$EXPECTED_IP/_health/")"
    [[ "$health_status" == "404" ]] || fail "external /_health/ returned $health_status instead of 404"

    printf '\n-- certificate --\n'
    openssl x509 -in "$CERT_LIVE_DIR/fullchain.pem" \
        -noout -issuer -subject -dates -ext subjectAltName

    printf '\n-- host listeners --\n'
    ss -H -ltnp | awk '$4 ~ /:80$/ || $4 ~ /:443$/ || $4 ~ /:8766$/ || $4 ~ /:5432$/ {print}'
    if ss -H -ltn | awk '$4 ~ /:8766$/ {print $4}' | grep -Ev '^127\.0\.0\.1:8766$' | grep -q .; then
        fail "development port 8766 is not restricted to IPv4 loopback"
    fi
    if ss -H -ltn | awk '$4 ~ /:5432$/ {print}' | grep -q .; then
        fail "PostgreSQL is unexpectedly published on the host"
    fi

    printf '\n-- UFW final state --\n'
    ufw status verbose

    printf '\n-- renewal timer --\n'
    systemctl status eod-access001-certbot-renew.timer --no-pager
    systemctl list-timers eod-access001-certbot-renew.timer --no-pager

    local preview_after
    preview_after="$(capture_preview_state)"
    [[ "$preview_after" == "$PREVIEW_BEFORE" ]] || fail "preview container state changed"
    printf 'preview=UNTOUCHED\n'

    printf '\n-- controller pending state before confirmation --\n'
    "$CONTROLLER" status
}

confirm_exact_head() {
    section "CONFIRM EXACT HEAD"
    controller_command "confirm $RUN_ID $HEAD_SHA"
    CONTROLLER_PENDING=0
    "$CONTROLLER" status
}

main() {
    require_root
    parse_args "$@"
    verify_operator_gate

    for command in awk bash cp curl cut date docker dpkg grep head install ip openssl \
        python3 sed sha256sum sort ss systemctl tee ufw uname; do
        require_command "$command"
    done

    prepare_audit
    trap on_exit EXIT
    trap 'exit $?' ERR

    section "ACCESS-001 START"
    printf 'branch=%s\npr=%s\nhead=%s\nrun=%s\n' \
        "$EXPECTED_BRANCH" "$PR_NUMBER" "$HEAD_SHA" "$RUN_ID"

    print_inventory
    validate_inventory
    deploy_exact_head
    ensure_nginx
    open_required_firewall_ports
    ensure_certbot
    issue_certificate
    update_development_environment
    activate_tls_nginx
    install_renewal_contract
    verify_final_state
    confirm_exact_head

    SUCCESS=1
    section "ACCESS-001 ACTIVATION SUCCESS"
    printf 'exact_head=%s\n' "$HEAD_SHA"
    printf 'public_url=https://%s/\n' "$EXPECTED_IP"
    printf 'local_health=http://127.0.0.1:8766/_health/\n'
    printf 'external_health=404\n'
    printf 'preview=UNTOUCHED\n'
    printf 'audit_log=%s\n' "$LOG_FILE"
    printf 'merge_authorization=ABSENT\n'
}

main "$@"
