#!/bin/bash
# Iteration 49 hard/extreme-tier transfer-gate run: monitor-OFF vs released union
# (box-side, detached per the playbook:
#   sudo bash -c 'setsid nohup bash /tmp/iter49_run_hard_tier_gate.sh </dev/null \
#     >/var/log/sentinel-iter49-hard.log 2>&1 &'
# Requires /tmp/iter49_client_patch.py — a byte copy of the committed
# experiments/iter48_hugsim_transfer_gate/client_patch_union_iter48.py; this launcher
# REFUSES to start unless it hashes to the frozen iteration-48 value (F1 discipline).
# This is the iteration-48 launcher pattern with the frozen iteration-49 schedule: per
# scenario, in lexicographic order over the frozen first-26 subset of the 36 harder-tier
# yamls, WITHIN-LAUNCH BACK-TO-BACK  OFF r1 -> ON r1 -> OFF r2 -> ON r2  (104 episodes),
# per the carried stochastic D0 verdict (decided once in iteration 46; no re-probe).
# Markers: I49_START, I49_PRECHECK_OK|FAIL, I49_PROVENANCE_OK|FAIL,
# I49_EP_START/I49_EP_RC/I49_EP_DONE (arm-labelled), I49_EP_SKIP_DONE, I49_PREP_FAIL,
# I49_REALCAR_COMPAT_LINKS, I49_ABORT_DISK, I49_ABORT_CONSECUTIVE_FAILURES, I49_HARD_DONE.
# All frozen values mirror HYPOTHESIS.md exactly. Monitor parameters are the patch's
# baked-in frozen defaults — only SENTINEL_ENABLED is forwarded into the container.
set -x
echo "I49_START $(date -u)"

HUGSIM=/opt/sentinel-stack/HUGSIM
UNIAD_SIM=/opt/sentinel-stack/UniAD_SIM
SCEN_DIR=/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes
ZIP_DIR=/datasets/nuscenes-full/hugsim/scenes/nuscenes
SCENES_DIR=/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes
OUT_BASE=/datasets/nuscenes-full/hugsim/outputs/nusc_uniad
RUNS=/datasets/nuscenes-full/hugsim/iter49_runs
RUNS46=/datasets/nuscenes-full/hugsim/iter46_runs
MAPS_EXPANSION=/datasets/nuscenes-full/maps/expansion
REALCAR=/datasets/nuscenes-full/hugsim/3DRealCar
PATCH=/tmp/iter49_client_patch.py
SHIM=/opt/sentinel-stack/hugsim-shim/sitecustomize.py
CKPT=/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth

FROZEN_HUGSIM_SHA=62c690d39fd90020e68a196bd8bcc1c4d4191f2e
FROZEN_UNIADSIM_SHA=5fb279e39912a5ac7f58e00d56b065cadcd0a749
FROZEN_CKPT_SHA=0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990
FROZEN_SHIM_SHA=5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c
FROZEN_PATCH_SHA=6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c
FROZEN_IMAGE_ID=f73ef3884063
EPISODE_TIMEOUT=1200
DISK_MIN_GIB=20

export PIXI_HOME=/datasets/nuscenes-full/hugsim-envs/pixi-home
export PIXI_CACHE_DIR=/datasets/nuscenes-full/hugsim-envs/pixi-cache
export PATH="$PIXI_HOME/bin:$PATH"
mkdir -p "$RUNS"

