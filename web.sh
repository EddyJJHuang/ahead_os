#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/env.sh"

cd "$PMOS_ROOT/frontend"

if [ ! -d node_modules ]; then
  echo "Installing frontend dependencies…"
  npm install
fi

echo "Starting Local PM OS web UI"
echo "  API target:  $VITE_API_URL"
echo "  Frontend:    http://localhost:${FRONTEND_PORT}"
echo ""
echo "Ensure backend is running: bash serve.sh  (on GB10)"
echo ""

VITE_API_URL="$VITE_API_URL" npm run dev -- --port "$FRONTEND_PORT" --host
