#!/bin/sh
set -eu

if [ "${EOD_SKIP_STARTUP_TASKS:-0}" != "1" ]; then
    python manage.py check
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput --clear
fi

exec "$@"
