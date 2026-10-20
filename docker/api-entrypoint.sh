#!/bin/sh
set -e

PORT="${PORT:-8000}"

mkdir -p /app/data/uploads /app/data/qdrant /app/data/hf-cache

if [ "$(id -u)" = "0" ]; then
    chown -R appuser:appuser /app/data
    if command -v setpriv >/dev/null 2>&1; then
        exec setpriv --reuid=1000 --regid=1000 --init-groups \
            uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 1 \
            --proxy-headers --forwarded-allow-ips '*'
    fi
fi

exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 1 \
    --proxy-headers --forwarded-allow-ips '*'
