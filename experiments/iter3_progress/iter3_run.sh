#!/bin/bash
# Iteration 3 — the deployment metric: avoid the crash AND complete the route.
# Three arms (OFF / always-brake / Sentinel-TTC) on a clean scene (progress matters) + danger scenes.
# Output dirs tagged i3-<arm> so progress is computed per arm from ego_poses vs reference.
exec > /var/log/sentinel-i3.log 2>&1
set -x
cd /opt/sentinel-stack/neuro-ncap || exit 1
BASE_DIR='/opt/sentinel-stack'; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'; MODEL_FOLDER=$BASE_DIR/$MODEL_NAME
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'; MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'; RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=6
# arm = name:enabled:mode
ARMS="off:0:ttc always:1:always ttc:1:ttc"
PAIRS="stationary:0103 frontal:0103 side:0103"
for arm in $ARMS; do
  AN="${arm%%:*}"; rest="${arm#*:}"; EN="${rest%%:*}"; MO="${rest##*:}"
  echo "##### I3_ARM_START $AN enabled=$EN mode=$MO $(date) #####"
  for pair in $PAIRS; do
    SCENARIO="${pair%%:*}"; seq="${pair##*:}"
    echo "##### I3PAIR $AN $SCENARIO $seq #####"
    docker rm -f renderer model ncap >/dev/null 2>&1
    TIME_NOW="i3-$AN"
    BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
     MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
     RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
     RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
     SENTINEL_ENABLED=$EN SENTINEL_MODE=$MO SENTINEL_TTC=2.5 SENTINEL_PROXD=6.0 SENTINEL_MIN_SCORE=0.3 \
     SENTINEL_LOG=/model/sentinel_i3_$AN.jsonl \
     bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
  done
  echo "##### I3_ARM_DONE $AN $(date) #####"
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "I3_ALL_DONE $(date)"
