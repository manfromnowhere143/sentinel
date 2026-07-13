#!/bin/bash
# Iteration 58 HUGSIM provenance instrumented canary.
# Box-side launch, detached per the playbook:
#   sudo bash -c 'setsid nohup bash /tmp/iter58_run_provenance_canary.sh </dev/null \
#     >/var/log/sentinel-iter58-provenance-canary.log 2>&1 &'
# Requires:
#   /tmp/iter58_hugsim_provenance.patch
#   /tmp/iter58_client_patch.py
set -x
echo "I58_START $(date -u)"

HUGSIM=/opt/sentinel-stack/HUGSIM
UNIAD_SIM=/opt/sentinel-stack/UniAD_SIM
SCEN_DIR=/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes
ZIP_DIR=/datasets/nuscenes-full/hugsim/scenes/nuscenes
SCENES_DIR=/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes
OUT_BASE=/datasets/nuscenes-full/hugsim/outputs/nusc_uniad
RUNS=/datasets/nuscenes-full/hugsim/iter58_runs
RUNS46=/datasets/nuscenes-full/hugsim/iter46_runs
MAPS_EXPANSION=/datasets/nuscenes-full/maps/expansion
REALCAR=/datasets/nuscenes-full/hugsim/3DRealCar
HUGSIM_PATCH=/tmp/iter58_hugsim_provenance.patch
MONITOR_PATCH=/tmp/iter58_client_patch.py
SHIM=/opt/sentinel-stack/hugsim-shim/sitecustomize.py
CKPT=/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth

SCENARIO=scene-0013-hard-00
FROZEN_SCENARIO_SHA=6947a5381c09485f20d5fed55eef2406d868ce047bdd44864aad81902f54e48e
FROZEN_HUGSIM_SHA=62c690d39fd90020e68a196bd8bcc1c4d4191f2e
FROZEN_UNIADSIM_SHA=5fb279e39912a5ac7f58e00d56b065cadcd0a749
FROZEN_CKPT_SHA=0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990
FROZEN_SHIM_SHA=5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c
FROZEN_IMAGE_ID=f73ef3884063
FROZEN_MONITOR_PATCH_SHA=6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c
FROZEN_HUGSIM_PATCH_SHA=49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd
EPISODE_TIMEOUT=1200
DISK_MIN_GIB=20

export PIXI_HOME=/datasets/nuscenes-full/hugsim-envs/pixi-home
export PIXI_CACHE_DIR=/datasets/nuscenes-full/hugsim-envs/pixi-cache
export PATH="$PIXI_HOME/bin:$PATH"
mkdir -p "$RUNS"

fail_gate() {
    echo "I58_PROVENANCE_FAIL $1 $(date -u)"
    exit 1
}

disk_guard() {
    local avail
    avail=$(df --output=avail -BG /datasets/nuscenes-full | tail -1 | tr -dc '0-9')
    if [ "$avail" -lt "$DISK_MIN_GIB" ]; then
        echo "I58_ABORT_DISK avail=${avail}G $(date -u)"
        exit 1
    fi
}

prep_scene() {
    local scene=$1
    if [ ! -d "$SCENES_DIR/$scene" ]; then
        python3 - "$ZIP_DIR/$scene.zip" "$scene" "$SCENES_DIR" <<'PYEOF'
import pathlib, shutil, sys, tempfile, zipfile
zip_path, scene, scenes_dir = sys.argv[1], sys.argv[2], sys.argv[3]
with tempfile.TemporaryDirectory(dir=scenes_dir) as tmp:
    zipfile.ZipFile(zip_path).extractall(tmp)
    hits = [p for p in pathlib.Path(tmp).rglob(scene) if (p / "cfg.yaml").is_file()]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one {scene} dir with cfg.yaml in {zip_path}, got {hits}")
    shutil.move(str(hits[0]), str(pathlib.Path(scenes_dir) / scene))
PYEOF
    fi
    local cfg="$SCENES_DIR/$scene/cfg.yaml"
    if [ ! -f "$cfg" ]; then
        echo "I58_PREP_FAIL scene=$scene cfg.yaml missing after extraction"
        return 1
    fi
    [ -f "$cfg.orig" ] || cp "$cfg" "$cfg.orig"
    python3 - "$cfg" "$SCENES_DIR/$scene" <<'PYEOF'
import re, sys
cfg, path = sys.argv[1], sys.argv[2]
text = open(cfg).read()
text = re.sub(r"(?m)^model_path:.*$", f"model_path: {path}", text)
open(cfg, "w").write(text)
PYEOF
}

