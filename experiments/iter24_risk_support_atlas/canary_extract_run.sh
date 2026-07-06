#!/bin/bash
# Iteration-24 S0 canary extraction. Runs two clean model processes over the
# first manifest scene in each split, at most five frames per scene.
exec > /var/log/sentinel-e24-canary.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

run_one() {
  local tag="$1"
  local port="$2"
  git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py || exit 1
  python3 /tmp/server_patch_stage1_iter24.py || exit 1
  rm -f "/opt/sentinel-stack/UniAD/sentinel_e24_canary_${tag}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e24_canary_${tag}_gt.jsonl" \
    /opt/sentinel-stack/UniAD/sentinel_e24_context.json
  docker rm -f model >/dev/null 2>&1 || true
  docker run --name model --rm --gpus all \
    -v /opt/sentinel-stack/UniAD:/model \
    -v /datasets/nuscenes:/datasets/nuscenes:ro \
    -w /model \
    --network host \
    -e PYTHONPATH=. \
    -e SENTINEL_E24_STAGE1=1 \
    -e SENTINEL_E24_LOG="/model/sentinel_e24_canary_${tag}.jsonl" \
    -e SENTINEL_E24_CONTEXT=/model/sentinel_e24_context.json \
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
  cp /tmp/feeder_stage1_iter24.py /opt/sentinel-stack/UniAD/feeder_stage1_iter24.py
  cp /tmp/availability_manifest_iter24.json /opt/sentinel-stack/UniAD/availability_manifest.json
  docker exec model python -u /model/feeder_stage1_iter24.py \
    --manifest /model/availability_manifest.json \
    --mode canary \
    --split all \
    --canary-frames 5 \
    --port "$port" \
    --out "/model/sentinel_e24_canary_${tag}_gt.jsonl"
  docker rm -f model >/dev/null 2>&1 || true
  gzip -kf "/opt/sentinel-stack/UniAD/sentinel_e24_canary_${tag}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e24_canary_${tag}_gt.jsonl"
  echo "E24_CANARY_${tag}_DONE $(date)"
}

run_one a 9210
run_one b 9211
ls -la /opt/sentinel-stack/UniAD/sentinel_e24_canary*.gz
echo "E24_CANARY_DONE $(date)"
