#!/bin/bash
# Iteration 42 — released-union best-arm exact trace capture over the frozen full14/power set.
# This is trace-support only: no OFF arm, no perturbation, no selector, no safety claim.
TRACE_PATCH="${TRACE_PATCH:-/tmp/server_patch_union_trace.py}"
exec > /var/log/sentinel-iter42-trace.log 2>&1
set -x
date

if ! pgrep -f '[s]entinel_vitals_loop' >/dev/null; then
  nohup bash -c 'echo sentinel_vitals_loop >/dev/null; while true; do
    {
      printf "%s | " "$(date -u +%FT%TZ)"
      printf "mem %s | " "$(free -m | awk "/^Mem/{print \$3\"/\"\$2}")"
      printf "load %s | " "$(cut -d" " -f1-3 /proc/loadavg)"
      printf "D %s | " "$(ps -eo stat= | grep -c "^D")"
      printf "gpu %s\n" "$(timeout 10 nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>&1 | head -1)"
    } >> /var/log/sentinel-vitals.log 2>&1
    sleep 30
  done' </dev/null >/dev/null 2>&1 &
fi

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
python3 "$TRACE_PATCH" || exit 1
rm -f /opt/sentinel-stack/UniAD/sentinel_iter42_trace.jsonl /opt/sentinel-stack/UniAD/sentinel_iter42_trace.jsonl.gz

echo "##### I42_TRACE_ARM_START best enabled=1 patch=$TRACE_PATCH $(date) #####"
for SCENARIO in stationary frontal side; do
  case $SCENARIO in
    stationary) SEQS="$STATIONARY";;
    frontal)    SEQS="$FRONTAL";;
    side)       SEQS="$SIDE";;
  esac
  for seq in $SEQS; do
    echo "##### I42PAIR trace $SCENARIO $seq #####"
    docker rm -f renderer model ncap >/dev/null 2>&1
    TIME_NOW="iter42-trace"
    BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
     MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
     RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
     RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
     SENTINEL_ENABLED=1 SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
     SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 SENTINEL_RELEASE_K=4 \
     SENTINEL_LOG=/model/sentinel_iter42_trace.jsonl \
     bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
  done
done
docker rm -f renderer model ncap >/dev/null 2>&1
if [ -f /opt/sentinel-stack/UniAD/sentinel_iter42_trace.jsonl ]; then
  gzip -c /opt/sentinel-stack/UniAD/sentinel_iter42_trace.jsonl > /opt/sentinel-stack/UniAD/sentinel_iter42_trace.jsonl.gz
fi
echo "I42_TRACE_ALL_DONE $(date)"