apply_hugsim_patch() {
    [ "$(sha256sum "$HUGSIM_PATCH" | cut -d' ' -f1)" = "$FROZEN_HUGSIM_PATCH_SHA" ] \
        || fail_gate "hugsim patch sha mismatch"
    if git -C "$HUGSIM" apply --check "$HUGSIM_PATCH"; then
        git -C "$HUGSIM" apply "$HUGSIM_PATCH" || fail_gate "hugsim patch apply failed"
        echo "I58_HUGSIM_PATCH_APPLIED"
    elif git -C "$HUGSIM" apply --reverse --check "$HUGSIM_PATCH"; then
        echo "I58_HUGSIM_PATCH_ALREADY_APPLIED"
    else
        fail_gate "hugsim patch neither applies nor reverses"
    fi
    python3 -m py_compile "$HUGSIM/sim/utils/score_calculator.py" \
        || fail_gate "patched score_calculator compile failed"
}

run_one() {
    local arm=$1 run_idx=1 scene=${SCENARIO%-*-*}
    local mode_dashed=${SCENARIO#"$scene"-}
    local mode=${mode_dashed//-/_}
    local out_dir="$OUT_BASE/${scene}_${mode}"
    local dest="$RUNS/${SCENARIO}__${arm}_r${run_idx}"
    local enable=0
    [ "$arm" = "on" ] && enable=1
    if [ -f "$dest/episode_meta.json" ] && ! grep -q '"failed":true' "$dest/episode_meta.json"; then
        echo "I58_EP_SKIP_DONE $SCENARIO $arm r$run_idx"
        return 0
    fi
    prep_scene "$scene" || return 1
    local attempt rc steps hd marker decisions
    for attempt in 1 2; do
        disk_guard
        echo "I58_EP_START $SCENARIO $arm r$run_idx a$attempt $(date -u)"
        local t0
        t0=$(date -u +%s)
        docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true
        rm -rf "$out_dir"
        (cd "$HUGSIM" && SENTINEL_ENABLED=$enable timeout "$EPISODE_TIMEOUT" pixi run python -u closed_loop.py \
            --scenario_path "$SCEN_DIR/$SCENARIO.yaml" \
            --base_path configs/sim/nuscenes_base.yaml \
            --camera_path configs/sim/nuscenes_camera.yaml \
            --kinematic_path configs/sim/kinematic.yaml \
            --ad uniad --ad_cuda 0)
        rc=$?
        echo "I58_EP_RC=$rc $SCENARIO $arm r$run_idx a$attempt"
        docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true
        hd=$(python3 -c "
import json, math
try:
    v = json.load(open('$out_dir/eval.json')).get('hdscore')
    print(v if isinstance(v, (int, float)) and math.isfinite(v) else 'INVALID')
except Exception:
    print('MISSING')
")
        steps=$(grep -c 'sent' "$out_dir/output.txt" 2>/dev/null)
        [ -n "$steps" ] || steps=0
        marker=$(grep -c 'SENTINEL_I48_UNION_PATCH_LOADED enabled='$enable "$out_dir/output.txt" 2>/dev/null)
        [ -n "$marker" ] || marker=0
        decisions=1
        if [ "$arm" = "on" ]; then
            decisions=0
            if [ -s "$out_dir/sentinel_iter48_decisions.jsonl" ] \
                && [ "$(grep -c 'SENTINEL_I48_DECISION frame=' "$out_dir/output.txt" 2>/dev/null)" -gt 0 ]; then
                decisions=1
            fi
        fi
        if [ "$rc" = "0" ] && [ "$hd" != "MISSING" ] && [ "$hd" != "INVALID" ] \
            && [ "$steps" -gt 0 ] && [ "$marker" -gt 0 ] && [ "$decisions" = "1" ]; then
            rm -rf "$dest"
            mkdir -p "$dest"
            find "$out_dir" -type p -delete
            mv "$out_dir"/* "$dest"/
            rmdir "$out_dir" 2>/dev/null || true
            printf '{"scenario":"%s","arm":"%s","run":%s,"attempt":%s,"rc":%s,"hdscore":%s,"steps":%s,"start_epoch":%s,"end_epoch":%s}\n' \
                "$SCENARIO" "$arm" "$run_idx" "$attempt" "$rc" "$hd" "$steps" "$t0" "$(date -u +%s)" \
                > "$dest/episode_meta.json"
            echo "I58_EP_DONE $SCENARIO $arm r$run_idx ok hd=$hd steps=$steps"
            return 0
        fi
        echo "I58_EP_ATTEMPT_FAIL $SCENARIO $arm r$run_idx a$attempt rc=$rc hd=$hd steps=$steps marker=$marker decisions=$decisions"
    done
    rm -rf "${dest}__failed"
    mkdir -p "${dest}__failed"
    [ -d "$out_dir" ] && { find "$out_dir" -type p -delete; mv "$out_dir" "${dest}__failed/last_attempt"; }
    printf '{"scenario":"%s","arm":"%s","run":%s,"attempt":2,"rc":%s,"failed":true,"start_epoch":0,"end_epoch":%s}\n' \
        "$SCENARIO" "$arm" "$run_idx" "$rc" "$(date -u +%s)" > "${dest}__failed/episode_meta.json"
    echo "I58_EP_DONE $SCENARIO $arm r$run_idx FAILED"
    return 1
}

# ---- hard provenance gates ----
[ "$(git -C "$HUGSIM" rev-parse HEAD)" = "$FROZEN_HUGSIM_SHA" ] || fail_gate "HUGSIM SHA mismatch"
[ "$(git -C "$UNIAD_SIM" rev-parse HEAD)" = "$FROZEN_UNIADSIM_SHA" ] || fail_gate "UniAD_SIM SHA mismatch"
[ "$(sha256sum "$CKPT" | cut -d' ' -f1)" = "$FROZEN_CKPT_SHA" ] || fail_gate "checkpoint SHA mismatch"
[ "$(sha256sum "$SHIM" | cut -d' ' -f1)" = "$FROZEN_SHIM_SHA" ] || fail_gate "shim SHA mismatch"
[ "$(sha256sum "$MONITOR_PATCH" | cut -d' ' -f1)" = "$FROZEN_MONITOR_PATCH_SHA" ] || fail_gate "monitor patch SHA mismatch"
docker images --format '{{.ID}}' uniad:latest | grep -q "$FROZEN_IMAGE_ID" || fail_gate "Docker image mismatch"
echo "$FROZEN_SCENARIO_SHA  $SCENARIO.yaml" > "$RUNS/scenario.sha256"
(cd "$SCEN_DIR" && sha256sum -c "$RUNS/scenario.sha256") || fail_gate "scenario SHA mismatch"
for loc in singapore-onenorth singapore-hollandvillage singapore-queenstown boston-seaport; do
    [ -s "$MAPS_EXPANSION/$loc.json" ] || fail_gate "missing map expansion $loc"
done
[ "$(cat "$RUNS46/d0_verdict.txt" 2>/dev/null)" = "stochastic" ] || fail_gate "carried D0 missing"
if [ "$(docker ps -q | wc -l)" != "0" ]; then
    fail_gate "another Docker container is running"
fi

apply_hugsim_patch
PATCH_OUT=$(python3 "$MONITOR_PATCH")
echo "$PATCH_OUT"
echo "$PATCH_OUT" | grep -q ITER48_UNION_PATCHED || fail_gate "monitor patch did not apply"
E2E_PY_SHA=$(echo "$PATCH_OUT" | grep ITER48_E2E_PY_SHA256= | cut -d= -f2)
E2E_SH_SHA=$(echo "$PATCH_OUT" | grep ITER48_E2E_SH_SHA256= | cut -d= -f2)

LINKED=0
for car in "$REALCAR"/*/; do
    if [ -f "$car/gs.pth" ] && [ ! -e "$car/postprocess/shadow.pth" ]; then
        mkdir -p "$car/postprocess"
        ln -s .. "$car/postprocess/shadow.pth"
        LINKED=$((LINKED + 1))
    fi
done
echo "I58_REALCAR_COMPAT_LINKS linked=$LINKED"

{
    echo "{"
    echo "  \"hugsim_sha\": \"$(git -C "$HUGSIM" rev-parse HEAD)\","
    echo "  \"uniad_sim_sha\": \"$(git -C "$UNIAD_SIM" rev-parse HEAD)\","
    echo "  \"ckpt_sha\": \"$(sha256sum "$CKPT" | cut -d' ' -f1)\","
    echo "  \"shim_sha\": \"$(sha256sum "$SHIM" | cut -d' ' -f1)\","
    echo "  \"image_id\": \"$(docker images --format '{{.ID}}' uniad:latest)\","
    echo "  \"scenario\": \"$SCENARIO\","
    echo "  \"scenario_sha\": \"$FROZEN_SCENARIO_SHA\","
    echo "  \"hugsim_patch_sha\": \"$(sha256sum "$HUGSIM_PATCH" | cut -d' ' -f1)\","
    echo "  \"score_calculator_sha_after_patch\": \"$(sha256sum "$HUGSIM/sim/utils/score_calculator.py" | cut -d' ' -f1)\","
    echo "  \"monitor_patch_sha\": \"$(sha256sum "$MONITOR_PATCH" | cut -d' ' -f1)\","
    echo "  \"e2e_py_patched_sha\": \"$E2E_PY_SHA\","
    echo "  \"e2e_sh_patched_sha\": \"$E2E_SH_SHA\","
    echo "  \"schedule\": \"scene-0013-hard-00 OFF r1 then ON r1\","
    echo "  \"start_utc\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
    echo "}"
} > "$RUNS/receipts.json"
echo "I58_PROVENANCE_OK $(date -u)"

run_one off || exit 1
run_one on || exit 1

(cd "$RUNS" && find . -path ./prior_launches -prune -o -type f \( -name 'data.pkl' \
    -o -name 'infos.pkl' -o -name 'video.mp4' -o -name '*.ply' \) -print \
    | sort | xargs -r sha256sum > heavy_manifest_iter58.txt)
df -B1 /datasets/nuscenes-full | tail -1 >> "$RUNS/heavy_manifest_iter58.txt"
echo "I58_CANARY_DONE $(date -u)"