# ---- frozen harder-tier manifest (all 36 verified; per-yaml SHAs from the read-only
#      inventory recorded in HYPOTHESIS.md) ----
MANIFEST=$RUNS/frozen_scenarios_hard.sha256
cat > "$MANIFEST" <<'EOF'
7b4b374bda9c9520114c9fdcb8ce8f3f91686dc9c0caacc261838ae4fe2a3442  scene-0013-extreme-00.yaml
6947a5381c09485f20d5fed55eef2406d868ce047bdd44864aad81902f54e48e  scene-0013-hard-00.yaml
ee3dafac4a7c8505829192906d4b39ad48cfed95d0e0fbebda64d86b99708776  scene-0038-extreme-00.yaml
5e1dafedccdde485834d5809dee2fcd3cc0b5c31f7315e454d6b4bd8b04b146d  scene-0038-hard-00.yaml
7d186ac9491de1cc3aab58a3a636ab0eb00088179f68d8a563214aaada3aa8af  scene-0041-extreme-00.yaml
ac8c82778713aecf6f9b1af9dbe646f51db5bde7a15b124a24f2f733e11cb1fa  scene-0041-hard-00.yaml
0bde23ad758f52aa74946c9db7b68888537308f020315476de7bcbb43b39a09d  scene-0051-extreme-00.yaml
10d048c8d76c06a72696e9fe519cb2361b5b54854eea4acaccedf8fdd14a9d39  scene-0051-hard-00.yaml
0a89b5660cf50720263b2379b0c2341c3b8c1a4d2fadb07eff30c7b519e26e2e  scene-0062-extreme-00.yaml
a318c5a49a43fc50e66b6b1b73bd53df165cca3c49e409e7b22f65276361e90e  scene-0062-hard-00.yaml
b223ef214c1ea8961b5103e34650b5e664f40797721aa18aa35ca50f2b70f4c0  scene-0064-extreme-00.yaml
2acfe05ed22c4c287daf74dabbbb6ef61d130bd9351088fb1be40b9270d6516e  scene-0064-hard-00.yaml
97b55b931c7ac5bf5991b1b0ba46907468dc4c6c8a3108df5b2dddbcf43ab0ed  scene-0071-extreme-00.yaml
1fd0c4b87d3b1fb28ecf0672b0779150fb0b866e93e168bd4a8f0babee3d6ee7  scene-0071-hard-00.yaml
d4e83c49e3240c8091294a5b545920f0c6f3b0e3498cb49c8b132e824c7cf1d9  scene-0138-extreme-00.yaml
8d0e3ec0d0068ae51047c0f3d2d63995d3a9dfeb60dc4071d7ec017d869fed2e  scene-0138-hard-00.yaml
c1ee5627487ece22e88937a43f82901fff1a823ab7447e45cac51fa2d922099f  scene-0166-extreme-00.yaml
33c2d545537a213510383e33bc406b4f4131bead5c3278d7a91d3375976a612a  scene-0166-hard-00.yaml
bd247f7111566c7ae2c232b1ce06d7e1e6173f1f4616a84131db413213af8065  scene-0167-extreme-00.yaml
ba58cafd0a571c4701ddba37aace7a3f4618d206796e749e1fb67b21edee8ff7  scene-0167-hard-00.yaml
40c32535a7ac7d0bff923374591d64ddeca89922182e391ba5b407718b46e08c  scene-0254-extreme-00.yaml
506229ef5fe677ffe2fee91b940a9d1b633a5d4177fbcd33b2fb0b4e7e2eb937  scene-0254-hard-00.yaml
f91d42db520f1e4d716fdbd3544fb701d4550062b2f9f933c86f3eb09c958ecf  scene-0383-extreme-00.yaml
82b36b555747ab3934085ba170799cbe957c7d2bcc64b3cb8495dc64111bc92a  scene-0383-hard-00.yaml
cd9c86bd4dbad2e6ff74f275f9fe43ad60aa0d9bf314971473ae2ddb01b703fb  scene-0411-extreme-00.yaml
9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9  scene-0411-hard-00.yaml
525e98e83d679248a54c3120096907be1cf8d332a4d608890eec019a4708f0a3  scene-0418-extreme-00.yaml
10953386474284abb0e63c85dfc98fb813d7986d4c9447a7db311fc8f76ce846  scene-0418-hard-00.yaml
d7c3118d40d7e5cf51153feb290b05faed69a76bcc50dc71f619e8e9257119ff  scene-0528-extreme-00.yaml
0599b2580b7f1b194e688b10b67bd6a9f610097a70db2e96a69b1bae70114e49  scene-0528-hard-00.yaml
333109cee4773926140c9a2305e01a12cab06a5c4c3a4b3503939ae75fad9115  scene-0661-extreme-00.yaml
e0089b4f14f251cbc739cbe8aff59ceb96b688e9a3017f12c5a76a03338aa50c  scene-0661-hard-00.yaml
b6cd72cae0c053c8d95fc7b981624bb254393be071a70986762bf15f42162ff1  scene-0920-extreme-00.yaml
037afe26aa2835fc3974b3ef6685c9941fe64fb64ffba30ab7f13bfb51cddf80  scene-0920-hard-00.yaml
8e32a4d7d95da9c508669e0f18b74c76527efcd3c773c9a1d8d02376fbd28c04  scene-0930-extreme-00.yaml
fe8682671f22f13cc17c9a315f52109002923b00635a8a4f22681ede32ac4d4d  scene-0930-hard-00.yaml
EOF

