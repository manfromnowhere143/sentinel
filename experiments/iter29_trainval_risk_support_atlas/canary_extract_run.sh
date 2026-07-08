#!/bin/bash
# Iteration-29 S0 canary extraction. Runs two clean model processes over the
# first two manifest scenes in each split, at most five frames per scene.
exec > /var/log/sentinel-e29-canary.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

run_one() {
  local tag="$1"
  local port="$2"
  git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py || exit 1
  python3 /tmp/server_patch_stage1_iter29.py || exit 1
  rm -f "/opt/sentinel-stack/UniAD/sentinel_e29_canary_${tag}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e29_canary_${tag}_gt.jsonl" \
    /opt/sentinel-stack/UniAD/sentinel_e29_context.json
  docker rm -f model >/dev/null 2>&1 || true
  docker run --name model --rm --gpus all \
    -v /opt/sentinel-stack/UniAD:/model \
    -v /datasets/nuscenes-full:/datasets/nuscenes-full:ro \
    -w /model \
    --network host \
    -e PYTHONPATH=. \
    -e SENTINEL_E29_STAGE1=1 \
    -e SENTINEL_E29_LOG="/model/sentinel_e29_canary_${tag}.jsonl" \
    -e SENTINEL_E29_CONTEXT=/model/sentinel_e29_context.json \
    uniad:latest \
    python -u inference/server.py \
    --port "$port" \
    --config_path projects/configs/stage2_e2e/inference_e2e.py \
    --checkpoint_path ckpts/uniad_base_e2e.pth &

  echo "waiting for model server ${tag}..."
  for _ in $(seq 1 120); do
    curl -sf "http://127.0.0.1:${port}/alive" >/dev/null 2>&1 && break
    sleep 5
  done
  curl -sf "http://127.0.0.1:${port}/alive" || { echo "SERVER_NEVER_ALIVE ${tag}"; exit 1; }
  cp /tmp/feeder_stage1_iter29.py /opt/sentinel-stack/UniAD/feeder_stage1_iter29.py
  cp /tmp/availability_manifest_iter29.json /opt/sentinel-stack/UniAD/availability_manifest.json
  docker exec model python -u /model/feeder_stage1_iter29.py \
    --manifest /model/availability_manifest.json \
    --mode canary \
    --split all \
    --canary-frames 5 \
    --canary-scenes-per-split 2 \
    --port "$port" \
    --out "/model/sentinel_e29_canary_${tag}_gt.jsonl"
  docker rm -f model >/dev/null 2>&1 || true
  gzip -kf "/opt/sentinel-stack/UniAD/sentinel_e29_canary_${tag}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e29_canary_${tag}_gt.jsonl"
  echo "E29_CANARY_${tag}_DONE $(date)"
}

run_one a 9290
run_one b 9291
ls -la /opt/sentinel-stack/UniAD/sentinel_e29_canary*.gz
echo "E29_CANARY_DONE $(date)"
