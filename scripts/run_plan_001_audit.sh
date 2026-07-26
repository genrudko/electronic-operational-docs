#!/usr/bin/env bash
set -Eeuo pipefail

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

# This runner is intentionally container-only. It must not be executed as a
# PR-controlled root host script. The prepared VPS command starts it inside the
# already deployed exact-SHA application image as the unprivileged image user.
[[ "${EUID}" -ne 0 ]] || fail "container runner must not execute as root"
[[ -f /app/manage.py ]] || fail "application image root /app is unavailable"
[[ -f /repo/scripts/plan_001_evidence_audit.py ]] || \
    fail "exact-SHA release is not mounted read-only at /repo"
[[ -d /audit ]] || fail "audit output mount /audit is unavailable"

: "${PLAN_001_PR_NUMBER:?PLAN_001_PR_NUMBER is required}"
: "${PLAN_001_HEAD_SHA:?PLAN_001_HEAD_SHA is required}"
: "${PLAN_001_TRUSTED_MAIN_HEAD:?PLAN_001_TRUSTED_MAIN_HEAD is required}"
: "${PLAN_001_ACCEPTED_APPLICATION_BASELINE:?PLAN_001_ACCEPTED_APPLICATION_BASELINE is required}"
: "${PLAN_001_IMAGE_REF:?PLAN_001_IMAGE_REF is required}"

[[ "$PLAN_001_PR_NUMBER" =~ ^[0-9]+$ ]] || fail "invalid PR number"
[[ "$PLAN_001_HEAD_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "invalid exact head SHA"
[[ "$PLAN_001_TRUSTED_MAIN_HEAD" =~ ^[0-9a-f]{40}$ ]] || \
    fail "invalid trusted main SHA"
[[ "$PLAN_001_ACCEPTED_APPLICATION_BASELINE" =~ ^[0-9a-f]{40}$ ]] || \
    fail "invalid accepted application baseline"
[[ "$PLAN_001_IMAGE_REF" == "eod-development-app:$PLAN_001_HEAD_SHA" ]] || \
    fail "image ref does not match exact head SHA"

umask 022
exec python /repo/scripts/plan_001_evidence_audit.py \
    --output-dir /audit/report \
    --pr-number "$PLAN_001_PR_NUMBER" \
    --head-sha "$PLAN_001_HEAD_SHA" \
    --trusted-main-head "$PLAN_001_TRUSTED_MAIN_HEAD" \
    --accepted-application-baseline "$PLAN_001_ACCEPTED_APPLICATION_BASELINE" \
    --image-ref "$PLAN_001_IMAGE_REF" \
    --repo-root /repo \
    --app-root /app