# The frozen scheduled subset: lexicographically first 26 of the 36 (13 scenes x 2 tiers).
SCHEDULE=$RUNS/schedule_26.txt
sort -k2 "$MANIFEST" | awk '{print $2}' | sed 's/\.yaml$//' | head -26 > "$SCHEDULE"
if [ "$(wc -l < "$SCHEDULE")" != "26" ] || [ "$(tail -1 "$SCHEDULE")" != "scene-0411-hard-00" ]; then
    echo "I49_PRECHECK_FAIL schedule derivation wrong"
    exit 1
fi

# ---- pre-launch asset pre-check gate (the iterations-46/47 lesson; read-only) ----
PRE_FAIL=0
for loc in singapore-onenorth singapore-hollandvillage singapore-queenstown boston-seaport; do
    [ -s "$MAPS_EXPANSION/$loc.json" ] || { echo "I49_PRECHECK_FAIL map json $loc"; PRE_FAIL=1; }
done
for scene in $(sed 's/-[a-z]*-00$//' "$SCHEDULE" | sort -u); do
    if [ ! -f "$SCENES_DIR/$scene/cfg.yaml" ]; then
        if [ ! -f "$ZIP_DIR/$scene.zip" ]; then
            echo "I49_PRECHECK_FAIL scene $scene: no extracted cfg.yaml and no zip"
            PRE_FAIL=1
        elif ! python3 -c "
import sys, zipfile
names = zipfile.ZipFile('$ZIP_DIR/$scene.zip').namelist()
sys.exit(0 if any(n.endswith('cfg.yaml') for n in names) else 1)
"; then
            echo "I49_PRECHECK_FAIL scene $scene: zip lists no cfg.yaml member"
            PRE_FAIL=1
        fi
    fi
done
for car in $(while read s; do grep 'shadow.pth' "$SCEN_DIR/$s.yaml"; done < "$SCHEDULE" \
        | sed 's/.*- //;s|/postprocess.*||' | sort -u); do
    [ -f "$REALCAR/$car/gs.pth" ] || { echo "I49_PRECHECK_FAIL realcar $car gs.pth missing"; PRE_FAIL=1; }
done
if [ "$PRE_FAIL" != "0" ]; then
    echo "I49_PRECHECK_FAIL $(date -u)"
    exit 1
fi
echo "I49_PRECHECK_OK $(date -u)"

# ---- apply the byte-identical iteration-48 monitor patch (the ONLY permitted delta) ----
if [ "$(sha256sum $PATCH | cut -d' ' -f1)" != "$FROZEN_PATCH_SHA" ]; then
    echo "I49_PROVENANCE_FAIL monitor patch is not the committed iter48 byte copy"
    exit 1
fi
PATCH_OUT=$(python3 "$PATCH")
echo "$PATCH_OUT"
if ! echo "$PATCH_OUT" | grep -q ITER48_UNION_PATCHED; then
    echo "I49_PROVENANCE_FAIL monitor patch did not apply"
    exit 1
fi
E2E_PY_SHA=$(echo "$PATCH_OUT" | grep ITER48_E2E_PY_SHA256= | cut -d= -f2)
E2E_SH_SHA=$(echo "$PATCH_OUT" | grep ITER48_E2E_SH_SHA256= | cut -d= -f2)

# ---- provenance gate (hard: refuse to start on any mismatch) ----
PROV_FAIL=0
[ "$(git -C $HUGSIM rev-parse HEAD)" = "$FROZEN_HUGSIM_SHA" ] || PROV_FAIL=1
[ "$(git -C $UNIAD_SIM rev-parse HEAD)" = "$FROZEN_UNIADSIM_SHA" ] || PROV_FAIL=1
[ "$(sha256sum $CKPT | cut -d' ' -f1)" = "$FROZEN_CKPT_SHA" ] || PROV_FAIL=1
[ "$(sha256sum $SHIM | cut -d' ' -f1)" = "$FROZEN_SHIM_SHA" ] || PROV_FAIL=1
docker images --format '{{.ID}}' uniad:latest | grep -q "$FROZEN_IMAGE_ID" || PROV_FAIL=1
(cd "$SCEN_DIR" && sha256sum -c "$MANIFEST") || PROV_FAIL=1
# Carried D0 verdict (decided once in iteration 46; no re-probe) must read stochastic.
if [ "$(cat "$RUNS46/d0_verdict.txt" 2>/dev/null)" != "stochastic" ]; then
    echo "I49_PROVENANCE_FAIL carried D0 verdict missing or not stochastic"
    PROV_FAIL=1
