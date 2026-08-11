#!/bin/sh
set -eu

require_equal() {
    name="$1"
    expected="$2"
    eval "actual=\${$name:-}"
    if [ "$actual" != "$expected" ]; then
        echo "Unsafe development configuration: $name must be '$expected', got '$actual'." >&2
        exit 1
    fi
}

require_nonempty() {
    name="$1"
    eval "actual=\${$name:-}"
    if [ -z "$actual" ]; then
        echo "Unsafe development configuration: $name must be set." >&2
        exit 1
    fi
}

require_equal EOD_DEPLOYMENT_MODE development
require_equal DJANGO_DEBUG 1
require_equal DB_ENGINE postgresql
require_equal POSTGRES_DB eod_development
require_equal POSTGRES_USER eod_development
require_equal POSTGRES_HOST db
require_equal POSTGRES_PORT 5432
require_equal EOD_DATABASE_PROFILE development
require_equal EOD_ALLOW_SQLITE_PATH_OVERRIDE 0
require_nonempty POSTGRES_PASSWORD
require_nonempty DJANGO_SECRET_KEY

if [ "$POSTGRES_PASSWORD" = "eod_local_password" ]; then
    echo "Unsafe development configuration: default PostgreSQL password is forbidden." >&2
    exit 1
fi

if [ "$DJANGO_SECRET_KEY" = "development-only-change-me" ]; then
    echo "Unsafe development configuration: default Django secret key is forbidden." >&2
    exit 1
fi

# The repository-local Development stack is intentionally disposable.  CI and
# a fresh local checkout may start it without a pre-provisioned demo credential.
# Generate a process-scoped random value in that case so post_migrate can create
# and reconcile the two Development demo principals and /_health/ can prove the
# real authentication path.  The value is never printed or persisted by this
# entrypoint; the Development-only login page is the deliberate presentation
# surface.  Trusted persistent VPS deployment uses a different host-owned
# entrypoint and must still receive EOD_DEMO_USER_PASSWORD from its host secret.
if [ -z "${EOD_DEMO_USER_PASSWORD:-}" ]; then
    EOD_DEMO_USER_PASSWORD="$(python -c 'import secrets; print("Dev-Aa1!" + secrets.token_urlsafe(32))')"
    export EOD_DEMO_USER_PASSWORD
fi

python manage.py check
python manage.py migrate --noinput

exec "$@"
