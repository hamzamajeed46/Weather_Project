# docker/entrypoint.web.sh
#!/usr/bin/env bash
set -e

# Tiny wait for DB
./docker/wait-for-it.sh ${DB_HOST:-db}:${DB_PORT:-3306} --timeout=60 -- echo "DB is up"

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

# Optional: create a basic health endpoint if not present (Django url /health)
# Start Gunicorn
exec gunicorn weather_project.wsgi:application \
  --bind ${GUNICORN_BIND:-0.0.0.0:8000} \
  --workers ${GUNICORN_WORKERS:-3} \
  --timeout 120