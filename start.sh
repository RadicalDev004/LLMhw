#!/bin/bash
set -e

# Extract host and port from DATABASE_URL
HOST_PORT=$(echo "$DATABASE_URL" | sed -e 's/^.*@//' -e 's#/.*##')

# Split host and port
if [[ "$HOST_PORT" == *:* ]]; then
  DB_HOST=$(echo "$HOST_PORT" | cut -d: -f1)
  DB_PORT=$(echo "$HOST_PORT" | cut -d: -f2)
else
  DB_HOST="$HOST_PORT"
  DB_PORT="5432"
fi

PORT="${PORT:-5000}"

echo "[start.sh] Waiting for $DB_HOST:$DB_PORT..."
echo "[start.sh] Starting app on port $PORT"
./wait-for-it.sh "$DB_HOST" "$DB_PORT" -- gunicorn -w 4 -b 0.0.0.0:$PORT main:app
