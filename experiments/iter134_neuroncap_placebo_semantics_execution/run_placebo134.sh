#!/bin/bash
# Iteration 134 - the placebo semantics execution: OFF vs released union vs semantics-scrambled
# budget-matched placebo, all 14 official scenes / 20 pairs, 20 runs per pair, 3 arms,
# 1,200 episodes, ONE launch, arm-major.
#
# OFF and UNION are the SAME binary, env-gated (SENTINEL_ENABLED), exactly as the power run did.
# PLACEBO is a different binary that cannot observe the world; it fires from the frozen donor
# schedule only.
#
# G0 provenance gate runs BEFORE the first episode: the patch and analyzer files on this box must
# be byte-identical to the committed copies recorded in the launch manifest. Mismatch aborts.
exec > /var/log/sentinel-i134.log 2>&1
set -x

STACK=/opt/sentinel-stack
I134=$STACK/iter134
UNION_PATCH=$I134/server_patch_union_release.py
PLACEBO_PATCH=$I134/server_patch_placebo.py
MANIFEST=$I134/launch_manifest.json
SCHED=$I134/donor_schedules.json

# ---- G0 provenance gate ------------------------------------------------------------------------
python3 - <<'PY' || { echo "I134_ABORT_PROVENANCE"; exit 1; }
import hashlib, json, sys
man = json.load(open('/opt/sentinel-stack/iter134/launch_manifest.json'))
bad = []
for name, rec in man['hash_bound_files'].items():
    p = '/opt/sentinel-stack/iter134/' + name
    try:
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    except OSError as e:
        bad.append(f'{name}:missing:{e}')
        continue
    if h != rec['sha256']:
        bad.append(f'{name}:{h}!={rec["sha256"]}')
if bad:
    print('PROVENANCE_FAIL', bad)
    sys.exit(1)
print('I134_PROVENANCE_OK', len(man['hash_bound_files']), 'files byte-identical')
PY

git config --global --add safe.directory $STACK/UniAD 2>/dev/null
cd $STACK/neuro-ncap || exit 1

# the schedule must be visible inside the model container as /model/donor_schedules.json
cp -f $SCHED $STACK/UniAD/donor_schedules.json || exit 1

BASE_DIR=$STACK; NUSCENES_PATH='/datasets/nuscenes'
MODEL_NAME='UniAD'; MODEL_FOLDER=$BASE_DIR/UniAD
MODEL_CHECKPOINT_PATH='ckpts/uniad_base_e2e.pth'
MODEL_CFG_PATH='projects/configs/stage2_e2e/inference_e2e.py'; MODEL_IMAGE='uniad:latest'
RENDERING_FOLDER=$BASE_DIR/'neurad-studio'; RENDERING_CHECKPOITNS_PATH='checkpoints'; RENDERING_IMAGE='neurad:latest'
NCAP_FOLDER=$BASE_DIR/'neuro-ncap'; NCAP_IMAGE='ncap:latest'
RUNS=20

STATIONARY="0099 0101 0103 0106 0108 0278 0331 0783 0796 0966"
FRONTAL="0103 0106 0110 0346 0923"
SIDE="0103 0108 0110 0278 0921"

# arm : enabled : patch
for arm in off:0:$UNION_PATCH union:1:$UNION_PATCH placebo:1:$PLACEBO_PATCH; do
  AN="${arm%%:*}"; REST="${arm#*:}"; EN="${REST%%:*}"; PATCH="${REST#*:}"
  git -C $STACK/UniAD checkout -- inference/runner.py inference/server.py || exit 1
  python3 "$PATCH" || exit 1
  echo "##### I134_ARM_START $AN enabled=$EN patch=$PATCH $(date) #####"
  for SCENARIO in stationary frontal side; do
    case $SCENARIO in
      stationary) SEQS="$STATIONARY";;
      frontal)    SEQS="$FRONTAL";;
      side)       SEQS="$SIDE";;
    esac
    for seq in $SEQS; do
      echo "##### I134PAIR $AN $SCENARIO $seq #####"
      docker rm -f renderer model ncap >/dev/null 2>&1
      TIME_NOW="i134-$AN"
      env SENTINEL_RELEASE_K=4 \
       BASE_DIR=$BASE_DIR NUSCENES_PATH=$NUSCENES_PATH MODEL_NAME=$MODEL_NAME MODEL_FOLDER=$MODEL_FOLDER \
       MODEL_CHECKPOINT_PATH=$MODEL_CHECKPOINT_PATH MODEL_CFG_PATH=$MODEL_CFG_PATH MODEL_IMAGE=$MODEL_IMAGE \
       RENDERING_FOLDER=$RENDERING_FOLDER RENDERING_CHECKPOITNS_PATH=$RENDERING_CHECKPOITNS_PATH \
       RENDERING_IMAGE=$RENDERING_IMAGE NCAP_FOLDER=$NCAP_FOLDER NCAP_IMAGE=$NCAP_IMAGE TIME_NOW=$TIME_NOW \
       SENTINEL_ENABLED=$EN SENTINEL_MIN_SCORE=0.3 SENTINEL_MAXGAP=30 SENTINEL_CPA_MARGIN=1.5 \
       SENTINEL_TTC=2.5 SENTINEL_MIN_CLOSING=3 \
       SENTINEL_PLACEBO_PAIR="$SCENARIO/$seq" \
       SENTINEL_PLACEBO_SCHEDULE=/model/donor_schedules.json \
       SENTINEL_LOG=/model/sentinel_i134_$AN.jsonl \
       bash scripts/_docker_compose_release.sh $seq $SCENARIO --scenario-category=$SCENARIO --runs $RUNS
    done
  done
  echo "##### I134_ARM_DONE $AN $(date) #####"
done
docker rm -f renderer model ncap >/dev/null 2>&1
echo "I134_PLACEBO_DONE $(date)"
