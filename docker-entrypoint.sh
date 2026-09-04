#!/bin/sh
# Waits for the database to accept connections, then runs migrations
# before handing off to the container's main command.
set -e

if [ "$DATABASE_ENGINE" = "django.db.backends.mysql" ]; then
    echo "Waiting for database at $DATABASE_HOST:$DATABASE_PORT..."
    python - << 'PYEOF'
import os
import socket
import time

host = os.environ.get("DATABASE_HOST", "db")
port = int(os.environ.get("DATABASE_PORT", "3306"))

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit(f"Database at {host}:{port} never became available")
PYEOF
fi

python manage.py migrate --noinput

exec "$@"