fi
if [ "$(docker ps -q | wc -l)" != "0" ]; then
    echo "I49_PROVENANCE_FAIL another container is running; single-tenant rule"
    exit 1
fi
if [ "$PROV_FAIL" != "0" ]; then
    echo "I49_PROVENANCE_FAIL $(date -u)"
    exit 1
fi

cp "$RUNS46/d0_verdict.txt" "$RUNS/d0_verdict_carried.txt"
{
    echo "{"
    echo "  \"hugsim_sha\": \"$(git -C $HUGSIM rev-parse HEAD)\","
    echo "  \"uniad_sim_sha\": \"$(git -C $UNIAD_SIM rev-parse HEAD)\","
    echo "  \"ckpt_sha\": \"$(sha256sum $CKPT | cut -d' ' -f1)\","
    echo "  \"shim_sha\": \"$(sha256sum $SHIM | cut -d' ' -f1)\","
    echo "  \"image_id\": \"$(docker images --format '{{.ID}}' uniad:latest)\","
    echo "  \"scenario_manifest_check\": \"pass\","
    echo "  \"precheck\": \"pass\","
    echo "  \"map_expansion_jsons\": \"present\","
    echo "  \"carried_d0_verdict\": \"$(cat "$RUNS46/d0_verdict.txt")\","
    echo "  \"monitor_patch_sha\": \"$(sha256sum $PATCH | cut -d' ' -f1)\","
    echo "  \"e2e_py_patched_sha\": \"$E2E_PY_SHA\","
    echo "  \"e2e_sh_patched_sha\": \"$E2E_SH_SHA\","
    echo "  \"monitor_params\": {\"cpa_margin\": 1.5, \"ttc_thresh\": 2.5,"
    echo "    \"min_closing\": 3.0, \"max_gap\": 30.0, \"min_score\": 0.3,"
    echo "    \"release_k\": 4, \"dt\": 0.5},"
    echo "  \"schedule\": \"26 hard/extreme scenarios x (OFF r1, ON r1, OFF r2, ON r2) = 104 episodes\","
    echo "  \"start_utc\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
    echo "}"
} > "$RUNS/receipts.json"
echo "I49_PROVENANCE_OK $(date -u)"

