#!/bin/bash
# Sentinel iter1b — real partial NeuroNCAP run on the scenes available in public v1.0-mini
# (0103 across stationary/frontal/side, 0796 stationary), at real run counts. Collision-prone
# scenarios (frontal/side) first — those are the UniAD failures Sentinel will monitor.
# Runs as root. Each (scenario,scene) is one docker-compose eval of RUNS episodes.
exec > /var/log/sentinel-iter1b.log 2>&1
set -x
cd /opt/sentinel-stack/neuro-ncap || exit 1

# config (mirrors sentinel_smoke.sh; checkpoints->ckpts symlink + fork + fixes already in place)
BASE_DIR='/opt/sentinel-stack'
NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'
MODEL_FOLDER=$BASE_DIR/$MODEL_NAME
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'
MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'
RENDERING_CHECKPOITNS_PATH='checkpoints'
RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'
NCAP_IMAGE='ncap:latest'
TIME_NOW=$(date +"%Y-%m-%d_%H-%M-%S")

RUNS=15
# collision-prone first (frontal/side = actor drives at ego), then stationary
PAIRS="frontal:0103 side:0103 stationary:0103 stationary:0796"

echo "ITER1B_START $(date) RUNS=$RUNS PAIRS=$PAIRS TIME_NOW=$TIME_NOW"
for pair in $PAIRS; do
  SCENARIO="${pair%%:*}"; seq="${pair##*:}"
  echo "===== RUN_PAIR $SCENARIO $seq x${RUNS} ====="
  docker rm -f renderer model ncap >/dev/null 2>&1
  BASE_DIR=$BASE_DIR \
   NUSCENES_PATH=$NUSCENES_PATH \
   MODEL_NAME=$MODEL_NAME \
   MODEL_FOLDER=$MODEL_FOLDER \
   MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH \
   MODEL_CFG_PATH=$MODEL_CFG_PATH \
   MODEL_IMAGE=$MODEL_IMAGE \
   RENDERING_FOLDER=$RENDERING_FOLDER \
   RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
   RENDERING_IMAGE=$RENDERING_IMAGE \
   NCAP_FOLDER=$NCAP_FOLDER \
   NCAP_IMAGE=$NCAP_IMAGE \
   TIME_NOW=$TIME_NOW \
   bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
  echo "===== DONE_PAIR $SCENARIO $seq $(date) ====="
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "ITER1B_DONE $(date) OUTDIR=/opt/sentinel-stack/NeuroNCAP/outoutput/$TIME_NOW"
