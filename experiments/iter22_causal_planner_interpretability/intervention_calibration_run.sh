#!/bin/bash
# Iteration-22 Stage 1 calibration-grid intervention replay.
# Requires /tmp/server_patch_stage1.py, /tmp/feeder_stage1.py, /tmp/split_manifest.json, and
# /opt/sentinel-stack/UniAD/sentinel_e22_direction.json from the committed analysis step.
exec > /var/log/sentinel-e22-calibration.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

DIRECTION_JSON=${DIRECTION_JSON:-/opt/sentinel-stack/UniAD/sentinel_e22_direction.json}
test -f "$DIRECTION_JSON" || { echo "MISSING_DIRECTION_JSON $DIRECTION_JSON"; exit 1; }

cp /tmp/feeder_stage1.py /opt/sentinel-stack/UniAD/feeder_stage1.py
cp /tmp/split_manifest.json /opt/sentinel-stack/UniAD/split_manifest.json
cp "$DIRECTION_JSON" /opt/sentinel-stack/UniAD/sentinel_e22_direction.json

for ALPHA in 0.0 0.25 0.5 1.0 2.0; do
  TAG=$(echo "$ALPHA" | tr . p)
  LOG_JSON="/model/sentinel_e22_calibration_alpha_${TAG}.jsonl"
  GT_JSON="/model/sentinel_e22_calibration_alpha_${TAG}_gt.jsonl"
  rm -f "/opt/sentinel-stack/UniAD/sentinel_e22_calibration_alpha_${TAG}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e22_calibration_alpha_${TAG}_gt.jsonl"
  docker rm -f model >/dev/null 2>&1

  git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py || exit 1
  python3 /tmp/server_patch_stage1.py || exit 1

  PORT=9100
  docker run --name model --rm --gpus all \
    -v /opt/sentinel-stack/UniAD:/model \
    -v /datasets/nuscenes:/datasets/nuscenes:ro \
    -w /model \
    --network host \
    -e PYTHONPATH=. \
    -e SENTINEL_E22_STAGE1=1 \
    -e SENTINEL_E22_LOG="$LOG_JSON" \
    -e SENTINEL_E22_DIRECTION_JSON=/model/sentinel_e22_direction.json \
    -e SENTINEL_E22_ALPHA="$ALPHA" \
    uniad:latest \
    python -u inference/server.py \
    --port $PORT \
    --config_path projects/configs/stage2_e2e/inference_e2e.py \
    --checkpoint_path ckpts/uniad_base_e2e.pth &

  echo "waiting for model server alpha=$ALPHA..."
  for _ in $(seq 1 120); do
    curl -sf "http://127.0.0.1:$PORT/alive" >/dev/null 2>&1 && break
    sleep 5
  done
  curl -sf "http://127.0.0.1:$PORT/alive" || { echo "SERVER_NEVER_ALIVE alpha=$ALPHA"; exit 1; }

  docker exec model python -u /model/feeder_stage1.py \
    --manifest /model/split_manifest.json \
    --split calibration \
    --port $PORT \
    --out "$GT_JSON"

  docker rm -f model >/dev/null 2>&1
  gzip -kf "/opt/sentinel-stack/UniAD/sentinel_e22_calibration_alpha_${TAG}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e22_calibration_alpha_${TAG}_gt.jsonl"
  echo "E22_CALIBRATION_ALPHA_DONE $ALPHA $(date)"
done

ls -la /opt/sentinel-stack/UniAD/sentinel_e22_calibration_alpha_*.gz
echo "E22_CALIBRATION_GRID_DONE $(date)"
