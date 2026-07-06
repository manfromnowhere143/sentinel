#!/bin/bash
# Iteration-22 Stage 1 baseline extraction on the committed non-evaluation manifest.
# This script is pre-run infrastructure only until explicitly launched on sentinel-gpu.
exec > /var/log/sentinel-e22-extract.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py || exit 1
python3 /tmp/server_patch_stage1.py || exit 1

rm -f /opt/sentinel-stack/UniAD/sentinel_e22_stage1.jsonl \
  /opt/sentinel-stack/UniAD/sentinel_e22_stage1_gt.jsonl
docker rm -f model >/dev/null 2>&1

PORT=9100
docker run --name model --rm --gpus all \
  -v /opt/sentinel-stack/UniAD:/model \
  -v /datasets/nuscenes:/datasets/nuscenes:ro \
  -w /model \
  --network host \
  -e PYTHONPATH=. \
  -e SENTINEL_E22_STAGE1=1 \
  -e SENTINEL_E22_LOG=/model/sentinel_e22_stage1.jsonl \
  uniad:latest \
  python -u inference/server.py \
  --port $PORT \
  --config_path projects/configs/stage2_e2e/inference_e2e.py \
  --checkpoint_path ckpts/uniad_base_e2e.pth &

echo "waiting for model server..."
for _ in $(seq 1 120); do
  curl -sf "http://127.0.0.1:$PORT/alive" >/dev/null 2>&1 && break
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/alive" || { echo "SERVER_NEVER_ALIVE"; exit 1; }
echo "server alive; copying feeder and manifest"

cp /tmp/feeder_stage1.py /opt/sentinel-stack/UniAD/feeder_stage1.py
cp /tmp/split_manifest.json /opt/sentinel-stack/UniAD/split_manifest.json

docker exec model python -u /model/feeder_stage1.py \
  --manifest /model/split_manifest.json \
  --split all \
  --port $PORT \
  --out /model/sentinel_e22_stage1_gt.jsonl

docker rm -f model >/dev/null 2>&1
gzip -kf /opt/sentinel-stack/UniAD/sentinel_e22_stage1.jsonl \
  /opt/sentinel-stack/UniAD/sentinel_e22_stage1_gt.jsonl
ls -la /opt/sentinel-stack/UniAD/sentinel_e22_stage1*.gz
echo "E22_STAGE1_EXTRACT_DONE $(date)"
