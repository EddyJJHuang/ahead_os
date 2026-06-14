#!/usr/bin/env bash
# Live setup dashboard — runs in a terminal window on the monitor.
# Auto-refreshes every 3s. Ctrl-C to stop (does NOT affect the setup itself).
WORK="$HOME/hack"
LOG="$WORK/setup.log"
trap 'echo; echo "(dashboard closed — setup keeps running in background)"; exit 0' INT TERM
while true; do
  clear
  echo "=================================================================="
  echo "   GB10 HACKATHON  --  LIVE SETUP DASHBOARD      $(date '+%H:%M:%S')"
  echo "=================================================================="
  echo
  echo "  COPY TO NVMe  (~/hack):"
  for d in models images wheels mock_data repos; do
    if [ -e "$WORK/$d" ]; then
      sz=$(du -sh "$WORK/$d" 2>/dev/null | cut -f1)
      printf "    %-12s %s\n" "$d" "${sz:-?}"
    else
      printf "    %-12s (pending)\n" "$d"
    fi
  done
  printf "    %-12s %s\n" "models tgt" "~110G"
  echo
  echo "  DOCKER IMAGES LOADED:"
  docker images --format '    {{.Repository}}:{{.Tag}}  ({{.Size}})' 2>/dev/null \
    | grep -v '<none>' | head -6 || echo "    (none yet)"
  echo
  printf "  VENV:        "; [ -x "$WORK/.venv/bin/python" ] && "$WORK/.venv/bin/python" --version 2>&1 || echo "(pending)"
  printf "  vLLM :8000   "; curl -sf -m 2 http://localhost:8000/v1/models >/dev/null 2>&1 && echo "UP" || echo "down"
  printf "  MOCK :8088   "; curl -sf -m 2 http://localhost:8088/health   >/dev/null 2>&1 && echo "UP" || echo "down"
  echo
  echo "  ---- setup.log (recent) ------------------------------------------"
  tail -n 14 "$LOG" 2>/dev/null | sed 's/^/  /'
  echo "=================================================================="
  echo "  auto-refresh 3s | Ctrl-C closes this view (setup keeps running)"
  sleep 3
done
