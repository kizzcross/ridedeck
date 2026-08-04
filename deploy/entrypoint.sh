#!/usr/bin/env bash
set -Eeuo pipefail

echo "-----> waiting for postgres"
until python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2); \
sys.exit(0) if s.connect_ex((os.environ.get('POSTGRES_HOST','db'), \
int(os.environ.get('POSTGRES_PORT','5432')))) == 0 else sys.exit(1)" 2>/dev/null; do
  sleep 1
done

echo "-----> migrate"
python manage.py migrate --noinput

echo "-----> collectstatic"
python manage.py collectstatic --noinput 2>&1 | tail -1 || true

if [ "${DJANGO_SEED_ON_START:-false}" = "true" ]; then
  echo "-----> seed (if empty)"
  python manage.py seed_dev --if-empty || true
fi

exec "$@"
