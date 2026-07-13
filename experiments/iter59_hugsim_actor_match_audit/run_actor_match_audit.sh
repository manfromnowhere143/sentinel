#!/bin/bash
# Iteration 59 HUGSIM actor-match support audit.
# Box-side launch:
#   sudo bash -c 'setsid nohup bash /tmp/iter59_run_actor_match_audit.sh </dev/null \
#     >/var/log/sentinel-iter59-actor-match.log 2>&1 &'
# Requires:
#   /tmp/iter59_hugsim_provenance.patch
#   /tmp/iter59_client_patch.py
set -x
echo "I59_START $(date -u)"

HUGSIM=/opt/sentinel-stack/HUGSIM
UNIAD_SIM=/opt/sentinel-stack/UniAD_SIM
SCEN_DIR=/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes
ZIP_DIR=/datasets/nuscenes-full/hugsim/scenes/nuscenes
SCENES_DIR=/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes
OUT_BASE=/datasets/nuscenes-full/hugsim/outputs/nusc_uniad
RUNS=/datasets/nuscenes-full/hugsim/iter59_runs
RUNS46=/datasets/nuscenes-full/hugsim/iter46_runs
MAPS_EXPANSION=/datasets/nuscenes-full/maps/expansion
REALCAR=/datasets/nuscenes-full/hugsim/3DRealCar
HUGSIM_PATCH=/tmp/iter59_hugsim_provenance.patch
MONITOR_PATCH=/tmp/iter59_client_patch.py
SHIM=/opt/sentinel-stack/hugsim-shim/sitecustomize.py
CKPT=/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth

FROZEN_HUGSIM_SHA=62c690d39fd90020e68a196bd8bcc1c4d4191f2e
FROZEN_UNIADSIM_SHA=5fb279e39912a5ac7f58e00d56b065cadcd0a749
FROZEN_CKPT_SHA=0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990
FROZEN_SHIM_SHA=5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c
FROZEN_IMAGE_ID=f73ef3884063
FROZEN_MONITOR_PATCH_SHA=6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c
FROZEN_HUGSIM_PATCH_SHA=49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd
EPISODE_TIMEOUT=1200
DISK_MIN_GIB=20

AUDIT_IDS=(
    ttc_extreme_short
    mixed_extreme
    both_distinct_extreme
    nofire_hard_control
    cpa_medium_a
    ttc_medium_a
    cpa_medium_b
    ttc_extreme_b
)
SCENARIOS=(
    scene-0038-extreme-00
    scene-0062-extreme-00
    scene-0138-extreme-00
    scene-0041-hard-00
    scene-0071-medium-00
    scene-0071-medium-01
    scene-0166-medium-00
    scene-0383-extreme-00
)
SCENARIO_SHAS=(
    ee3dafac4a7c8505829192906d4b39ad48cfed95d0e0fbebda64d86b99708776
    0a89b5660cf50720263b2379b0c2341c3b8c1a4d2fadb07eff30c7b519e26e2e
    d4e83c49e3240c8091294a5b545920f0c6f3b0e3498cb49c8b132e824c7cf1d9
    ac8c82778713aecf6f9b1af9dbe646f51db5bde7a15b124a24f2f733e11cb1fa
    19542bfd37e20b34635f3b8279fa909a1a6dba0774b5c8076100b0969897faa5
    1fc17294a29cd90ba424c9d481d7f91f94aa8c5e9649ccf8c79115acc7a8744d
    f48075e69aa246bdd26b3fb468814151c412ebd0e94bf4f6c4313d3c6aba9430
    f91d42db520f1e4d716fdbd3544fb701d4550062b2f9f933c86f3eb09c958ecf
)

export PIXI_HOME=/datasets/nuscenes-full/hugsim-envs/pixi-home
export PIXI_CACHE_DIR=/datasets/nuscenes-full/hugsim-envs/pixi-cache
export PATH="$PIXI_HOME/bin:$PATH"
mkdir -p "$RUNS"

fail_gate() {
    echo "I59_ACTOR_MATCH_FAIL $1 $(date -u)"
    exit 1
}

disk_guard() {
    local avail
    avail=$(df --output=avail -BG /datasets/nuscenes-full | tail -1 | tr -dc '0-9')
    if [ "$avail" -lt "$DISK_MIN_GIB" ]; then
        echo "I59_ABORT_DISK avail=${avail}G $(date -u)"
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
        echo "I59_PREP_FAIL scene=$scene cfg.yaml missing after extraction"
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
        echo "I59_HUGSIM_PATCH_APPLIED"
    elif git -C "$HUGSIM" apply --reverse --check "$HUGSIM_PATCH"; then
        echo "I59_HUGSIM_PATCH_ALREADY_APPLIED"
    else
        fail_gate "hugsim patch neither applies nor reverses"
    fi
    python3 -m py_compile "$HUGSIM/sim/utils/score_calculator.py" \
        || fail_gate "patched score_calculator compile failed"
}

write_scenario_sha_file() {
    : > "$RUNS/frozen_scenarios_iter59.sha256"
    local idx
    for idx in "${!SCENARIOS[@]}"; do
        echo "${SCENARIO_SHAS[$idx]}  ${SCENARIOS[$idx]}.yaml" >> "$RUNS/frozen_scenarios_iter59.sha256"
    done
}

