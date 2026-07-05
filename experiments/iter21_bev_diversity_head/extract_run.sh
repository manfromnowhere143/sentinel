#!/bin/bash
# Iteration-21 Stage 1: BEV summary extraction on disjoint train scenes. Standalone model
# container, patched for scene-level BEV dumps; the feeder drives real keyframes.
exec > /var/log/sentinel-bev-extract.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py || exit 1
python3 /tmp/server_patch_bev_extract.py || exit 1

rm -f /opt/sentinel-stack/UniAD/sentinel_bev_extract.jsonl \
  /opt/sentinel-stack/UniAD/sentinel_bev_extract_gt.jsonl
docker rm -f model >/dev/null 2>&1

PORT=9100
docker run --name model --rm --gpus all \
  -v /opt/sentinel-stack/UniAD:/model \
  -v /datasets/nuscenes:/datasets/nuscenes:ro \
  -w /model \
  --network host \
  -e PYTHONPATH=. \
  -e SENTINEL_BEV_EXTRACT=1 \
  -e SENTINEL_BEV_EXTRACT_LOG=/model/sentinel_bev_extract.jsonl \
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
echo "server alive; copying feeder + scene list into container's view"

cp /tmp/feeder.py /opt/sentinel-stack/UniAD/feeder.py
cp /tmp/train_scenes.txt /opt/sentinel-stack/UniAD/train_scenes.txt

docker exec model python -u /model/feeder.py \
  --scenes /model/train_scenes.txt --port $PORT --out /model/sentinel_bev_extract_gt.jsonl

docker rm -f model >/dev/null 2>&1
gzip -kf /opt/sentinel-stack/UniAD/sentinel_bev_extract.jsonl \
  /opt/sentinel-stack/UniAD/sentinel_bev_extract_gt.jsonl
ls -la /opt/sentinel-stack/UniAD/sentinel_bev_extract*.gz
echo "BEV_EXTRACT_DONE $(date)"
