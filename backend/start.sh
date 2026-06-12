#!/bin/sh
# Production boot: migrations, then the API server.
# Railway's runtime execs the container command without a shell, so the
# `migrate && serve` sequencing must live here, not in railway.toml.
set -e

echo "BOOT: running migrations"
.venv/bin/alembic upgrade head
echo "BOOT: migrations done, starting uvicorn on port ${PORT:-8000}"
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
