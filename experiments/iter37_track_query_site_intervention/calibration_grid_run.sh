#!/bin/bash
# Iteration-37 calibration grid: prefix-preserving replay for each frozen alpha.
exec > /var/log/sentinel-e37-calibration.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

UNIAD=/opt/sentinel-stack/UniAD
PATCH=/tmp/server_patch_intervention_iter37.py
FEEDER=/tmp/feeder_intervention_iter37.py
DIRECTION=/tmp/track_query_direction_iter37.json
MANIFEST=/tmp/prefix_manifest_calibration_iter37.json
PATCH_SHA256=$(sha256sum "$PATCH" | awk '{print $1}')
UNIAD_COMMIT=$(git -C "$UNIAD" rev-parse HEAD)
if [ -z "$PATCH_SHA256" ] || [ -z "$UNIAD_COMMIT" ]; then
  echo "missing patch hash or UniAD commit"
  exit 1
fi

run_alpha() {
  local alpha="$1"
  local port="$2"
  local encoded="${alpha/./p}"
  git -C "$UNIAD" checkout -- inference/server.py inference/runner.py || exit 1
  python3 "$PATCH" || exit 1
  rm -f "$UNIAD/sentinel_e37_calibration_alpha${encoded}.jsonl" \
    "$UNIAD/sentinel_e37_calibration_alpha${encoded}_gt.jsonl" \
    "$UNIAD/sentinel_e37_context.json"
  docker rm -f model >/dev/null 2>&1 || true
  docker run --name model --rm --gpus all \
    -v "$UNIAD":/model \
    -v /datasets/nuscenes-full:/datasets/nuscenes-full:ro \
    -w /model \
    --network host \
    -e PYTHONPATH=. \
    -e SENTINEL_E37_PREFIX_INTERVENTION=1 \
    -e SENTINEL_E37_ALPHA="$alpha" \
    -e SENTINEL_E37_DIRECTION=/model/track_query_direction_iter37.json \
    -e SENTINEL_E37_PATCH_SHA256="$PATCH_SHA256" \
    -e SENTINEL_E37_UNIAD_COMMIT="$UNIAD_COMMIT" \
    -e SENTINEL_E37_LOG="/model/sentinel_e37_calibration_alpha${encoded}.jsonl" \
    -e SENTINEL_E37_CONTEXT=/model/sentinel_e37_context.json \
    uniad:latest \
    python -u inference/server.py \
    --port "$port" \
    --config_path projects/configs/stage2_e2e/inference_e2e.py \
    --checkpoint_path ckpts/uniad_base_e2e.pth &

  echo "waiting for model server iter37 calibration alpha=${alpha}..."
  for _ in $(seq 1 120); do
    curl -sf "http://127.0.0.1:${port}/alive" >/dev/null 2>&1 && break
    sleep 5
  done
  curl -sf "http://127.0.0.1:${port}/alive" || { echo "SERVER_NEVER_ALIVE alpha=${alpha}"; exit 1; }
  cp "$FEEDER" "$UNIAD/feeder_intervention_iter37.py"
  cp "$DIRECTION" "$UNIAD/track_query_direction_iter37.json"
  cp "$MANIFEST" "$UNIAD/prefix_manifest_calibration_iter37.json"
  docker exec model python -u /model/feeder_intervention_iter37.py \
    --prefix-manifest /model/prefix_manifest_calibration_iter37.json \
    --alpha "$alpha" \
    --port "$port" \
    --out "/model/sentinel_e37_calibration_alpha${encoded}_gt.jsonl"
  docker rm -f model >/dev/null 2>&1 || true
  gzip -kf "$UNIAD/sentinel_e37_calibration_alpha${encoded}.jsonl" \
    "$UNIAD/sentinel_e37_calibration_alpha${encoded}_gt.jsonl"
  echo "E37_CALIBRATION_ALPHA_${encoded}_DONE $(date)"
}

run_alpha 0.00 9350
run_alpha 0.25 9351
run_alpha 0.50 9352
run_alpha 0.75 9353
run_alpha 1.00 9354
ls -la "$UNIAD"/sentinel_e37_calibration*.gz
echo "E37_CALIBRATION_DONE $(date)"
