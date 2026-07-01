#!/bin/bash
# Iteration 13 — RSS-style formal-envelope baseline arm, 20 unique episodes, 3 scenes.
# OFF and union comparators come from the verification §4 v20 pass (same run indices).
exec > /var/log/sentinel-rss.log 2>&1
set -x
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null
cd /opt/sentinel-stack/neuro-ncap || exit 1
BASE_DIR='/opt/sentinel-stack'; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'; MODEL_FOLDER=$BASE_DIR/$MODEL_NAME
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'; MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'; RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=20

git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
python3 /tmp/server_patch_rss.py || exit 1

for pair in "stationary:0103" "frontal:0103" "side:0103"; do
  SCENARIO="${pair%%:*}"; seq="${pair##*:}"
  echo "##### RSSPAIR rss $SCENARIO $seq #####"
  docker rm -f renderer model ncap >/dev/null 2>&1
  TIME_NOW="rss-arm"
  BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
   MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
   RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
   RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
   SENTINEL_ENABLED=1 SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 \
   SENTINEL_LOG=/model/sentinel_rss.jsonl \
   bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "RSS_ALL_DONE $(date)"
