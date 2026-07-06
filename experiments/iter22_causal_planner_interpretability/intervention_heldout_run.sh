#!/bin/bash
# Iteration-22 Stage 1 heldout replay for the single calibration-selected alpha.
# E22_ALPHA must be set by the committed calibration analysis; do not sweep heldout.
exec > /var/log/sentinel-e22-heldout.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

test -n "$E22_ALPHA" || { echo "MISSING_E22_ALPHA"; exit 1; }
DIRECTION_JSON=${DIRECTION_JSON:-/opt/sentinel-stack/UniAD/sentinel_e22_direction.json}
test -f "$DIRECTION_JSON" || { echo "MISSING_DIRECTION_JSON $DIRECTION_JSON"; exit 1; }

cp /tmp/feeder_stage1.py /opt/sentinel-stack/UniAD/feeder_stage1.py
cp /tmp/split_manifest.json /opt/sentinel-stack/UniAD/split_manifest.json
cp "$DIRECTION_JSON" /opt/sentinel-stack/UniAD/sentinel_e22_direction.json

TAG=$(echo "$E22_ALPHA" | tr . p)
rm -f "/opt/sentinel-stack/UniAD/sentinel_e22_heldout_alpha_${TAG}.jsonl" \
  "/opt/sentinel-stack/UniAD/sentinel_e22_heldout_alpha_${TAG}_gt.jsonl"
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
  -e SENTINEL_E22_LOG="/model/sentinel_e22_heldout_alpha_${TAG}.jsonl" \
  -e SENTINEL_E22_DIRECTION_JSON=/model/sentinel_e22_direction.json \
  -e SENTINEL_E22_ALPHA="$E22_ALPHA" \
  uniad:latest \
  python -u inference/server.py \
  --port $PORT \
  --config_path projects/configs/stage2_e2e/inference_e2e.py \
  --checkpoint_path ckpts/uniad_base_e2e.pth &

echo "waiting for model server heldout alpha=$E22_ALPHA..."
for _ in $(seq 1 120); do
  curl -sf "http://127.0.0.1:$PORT/alive" >/dev/null 2>&1 && break
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/alive" || { echo "SERVER_NEVER_ALIVE"; exit 1; }

docker exec model python -u /model/feeder_stage1.py \
  --manifest /model/split_manifest.json \
  --split heldout \
  --port $PORT \
  --out "/model/sentinel_e22_heldout_alpha_${TAG}_gt.jsonl"

docker rm -f model >/dev/null 2>&1
gzip -kf "/opt/sentinel-stack/UniAD/sentinel_e22_heldout_alpha_${TAG}.jsonl" \
  "/opt/sentinel-stack/UniAD/sentinel_e22_heldout_alpha_${TAG}_gt.jsonl"
ls -la "/opt/sentinel-stack/UniAD/sentinel_e22_heldout_alpha_${TAG}"*.gz
echo "E22_HELDOUT_ALPHA_DONE $E22_ALPHA $(date)"
