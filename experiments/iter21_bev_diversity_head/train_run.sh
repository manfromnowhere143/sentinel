#!/bin/bash
# Iteration-21 Stage 2: train the BEV-conditioned diversity head after extraction completes.
exec > /var/log/sentinel-bev-train.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null

test -f /opt/sentinel-stack/UniAD/sentinel_bev_extract.jsonl.gz || {
  echo "MISSING_BEV_EXTRACT"; exit 1;
}
test -f /opt/sentinel-stack/UniAD/sentinel_bev_extract_gt.jsonl.gz || {
  echo "MISSING_BEV_GT"; exit 1;
}

cp /tmp/train_bev_head.py /opt/sentinel-stack/UniAD/train_bev_head.py
docker rm -f bev-train >/dev/null 2>&1
docker run --name bev-train --rm --gpus all \
  -v /opt/sentinel-stack/UniAD:/model \
  -w /model \
  --network host \
  -e PYTHONPATH=. \
  uniad:latest \
  python -u /model/train_bev_head.py \
  --extract /model/sentinel_bev_extract.jsonl.gz \
  --gt /model/sentinel_bev_extract_gt.jsonl.gz \
  --out /model/bev_diversity_head.pt

ls -lh /opt/sentinel-stack/UniAD/bev_diversity_head.pt
echo "BEV_TRAIN_DONE $(date)"
