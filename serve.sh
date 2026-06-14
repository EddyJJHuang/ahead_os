#!/usr/bin/env bash
# serve.sh — start the backend the FRONTEND talks to.
# Starts: mock_server :8088 (internal tools) + api_server :8100 (frontend API).
# vLLM (the model) is started separately on the GB10: sg docker -c 'bash dock.sh vllm'
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
source "$ROOT/env.sh"
mkdir -p logs

pkill -f 'uvicorn mock_server:app' 2>/dev/null || true
pkill -f 'uvicorn api_server:app' 2>/dev/null || true
sleep 1

echo "starting mock_server :${MOCK_PORT} ..."
nohup uvicorn mock_server:app --host 0.0.0.0 --port "$MOCK_PORT" > logs/mock.log 2>&1 &
echo "  pid $!"

echo "starting api_server :${API_PORT} ..."
nohup uvicorn api_server:app --host 0.0.0.0 --port "$API_PORT" > logs/api.log 2>&1 &
echo "  pid $!"

sleep 3
echo "--- health ---"
curl -s "http://localhost:${API_PORT}/health" || echo "(api not ready yet)"
echo
echo
echo "frontend API : http://localhost:${API_PORT}  (docs at /docs)"
echo "web UI       : ./web.sh  →  http://localhost:${FRONTEND_PORT}"
echo "logs         : $ROOT/logs/{mock,api}.log"
echo "stop         : pkill -f 'uvicorn (mock_server|api_server):app'"
