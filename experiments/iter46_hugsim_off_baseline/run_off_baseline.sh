#!/bin/bash
# Iteration 46 monitor-OFF baseline run (box-side, detached per the playbook:
#   sudo bash -c 'setsid nohup bash /tmp/iter46_run_off_baseline.sh </dev/null \
#     >/var/log/sentinel-iter46-off.log 2>&1 &'
# Requires /tmp/iter46_d0_compare.py (scp of d0_compare.py) alongside.
# Markers: I46_OFF_START, I46_OFF_PROVENANCE_OK|FAIL, I46_OFF_EP_START/RC/DONE pairs,
# I46_OFF_D0_VERDICT=, I46_OFF_ABORT_DISK, I46_OFF_ABORT_CONSECUTIVE_FAILURES,
# I46_OFF_ALL_DONE. All frozen values below mirror HYPOTHESIS.md exactly.
#
# Amended 2026-07-12 (launcher defects only; see the HYPOTHESIS.md amendment note —
# no frozen bar/scenario/provenance value changed):
#   (a) prep_scene handles release zips that nest scene dirs under a top-level
#       'nuscenes/' prefix (7 of 19 zips do; the old extractall landed them at
#       $SCENES_DIR/nuscenes/<scene> and cfg.yaml was never found);
#   (b) idempotent '<car>/postprocess/shadow.pth -> ..' compatibility symlinks under
#       the staged 3DRealCar tree (released scenario yamls carry the authors' internal
#       layout suffix; the released car export is flat — upstream strips the same
#       suffix in HUGSIM eval_render/export_multiple_scenes.py);
#   (c) resume support: completed episodes are skipped (I46_OFF_EP_SKIP_DONE), a
#       recorded D0 verdict is carried (the branch decision is made once per the
#       pre-registration), and stale __failed dirs plus the prior receipts.json are
#       archived under $RUNS/prior_launches/<utc>/ as defect evidence.
# New markers: I46_OFF_PRIOR_LAUNCH_ARCHIVED, I46_OFF_REALCAR_COMPAT_LINKS,
# I46_OFF_PREP_FAIL, I46_OFF_EP_SKIP_DONE.
set -x
echo "I46_OFF_START $(date -u)"

HUGSIM=/opt/sentinel-stack/HUGSIM
UNIAD_SIM=/opt/sentinel-stack/UniAD_SIM
SCEN_DIR=/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes
ZIP_DIR=/datasets/nuscenes-full/hugsim/scenes/nuscenes
SCENES_DIR=/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes
OUT_BASE=/datasets/nuscenes-full/hugsim/outputs/nusc_uniad
RUNS=/datasets/nuscenes-full/hugsim/iter46_runs
HELPER=/tmp/iter46_d0_compare.py
SHIM=/opt/sentinel-stack/hugsim-shim/sitecustomize.py
CKPT=/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth

FROZEN_HUGSIM_SHA=62c690d39fd90020e68a196bd8bcc1c4d4191f2e
FROZEN_UNIADSIM_SHA=5fb279e39912a5ac7f58e00d56b065cadcd0a749
FROZEN_CKPT_SHA=0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990
FROZEN_SHIM_SHA=5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c
FROZEN_IMAGE_ID=f73ef3884063
EPISODE_TIMEOUT=1200
DISK_MIN_GIB=20

export PIXI_HOME=/datasets/nuscenes-full/hugsim-envs/pixi-home
export PIXI_CACHE_DIR=/datasets/nuscenes-full/hugsim-envs/pixi-cache
export PATH="$PIXI_HOME/bin:$PATH"
mkdir -p "$RUNS"

