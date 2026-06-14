#!/usr/bin/env bash
# healthcheck.sh — One-shot end-to-end stack verification.
#
# Run this AFTER you've completed ON_SITE_PLAYBOOK Phase 1-6 to confirm the
# full stack is healthy. Prints a colored pass/fail summary plus latency.
#
# Usage:
#     bash healthcheck.sh
#     bash healthcheck.sh --quick    # skip slow checks (model warmup)
#
# Exit code: 0 if all critical checks pass, 1 otherwise.

set -u
QUICK=0
[ "${1:-}" = "--quick" ] && QUICK=1

# Colors (skip if not a tty)
if [ -t 1 ]; then
  G="\033[32m"; R="\033[31m"; Y="\033[33m"; B="\033[34m"; D="\033[0m"
else
  G=""; R=""; Y=""; B=""; D=""
fi

PASS=0; FAIL=0; WARN=0

check() {  # check <label> <cmd...>
  local label="$1"; shift
  local out
  if out=$("$@" 2>&1); then
    printf "  ${G}✓${D} %-40s\n" "$label"
    PASS=$((PASS+1))
    return 0
  else
    printf "  ${R}✗${D} %-40s\n    %s\n" "$label" "$(echo "$out" | head -2)"
    FAIL=$((FAIL+1))
    return 1
  fi
}

warn() {  # warn <label> <message>
  printf "  ${Y}!${D} %-40s %s\n" "$1" "${2:-}"
  WARN=$((WARN+1))
}

section() {
  printf "\n${B}== %s ==${D}\n" "$1"
}

echo "GB10 healthcheck — $(date '+%Y-%m-%d %H:%M:%S')"

# ---------------------------------------------------------------------------
section "Hardware"
# ---------------------------------------------------------------------------
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
  printf "  ${G}✓${D} arch = aarch64\n"; PASS=$((PASS+1))
else
  printf "  ${R}✗${D} arch = $ARCH (expected aarch64)\n"; FAIL=$((FAIL+1))
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  GPU=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -1)
  if [ -n "$GPU" ]; then
    printf "  ${G}✓${D} GPU: %s\n" "$GPU"; PASS=$((PASS+1))
  else
    printf "  ${R}✗${D} nvidia-smi runs but no GPU listed\n"; FAIL=$((FAIL+1))
  fi
else
  printf "  ${R}✗${D} nvidia-smi not found\n"; FAIL=$((FAIL+1))
fi

# ---------------------------------------------------------------------------
section "Docker"
# ---------------------------------------------------------------------------
check "docker daemon"   docker info -f '{{.OperatingSystem}}'
check "docker images present"  bash -c 'docker images --format "{{.Repository}}" | grep -q -E "(vllm|llama.cpp)"'

# Verify container can see GPU
if [ $QUICK -eq 0 ]; then
  if docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi >/dev/null 2>&1; then
    printf "  ${G}✓${D} container can see GPU\n"; PASS=$((PASS+1))
  else
    warn "container GPU access" "NVIDIA Container Toolkit may need configuring"
  fi
fi

