#!/bin/bash
exec > /var/log/sentinel-i9.log 2>&1
set -x
cd /opt/sentinel-stack/neuro-ncap || exit 1
BASE_DIR='/opt/sentinel-stack'; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'; MODEL_FOLDER=$BASE_DIR/$MODEL_NAME
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'; MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'; RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=6
# arm = name:enabled:evade
ARMS="off:0:0 union:1:0 evade:1:1"
PAIRS="stationary:0103 frontal:0103 side:0103"
for arm in $ARMS; do
  AN="${arm%%:*}"; r="${arm#*:}"; EN="${r%%:*}"; EV="${r##*:}"
  echo "##### I9_ARM_START $AN enabled=$EN evade=$EV $(date) #####"
  for pair in $PAIRS; do
    SCENARIO="${pair%%:*}"; seq="${pair##*:}"
    echo "##### I9PAIR $AN $SCENARIO $seq #####"
    docker rm -f renderer model ncap >/dev/null 2>&1
    TIME_NOW="i9-$AN"
    BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
     MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
     RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
     RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
     SENTINEL_ENABLED=$EN SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
     SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 SENTINEL_EVADE=$EV SENTINEL_EVADE_LAT=4.0 \
     SENTINEL_LOG=/model/sentinel_i9_$AN.jsonl \
     bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
  done
  echo "##### I9_ARM_DONE $AN $(date) #####"
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "I9_ALL_DONE $(date)"
