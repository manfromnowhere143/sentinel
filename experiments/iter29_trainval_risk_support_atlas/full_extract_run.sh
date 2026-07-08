#!/bin/bash
# Iteration-29 full Stage 1 baseline extraction on the committed availability manifest.
exec > /var/log/sentinel-e29-extract.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py || exit 1
python3 /tmp/server_patch_stage1_iter29.py || exit 1

rm -f /opt/sentinel-stack/UniAD/sentinel_e29_stage1.jsonl \
  /opt/sentinel-stack/UniAD/sentinel_e29_stage1_gt.jsonl \
  /opt/sentinel-stack/UniAD/sentinel_e29_context.json
docker rm -f model >/dev/null 2>&1 || true

PORT=9292
docker run --name model --rm --gpus all \
  -v /opt/sentinel-stack/UniAD:/model \
  -v /datasets/nuscenes-full:/datasets/nuscenes-full:ro \
  -w /model \
  --network host \
  -e PYTHONPATH=. \
  -e SENTINEL_E29_STAGE1=1 \
  -e SENTINEL_E29_LOG=/model/sentinel_e29_stage1.jsonl \
  -e SENTINEL_E29_CONTEXT=/model/sentinel_e29_context.json \
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

cp /tmp/feeder_stage1_iter29.py /opt/sentinel-stack/UniAD/feeder_stage1_iter29.py
cp /tmp/availability_manifest_iter29.json /opt/sentinel-stack/UniAD/availability_manifest.json

docker exec model python -u /model/feeder_stage1_iter29.py \
  --manifest /model/availability_manifest.json \
  --mode full \
  --split all \
  --port $PORT \
  --out /model/sentinel_e29_stage1_gt.jsonl

docker rm -f model >/dev/null 2>&1 || true
gzip -kf /opt/sentinel-stack/UniAD/sentinel_e29_stage1.jsonl \
  /opt/sentinel-stack/UniAD/sentinel_e29_stage1_gt.jsonl
ls -la /opt/sentinel-stack/UniAD/sentinel_e29_stage1*.gz
echo "E29_STAGE1_EXTRACT_DONE $(date)"
