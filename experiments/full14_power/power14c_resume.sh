#!/bin/bash
# Resumable continuation of the power run — designed after four box-freezing hangs (two hosts;
# the freezes cluster on specific episodes, consistent with render states that hard-hang the
# GPU driver stack). Properties:
#   - idempotent: a pair is SKIPPED if its output dir already holds 20 complete metrics.json,
#     so any wedge costs only the in-flight pair and relaunching is always safe;
#   - the log APPENDS (never truncates history);
#   - a vitals watchdog writes memory/load/D-state/GPU state to disk every 30 s so a freeze
#     leaves forensics (vitals line order puts nvidia-smi last — a truncated line means the
#     GPU query itself hung).
# Analysis uses, per (arm, pair), the last complete 20-score block across all run logs
# (merge script committed with the proof).
BEST_PATCH="${BEST_PATCH:?set BEST_PATCH before launch}"
exec >> /var/log/sentinel-power14c.log 2>&1
set -x
date

# vitals watchdog (single instance)
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

pair_done() { # tag scen seq -> 0 if 20 complete metrics
  local n
  n=$(find "/opt/sentinel-stack/neuro-ncap/outoutput/$1/$2-$3" -name metrics.json 2>/dev/null | wc -l)
  [ "$n" -ge 20 ]
}

run_arm() { # armname enabled tag
  local AN=$1 EN=$2 TAG=$3
  git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
  python3 "$BEST_PATCH" || exit 1
  echo "##### P14C_ARM_START $AN enabled=$EN $(date) #####"
  for SCENARIO in stationary frontal side; do
    case $SCENARIO in
      stationary) SEQS="$STATIONARY";;
      frontal)    SEQS="$FRONTAL";;
      side)       SEQS="$SIDE";;
    esac
    for seq in $SEQS; do
      if pair_done "$TAG" "$SCENARIO" "$seq"; then
        echo "##### P14C_SKIP $AN $SCENARIO $seq (complete on disk) #####"
        continue
      fi
      echo "##### P14PAIR $AN $SCENARIO $seq #####"
      docker rm -f renderer model ncap >/dev/null 2>&1
      TIME_NOW="$TAG"
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
  echo "##### P14C_ARM_DONE $AN $(date) #####"
}

# OFF arm: BEST_EXTRA must not apply; run with it unset for clarity (ENABLED=0 makes it inert anyway)
BEST_EXTRA_SAVED="$BEST_EXTRA"
BEST_EXTRA="" run_arm off 0 p14-off
BEST_EXTRA="$BEST_EXTRA_SAVED"
run_arm best 1 p14-best

docker rm -f renderer model ncap >/dev/null 2>&1
echo "P14_ALL_DONE $(date)"
