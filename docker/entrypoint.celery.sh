# docker/entrypoint.celery.sh
#!/usr/bin/env bash
set -e

./docker/wait-for-it.sh ${DB_HOST:-db}:${DB_PORT:-3306} --timeout=60 -- echo "DB is up"
./docker/wait-for-it.sh redis:6379 --timeout=60 -- echo "Redis is up"

python manage.py migrate --noinput || true

if [ "$1" = "worker" ]; then
  exec celery -A weather_project worker --loglevel=info --pool=solo
elif [ "$1" = "beat" ]; then
  mkdir -p /app/celerybeat
  exec celery -A weather_project beat --loglevel=info --schedule=/app/celerybeat/celerybeat-schedule
else
  echo "Unknown celery role: $1" && exit 2
fi