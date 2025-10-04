#!/usr/bin/env bash
set -euo pipefail

# If DATABASE_HOST is set and DATABASE_ENGINE == postgresql, wait for Postgres
if [[ -n "${DATABASE_HOST:-}" ]] && [[ "${DATABASE_ENGINE:-}" == "postgresql" ]]; then
  echo "Waiting for Postgres at ${DATABASE_HOST}:${POSTGRES_PORT:-5432}..."
  # loop until nc reports port open
  until nc -z "${DATABASE_HOST}" "${POSTGRES_PORT:-5432}" >/dev/null 2>&1; do
    echo "Postgres is unavailable - sleeping"
    sleep 1
  done
  echo "Postgres is up"
fi

echo "Running makemigrations/migrate..."
python /Backend/code/manage.py makemigrations --noinput || true
python /Backend/code/manage.py migrate --noinput --verbosity=3

# Create superuser non-interactively using a small Python snippet that reads env vars
if [[ -n "${DJANGO_SUPERUSER:-}" ]] || [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]]; then
  # Prefer calling the bundled script which sets up DJANGO_SETTINGS_MODULE and handles updates.
  echo "Running create_superuser.py to create/update user from env..."
  if ! python /Backend/scripts/create_superuser.py; then
    echo "Warning: create_superuser.py failed, continuing" >&2
  fi
fi
fi

if [[ "${USE_GUNICORN:-0}" == "1" ]]; then
  echo "Starting gunicorn..."
  exec gunicorn --bind 0.0.0.0:${BACKEND_PORT:-8000} --workers ${GUNICORN_WORKERS:-3} configs.wsgi:application
else
  echo "Starting Django development server..."
  exec python /Backend/code/manage.py runserver 0.0.0.0:${BACKEND_PORT:-8000}
fi