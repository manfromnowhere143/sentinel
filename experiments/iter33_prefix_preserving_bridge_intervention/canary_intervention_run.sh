#!/bin/bash
# Iteration-33 S0 canary: prefix-preserving repeats at alpha 0.00 and 0.50.
exec > /var/log/sentinel-e33-canary.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

UNIAD=/opt/sentinel-stack/UniAD
PATCH=/tmp/server_patch_intervention_iter33.py
FEEDER=/tmp/feeder_intervention_iter33.py
DIRECTION=/tmp/iter33_direction.json
MANIFEST=/tmp/prefix_manifest_canary_iter33.json

run_one() {
  local alpha="$1"
  local tag="$2"
  local port="$3"
  local encoded="${alpha/./p}"
  git -C "$UNIAD" checkout -- inference/server.py inference/runner.py || exit 1
  python3 "$PATCH" || exit 1
  rm -f "$UNIAD/sentinel_e33_canary_alpha${encoded}_${tag}.jsonl" \
    "$UNIAD/sentinel_e33_canary_alpha${encoded}_${tag}_gt.jsonl" \
    "$UNIAD/sentinel_e33_context.json"
  docker rm -f model >/dev/null 2>&1 || true
  docker run --name model --rm --gpus all \
    -v "$UNIAD":/model \
    -v /datasets/nuscenes-full:/datasets/nuscenes-full:ro \
    -w /model \
    --network host \
    -e PYTHONPATH=. \
    -e SENTINEL_E33_PREFIX_INTERVENTION=1 \
    -e SENTINEL_E33_ALPHA="$alpha" \
    -e SENTINEL_E33_DIRECTION=/model/iter33_direction.json \
    -e SENTINEL_E33_LOG="/model/sentinel_e33_canary_alpha${encoded}_${tag}.jsonl" \
    -e SENTINEL_E33_CONTEXT=/model/sentinel_e33_context.json \
    uniad:latest \
    python -u inference/server.py \
    --port "$port" \
    --config_path projects/configs/stage2_e2e/inference_e2e.py \
    --checkpoint_path ckpts/uniad_base_e2e.pth &

  echo "waiting for model server iter33 canary alpha=${alpha} tag=${tag}..."
  for _ in $(seq 1 120); do
    curl -sf "http://127.0.0.1:${port}/alive" >/dev/null 2>&1 && break
    sleep 5
  done
  curl -sf "http://127.0.0.1:${port}/alive" || { echo "SERVER_NEVER_ALIVE alpha=${alpha} tag=${tag}"; exit 1; }
  cp "$FEEDER" "$UNIAD/feeder_intervention_iter33.py"
  cp "$DIRECTION" "$UNIAD/iter33_direction.json"
  cp "$MANIFEST" "$UNIAD/prefix_manifest_canary_iter33.json"
  docker exec model python -u /model/feeder_intervention_iter33.py \
    --prefix-manifest /model/prefix_manifest_canary_iter33.json \
    --alpha "$alpha" \
    --port "$port" \
    --out "/model/sentinel_e33_canary_alpha${encoded}_${tag}_gt.jsonl"
  docker rm -f model >/dev/null 2>&1 || true
  gzip -kf "$UNIAD/sentinel_e33_canary_alpha${encoded}_${tag}.jsonl" \
    "$UNIAD/sentinel_e33_canary_alpha${encoded}_${tag}_gt.jsonl"
  echo "E33_CANARY_ALPHA_${encoded}_${tag}_DONE $(date)"
}

run_one 0.00 a 9340
run_one 0.00 b 9341
run_one 0.50 a 9342
run_one 0.50 b 9343
ls -la "$UNIAD"/sentinel_e33_canary*.gz
echo "E33_CANARY_DONE $(date)"