# ---- 3DRealCar layout-compatibility symlinks (iter46 amendment b; idempotent) ----
LINKED=0
for car in "$REALCAR"/*/; do
    if [ -f "$car/gs.pth" ] && [ ! -e "$car/postprocess/shadow.pth" ]; then
        mkdir -p "$car/postprocess"
        ln -s .. "$car/postprocess/shadow.pth"
        LINKED=$((LINKED + 1))
    fi
done
echo "I49_REALCAR_COMPAT_LINKS linked=$LINKED"

disk_guard() {
    local avail
    avail=$(df --output=avail -BG /datasets/nuscenes-full | tail -1 | tr -dc '0-9')
    if [ "$avail" -lt "$DISK_MIN_GIB" ]; then
        echo "I49_ABORT_DISK avail=${avail}G $(date -u)"
        exit 1
    fi
}

prep_scene() {
    # iter46 amendment (a): temp-dir extraction keyed on cfg.yaml; idempotent. Four
    # scheduled scenes (0167, 0254, 0383, 0411) are new to the pipeline and extract here.
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
        echo "I49_PREP_FAIL scene=$scene cfg.yaml missing after extraction"
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

# run_one <scenario> <arm off|on> <run_idx>  -> 0 on validated success (at most one retry)
run_one() {
    local scenario=$1 arm=$2 run_idx=$3
    local scene=${scenario%-*-*}
    local mode_dashed=${scenario#"$scene"-}
    local mode=${mode_dashed//-/_}
    local out_dir="$OUT_BASE/${scene}_${mode}"
    local dest="$RUNS/${scenario}__${arm}_r${run_idx}"
    local enable=0
    [ "$arm" = "on" ] && enable=1
    # resume-skip (iter46 amendment c): an episode completed by a prior launch stays valid.
    if [ -f "$dest/episode_meta.json" ] && ! grep -q '"failed":true' "$dest/episode_meta.json"; then
        echo "I49_EP_SKIP_DONE $scenario $arm r$run_idx (completed by a prior launch)"
        return 0
    fi
    prep_scene "$scene" || return 1
    local attempt rc steps hd marker decisions
    for attempt in 1 2; do
        disk_guard
        echo "I49_EP_START $scenario $arm r$run_idx a$attempt $(date -u)"
        local t0
        t0=$(date -u +%s)
        docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true
        rm -rf "$out_dir"
        (cd "$HUGSIM" && SENTINEL_ENABLED=$enable timeout $EPISODE_TIMEOUT pixi run python -u closed_loop.py \
            --scenario_path "$SCEN_DIR/$scenario.yaml" \
            --base_path configs/sim/nuscenes_base.yaml \
            --camera_path configs/sim/nuscenes_camera.yaml \
            --kinematic_path configs/sim/kinematic.yaml \
            --ad uniad --ad_cuda 0)
        rc=$?
        echo "I49_EP_RC=$rc $scenario $arm r$run_idx a$attempt"
        docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true
        hd=$(python3 -c "
import json, math, sys
try:
    v = json.load(open('$out_dir/eval.json')).get('hdscore')
    print(v if isinstance(v, (int, float)) and math.isfinite(v) else 'INVALID')
except Exception:
    print('MISSING')
")
        steps=$(grep -c 'sent' "$out_dir/output.txt" 2>/dev/null)
        [ -n "$steps" ] || steps=0
        # K2 substrate: the patch load marker must prove which code ran (both arms);
        # ON episodes must additionally carry per-frame decision lines + the JSONL.
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
                "$scenario" "$arm" "$run_idx" "$attempt" "$rc" "$hd" "$steps" "$t0" "$(date -u +%s)" \
                > "$dest/episode_meta.json"
            echo "I49_EP_DONE $scenario $arm r$run_idx ok hd=$hd steps=$steps"
            return 0
        fi
        echo "I49_EP_ATTEMPT_FAIL $scenario $arm r$run_idx a$attempt rc=$rc hd=$hd steps=$steps marker=$marker decisions=$decisions"
    done
    rm -rf "${dest}__failed"
    mkdir -p "${dest}__failed"
    [ -d "$out_dir" ] && { find "$out_dir" -type p -delete; mv "$out_dir" "${dest}__failed/last_attempt"; }
    printf '{"scenario":"%s","arm":"%s","run":%s,"attempt":2,"rc":%s,"failed":true,"start_epoch":0,"end_epoch":%s}\n' \
        "$scenario" "$arm" "$run_idx" "$rc" "$(date -u +%s)" > "${dest}__failed/episode_meta.json"
    echo "I49_EP_DONE $scenario $arm r$run_idx FAILED"
    return 1
}

CONSEC=0
note_result() {
    if [ "$1" = "0" ]; then
        CONSEC=0
    else
        CONSEC=$((CONSEC + 1))
        if [ "$CONSEC" -ge 3 ]; then
            echo "I49_ABORT_CONSECUTIVE_FAILURES $(date -u)"
            exit 1
        fi
    fi
}

# ---- frozen schedule: per scenario OFF r1 -> ON r1 -> OFF r2 -> ON r2, within-launch ----
while read -r s; do
    run_one "$s" off 1; note_result $?
    run_one "$s" on 1; note_result $?
    run_one "$s" off 2; note_result $?
    run_one "$s" on 2; note_result $?
done < "$SCHEDULE"

# ---- heavy-artifact manifest + done marker ----
(cd "$RUNS" && find . -path ./prior_launches -prune -o -type f \( -name 'data.pkl' \
    -o -name 'infos.pkl' -o -name 'video.mp4' -o -name '*.ply' \) -print \
    | sort | xargs -r sha256sum > heavy_manifest_iter49.txt)
df -B1 /datasets/nuscenes-full | tail -1 >> "$RUNS/heavy_manifest_iter49.txt"
echo "I49_HARD_DONE $(date -u)"
