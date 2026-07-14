#!/bin/bash
# Iteration 107 HUGSIM timing-aware batch execution.
# Box-side launch:
#   sudo bash -c 'setsid nohup bash /tmp/iter107_run_timing_aware_batch_execution.sh </dev/null \
#     >/var/log/sentinel-iter107-timing-aware-batch.log 2>&1 &'
# Requires:
#   /tmp/iter107_hugsim_provenance.patch
#   /tmp/iter107_client_patch.py
#   /tmp/iter107_timing_aware_batch_launch_manifest.json
set -x
echo "I107_START $(date -u)"

HUGSIM=/opt/sentinel-stack/HUGSIM
UNIAD_SIM=/opt/sentinel-stack/UniAD_SIM
SCEN_DIR=/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes
ZIP_DIR=/datasets/nuscenes-full/hugsim/scenes/nuscenes
SCENES_DIR=/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes
OUT_BASE=/datasets/nuscenes-full/hugsim/outputs/nusc_uniad
RUNS=/datasets/nuscenes-full/hugsim/iter107_runs
RUNS46=/datasets/nuscenes-full/hugsim/iter46_runs
MAPS_EXPANSION=/datasets/nuscenes-full/maps/expansion
REALCAR=/datasets/nuscenes-full/hugsim/3DRealCar
HUGSIM_PATCH=/tmp/iter107_hugsim_provenance.patch
MONITOR_PATCH=/tmp/iter107_client_patch.py
MANIFEST=/tmp/iter107_timing_aware_batch_launch_manifest.json
SHIM=/opt/sentinel-stack/hugsim-shim/sitecustomize.py
CKPT=/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth

FROZEN_MANIFEST_SHA=19d336364ab46f9e2e6bc881ffe4c7bad354471a851195b8609797d42e735f5a
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
    echo "I107_TIMING_AWARE_BATCH_FAIL $1 $(date -u)"
    exit 1
}

disk_guard() {
    local avail
    avail=$(df --output=avail -BG /datasets/nuscenes-full | tail -1 | tr -dc '0-9')
    if [ "$avail" -lt "$DISK_MIN_GIB" ]; then
        echo "I107_ABORT_DISK avail=${avail}G $(date -u)"
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
        echo "I107_PREP_FAIL scene=$scene cfg.yaml missing after extraction"
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
        echo "I107_HUGSIM_PATCH_APPLIED"
    elif git -C "$HUGSIM" apply --reverse --check "$HUGSIM_PATCH"; then
        echo "I107_HUGSIM_PATCH_ALREADY_APPLIED"
    else
        fail_gate "hugsim patch neither applies nor reverses"
    fi
    python3 -m py_compile "$HUGSIM/sim/utils/score_calculator.py" \
        || fail_gate "patched score_calculator compile failed"
}

