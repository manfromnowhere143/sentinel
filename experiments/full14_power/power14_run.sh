#!/bin/bash
# The power run — OFF vs the best configuration, all 14 official scenes, 20 runs per pair
# (800 episodes). Run indices 0-5 double as an exact reproduction of the committed RUNS=6
# evidence (H-P0). The best arm's patch is chosen by the pre-registered decision rule:
#   BEST_PATCH=/tmp/server_patch_union_crawl.py   BEST_EXTRA="SENTINEL_RELEASE_K=4 SENTINEL_CRAWL_V=2.0"
#   BEST_PATCH=/tmp/server_patch_union_release.py BEST_EXTRA="SENTINEL_RELEASE_K=4"
# Set both below before launch; the launch record in RESULT.md states which branch fired.
BEST_PATCH="${BEST_PATCH:?set BEST_PATCH before launch}"
exec > /var/log/sentinel-power14.log 2>&1
set -x
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null
cd /opt/sentinel-stack/neuro-ncap || exit 1
BASE_DIR='/opt/sentinel-stack'; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'; MODEL_FOLDER=$BASE_DIR/UniAD
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'; MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'; RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=20

STATIONARY="0099 0101 0103 0106 0108 0278 0331 0783 0796 0966"
FRONTAL="0103 0106 0110 0346 0923"
SIDE="0103 0108 0110 0278 0921"

for arm in off:0 best:1; do
  AN="${arm%%:*}"; EN="${arm##*:}"
  git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
  python3 "$BEST_PATCH" || exit 1
  echo "##### P14_ARM_START $AN enabled=$EN patch=$BEST_PATCH extra=$BEST_EXTRA $(date) #####"
  for SCENARIO in stationary frontal side; do
    case $SCENARIO in
      stationary) SEQS="$STATIONARY";;
      frontal)    SEQS="$FRONTAL";;
      side)       SEQS="$SIDE";;
    esac
    for seq in $SEQS; do
      echo "##### P14PAIR $AN $SCENARIO $seq #####"
      docker rm -f renderer model ncap >/dev/null 2>&1
      TIME_NOW="p14-$AN"
      env $BEST_EXTRA \
       BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
       MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
       RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
       RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
       SENTINEL_ENABLED=$EN SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
       SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 \
       SENTINEL_LOG=/model/sentinel_p14_$AN.jsonl \
       bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
    done
  done
  echo "##### P14_ARM_DONE $AN $(date) #####"
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "P14_ALL_DONE $(date)"
