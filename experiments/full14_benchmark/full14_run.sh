#!/bin/bash
# The full official NeuroNCAP scene set — OFF vs union across all 14 scenes (20 scene-scenario
# pairs from the release arrays), 6 runs each: 240 episodes. The first number in this repository
# comparable in scope against the published UniAD baseline (1.84).
exec > /var/log/sentinel-full14.log 2>&1
set -x
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null
cd /opt/sentinel-stack/neuro-ncap || exit 1
BASE_DIR='/opt/sentinel-stack'; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'; MODEL_FOLDER=$BASE_DIR/$MODEL_NAME
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'; MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'; RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=6

git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
python3 /tmp/server_patch_union.py || exit 1

STATIONARY="0099 0101 0103 0106 0108 0278 0331 0783 0796 0966"
FRONTAL="0103 0106 0110 0346 0923"
SIDE="0103 0108 0110 0278 0921"

for arm in off:0 union:1; do
  AN="${arm%%:*}"; EN="${arm##*:}"
  echo "##### F14_ARM_START $AN enabled=$EN $(date) #####"
  for SCENARIO in stationary frontal side; do
    case $SCENARIO in
      stationary) SEQS="$STATIONARY";;
      frontal)    SEQS="$FRONTAL";;
      side)       SEQS="$SIDE";;
    esac
    for seq in $SEQS; do
      echo "##### F14PAIR $AN $SCENARIO $seq #####"
      docker rm -f renderer model ncap >/dev/null 2>&1
      TIME_NOW="f14-$AN"
      BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
       MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
       RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
       RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
       SENTINEL_ENABLED=$EN SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
       SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 \
       SENTINEL_LOG=/model/sentinel_f14_$AN.jsonl \
       bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
    done
  done
  echo "##### F14_ARM_DONE $AN $(date) #####"
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "F14_ALL_DONE $(date)"
