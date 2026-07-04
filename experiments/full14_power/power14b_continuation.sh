#!/bin/bash
# Continuation of the power run after the box wedge at OFF-arm episode 396/400
# (documented in RESULT.md): re-runs the two incomplete OFF pairs (stationary-0101, whose
# run_17 was aborted by the orchestrator mid-pair; side-0921, whose run_19 was cut by the
# wedge) and then the full best arm. Episodes are deterministic per run index, so the
# re-run pairs reproduce their completed prefix exactly — verified at analysis. Logs to
# sentinel-power14b.log; the analysis input is the original log with the two partial pair
# blocks excised, concatenated with this log (merge script committed with the proof).
BEST_PATCH="${BEST_PATCH:?set BEST_PATCH before launch}"
exec > /var/log/sentinel-power14b.log 2>&1
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

git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
python3 "$BEST_PATCH" || exit 1

echo "##### P14B_MAKEUP_START off $(date) #####"
for PAIRSPEC in "stationary 0101" "side 0921"; do
  SCENARIO="${PAIRSPEC%% *}"; seq="${PAIRSPEC##* }"
  echo "##### P14PAIR off $SCENARIO $seq #####"
  docker rm -f renderer model ncap >/dev/null 2>&1
  TIME_NOW="p14-off"
  BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
   MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
   RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
   RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
   SENTINEL_ENABLED=0 SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
   SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 \
   SENTINEL_LOG=/model/sentinel_p14_off.jsonl \
   bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
done
echo "##### P14_ARM_DONE off $(date) #####"

git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
python3 "$BEST_PATCH" || exit 1
echo "##### P14_ARM_START best enabled=1 patch=$BEST_PATCH extra=$BEST_EXTRA $(date) #####"
for SCENARIO in stationary frontal side; do
  case $SCENARIO in
    stationary) SEQS="$STATIONARY";;
    frontal)    SEQS="$FRONTAL";;
    side)       SEQS="$SIDE";;
  esac
  for seq in $SEQS; do
    echo "##### P14PAIR best $SCENARIO $seq #####"
    docker rm -f renderer model ncap >/dev/null 2>&1
    TIME_NOW="p14-best"
    env $BEST_EXTRA \
     BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
     MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
     RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
     RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
     SENTINEL_ENABLED=1 SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
     SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 \
     SENTINEL_LOG=/model/sentinel_p14_best.jsonl \
     bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
  done
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "P14_ALL_DONE $(date)"
