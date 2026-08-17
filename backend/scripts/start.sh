#!/usr/bin/env bash
set -eo pipefail

echo "==> CampusOS Backend Container Entrypoint"
echo "==> Environment: ${ENVIRONMENT:-development}"
echo "==> Port: ${PORT:-8000}"

# Run Alembic migrations automatically if database is available
if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    echo "==> Executing Alembic database schema migrations..."
    alembic upgrade head || {
        echo "WARNING: Alembic migration failed or database unreachable. Check connection string."
        if [ "${ENVIRONMENT}" = "production" ]; then
            exit 1
        fi
    }
    echo "==> Database schema migration complete."
fi

# Automatically seed demo users in local development or demo environments
if [ "${ENVIRONMENT:-development}" = "development" ] || [ "${SEED_DEMO_DATA:-true}" = "true" ]; then
    echo "==> Seeding local demo users and initial testnet balances..."
    python3 -m app.scripts.seed_demo || {
        echo "NOTE: Demo seeding skipped or already initialized."
    }
fi

# Launch FastAPI application using Uvicorn
echo "==> Starting Uvicorn server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-4}" \
    --log-level "${LOG_LEVEL:-info}"
