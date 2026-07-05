#!/bin/bash
# Iteration 17 — the routed arm on all 20 scene-scenario pairs (120 episodes).
# Comparators are committed evidence (power-run OFF/released first-6 ≡ f14/i15 by H-P0; crawl
# from iter16), identical deterministic episodes. Re-arms the swapfile (the power run's
# memory-exhaustion fix — swapon does not survive reboot) and the vitals watchdog.
exec > /var/log/sentinel-iter17.log 2>&1
set -x
swapon /swapfile 2>/dev/null || true
free -h | tail -1
if ! pgrep -f '[s]entinel_vitals_loop' >/dev/null; then
  nohup bash -c 'echo sentinel_vitals_loop >/dev/null; while true; do
    {
      printf "%s | " "$(date -u +%FT%TZ)"
      printf "mem %s | " "$(free -m | awk "/^Mem/{print \$3\"/\"\$2}")"
      printf "swap %s | " "$(free -m | awk "/^Swap/{print \$3\"/\"\$2}")"
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
RUNS=6

git -C /opt/sentinel-stack/UniAD checkout -- inference/runner.py inference/server.py || exit 1
python3 /tmp/server_patch_union_routed.py || exit 1

STATIONARY="0099 0101 0103 0106 0108 0278 0331 0783 0796 0966"
FRONTAL="0103 0106 0110 0346 0923"
SIDE="0103 0108 0110 0278 0921"

echo "##### I17_ARM_START routed $(date) #####"
for SCENARIO in stationary frontal side; do
  case $SCENARIO in
    stationary) SEQS="$STATIONARY";;
    frontal)    SEQS="$FRONTAL";;
    side)       SEQS="$SIDE";;
  esac
  for seq in $SEQS; do
    echo "##### I17PAIR routed $SCENARIO $seq #####"
    docker rm -f renderer model ncap >/dev/null 2>&1
    TIME_NOW="i17-routed"
    BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
     MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
     RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
     RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
     SENTINEL_ENABLED=1 SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
     SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 SENTINEL_RELEASE_K=4 SENTINEL_CRAWL_V=2.0 \
     SENTINEL_ROUTE_MARGIN=2.0 \
     SENTINEL_LOG=/model/sentinel_i17_routed.jsonl \
     bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
  done
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "I17_ALL_DONE $(date)"