run_one() {
    local audit_id=$1 scenario=$2
    local scene=${scenario%-*-*}
    local mode_dashed=${scenario#"$scene"-}
    local mode=${mode_dashed//-/_}
    local out_dir="$OUT_BASE/${scene}_${mode}"
    local dest="$RUNS/${audit_id}__${scenario}__on"
    if [ -f "$dest/episode_meta.json" ] && ! grep -q '"failed":true' "$dest/episode_meta.json"; then
        echo "I59_EP_SKIP_DONE $audit_id $scenario on"
        return 0
    fi
    prep_scene "$scene" || return 1
    local attempt rc steps hd marker decisions
    for attempt in 1 2; do
        disk_guard
        echo "I59_EP_START $audit_id $scenario on a$attempt $(date -u)"
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
        echo "I59_EP_RC=$rc $audit_id $scenario on a$attempt"
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
        marker=$(grep -c 'SENTINEL_I48_UNION_PATCH_LOADED enabled=1' "$out_dir/output.txt" 2>/dev/null)
        [ -n "$marker" ] || marker=0
        decisions=0
        if [ -s "$out_dir/sentinel_iter48_decisions.jsonl" ] \
            && [ "$(grep -c 'SENTINEL_I48_DECISION frame=' "$out_dir/output.txt" 2>/dev/null)" -gt 0 ]; then
            decisions=1
        fi
        if [ "$rc" = "0" ] && [ "$hd" != "MISSING" ] && [ "$hd" != "INVALID" ] \
            && [ "$steps" -gt 0 ] && [ "$marker" -gt 0 ] && [ "$decisions" = "1" ]; then
            rm -rf "$dest"
            mkdir -p "$dest"
            find "$out_dir" -type p -delete
            mv "$out_dir"/* "$dest"/
            rmdir "$out_dir" 2>/dev/null || true
            printf '{"audit_id":"%s","scenario":"%s","arm":"on","attempt":%s,"rc":%s,"hdscore":%s,"steps":%s,"start_epoch":%s,"end_epoch":%s}\n' \
                "$audit_id" "$scenario" "$attempt" "$rc" "$hd" "$steps" "$t0" "$(date -u +%s)" \
                > "$dest/episode_meta.json"
            echo "I59_EP_DONE $audit_id $scenario on ok hd=$hd steps=$steps"
            return 0
        fi
        echo "I59_EP_ATTEMPT_FAIL $audit_id $scenario on a$attempt rc=$rc hd=$hd steps=$steps marker=$marker decisions=$decisions"
    done
    rm -rf "${dest}__failed"
    mkdir -p "${dest}__failed"
    [ -d "$out_dir" ] && { find "$out_dir" -type p -delete; mv "$out_dir" "${dest}__failed/last_attempt"; }
    printf '{"audit_id":"%s","scenario":"%s","arm":"on","attempt":2,"rc":%s,"failed":true,"start_epoch":0,"end_epoch":%s}\n' \
        "$audit_id" "$scenario" "$rc" "$(date -u +%s)" > "${dest}__failed/episode_meta.json"
    echo "I59_EP_DONE $audit_id $scenario on FAILED"
    return 1
}

# ---- hard provenance gates ----
[ "$(git -C "$HUGSIM" rev-parse HEAD)" = "$FROZEN_HUGSIM_SHA" ] || fail_gate "HUGSIM SHA mismatch"
[ "$(git -C "$UNIAD_SIM" rev-parse HEAD)" = "$FROZEN_UNIADSIM_SHA" ] || fail_gate "UniAD_SIM SHA mismatch"
[ "$(sha256sum "$CKPT" | cut -d' ' -f1)" = "$FROZEN_CKPT_SHA" ] || fail_gate "checkpoint SHA mismatch"
[ "$(sha256sum "$SHIM" | cut -d' ' -f1)" = "$FROZEN_SHIM_SHA" ] || fail_gate "shim SHA mismatch"
[ "$(sha256sum "$MONITOR_PATCH" | cut -d' ' -f1)" = "$FROZEN_MONITOR_PATCH_SHA" ] || fail_gate "monitor patch SHA mismatch"
docker images --format '{{.ID}}' uniad:latest | grep -q "$FROZEN_IMAGE_ID" || fail_gate "Docker image mismatch"
write_scenario_sha_file
(cd "$SCEN_DIR" && sha256sum -c "$RUNS/frozen_scenarios_iter59.sha256") || fail_gate "scenario SHA mismatch"
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
echo "I59_REALCAR_COMPAT_LINKS linked=$LINKED"

{
    echo "{"
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
    echo "  \"schedule\": \"eight ON episodes from Iter59 HYPOTHESIS\","
    echo "  \"start_utc\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
    echo "}"
} > "$RUNS/receipts.json"
echo "I59_PROVENANCE_OK $(date -u)"

idx=0
while [ "$idx" -lt "${#SCENARIOS[@]}" ]; do
    run_one "${AUDIT_IDS[$idx]}" "${SCENARIOS[$idx]}" || exit 1
    idx=$((idx + 1))
done

(cd "$RUNS" && find . -path ./prior_launches -prune -o -type f \( -name 'data.pkl' \
    -o -name 'infos.pkl' -o -name 'video.mp4' -o -name '*.ply' \) -print \
    | sort | xargs -r sha256sum > heavy_manifest_iter59.txt)
df -B1 /datasets/nuscenes-full | tail -1 >> "$RUNS/heavy_manifest_iter59.txt"
echo "I59_ACTOR_MATCH_DONE $(date -u)"
