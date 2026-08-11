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

python manage.py check
python manage.py migrate --noinput

exec "$@"