write_manifest_files() {
    [ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" = "$FROZEN_MANIFEST_SHA" ] \
        || fail_gate "manifest sha mismatch"
    echo "$FROZEN_MANIFEST_SHA  iter107_timing_aware_batch_launch_manifest.json" \
        > "$RUNS/frozen_manifest.sha256"
    python3 - "$MANIFEST" "$RUNS/frozen_scenarios_iter107.sha256" "$RUNS/slot_schedule_iter107.tsv" <<'PYEOF'
import json, pathlib, sys
manifest_path, sha_out, schedule_out = map(pathlib.Path, sys.argv[1:])
manifest = json.loads(manifest_path.read_text())
slots = manifest.get("slots")
policy = manifest.get("duplicate_slot_policy", {})
if not isinstance(slots, list) or len(slots) != 13:
    raise SystemExit("manifest slots must be list length 13")
if policy.get("primary_execution_key") != "slot_id" or policy.get("scenario_deduplication_allowed") is not False:
    raise SystemExit("manifest duplicate-slot policy mismatch")
if [slot.get("slot_index") for slot in slots] != list(range(1, 14)):
    raise SystemExit("manifest slot indexes mismatch")
slot_ids = [slot.get("slot_id") for slot in slots]
if len(set(slot_ids)) != 13:
    raise SystemExit("manifest slot ids not unique")
with sha_out.open("w") as sha_f, schedule_out.open("w") as schedule_f:
    for slot in slots:
        scenario = slot["scenario"]
        digest = slot["scenario_sha256"]
        sha_f.write(f"{digest}  {scenario}.yaml\n")
        schedule_f.write(f"{slot['slot_id']}\t{scenario}\t{digest}\n")
PYEOF
}

run_one() {
    local slot_id=$1 scenario=$2
    local scene=${scenario%-*-*}
    local mode_dashed=${scenario#"$scene"-}
    local mode=${mode_dashed//-/_}
    local out_dir="$OUT_BASE/${scene}_${mode}"
    local dest="$RUNS/${slot_id}__${scenario}__on"
    if [ -f "$dest/episode_meta.json" ] && ! grep -q '"failed":true' "$dest/episode_meta.json"; then
        echo "I107_SLOT_SKIP_DONE $slot_id $scenario on"
        return 0
    fi
    prep_scene "$scene" || return 1
    local attempt rc steps hd marker decisions provenance
    for attempt in 1 2; do
        disk_guard
        echo "I107_SLOT_START $slot_id $scenario on a$attempt $(date -u)"
        local t0
        t0=$(date -u +%s)
        docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true
        rm -rf "$out_dir"
        (cd "$HUGSIM" && SENTINEL_ENABLED=1 timeout "$EPISODE_TIMEOUT" pixi run python -u closed_loop.py \
            --scenario_path "$SCEN_DIR/$scenario.yaml" \
            --base_path configs/sim/nuscenes_base.yaml \
            --camera_path configs/sim/nuscenes_camera.yaml \
            --kinematic_path configs/sim/kinematic.yaml \
            --ad uniad --ad_cuda 0)
        rc=$?
        echo "I107_SLOT_RC=$rc $slot_id $scenario on a$attempt"
        docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true
        hd=$(python3 -c "
import json, math
try:
    v = json.load(open('$out_dir/eval.json')).get('hdscore')
    print(v if isinstance(v, (int, float)) and math.isfinite(v) else 'INVALID')
except Exception:
    print('MISSING')
")
        provenance=$(python3 -c "
import json
try:
    data = json.load(open('$out_dir/eval.json'))
    print(1 if 'collision_provenance' in data else 0)
except Exception:
    print(0)
")
        steps=$(grep -c 'sent' "$out_dir/output.txt" 2>/dev/null)
        [ -n "$steps" ] || steps=0
        marker=$(grep -c 'SENTINEL_I48_UNION_PATCH_LOADED enabled=1' "$out_dir/output.txt" 2>/dev/null)
        [ -n "$marker" ] || marker=0
        decisions=0
        if [ -s "$out_dir/sentinel_iter48_decisions.jsonl" ] \
            && [ "$(grep -c 'SENTINEL_I48_DECISION frame=' "$out_dir/output.txt" 2>/dev/null)" -gt 0 ]; then
            decisions=1
        fi
        if [ "$rc" = "0" ] && [ "$hd" != "MISSING" ] && [ "$hd" != "INVALID" ] \
            && [ "$provenance" = "1" ] && [ "$steps" -gt 0 ] && [ "$marker" -gt 0 ] \
            && [ "$decisions" = "1" ]; then
            rm -rf "$dest"
            mkdir -p "$dest"
            find "$out_dir" -type p -delete
            mv "$out_dir"/* "$dest"/
            rmdir "$out_dir" 2>/dev/null || true
            printf '{"slot_id":"%s","scenario":"%s","arm":"on","attempt":%s,"rc":%s,"hdscore":%s,"steps":%s,"start_epoch":%s,"end_epoch":%s}\n' \
                "$slot_id" "$scenario" "$attempt" "$rc" "$hd" "$steps" "$t0" "$(date -u +%s)" \
                > "$dest/episode_meta.json"
            echo "I107_SLOT_DONE $slot_id $scenario on ok hd=$hd steps=$steps"
            return 0
        fi
        echo "I107_SLOT_ATTEMPT_FAIL $slot_id $scenario on a$attempt rc=$rc hd=$hd provenance=$provenance steps=$steps marker=$marker decisions=$decisions"
    done
    rm -rf "${dest}__failed"
    mkdir -p "${dest}__failed"
    [ -d "$out_dir" ] && { find "$out_dir" -type p -delete; mv "$out_dir" "${dest}__failed/last_attempt"; }
    printf '{"slot_id":"%s","scenario":"%s","arm":"on","attempt":2,"rc":%s,"failed":true,"start_epoch":0,"end_epoch":%s}\n' \
        "$slot_id" "$scenario" "$rc" "$(date -u +%s)" > "${dest}__failed/episode_meta.json"
    echo "I107_SLOT_DONE $slot_id $scenario on FAILED"
    return 1
}

# ---- hard provenance gates ----
[ "$(git -C "$HUGSIM" rev-parse HEAD)" = "$FROZEN_HUGSIM_SHA" ] || fail_gate "HUGSIM SHA mismatch"
[ "$(git -C "$UNIAD_SIM" rev-parse HEAD)" = "$FROZEN_UNIADSIM_SHA" ] || fail_gate "UniAD_SIM SHA mismatch"
[ "$(sha256sum "$CKPT" | cut -d' ' -f1)" = "$FROZEN_CKPT_SHA" ] || fail_gate "checkpoint SHA mismatch"
[ "$(sha256sum "$SHIM" | cut -d' ' -f1)" = "$FROZEN_SHIM_SHA" ] || fail_gate "shim SHA mismatch"
[ "$(sha256sum "$MONITOR_PATCH" | cut -d' ' -f1)" = "$FROZEN_MONITOR_PATCH_SHA" ] || fail_gate "monitor patch SHA mismatch"
docker images --format '{{.ID}}' uniad:latest | grep -q "$FROZEN_IMAGE_ID" || fail_gate "Docker image mismatch"
write_manifest_files
(cd "$SCEN_DIR" && sha256sum -c "$RUNS/frozen_scenarios_iter107.sha256") || fail_gate "scenario SHA mismatch"
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
echo "I107_REALCAR_COMPAT_LINKS linked=$LINKED"

{
    echo "{"
    echo "  \"manifest_sha\": \"$(sha256sum "$MANIFEST" | cut -d' ' -f1)\","
    echo "  \"hugsim_sha\": \"$(git -C "$HUGSIM" rev-parse HEAD)\","
    echo "  \"uniad_sim_sha\": \"$(git -C "$UNIAD_SIM" rev-parse HEAD)\","
    echo "  \"ckpt_sha\": \"$(sha256sum "$CKPT" | cut -d' ' -f1)\","
    echo "  \"shim_sha\": \"$(sha256sum "$SHIM" | cut -d' ' -f1)\","
    echo "  \"image_id\": \"$(docker images --format '{{.ID}}' uniad:latest)\","
    echo "  \"hugsim_patch_sha\": \"$(sha256sum "$HUGSIM_PATCH" | cut -d' ' -f1)\","
    echo "  \"score_calculator_sha_after_patch\": \"$(sha256sum "$HUGSIM/sim/utils/score_calculator.py" | cut -d' ' -f1)\","
    echo "  \"monitor_patch_sha\": \"$(sha256sum "$MONITOR_PATCH" | cut -d' ' -f1)\","
    echo "  \"e2e_py_patched_sha\": \"$E2E_PY_SHA\","
    echo "  \"e2e_sh_patched_sha\": \"$E2E_SH_SHA\","
    echo "  \"schedule\": \"thirteen ON slots from Iter106 timing-aware manifest\","
    echo "  \"slot_count\": 13,"
    echo "  \"start_utc\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
    echo "}"
} > "$RUNS/receipts.json"
echo "I107_TIMING_AWARE_OK $(date -u)"

while IFS=$'\t' read -r slot_id scenario _scenario_sha; do
    run_one "$slot_id" "$scenario" || exit 1
done < "$RUNS/slot_schedule_iter107.tsv"

(cd "$RUNS" && find . -path ./prior_launches -prune -o -type f \( -name 'data.pkl' \
    -o -name 'infos.pkl' -o -name 'video.mp4' -o -name '*.ply' \) -print \
    | sort | xargs -r sha256sum > heavy_manifest_iter107.txt)
df -B1 /datasets/nuscenes-full | tail -1 >> "$RUNS/heavy_manifest_iter107.txt"
echo "I107_TIMING_AWARE_BATCH_DONE $(date -u)"
