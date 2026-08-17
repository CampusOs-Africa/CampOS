#!/usr/bin/env bash
set -eo pipefail

echo "==> CampusOS Next.js Frontend Container Entrypoint"
echo "==> Environment: ${NODE_ENV:-production}"
echo "==> Port: ${PORT:-3000}"
echo "==> API URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}"

if [ -f "server.js" ]; then
    echo "==> Starting Next.js standalone server..."
    exec node server.js
else
    echo "==> Starting Next.js production server..."
    exec npm run start
fi