# ---- frozen scenario manifest (52 easy+medium, lexicographic; SHAs per HYPOTHESIS.md) ----
MANIFEST=$RUNS/frozen_scenarios.sha256
cat > "$MANIFEST" <<'EOF'
22d30c2a3dadf59451ff3704b50c412fb6fa74d261ee96dd4e6bf17c9a064735  scene-0013-easy-00.yaml
162bd65e0fa40d6f46a992063da665f858ccf78b00879b0a34fdfc76103a2401  scene-0013-medium-00.yaml
275066a06afb7a909748739e28de0eabc3d8c711d8c73f8769225a959ac5c3d5  scene-0038-easy-00.yaml
fb18b473300b9373e089fb0656caf533e6920de3314df4e6703b04cdb30d08c4  scene-0038-medium-00.yaml
cbc56796e802e964bca700662f34c77fb2500ee8ee32225820276521d4a230e2  scene-0038-medium-01.yaml
0d6f403dacf5f9f5b069f4fa9009e60dc0a8d76bb52d0843e18de63926d57756  scene-0041-easy-00.yaml
276024f3a668b64262829eecff89f27b9b318e32d71a85fdf5ccfbfa4f58d564  scene-0041-medium-00.yaml
3f082023ffc6d117897cb342c8e0b09d638579c84389e8beb30f9e224d2c5f93  scene-0041-medium-01.yaml
48ed82b0b0700803e77940fbfd401b34fe2f40d5d5d1f7deaa2e23053c3990f1  scene-0051-easy-00.yaml
bcdee66520d70d3666e51b00ed155e494f7f06772c9e50cfd2c4d5f678906016  scene-0051-medium-00.yaml
d239eabe85a5d6e518c86263d293d45bde2b50b4bf0c984268c78e5ee2db8b16  scene-0051-medium-01.yaml
5d49e3535d6b61eca97fe350baa000c35db9c7f75c4dd01f09712a64ec5e4429  scene-0062-easy-00.yaml
8ab4eaa941cf292710701f1a8e0d791ee81fede1874c985d0bf126951018e2ae  scene-0062-medium-00.yaml
299c8ed35a83d5bdfa4f2c9aaf42911d83a334f072adac457a4dbf348d7b5bd5  scene-0062-medium-01.yaml
b7665e1495ffe4fa045af495a44defe247e5497cb8d79330e5f054de86898392  scene-0064-easy-00.yaml
aef45943c6675c79872f305403632e72c47c4cf1ea7fc312a438a47009503b75  scene-0064-medium-00.yaml
e8a5c2d53b016257f7c1e0758137395c72ff7d36de368af8937ff7d2249efd98  scene-0064-medium-01.yaml
f04f159365d966c3bacf326375eb67463cf2614b85b9343eff2adec84d640750  scene-0071-easy-00.yaml
19542bfd37e20b34635f3b8279fa909a1a6dba0774b5c8076100b0969897faa5  scene-0071-medium-00.yaml
1fc17294a29cd90ba424c9d481d7f91f94aa8c5e9649ccf8c79115acc7a8744d  scene-0071-medium-01.yaml
8e4dd7879dc5571396f2cbc332175e869f9a806932e33665a79b34976abb9669  scene-0138-easy-00.yaml
a789c2df8e5a128e618b84a0e84197f6130c2de5b61cd5893bae1ec91817be98  scene-0138-medium-00.yaml
69e97a6c983982365b4336e95d2b48570729ab92984ebaa63b5e644118505f9a  scene-0138-medium-01.yaml
c83e3968a727d199c91dfda0987431fc943e47ca238d2a47f91ef7fc903bfb39  scene-0166-easy-00.yaml
f48075e69aa246bdd26b3fb468814151c412ebd0e94bf4f6c4313d3c6aba9430  scene-0166-medium-00.yaml
fa7d9c8912cf4ea62aa9c2498de516f048742cb93e903b59f0f7d6580138d30b  scene-0166-medium-01.yaml
3b4881b920dca9b410cd8112a329c331e5900642967e44ecb4da590235ee0060  scene-0167-easy-00.yaml
992431bd838b3ffd232c9f3ba052fc24553c5478e3fffed580ff1e6ba70341de  scene-0167-medium-00.yaml
9f230954ce903fe6587edc044a069559e6121dcbd7b77b6b83dc255df5fe084c  scene-0167-medium-01.yaml
70ffeb11cb5178d6244caef9f243f2fa3ee0ac864aebf6694626f4162508d496  scene-0254-easy-00.yaml
efca4498f7b08e25767a04ae8007f164c1a837c3f7ceb88e9c5a76525dfbb045  scene-0254-medium-00.yaml
9ec53138759dac721d6abbe939647574a8f1025ecfaad3e24c955fc0099c9ea9  scene-0254-medium-01.yaml
b0264012e4abdfacd69c24d66d584c5cc3bd403719d4337f635b861327382efb  scene-0383-easy-00.yaml
845eb2efdf4ea5e71fd38f3bd3a22798f8bc733a1547b569a080e57a10885671  scene-0383-medium-00.yaml
5db6b1fa03fa5125c5705ba7b0decdfe876075737ac7c5e0a23023a9b8f34bc3  scene-0383-medium-01.yaml
b240cd999d2965a3065c8bed180963f6ea2b142a71c0e9db060c131667424f4f  scene-0411-easy-00.yaml
e523239202841b593337756c8574066ec4ebf78c8e21327dc4d8fe0e6df48d5a  scene-0411-medium-00.yaml
6be5e30531971509201d03e7a562a3979932dcc4969a8d9f001379f9be903475  scene-0411-medium-01.yaml
43835067f13a42bc2b2ba5e1f6194c53e3ccf66f4ec97158f058cbacd11039e3  scene-0418-easy-00.yaml
7352e0f2274b5995cd2f7e4b25a40e33065a0ef360ddc100648ca37a2838e596  scene-0418-medium-00.yaml
8486d3105f9a3e9957bb8618009d105a57493d3818eba479cc7896153a95ae43  scene-0418-medium-01.yaml
b86f4ecdac8da1ccf5f63b47f8393977dacbcd60b2110046b93c30c80f09fdb6  scene-0528-easy-00.yaml
1601f6abb8c0f17f0582a51fa74f9d543928c1ff8c417588624e9727bfdc0fda  scene-0528-medium-00.yaml
496332fae21957d585067260f36f87d7ee83544edfe252ef22bc203273ca5311  scene-0528-medium-01.yaml
9505645725545ae4c28fd9ea909fbcc665631434af59527af8802322553540f5  scene-0661-easy-00.yaml
79201b40fba2e32e5194236a080629b51c89308cc3ff38d097e744294f5fb9bf  scene-0661-medium-00.yaml
8ab2194ea48cf5b0c5e1640fc421926956d49049b6049c182923cd03ce577504  scene-0661-medium-01.yaml
f28ceeb17036d5671943fae8428ef3c00c0bd52383c347fd7c3a3268e139e8c9  scene-0920-easy-00.yaml
8edbdea084cca4ad9b6e5548bab49b1edcc66309a54fbe163c8c5f3b7518512b  scene-0920-medium-00.yaml
27fbcc2c4639d010601169139e90e51647dfaf8f239df9cb1c9c83c314d34179  scene-0930-easy-00.yaml
ff5b7b16146780663da0a28be5f9b477fc223517bbf5111463243e72bb83b614  scene-0930-medium-00.yaml
e60488e152656de157742141c1cf68d834059c9645507edafb3764f2d6ad10d5  scene-0930-medium-01.yaml
EOF

