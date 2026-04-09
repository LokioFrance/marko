#!/bin/sh
set -e

echo "==> Applying migrations..."
python manage.py migrate --noinput

echo "==> Starting gunicorn..."
exec gunicorn configProject.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-30}" \
    --access-logfile - \
    --error-logfile -
