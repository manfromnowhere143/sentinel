#!/usr/bin/env bash
set -euo pipefail
set -x

UNIAD=/opt/sentinel-stack/UniAD
PATCH=/tmp/server_patch_noop_iter32.py
FEEDER=/tmp/feeder_prefix_replay_iter32.py
MANIFEST=/tmp/prefix_manifest_iter32.json

run_one() {
  local tag="$1"
  local port="$2"

  git -C "$UNIAD" checkout -- inference/server.py inference/runner.py
  python3 "$PATCH"
  rm -f \
    "$UNIAD/sentinel_e32_prefix_${tag}.jsonl" \
    "$UNIAD/sentinel_e32_prefix_${tag}_gt.jsonl" \
    "$UNIAD/sentinel_e32_context.json"
  docker rm -f model || true
  echo "waiting for model server iter32 tag=${tag}..."
  docker run \
    --name model \
    --rm \
    --gpus all \
    -v "$UNIAD":/model \
    -v /datasets/nuscenes-full:/datasets/nuscenes-full:ro \
    -w /model \
    --network host \
    -e PYTHONPATH=. \
    -e SENTINEL_E32_PREFIX_REPLAY=1 \
    -e SENTINEL_E32_LOG="/model/sentinel_e32_prefix_${tag}.jsonl" \
    -e SENTINEL_E32_CONTEXT=/model/sentinel_e32_context.json \
    uniad:latest \
    python -u inference/server.py \
      --port "$port" \
      --config_path projects/configs/stage2_e2e/inference_e2e.py \
      --checkpoint_path ckpts/uniad_base_e2e.pth &
  for _ in $(seq 1 120); do
    if curl -sf "http://127.0.0.1:${port}/alive"; then
      break
    fi
    sleep 5
  done
  curl -sf "http://127.0.0.1:${port}/alive"
  cp "$FEEDER" "$UNIAD/feeder_prefix_replay_iter32.py"
  cp "$MANIFEST" "$UNIAD/prefix_manifest_iter32.json"
  docker exec model python -u /model/feeder_prefix_replay_iter32.py \
    --prefix-manifest /model/prefix_manifest_iter32.json \
    --port "$port" \
    --out "/model/sentinel_e32_prefix_${tag}_gt.jsonl"
  docker rm -f model
  gzip -kf \
    "$UNIAD/sentinel_e32_prefix_${tag}.jsonl" \
    "$UNIAD/sentinel_e32_prefix_${tag}_gt.jsonl"
  echo "E32_PREFIX_REPLAY_${tag}_DONE $(date)"
}

run_one a 9320
run_one b 9321

ls -la \
  "$UNIAD/sentinel_e32_prefix_a.jsonl.gz" \
  "$UNIAD/sentinel_e32_prefix_a_gt.jsonl.gz" \
  "$UNIAD/sentinel_e32_prefix_b.jsonl.gz" \
  "$UNIAD/sentinel_e32_prefix_b_gt.jsonl.gz"
echo "E32_PREFIX_REPLAY_DONE $(date)"
