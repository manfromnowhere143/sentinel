#!/bin/bash
# Iteration 48 pre-launch ON-arm SMOKE (box-side, detached):
#   sudo bash -c 'setsid nohup bash /tmp/iter48_smoke_on_arm.sh </dev/null \
#     >/var/log/sentinel-iter48-smoke.log 2>&1 &'
# SMOKE DISCLOSURE (binding): this is NOT a scheduled Stage-2 episode. It is a single
# tooling sanity check of the committed monitor patch on scene-0013-easy-00 (the iter45
# smoke scene, frozen lexicographic rule), run BEFORE the registered 104-episode launch.
# Its output goes to /datasets/nuscenes-full/hugsim/iter48_smoke/ — NEVER into the
# iter48_runs collection root — and is excluded from the analyzer and every bar/claim.
# It verifies exactly three things and tunes NOTHING (frozen params are the patch's
# baked-in defaults): (1) the patch load marker prints with enabled=1, (2) per-frame
# decision lines + the decisions JSONL are produced, (3) a brake override altered the
# pipe payload at least once OR zero-fire is logged cleanly.
# Markers: I48_SMOKE_START, I48_SMOKE_PATCHED, I48_SMOKE_RC, I48_SMOKE_VERIFY_*,
# I48_SMOKE_DONE | I48_SMOKE_FAIL.
set -x
echo "I48_SMOKE_START $(date -u)"

HUGSIM=/opt/sentinel-stack/HUGSIM
SCEN_DIR=/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes
OUT_BASE=/datasets/nuscenes-full/hugsim/outputs/nusc_uniad
SMOKE=/datasets/nuscenes-full/hugsim/iter48_smoke
PATCH=/tmp/iter48_client_patch.py
SCENARIO=scene-0013-easy-00
OUT_DIR=$OUT_BASE/scene-0013_easy_00

export PIXI_HOME=/datasets/nuscenes-full/hugsim-envs/pixi-home
export PIXI_CACHE_DIR=/datasets/nuscenes-full/hugsim-envs/pixi-cache
export PATH="$PIXI_HOME/bin:$PATH"
mkdir -p "$SMOKE"

if [ "$(docker ps -q | wc -l)" != "0" ]; then
    echo "I48_SMOKE_FAIL another container is running; single-tenant rule"
    exit 1
fi

PATCH_OUT=$(python3 "$PATCH")
echo "$PATCH_OUT"
echo "$PATCH_OUT" | grep -q ITER48_UNION_PATCHED || { echo "I48_SMOKE_FAIL patch"; exit 1; }
echo "I48_SMOKE_PATCHED $(date -u)"

docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true
rm -rf "$OUT_DIR"
(cd "$HUGSIM" && SENTINEL_ENABLED=1 timeout 1200 pixi run python -u closed_loop.py \
    --scenario_path "$SCEN_DIR/$SCENARIO.yaml" \
    --base_path configs/sim/nuscenes_base.yaml \
    --camera_path configs/sim/nuscenes_camera.yaml \
    --kinematic_path configs/sim/kinematic.yaml \
    --ad uniad --ad_cuda 0)
RC=$?
echo "I48_SMOKE_RC=$RC"
docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true

FAIL=0
if grep -q 'SENTINEL_I48_UNION_PATCH_LOADED enabled=1' "$OUT_DIR/output.txt"; then
    echo "I48_SMOKE_VERIFY_MARKER ok"
else
    echo "I48_SMOKE_VERIFY_MARKER MISSING"; FAIL=1
fi
DEC_LINES=$(grep -c 'SENTINEL_I48_DECISION frame=' "$OUT_DIR/output.txt" 2>/dev/null)
[ -n "$DEC_LINES" ] || DEC_LINES=0
echo "I48_SMOKE_VERIFY_DECISION_LINES count=$DEC_LINES"
[ "$DEC_LINES" -gt 0 ] || FAIL=1
if [ -s "$OUT_DIR/sentinel_iter48_decisions.jsonl" ]; then
    echo "I48_SMOKE_VERIFY_JSONL ok rows=$(wc -l < "$OUT_DIR/sentinel_iter48_decisions.jsonl")"
else
    echo "I48_SMOKE_VERIFY_JSONL MISSING"; FAIL=1
fi
BRAKE=$(grep -c 'SENTINEL_I48_DECISION frame=[0-9]* fired=[01] brake=1' "$OUT_DIR/output.txt" 2>/dev/null)
[ -n "$BRAKE" ] || BRAKE=0
FIRED=$(grep -c 'SENTINEL_I48_DECISION frame=[0-9]* fired=1' "$OUT_DIR/output.txt" 2>/dev/null)
[ -n "$FIRED" ] || FIRED=0
if [ "$BRAKE" -gt 0 ]; then
    echo "I48_SMOKE_VERIFY_OVERRIDE brake_frames=$BRAKE (zeros written to plan pipe on those frames)"
elif [ "$FIRED" = "0" ] && [ "$DEC_LINES" -gt 0 ]; then
    echo "I48_SMOKE_VERIFY_OVERRIDE zero-fire logged cleanly (fired=0 on all $DEC_LINES frames)"
else
    echo "I48_SMOKE_VERIFY_OVERRIDE inconsistent fired=$FIRED brake=$BRAKE"; FAIL=1
fi
grep -q 'SENTINEL_I48_DECISION_ERROR' "$OUT_DIR/output.txt" && { echo "I48_SMOKE_VERIFY_ERRORS present"; FAIL=1; }

# Keep the evidence OUTSIDE the registered collection root; never counted in analysis.
DEST=$SMOKE/${SCENARIO}__on_smoke_$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$DEST"
find "$OUT_DIR" -type p -delete
mv "$OUT_DIR"/* "$DEST"/ 2>/dev/null
rmdir "$OUT_DIR" 2>/dev/null || true

if [ "$RC" = "0" ] && [ "$FAIL" = "0" ]; then
    echo "I48_SMOKE_DONE $(date -u) evidence=$DEST"
else
    echo "I48_SMOKE_FAIL rc=$RC fail=$FAIL $(date -u) evidence=$DEST"
fi
