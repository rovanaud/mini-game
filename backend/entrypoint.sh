#!/usr/bin/env sh
set -e

: "${DB_HOST:=db}"
: "${DB_PORT:=5432}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until python -c "import socket; socket.create_connection(('${DB_HOST}', int('${DB_PORT}')), timeout=2).close()" 2>/dev/null; do
  sleep 1
done

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Daphne ASGI server on 0.0.0.0:8000..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
