#!/usr/bin/env bash
# ahead_os environment — source before running backend or frontend.

export PMOS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SSD_ROOT="${SSD_ROOT:-$PMOS_ROOT}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://localhost:8000/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-not-needed}"
export MODEL_ID="${MODEL_ID:-nemotron-super}"
export MOCK_BASE_URL="${MOCK_BASE_URL:-http://localhost:${MOCK_PORT:-8088}}"
export API_PORT="${API_PORT:-8100}"
export MOCK_PORT="${MOCK_PORT:-8088}"
export FRONTEND_PORT="${FRONTEND_PORT:-5173}"
export API_URL="http://localhost:${API_PORT}"
export VITE_API_URL="${VITE_API_URL:-$API_URL}"
export PATH="$HOME/.local/bin:$PATH"

if [ -f "$PMOS_ROOT/.venv/bin/activate" ]; then
  source "$PMOS_ROOT/.venv/bin/activate"
fi
