#!/bin/bash
# Checkpoint D data collection — candidate logging pass, planner behaviour unchanged (no monitor).
# Deterministic run indices 0-7 reproduce the known corpus: frontal has 6/8 collisions, side 8/8,
# stationary 0/8 — exactly the frames the candidate analysis needs.
exec > /var/log/sentinel-cand.log 2>&1
set -x
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null
cd /opt/sentinel-stack/neuro-ncap || exit 1
BASE_DIR='/opt/sentinel-stack'; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'; MODEL_FOLDER=$BASE_DIR/$MODEL_NAME
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'; MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'; RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=8

# pristine server (no monitor), runner patched for candidate logging only
git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
python3 /tmp/patch_candidate_logging.py || exit 1
rm -f /opt/sentinel-stack/UniAD/sentinel_cand.jsonl

for pair in "frontal:0103" "side:0103" "stationary:0103"; do
  SCENARIO="${pair%%:*}"; seq="${pair##*:}"
  echo "##### CANDPAIR off $SCENARIO $seq #####"
  docker rm -f renderer model ncap >/dev/null 2>&1
  TIME_NOW="cand-off"
  BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
   MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
   RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
   RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
   SENTINEL_ENABLED=0 \
   bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "CAND_MARKER lines: $(grep -c . /opt/sentinel-stack/UniAD/sentinel_cand.jsonl 2>/dev/null)"
echo "CAND_ALL_DONE $(date)"
