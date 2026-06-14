#!/usr/bin/env bash
# trigger_emergency.sh — the demo "trigger".
#
# Peacetime data (mock_data/pm_agent/peacetime/) is always loaded. Turning the
# emergency ON merges mock_data/pm_agent/emergency/ records into the live
# dataset, so the AI monitor detects the new P0s / escalations on its next scan
# (<=20s) and surfaces emergency suggestions. Turning it OFF restores peacetime.
#
#   ./trigger_emergency.sh on       # inject the emergency + ask the AI to scan now
#   ./trigger_emergency.sh off      # back to peacetime
#   ./trigger_emergency.sh status   # show current state
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT/env.sh" 2>/dev/null || true
DATA_DIR="${PM_DATA_DIR:-$ROOT/mock_data/pm_agent}"
FLAG="$DATA_DIR/.emergency_active"
API="http://localhost:${API_PORT:-8100}"

case "${1:-status}" in
  on)
    : > "$FLAG"
    echo "🚨 EMERGENCY ON — emergency/ records merged into the live dataset."
    # Best-effort: ask the running backend to scan immediately so the suggestion
    # appears now instead of waiting for the next scheduler poll.
    if curl -fsS -X POST "$API/api/pm/autonomy/emergency" \
         -H 'Content-Type: application/json' -d '{"active":true}' >/dev/null 2>&1; then
      echo "   Backend scanned now — check the dashboard / Ask PM OS for the emergency advice."
    else
      echo "   (Backend not reachable; the scheduler will pick it up within ~20s once it is.)"
    fi
    ;;
  off)
    rm -f "$FLAG"
    curl -fsS -X POST "$API/api/pm/autonomy/emergency" \
      -H 'Content-Type: application/json' -d '{"active":false}' >/dev/null 2>&1 || true
    echo "✅ EMERGENCY OFF — restored peacetime data."
    ;;
  status)
    if [ -f "$FLAG" ]; then echo "emergency: ON"; else echo "emergency: OFF"; fi
    ;;
  *)
    echo "usage: $0 {on|off|status}"; exit 1 ;;
esac
