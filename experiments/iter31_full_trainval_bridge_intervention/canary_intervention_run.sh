#!/bin/bash
# Iteration-31 S0 canary: two repeats at alpha 0.00 and 0.50 over the frozen canary row manifest.
exec > /var/log/sentinel-e31-canary.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

run_one() {
  local alpha="$1"
  local tag="$2"
  local port="$3"
  local encoded="${alpha/./p}"
  git -C /opt/sentinel-stack/UniAD checkout -- inference/server.py inference/runner.py || exit 1
  python3 /tmp/server_patch_intervention_iter31.py || exit 1
  rm -f "/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha${encoded}_${tag}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha${encoded}_${tag}_gt.jsonl" \
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
    -e SENTINEL_E31_LOG="/model/sentinel_e31_canary_alpha${encoded}_${tag}.jsonl" \
    -e SENTINEL_E31_CONTEXT=/model/sentinel_e31_context.json \
    uniad:latest \
    python -u inference/server.py \
    --port "$port" \
    --config_path projects/configs/stage2_e2e/inference_e2e.py \
    --checkpoint_path ckpts/uniad_base_e2e.pth &

  echo "waiting for model server alpha=${alpha} tag=${tag}..."
  for _ in $(seq 1 120); do
    curl -sf "http://127.0.0.1:${port}/alive" >/dev/null 2>&1 && break
    sleep 5
  done
  curl -sf "http://127.0.0.1:${port}/alive" || { echo "SERVER_NEVER_ALIVE alpha=${alpha} tag=${tag}"; exit 1; }
  cp /tmp/feeder_intervention_iter31.py /opt/sentinel-stack/UniAD/feeder_intervention_iter31.py
  cp /tmp/iter31_direction.json /opt/sentinel-stack/UniAD/iter31_direction.json
  cp /tmp/replay_manifest_canary_iter31.json /opt/sentinel-stack/UniAD/replay_manifest_canary.json
  docker exec model python -u /model/feeder_intervention_iter31.py \
    --row-manifest /model/replay_manifest_canary.json \
    --alpha "$alpha" \
    --port "$port" \
    --out "/model/sentinel_e31_canary_alpha${encoded}_${tag}_gt.jsonl"
  docker rm -f model >/dev/null 2>&1 || true
  gzip -kf "/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha${encoded}_${tag}.jsonl" \
    "/opt/sentinel-stack/UniAD/sentinel_e31_canary_alpha${encoded}_${tag}_gt.jsonl"
  echo "E31_CANARY_ALPHA_${encoded}_${tag}_DONE $(date)"
}

run_one 0.00 a 9310
run_one 0.00 b 9311
run_one 0.50 a 9312
run_one 0.50 b 9313
ls -la /opt/sentinel-stack/UniAD/sentinel_e31_canary*.gz
echo "E31_CANARY_DONE $(date)"
