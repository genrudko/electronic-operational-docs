#!/bin/sh
set -eu
python manage.py check
python manage.py collectstatic --noinput --clear
exec "$@"
