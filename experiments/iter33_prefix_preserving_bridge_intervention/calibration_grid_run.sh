#!/bin/bash
# Iteration-33 calibration grid: prefix-preserving replay for each frozen alpha.
exec > /var/log/sentinel-e33-calibration.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

UNIAD=/opt/sentinel-stack/UniAD
PATCH=/tmp/server_patch_intervention_iter33.py
FEEDER=/tmp/feeder_intervention_iter33.py
DIRECTION=/tmp/iter33_direction.json
MANIFEST=/tmp/prefix_manifest_calibration_iter33.json

run_alpha() {
  local alpha="$1"
  local port="$2"
  local encoded="${alpha/./p}"
  git -C "$UNIAD" checkout -- inference/server.py inference/runner.py || exit 1
  python3 "$PATCH" || exit 1
  rm -f "$UNIAD/sentinel_e33_calibration_alpha${encoded}.jsonl" \
    "$UNIAD/sentinel_e33_calibration_alpha${encoded}_gt.jsonl" \
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
    -e SENTINEL_E33_LOG="/model/sentinel_e33_calibration_alpha${encoded}.jsonl" \
    -e SENTINEL_E33_CONTEXT=/model/sentinel_e33_context.json \
    uniad:latest \
    python -u inference/server.py \
    --port "$port" \
    --config_path projects/configs/stage2_e2e/inference_e2e.py \
    --checkpoint_path ckpts/uniad_base_e2e.pth &

  echo "waiting for model server iter33 calibration alpha=${alpha}..."
  for _ in $(seq 1 120); do
    curl -sf "http://127.0.0.1:${port}/alive" >/dev/null 2>&1 && break
    sleep 5
  done
  curl -sf "http://127.0.0.1:${port}/alive" || { echo "SERVER_NEVER_ALIVE alpha=${alpha}"; exit 1; }
  cp "$FEEDER" "$UNIAD/feeder_intervention_iter33.py"
  cp "$DIRECTION" "$UNIAD/iter33_direction.json"
  cp "$MANIFEST" "$UNIAD/prefix_manifest_calibration_iter33.json"
  docker exec model python -u /model/feeder_intervention_iter33.py \
    --prefix-manifest /model/prefix_manifest_calibration_iter33.json \
    --alpha "$alpha" \
    --port "$port" \
    --out "/model/sentinel_e33_calibration_alpha${encoded}_gt.jsonl"
  docker rm -f model >/dev/null 2>&1 || true
  gzip -kf "$UNIAD/sentinel_e33_calibration_alpha${encoded}.jsonl" \
    "$UNIAD/sentinel_e33_calibration_alpha${encoded}_gt.jsonl"
  echo "E33_CALIBRATION_ALPHA_${encoded}_DONE $(date)"
}

run_alpha 0.00 9350
run_alpha 0.25 9351
run_alpha 0.50 9352
run_alpha 0.75 9353
run_alpha 1.00 9354
ls -la "$UNIAD"/sentinel_e33_calibration*.gz
echo "E33_CALIBRATION_DONE $(date)"