# ---- provenance gate (hard: refuse to start on any mismatch) ----
PROV_FAIL=0
[ "$(git -C $HUGSIM rev-parse HEAD)" = "$FROZEN_HUGSIM_SHA" ] || PROV_FAIL=1
[ "$(git -C $UNIAD_SIM rev-parse HEAD)" = "$FROZEN_UNIADSIM_SHA" ] || PROV_FAIL=1
[ "$(sha256sum $CKPT | cut -d' ' -f1)" = "$FROZEN_CKPT_SHA" ] || PROV_FAIL=1
[ "$(sha256sum $SHIM | cut -d' ' -f1)" = "$FROZEN_SHIM_SHA" ] || PROV_FAIL=1
docker images --format '{{.ID}}' uniad:latest | grep -q "$FROZEN_IMAGE_ID" || PROV_FAIL=1
(cd "$SCEN_DIR" && sha256sum -c "$MANIFEST") || PROV_FAIL=1
if [ "$(docker ps -q | wc -l)" != "0" ]; then
    echo "I46_OFF_PROVENANCE_FAIL another container is running; single-tenant rule"
    exit 1
fi
if [ "$PROV_FAIL" != "0" ]; then
    echo "I46_OFF_PROVENANCE_FAIL $(date -u)"
    exit 1
fi

