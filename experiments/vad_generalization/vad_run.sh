#!/bin/bash
# VAD generalization — OFF vs union on a second frozen planner, 20 unique episodes, 3 scenes.
# Uses the smoke-verified model config; the image-decode fix is applied after the union patch
# (the union patch git-checkouts server.py first, the decode fix composes on top).
exec > /var/log/sentinel-vad20.log 2>&1
set -x
git config --global --add safe.directory /opt/sentinel-stack/VAD 2>/dev/null
cd /opt/sentinel-stack/neuro-ncap || exit 1
BASE_DIR='/opt/sentinel-stack'; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='VAD'; MODEL_FOLDER=$BASE_DIR/VAD
MODEL_CHECKPOINT_PATH='ckpts/VAD_base.pth'
MODEL_CFG_PATH='projects/configs/VAD/VAD_inference.py'; MODEL_IMAGE='vad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'; RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=20

git -C /opt/sentinel-stack/VAD checkout -- inference/runner.py || exit 1
python3 /tmp/server_patch_union_vad.py || exit 1   # git-checkouts server.py, applies the union
python3 /tmp/patch_vad_image_decode.py || exit 1   # then the renderer-tensor decode fix
python3 /tmp/patch_vad_candidates.py || exit 1     # behaviour-preserving: log all 3 native modes
python3 /tmp/patch_vad_empty_fix.py || exit 1      # fork bugs: empty aux shape + cold-start forecasts
rm -f /opt/sentinel-stack/VAD/sentinel_vad_cand.jsonl

ARMS="off:0 union:1"
PAIRS="stationary:0103 frontal:0103 side:0103"
for arm in $ARMS; do
  AN="${arm%%:*}"; EN="${arm##*:}"
  echo "##### VAD20_ARM_START $AN enabled=$EN $(date) #####"
  for pair in $PAIRS; do
    SCENARIO="${pair%%:*}"; seq="${pair##*:}"
    echo "##### VAD20PAIR $AN $SCENARIO $seq #####"
    docker rm -f renderer model ncap >/dev/null 2>&1
    TIME_NOW="vad20-$AN"
    BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
     MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
     RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
     RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
     SENTINEL_ENABLED=$EN SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
     SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 \
     SENTINEL_LOG=/model/sentinel_vad20_$AN.jsonl \
     bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
  done
  echo "##### VAD20_ARM_DONE $AN $(date) #####"
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "VAD20_ALL_DONE $(date)"
