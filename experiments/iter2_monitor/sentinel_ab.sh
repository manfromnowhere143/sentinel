#!/bin/bash
# Sentinel A/B — monitor ON. Same corpus/run-count as the shadow (OFF) baseline. The brake fires
# inside the frozen-planner server when the imminent (h=1) predicted gap < theta(3.5m).
exec > /var/log/sentinel-ab.log 2>&1
set -x
cd /opt/sentinel-stack/neuro-ncap || exit 1

# Sentinel operating point (theta fixed on the G1 shadow data; high-precision, do-no-harm safe)
export SENTINEL_ENABLED=1
export SENTINEL_GAP=3.5
export SENTINEL_HORIZON=1
export SENTINEL_MIN_SCORE=0.2
export SENTINEL_DECEL=4.0
export SENTINEL_LOG=/model/sentinel_ab.jsonl

rm -f /opt/sentinel-stack/UniAD/sentinel_ab.jsonl
touch /opt/sentinel-stack/UniAD/sentinel_ab.jsonl
chmod 666 /opt/sentinel-stack/UniAD/sentinel_ab.jsonl

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

RUNS=10
PAIRS="frontal:0103 side:0103 stationary:0103 stationary:0796"

echo "AB_START $(date) ENABLED=$SENTINEL_ENABLED GAP=$SENTINEL_GAP H=$SENTINEL_HORIZON RUNS=$RUNS TIME_NOW=$TIME_NOW"
for pair in $PAIRS; do
  SCENARIO="${pair%%:*}"; seq="${pair##*:}"
  echo "===== RUN_PAIR $SCENARIO $seq x${RUNS} ====="
  docker rm -f renderer model ncap >/dev/null 2>&1
  BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
   MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
   RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
   RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
   SENTINEL_ENABLED=$SENTINEL_ENABLED SENTINEL_GAP=$SENTINEL_GAP SENTINEL_HORIZON=$SENTINEL_HORIZON \
   SENTINEL_MIN_SCORE=$SENTINEL_MIN_SCORE SENTINEL_DECEL=$SENTINEL_DECEL SENTINEL_LOG=$SENTINEL_LOG \
   bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
  echo "===== DONE_PAIR $SCENARIO $seq $(date) ====="
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "AB_DONE $(date) BRAKES=/opt/sentinel-stack/UniAD/sentinel_ab.jsonl"
echo -n 'brake events: '; grep -c '"brake"' /opt/sentinel-stack/UniAD/sentinel_ab.jsonl 2>/dev/null
