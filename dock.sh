#!/usr/bin/env bash
# Docker helper for the GB10 hackathon.
# 'dell' is in the docker group but this shell predates that, so invoke as:
#     sg docker -c 'bash ~/hack/dock.sh <cmd>'
set -u
WORK="$HOME/hack"
MODELS="$WORK/models"
NAME=vllm

case "${1:-}" in
  load)
    for t in "$WORK"/images/*.tar.gz; do
      [ -f "$t" ] || continue
      echo "==> docker load $(basename "$t")"
      gunzip -c "$t" | docker load
    done
    echo "=== loaded images ==="
    docker images --format '{{.Repository}}:{{.Tag}} ({{.Size}})' | grep -v '<none>'
    echo "=== arch check (expect arm64) ==="
    for img in $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -v '<none>'); do
      printf '  %-48s arch=%s\n' "$img" "$(docker image inspect "$img" --format '{{.Architecture}}')"
    done
    ;;
  vllm)  # L0 ideal path: 120B NVFP4 on the NGC image
    docker rm -f "$NAME" 2>/dev/null
    docker run -d --name "$NAME" --gpus all --shm-size=16gb --network host \
      -v "$MODELS/nemotron-3-super-120b-nvfp4:/model" \
      -e VLLM_USE_FLASHINFER_MOE_FP4=1 \
      -e VLLM_FLASHINFER_MOE_BACKEND=latency \
      -e VLLM_MOE_PADDING_SIZE=512 \
      nvcr.io/nvidia/vllm:26.01-py3 \
      vllm serve /model \
        --served-model-name nemotron-super \
        --quantization modelopt \
        --tensor-parallel-size 1 \
        --kv-cache-dtype fp8 \
        --max-model-len 4096 \
        --gpu-memory-utilization 0.85 \
        --trust-remote-code \
        --mamba-ssm-cache-dtype float32 \
        --reasoning-parser deepseek_r1 \
        --enable-auto-tool-choice \
        --tool-call-parser qwen3_coder
    docker ps --filter "name=$NAME" --format '{{.Names}}  {{.Status}}'
    ;;
  vllm-noparser)  # fallback if logs show "unknown parser" — drop reasoning/tool parsers
    docker rm -f "$NAME" 2>/dev/null
    docker run -d --name "$NAME" --gpus all --shm-size=16gb --network host \
      -v "$MODELS/nemotron-3-super-120b-nvfp4:/model" \
      -e VLLM_USE_FLASHINFER_MOE_FP4=1 -e VLLM_FLASHINFER_MOE_BACKEND=latency -e VLLM_MOE_PADDING_SIZE=512 \
      nvcr.io/nvidia/vllm:26.01-py3 \
      vllm serve /model --served-model-name nemotron-super --quantization modelopt \
        --tensor-parallel-size 1 --kv-cache-dtype fp8 --max-model-len 4096 \
        --gpu-memory-utilization 0.85 --trust-remote-code \
        --mamba-ssm-cache-dtype float32
    docker ps --filter "name=$NAME" --format '{{.Names}}  {{.Status}}'
    ;;
  vllm30)  # L2: 30B FP8 — reliable path (pure FP8, no mixed-precision issue). Demo-ready flags.
    docker rm -f "$NAME" 2>/dev/null
    docker run -d --name "$NAME" --gpus all --shm-size=16gb --network host \
      -v "$MODELS/nemotron-3-nano-30b-fp8:/model" \
      nvcr.io/nvidia/vllm:26.01-py3 \
      vllm serve /model \
        --served-model-name nemotron-super \
        --tensor-parallel-size 1 \
        --kv-cache-dtype fp8 \
        --max-model-len 4096 \
        --gpu-memory-utilization 0.85 \
        --trust-remote-code \
        --mamba-ssm-cache-dtype float32 \
        --reasoning-parser deepseek_r1 \
        --enable-auto-tool-choice \
        --tool-call-parser qwen3_coder
    docker ps --filter "name=$NAME" --format '{{.Names}}  {{.Status}}'
    ;;
  logs)   docker logs -f "$NAME" ;;
  tail)   docker logs --tail "${2:-60}" "$NAME" 2>&1 ;;
  status) docker ps -a --filter "name=$NAME" --format '{{.Names}}  {{.Status}}' ;;
  down)   docker rm -f "$NAME" 2>/dev/null && echo "removed $NAME" ;;
  *) echo "usage: dock.sh {load|vllm|vllm-noparser|vllm30|logs|tail [N]|status|down}" ;;
esac
