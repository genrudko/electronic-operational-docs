#!/bin/sh
set -eu

if [ "${EOD_SKIP_STARTUP_TASKS:-0}" != "1" ]; then
    if [ "${EOD_DEPLOYMENT_MODE:-development}" = "production" ]; then
        python /app/scripts/deployment_preflight.py
    else
        python manage.py check
    fi
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput --clear
fi

exec "$@"
