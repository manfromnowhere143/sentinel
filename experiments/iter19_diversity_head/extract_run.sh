#!/bin/bash
# Iteration-19 Stage 1b: extraction run. Standalone model container (compose's model block +
# a datasets mount), patched for conditioning dumps; the feeder drives it with real keyframes.
exec > /var/log/sentinel-extract.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py \
  projects/mmdet3d_plugin/uniad/dense_heads/planning_head.py || exit 1
python3 /tmp/server_patch_extract.py || exit 1

rm -f /opt/sentinel-stack/UniAD/sentinel_extract.jsonl /opt/sentinel-stack/UniAD/sentinel_extract_gt.jsonl
docker rm -f model >/dev/null 2>&1

PORT=9100
docker run --name model --rm --gpus all \
  -v /opt/sentinel-stack/UniAD:/model \
  -v /datasets/nuscenes:/datasets/nuscenes:ro \
  -w /model \
  --network host \
  -e PYTHONPATH=. \
  -e SENTINEL_EXTRACT=1 \
  -e SENTINEL_EXTRACT_LOG=/model/sentinel_extract.jsonl \
  uniad:latest \
  python -u inference/server.py \
  --port $PORT \
  --config_path projects/configs/stage2_e2e/inference_e2e.py \
  --checkpoint_path ckpts/uniad_base_e2e.pth &

echo "waiting for model server..."
for i in $(seq 1 120); do
  curl -sf "http://127.0.0.1:$PORT/alive" >/dev/null 2>&1 && break
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/alive" || { echo "SERVER_NEVER_ALIVE"; exit 1; }
echo "server alive; copying feeder + scene list into container's view (already via /model)"

cp /tmp/feeder.py /opt/sentinel-stack/UniAD/feeder.py
cp /tmp/train_scenes.txt /opt/sentinel-stack/UniAD/train_scenes.txt

docker exec model python -u /model/feeder.py \
  --scenes /model/train_scenes.txt --port $PORT --out /model/sentinel_extract_gt.jsonl

docker rm -f model >/dev/null 2>&1
gzip -kf /opt/sentinel-stack/UniAD/sentinel_extract.jsonl /opt/sentinel-stack/UniAD/sentinel_extract_gt.jsonl
ls -la /opt/sentinel-stack/UniAD/sentinel_extract*.gz
echo "EXTRACT_DONE $(date)"
