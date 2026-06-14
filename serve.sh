#!/usr/bin/env bash
# serve.sh — start the backend the FRONTEND talks to.
# Starts: mock_server :8088 (internal tools) + api_server :8100 (frontend API).
# vLLM (:8000, the model) is started separately:  sg docker -c 'bash ~/hack/dock.sh vllm'
set -u
cd "$HOME/hack" || exit 1
source "$HOME/hack/env.sh"
mkdir -p logs

pkill -f 'uvicorn mock_server:app' 2>/dev/null
pkill -f 'uvicorn api_server:app'  2>/dev/null
sleep 1

echo "starting mock_server :8088 ..."
nohup uvicorn mock_server:app --host 0.0.0.0 --port 8088 > logs/mock.log 2>&1 &
echo "  pid $!"
echo "starting api_server  :${API_PORT:-8100} ..."
nohup uvicorn api_server:app  --host 0.0.0.0 --port "${API_PORT:-8100}" > logs/api.log 2>&1 &
echo "  pid $!"

sleep 3
echo "--- health ---"
curl -s "http://localhost:${API_PORT:-8100}/health"; echo
echo
echo "frontend API : http://$(hostname -I | awk '{print $1}'):${API_PORT:-8100}   (docs at /docs)"
echo "logs         : ~/hack/logs/{mock,api}.log   (tail -f to watch)"
echo "stop         : pkill -f 'uvicorn (mock_server|api_server):app'"