# ---- archive prior-launch failure evidence before overwriting receipts (amendment c) ----
shopt -s nullglob
STALE_FAILED=("$RUNS"/*__failed)
if [ ${#STALE_FAILED[@]} -gt 0 ] || { [ -f "$RUNS/receipts.json" ] && [ -s "$RUNS/d0_verdict.txt" ]; }; then
    PRIOR="$RUNS/prior_launches/$(date -u +%Y%m%dT%H%M%SZ)"
    mkdir -p "$PRIOR"
    [ -f "$RUNS/receipts.json" ] && cp "$RUNS/receipts.json" "$PRIOR/receipts.json"
    for d in "${STALE_FAILED[@]}"; do mv "$d" "$PRIOR/"; done
    echo "I46_OFF_PRIOR_LAUNCH_ARCHIVED $PRIOR failed_dirs=${#STALE_FAILED[@]}"
fi
shopt -u nullglob

{
    echo "{"
    echo "  \"hugsim_sha\": \"$(git -C $HUGSIM rev-parse HEAD)\","
    echo "  \"uniad_sim_sha\": \"$(git -C $UNIAD_SIM rev-parse HEAD)\","
    echo "  \"ckpt_sha\": \"$(sha256sum $CKPT | cut -d' ' -f1)\","
    echo "  \"shim_sha\": \"$(sha256sum $SHIM | cut -d' ' -f1)\","
    echo "  \"image_id\": \"$(docker images --format '{{.ID}}' uniad:latest)\","
    echo "  \"scenario_manifest_check\": \"pass\","
    echo "  \"start_utc\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
    echo "}"
} > "$RUNS/receipts.json"
echo "I46_OFF_PROVENANCE_OK $(date -u)"

# ---- 3DRealCar layout-compatibility symlinks (amendment b; idempotent, adds only links) ----
REALCAR=/datasets/nuscenes-full/hugsim/3DRealCar
LINKED=0
for car in "$REALCAR"/*/; do
    if [ -f "$car/gs.pth" ] && [ ! -e "$car/postprocess/shadow.pth" ]; then
        mkdir -p "$car/postprocess"
        ln -s .. "$car/postprocess/shadow.pth"
        LINKED=$((LINKED + 1))
    fi
done
echo "I46_OFF_REALCAR_COMPAT_LINKS linked=$LINKED"

SCENARIOS=$(cut -c67- "$MANIFEST" | sed 's/\.yaml$//')

disk_guard() {
    local avail
    avail=$(df --output=avail -BG /datasets/nuscenes-full | tail -1 | tr -dc '0-9')
    if [ "$avail" -lt "$DISK_MIN_GIB" ]; then
        echo "I46_OFF_ABORT_DISK avail=${avail}G $(date -u)"
        exit 1
    fi
}

prep_scene() {
    # iter45-recorded edit class: extract once, patch extracted cfg.yaml model_path only.
    # Amendment (a): extract via a temp dir and locate the scene dir by its cfg.yaml,
    # because 7 of the 19 release zips nest members under a top-level 'nuscenes/' prefix.
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
        echo "I46_OFF_PREP_FAIL scene=$scene cfg.yaml missing after extraction"
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

# run_one <scenario> <run_idx>  -> 0 on validated success (after at most one retry)
run_one() {
    local scenario=$1 run_idx=$2
    local scene=${scenario%-*-*}
    local mode_dashed=${scenario#"$scene"-}
    local mode=${mode_dashed//-/_}
    local out_dir="$OUT_BASE/${scene}_${mode}"
    local dest="$RUNS/${scenario}__r${run_idx}"
    # Amendment (c): resume — an episode completed by a prior launch stays valid.
    if [ -f "$dest/episode_meta.json" ] && ! grep -q '"failed":true' "$dest/episode_meta.json"; then
        echo "I46_OFF_EP_SKIP_DONE $scenario r$run_idx (completed by a prior launch)"
        return 0
    fi
    prep_scene "$scene"
    local attempt rc steps hd
    for attempt in 1 2; do
        disk_guard
        echo "I46_OFF_EP_START $scenario r$run_idx a$attempt $(date -u)"
        local t0
        t0=$(date -u +%s)
        docker rm -f hugsim_uniad_client >/dev/null 2>&1 || true
        rm -rf "$out_dir"
        (cd "$HUGSIM" && timeout $EPISODE_TIMEOUT pixi run python -u closed_loop.py \
            --scenario_path "$SCEN_DIR/$scenario.yaml" \
            --base_path configs/sim/nuscenes_base.yaml \
            --camera_path configs/sim/nuscenes_camera.yaml \
            --kinematic_path configs/sim/kinematic.yaml \
            --ad uniad --ad_cuda 0)
        rc=$?
        echo "I46_OFF_EP_RC=$rc $scenario r$run_idx a$attempt"
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
        if [ "$rc" = "0" ] && [ "$hd" != "MISSING" ] && [ "$hd" != "INVALID" ] && [ "$steps" -gt 0 ]; then
            rm -rf "$dest"
            mkdir -p "$dest"
            find "$out_dir" -type p -delete
            mv "$out_dir"/* "$dest"/
            rmdir "$out_dir" 2>/dev/null || true
            printf '{"scenario":"%s","run":%s,"attempt":%s,"rc":%s,"hdscore":%s,"steps":%s,"start_epoch":%s,"end_epoch":%s}\n' \
                "$scenario" "$run_idx" "$attempt" "$rc" "$hd" "$steps" "$t0" "$(date -u +%s)" \
                > "$dest/episode_meta.json"
            echo "I46_OFF_EP_DONE $scenario r$run_idx ok hd=$hd steps=$steps"
            return 0
        fi
        echo "I46_OFF_EP_ATTEMPT_FAIL $scenario r$run_idx a$attempt rc=$rc hd=$hd steps=$steps"
    done
    rm -rf "$RUNS/${scenario}__r${run_idx}__failed"
    mkdir -p "$RUNS/${scenario}__r${run_idx}__failed"
    [ -d "$out_dir" ] && { find "$out_dir" -type p -delete; mv "$out_dir" "$RUNS/${scenario}__r${run_idx}__failed/last_attempt"; }
    printf '{"scenario":"%s","run":%s,"attempt":2,"rc":%s,"failed":true,"start_epoch":0,"end_epoch":%s}\n' \
        "$scenario" "$run_idx" "$rc" "$(date -u +%s)" > "$RUNS/${scenario}__r${run_idx}__failed/episode_meta.json"
    echo "I46_OFF_EP_DONE $scenario r$run_idx FAILED"
    return 1
}

CONSEC=0
note_result() {
    if [ "$1" = "0" ]; then
        CONSEC=0
    else
        CONSEC=$((CONSEC + 1))
        if [ "$CONSEC" -ge 3 ]; then
            echo "I46_OFF_ABORT_CONSECUTIVE_FAILURES $(date -u)"
            exit 1
        fi
    fi
}

FIRST=$(echo "$SCENARIOS" | head -1)

# ---- D0 determinism probe: first scenario twice, back to back ----
# Amendment (c): the branch decision is made ONCE (pre-registration); a verdict recorded
# by a prior launch is carried, never re-derived.
if [ -s "$RUNS/d0_verdict.txt" ] && [ -f "$RUNS/d0_comparison.json" ] \
    && [ -f "$RUNS/${FIRST}__r1/episode_meta.json" ] && [ -f "$RUNS/${FIRST}__r2/episode_meta.json" ]; then
    echo "I46_OFF_D0_VERDICT=$(cat "$RUNS/d0_verdict.txt") (carried from the recorded D0 probe)"
else
    run_one "$FIRST" 1; note_result $?
    run_one "$FIRST" 2; note_result $?
    if [ -d "$RUNS/${FIRST}__r1" ] && [ -d "$RUNS/${FIRST}__r2" ]; then
        (cd "$HUGSIM" && pixi run python "$HELPER" "$RUNS/${FIRST}__r1" "$RUNS/${FIRST}__r2" \
            --out "$RUNS/d0_comparison.json" --verdict-file "$RUNS/d0_verdict.txt")
    else
        echo '{"verdict": "stochastic", "error": "D0 episode(s) failed to complete"}' > "$RUNS/d0_comparison.json"
        echo "stochastic" > "$RUNS/d0_verdict.txt"
        echo "I46_OFF_D0_VERDICT=stochastic (episodes failed)"
    fi
fi
VERDICT=$(cat "$RUNS/d0_verdict.txt")

# ---- branch loop (frozen in HYPOTHESIS.md) ----
if [ "$VERDICT" = "deterministic" ]; then
    for s in $(echo "$SCENARIOS" | tail -n +2); do
        run_one "$s" 1; note_result $?
    done
else
    for s in $(echo "$SCENARIOS" | head -26 | tail -n +2); do
        run_one "$s" 1; note_result $?
        run_one "$s" 2; note_result $?
    done
fi

# ---- heavy-artifact manifest + closing receipts ----
(cd "$RUNS" && find . -type f \( -name 'data.pkl' -o -name 'infos.pkl' -o -name 'video.mp4' \
    -o -name '*.ply' \) -exec sha256sum {} \; > heavy_manifest.txt)
df -B1 /datasets/nuscenes-full | tail -1 >> "$RUNS/heavy_manifest.txt"
echo "I46_OFF_ALL_DONE $(date -u)"
