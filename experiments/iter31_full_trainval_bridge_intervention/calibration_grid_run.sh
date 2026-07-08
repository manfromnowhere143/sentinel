#!/bin/bash
# Iteration-31 calibration grid. Runs each frozen alpha once on the calibration row manifest.
exec > /var/log/sentinel-e31-calibration.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

run_alpha() {
  local alpha="$1"
  local port="$2"
  local encoded="${alpha/./p}"
  git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py || exit 1
  python3 /tmp/server_patch_intervention_iter31.py || exit 1
  rm -f "/opt/sentinel-stack/UniAD/sentinel_e31_calibration_alpha${encoded}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e31_calibration_alpha${encoded}_gt.jsonl" \
    /opt/sentinel-stack/UniAD/sentinel_e31_context.json
  docker rm -f model >/dev/null 2>&1 || true
  docker run --name model --rm --gpus all \
    -v /opt/sentinel-stack/UniAD:/model \
    -v /datasets/nuscenes-full:/datasets/nuscenes-full:ro \
    -w /model \
    --network host \
    -e PYTHONPATH=. \
    -e SENTINEL_E31_INTERVENTION=1 \
    -e SENTINEL_E31_ALPHA="$alpha" \
    -e SENTINEL_E31_DIRECTION=/model/iter31_direction.json \
    -e SENTINEL_E31_LOG="/model/sentinel_e31_calibration_alpha${encoded}.jsonl" \
    -e SENTINEL_E31_CONTEXT=/model/sentinel_e31_context.json \
    uniad:latest \
    python -u inference/server.py \
    --port "$port" \
    --config_path projects/configs/stage2_e2e/inference_e2e.py \
    --checkpoint_path ckpts/uniad_base_e2e.pth &

  echo "waiting for model server alpha=${alpha}..."
  for _ in $(seq 1 120); do
    curl -sf "http://127.0.0.1:${port}/alive" >/dev/null 2>&1 && break
    sleep 5
  done
  curl -sf "http://127.0.0.1:${port}/alive" || { echo "SERVER_NEVER_ALIVE alpha=${alpha}"; exit 1; }
  cp /tmp/feeder_intervention_iter31.py /opt/sentinel-stack/UniAD/feeder_intervention_iter31.py
  cp /tmp/iter31_direction.json /opt/sentinel-stack/UniAD/iter31_direction.json
  cp /tmp/replay_manifest_calibration_iter31.json /opt/sentinel-stack/UniAD/replay_manifest_calibration.json
  docker exec model python -u /model/feeder_intervention_iter31.py \
    --row-manifest /model/replay_manifest_calibration.json \
    --alpha "$alpha" \
    --port "$port" \
    --out "/model/sentinel_e31_calibration_alpha${encoded}_gt.jsonl"
  docker rm -f model >/dev/null 2>&1 || true
  gzip -kf "/opt/sentinel-stack/UniAD/sentinel_e31_calibration_alpha${encoded}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e31_calibration_alpha${encoded}_gt.jsonl"
  echo "E31_CALIBRATION_ALPHA_${encoded}_DONE $(date)"
}

run_alpha 0.00 9320
run_alpha 0.25 9321
run_alpha 0.50 9322
run_alpha 0.75 9323
run_alpha 1.00 9324
ls -la /opt/sentinel-stack/UniAD/sentinel_e31_calibration*.gz
echo "E31_CALIBRATION_DONE $(date)"