# ---------------------------------------------------------------------------
section "Inference backend (:8000)"
# ---------------------------------------------------------------------------
if curl -sf -m 3 http://localhost:8000/v1/models -o /tmp/models.json; then
  MODEL_ID=$(python3 -c "import json; print(json.load(open('/tmp/models.json'))['data'][0]['id'])" 2>/dev/null || echo "?")
  printf "  ${G}✓${D} /v1/models reachable (model=%s)\n" "$MODEL_ID"; PASS=$((PASS+1))

  if [ $QUICK -eq 0 ]; then
    # Smoke test chat completion + measure latency
    T0=$(date +%s)
    if curl -sf -m 60 http://localhost:8000/v1/chat/completions \
         -H 'Content-Type: application/json' \
         -d "{\"model\":\"$MODEL_ID\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hi.\"}],\"max_tokens\":16}" \
         -o /tmp/chat.json; then
      T1=$(date +%s)
      DT=$((T1-T0))
      CONTENT=$(python3 -c "import json; print(json.load(open('/tmp/chat.json'))['choices'][0]['message']['content'][:60])" 2>/dev/null || echo "?")
      printf "  ${G}✓${D} chat completion ok (%ds) → %s\n" "$DT" "$CONTENT"; PASS=$((PASS+1))
    else
      printf "  ${R}✗${D} chat completion failed\n"; FAIL=$((FAIL+1))
    fi

    # Test tool calling
    TOOLS_TEST=$(curl -sf -m 30 http://localhost:8000/v1/chat/completions \
      -H 'Content-Type: application/json' \
      -d "{\"model\":\"$MODEL_ID\",\"messages\":[{\"role\":\"user\",\"content\":\"Look up alice@meridian.com\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"lookup_employee\",\"parameters\":{\"type\":\"object\",\"properties\":{\"email\":{\"type\":\"string\"}}}}}],\"tool_choice\":\"auto\",\"max_tokens\":128}" 2>/dev/null)
    if echo "$TOOLS_TEST" | python3 -c "import json, sys; d=json.load(sys.stdin); sys.exit(0 if d['choices'][0]['message'].get('tool_calls') else 1)" 2>/dev/null; then
      printf "  ${G}✓${D} tool_calls field populated\n"; PASS=$((PASS+1))
    else
      warn "tool_calls field empty" "Parser may not match; try ReAct fallback in agent.py"
    fi
  fi
else
  printf "  ${R}✗${D} /v1/models unreachable — vLLM not started?\n"; FAIL=$((FAIL+1))
fi

# ---------------------------------------------------------------------------
section "Mock tool server (:8088)"
# ---------------------------------------------------------------------------
if curl -sf -m 3 http://localhost:8088/health >/dev/null 2>&1; then
  printf "  ${G}✓${D} /health reachable\n"; PASS=$((PASS+1))
  check "lookup_employee" curl -sf "http://localhost:8088/employees/lookup?email=alice@meridian.com"
else
  warn "mock_server.py not running" "uvicorn mock_server:app --host 0.0.0.0 --port 8088 &"
fi

# ---------------------------------------------------------------------------
section "Data + RAG"
# ---------------------------------------------------------------------------
SSD=${SSD_ROOT:-/mnt/ssd/Hackathon}
[ -d /Volumes/SSD-3/Hackathon ] && SSD=/Volumes/SSD-3/Hackathon

check "SSD mounted"             test -d "$SSD"
check "company.db readable"     sqlite3 "$SSD/mock_data/analytics_agent/company.db" "SELECT COUNT(*) FROM orders;"
check "rag_index.faiss exists"  test -f "$SSD/rag_index.faiss"
check "rag_chunks.json exists"  test -f "$SSD/rag_chunks.json"

# ---------------------------------------------------------------------------
section "Python venv"
# ---------------------------------------------------------------------------
VENV=${VENV:-$HOME/hack/.venv}
if [ -d "$VENV" ]; then
  printf "  ${G}✓${D} venv at $VENV\n"; PASS=$((PASS+1))
  for mod in openai fastapi faiss onnxruntime requests; do
    if "$VENV/bin/python3" -c "import $mod" 2>/dev/null; then
      printf "  ${G}✓${D} import $mod\n"; PASS=$((PASS+1))
    else
      printf "  ${R}✗${D} import $mod\n"; FAIL=$((FAIL+1))
    fi
  done
else
  warn "venv missing" "python3.12 -m venv $VENV && pip install --no-index --find-links wheels/app -r requirements.app.txt"
fi

# ---------------------------------------------------------------------------
section "Summary"
# ---------------------------------------------------------------------------
printf "${G}pass=$PASS${D}  ${Y}warn=$WARN${D}  ${R}fail=$FAIL${D}\n"

if [ $FAIL -eq 0 ]; then
  printf "\n${G}ALL GOOD — demo away.${D}\n"
  exit 0
else
  printf "\n${R}NOT READY — fix the ✗ above before demoing.${D}\n"
  exit 1
fi
