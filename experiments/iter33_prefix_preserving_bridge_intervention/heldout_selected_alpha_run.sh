#!/bin/bash
# Iteration-33 heldout replay. Requires ITER33_SELECTED_ALPHA from committed calibration proof.
exec > /var/log/sentinel-e33-heldout.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

if [ -z "$ITER33_SELECTED_ALPHA" ]; then
  echo "ITER33_SELECTED_ALPHA is required"
  exit 1
fi

UNIAD=/opt/sentinel-stack/UniAD
PATCH=/tmp/server_patch_intervention_iter33.py
FEEDER=/tmp/feeder_intervention_iter33.py
DIRECTION=/tmp/iter33_direction.json
MANIFEST=/tmp/prefix_manifest_heldout_iter33.json
PATCH_SHA256=$(sha256sum "$PATCH" | awk '{print $1}')
UNIAD_COMMIT=$(git -C "$UNIAD" rev-parse HEAD)
if [ -z "$PATCH_SHA256" ] || [ -z "$UNIAD_COMMIT" ]; then
  echo "missing patch hash or UniAD commit"
  exit 1
fi
encoded="${ITER33_SELECTED_ALPHA/./p}"
PORT=9360

git -C "$UNIAD" checkout -- inference/server.py inference/runner.py || exit 1
python3 "$PATCH" || exit 1
rm -f "$UNIAD/sentinel_e33_heldout_alpha${encoded}.jsonl" \
  "$UNIAD/sentinel_e33_heldout_alpha${encoded}_gt.jsonl" \
  "$UNIAD/sentinel_e33_context.json"
docker rm -f model >/dev/null 2>&1 || true
docker run --name model --rm --gpus all \
  -v "$UNIAD":/model \
  -v /datasets/nuscenes-full:/datasets/nuscenes-full:ro \
  -w /model \
  --network host \
  -e PYTHONPATH=. \
  -e SENTINEL_E33_PREFIX_INTERVENTION=1 \
  -e SENTINEL_E33_ALPHA="$ITER33_SELECTED_ALPHA" \
  -e SENTINEL_E33_DIRECTION=/model/iter33_direction.json \
  -e SENTINEL_E33_PATCH_SHA256="$PATCH_SHA256" \
  -e SENTINEL_E33_UNIAD_COMMIT="$UNIAD_COMMIT" \
  -e SENTINEL_E33_LOG="/model/sentinel_e33_heldout_alpha${encoded}.jsonl" \
  -e SENTINEL_E33_CONTEXT=/model/sentinel_e33_context.json \
  uniad:latest \
  python -u inference/server.py \
  --port "$PORT" \
  --config_path projects/configs/stage2_e2e/inference_e2e.py \
  --checkpoint_path ckpts/uniad_base_e2e.pth &

echo "waiting for model server iter33 heldout alpha=${ITER33_SELECTED_ALPHA}..."
for _ in $(seq 1 120); do
  curl -sf "http://127.0.0.1:${PORT}/alive" >/dev/null 2>&1 && break
  sleep 5
done
curl -sf "http://127.0.0.1:${PORT}/alive" || { echo "SERVER_NEVER_ALIVE heldout"; exit 1; }
cp "$FEEDER" "$UNIAD/feeder_intervention_iter33.py"
cp "$DIRECTION" "$UNIAD/iter33_direction.json"
cp "$MANIFEST" "$UNIAD/prefix_manifest_heldout_iter33.json"
docker exec model python -u /model/feeder_intervention_iter33.py \
  --prefix-manifest /model/prefix_manifest_heldout_iter33.json \
  --alpha "$ITER33_SELECTED_ALPHA" \
  --port "$PORT" \
  --out "/model/sentinel_e33_heldout_alpha${encoded}_gt.jsonl"
docker rm -f model >/dev/null 2>&1 || true
gzip -kf "$UNIAD/sentinel_e33_heldout_alpha${encoded}.jsonl" \
  "$UNIAD/sentinel_e33_heldout_alpha${encoded}_gt.jsonl"
ls -la "$UNIAD"/sentinel_e33_heldout*.gz
echo "E33_HELDOUT_DONE $(date)"
