#!/usr/bin/env bash
set -e

echo "Waiting for Postgres at ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."
until python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2); \
sys.exit(0) if s.connect_ex((os.environ.get('POSTGRES_HOST','postgres'), \
int(os.environ.get('POSTGRES_PORT','5432')))) == 0 else sys.exit(1)" 2>/dev/null; do
  sleep 1
done
echo "Postgres is up."

python manage.py migrate --noinput

if [ "${DJANGO_SEED_ON_START:-false}" = "true" ]; then
  python manage.py seed_dev --if-empty || true
fi

exec "$@"
