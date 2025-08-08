#!/bin/sh

HOST="$1"
PORT="$2"
shift 3

echo "Waiting for $HOST:$PORT..."

while ! nc -z "$HOST" "$PORT"; do
  sleep 1
done

echo "$HOST:$PORT is up — launching app"
echo "Executing command: $@"
exec "$@"
