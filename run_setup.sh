#!/usr/bin/env bash
# Master background setup: copy bundle SSD->NVMe, docker load, build venv.
# Routes verbose output to side logs; milestones go to setup.log (the dashboard tails it).
WORK="$HOME/hack"
SSD="/media/dell/SSD-3/Hackathon"
LOG="$WORK/setup.log"
ILOG="$WORK/images_load.log"
VLOG="$WORK/venv_install.log"
RLOG="$WORK/repos_extract.log"
log(){ echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }
cd "$WORK" || exit 1

log "================ run_setup START ================"

# ---- Sequential: small/medium assets first, so docker-load + venv can run DURING the big models copy ----
for d in mock_data wheels; do
  log "copy $d ..."
  rsync -a "$SSD/$d/" "$WORK/$d/" && log "copy $d done ($(du -sh "$WORK/$d" 2>/dev/null|cut -f1))" || log "copy $d FAILED"
done
log "copy repos.tar.gz ..."
rsync -a "$SSD/repos.tar.gz" "$WORK/repos.tar.gz" && log "repos.tar.gz copied" || log "repos.tar.gz FAILED"
log "copy images (~19GB) ..."
rsync -a "$SSD/images/" "$WORK/images/" && log "images copied" || log "images FAILED"

log "---- parallel phase: models copy || docker load || venv || repos extract ----"

# (1) MODELS — the long pole (SSD-bound)
(
  log "[models] starting ~110GB copy SSD->NVMe ..."
  rsync -a "$SSD/models/" "$WORK/models/" \
    && log "[models] COPY COMPLETE ($(du -sh "$WORK/models" 2>/dev/null|cut -f1))" \
    || log "[models] COPY FAILED"
) & P_MODELS=$!

# (2) DOCKER LOAD — NVMe-bound (won't contend with SSD models copy). NGC vLLM image first.
(
  : > "$ILOG"
  ng="$WORK/images/nvcr.io_nvidia_vllm_26.01-py3.tar.gz"
  if [ -f "$ng" ]; then
    log "[docker] loading NGC vLLM (priority) ..."
    gunzip -c "$ng" | docker load >>"$ILOG" 2>&1 && log "[docker] NGC vLLM loaded" || log "[docker] NGC vLLM FAILED"
  fi
  for t in "$WORK"/images/*.tar.gz; do
    [ "$t" = "$ng" ] && continue
    [ -f "$t" ] || continue
    b=$(basename "$t"); log "[docker] loading $b ..."
    gunzip -c "$t" | docker load >>"$ILOG" 2>&1 && log "[docker] loaded $b" || log "[docker] FAILED $b"
  done
  for img in $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -v '<none>'); do
    a=$(docker image inspect "$img" --format '{{.Architecture}}' 2>/dev/null)
    log "[docker] $img -> arch=$a"
  done
) & P_DOCKER=$!

# (3) REPOS extract (NVMe)
(
  : > "$RLOG"
  if [ -f "$WORK/repos.tar.gz" ]; then
    log "[repos] extracting ..."
    tar -xzf "$WORK/repos.tar.gz" -C "$WORK" >>"$RLOG" 2>&1 \
      && log "[repos] done: $(ls "$WORK/repos" 2>/dev/null|tr '\n' ' ')" \
      || log "[repos] extract FAILED"
  fi
) & P_REPOS=$!

# (4) VENV + offline deps (needs wheels copied above; NVMe-bound)
(
  : > "$VLOG"
  log "[venv] creating .venv ..."
  { python3.12 -m venv "$WORK/.venv" || python3 -m venv "$WORK/.venv"; } >>"$VLOG" 2>&1
  REQ="$SSD/download/requirements.app.txt"
  log "[venv] pip install --no-index from wheels/app ..."
  "$WORK/.venv/bin/pip" install --no-index --find-links "$WORK/wheels/app" -r "$REQ" >>"$VLOG" 2>&1 \
     && log "[venv] app deps installed" || log "[venv] pip had errors (see venv_install.log)"
  "$WORK/.venv/bin/python" -c "import openai,fastapi,faiss,onnxruntime,requests;print('imports ok')" >>"$VLOG" 2>&1 \
     && log "[venv] key imports OK" || log "[venv] import check FAILED (see venv_install.log)"
) & P_VENV=$!

# (5) uv -> ~/.local/bin (no sudo; optional, only for OpenShell full-stack path)
(
  mkdir -p "$HOME/.local/bin"
  tar -C /tmp -xzf "$SSD/bin/uv-aarch64-unknown-linux-gnu.tar.gz" 2>/dev/null
  uvb=$(find /tmp -maxdepth 3 -type f -name uv 2>/dev/null | head -1)
  [ -n "$uvb" ] && install "$uvb" "$HOME/.local/bin/uv" 2>/dev/null \
    && log "[uv] installed: $("$HOME/.local/bin/uv" --version 2>/dev/null)" || log "[uv] skipped"
) & P_UV=$!

wait "$P_MODELS" "$P_DOCKER" "$P_REPOS" "$P_VENV" "$P_UV"

log "---- SUMMARY ----"
log "models : $(du -sh "$WORK/models" 2>/dev/null|cut -f1)"
log "images : $(docker images --format '{{.Repository}}:{{.Tag}}'|grep -v '<none>'|tr '\n' ' ')"
log "venv   : $("$WORK/.venv/bin/python" --version 2>/dev/null)"
log "repos  : $(ls "$WORK/repos" 2>/dev/null|tr '\n' ' ')"
log "================ run_setup DONE ================"
