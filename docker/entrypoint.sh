#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

exec "$@"
