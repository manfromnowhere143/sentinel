#!/bin/bash
# Iteration-21 evaluation-side extraction: replay iteration-12's shadow protocol through
# the full NeuroNCAP loop with the BEV extraction hook. EVAL-ONLY data; never used in training.
exec > /var/log/sentinel-bev-evalextract.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
git config --global --add safe.directory /opt/sentinel-stack/UniAD 2>/dev/null
cd /opt/sentinel-stack/neuro-ncap || exit 1
BASE_DIR='/opt/sentinel-stack'; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'; MODEL_FOLDER=$BASE_DIR/UniAD
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'; MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'
RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=8

git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
python3 /tmp/server_patch_bev_extract.py || exit 1
rm -f /opt/sentinel-stack/UniAD/sentinel_bev_evalextract.jsonl

# compose forwards only a fixed env list; add the BEV extraction vars in a variant.
sed 's/-e SENTINEL_ENABLED /-e SENTINEL_ENABLED -e SENTINEL_BEV_EXTRACT -e SENTINEL_BEV_EXTRACT_LOG /' \
  scripts/_docker_compose_release.sh > scripts/_docker_compose_bev_extract.sh
chmod +x scripts/_docker_compose_bev_extract.sh

echo "##### E21_ARM_START bev_evalextract $(date) #####"
for SCENARIO in frontal side stationary; do
  seq=0103
  echo "##### E21PAIR bev_evalextract $SCENARIO $seq #####"
  docker rm -f renderer model ncap >/dev/null 2>&1
  TIME_NOW="e21-bev-evalextract"
  BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
   MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
   RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
   RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
   SENTINEL_ENABLED=0 SENTINEL_BEV_EXTRACT=1 \
   SENTINEL_BEV_EXTRACT_LOG=/model/sentinel_bev_evalextract.jsonl \
   SENTINEL_LOG=/model/sentinel_e21_shadow.jsonl \
   bash scripts/_docker_compose_bev_extract.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
done
docker rm -f renderer model ncap >/dev/null 2>&1
gzip -kf /opt/sentinel-stack/UniAD/sentinel_bev_evalextract.jsonl \
  /opt/sentinel-stack/UniAD/sentinel_e21_shadow.jsonl
echo "E21_BEV_EVAL_EXTRACT_DONE $(date)"
