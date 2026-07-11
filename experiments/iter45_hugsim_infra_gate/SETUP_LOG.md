# Iteration 45 setup log — running record (commit at every state change)

Operator: Claude (Fable 5) via delegated executor. All commands on `sentinel-gpu` unless
noted. Detached jobs follow the box playbook (`setsid nohup`, `set -x` logs under
`/var/log/sentinel-hugsim-*.log`, start/done markers). Box was IDLE (no Docker containers)
throughout this window; no NeuroNCAP run was touched.

## 2026-07-11 22:12-22:28 UTC — prerequisite disk cleanup (Stage 1 of this shift)

Verified cleanup per `docs/research/BOX_CLEANUP_2026-07-12.md`: root disk went from
15.4 GiB free (96%) to 42.1 GiB free (87%); `/datasets/nuscenes-full` has 266 GiB free.
Both targets for this lane met before any HUGSIM byte landed.

## 2026-07-11 22:31 UTC — repositories cloned (G-code provenance)

- `/opt/sentinel-stack/HUGSIM` @ commit `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`
- `/opt/sentinel-stack/UniAD_SIM` @ commit `5fb279e39912a5ac7f58e00d56b065cadcd0a749`
- No sentinel modification to either repo. The only build-required edit so far is the
  README-mandated two-step `pixi.toml` comment/uncomment dance, performed by script with the
  pristine file preserved as `pixi.toml.orig` (see environment step below).

## 2026-07-11 22:31 UTC — asset staging launched (detached)

- Tool: `huggingface_hub[cli] 1.23.0` (system pip, user install).
- Command (in `/tmp/hugsim_assets.sh`, log `/var/log/sentinel-hugsim-assets.log`, markers
  `HUGSIM_ASSETS_START` / `HUGSIM_ASSETS_RC=` / `HUGSIM_ASSETS_DONE`):
  `hf download XDimLab/HUGSIM --repo-type dataset --local-dir /datasets/nuscenes-full/hugsim`
- Release contents (from the HF tree API before download): `scenes/{nuscenes(19 zips),
  kitti360, pandaset, waymo}`, `3DRealCar/` vehicle captures, `nusc_map_cache.zip`,
  `scenarios.zip`; 306 files total.
- 22:37 UTC: 279/306 files, 51 GiB on disk, no errors. Manifest with per-file SHA256/sizes
  is generated after `HUGSIM_ASSETS_DONE` (G1 evidence, `proof-infra/hugsim_asset_manifest.txt`).

## 2026-07-11 22:34 UTC — planner checkpoint receipts (same-checkpoint premise)

- `/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth` SHA256
  `0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990`
- `/opt/sentinel-stack/UniAD/ckpts/motion_anchor_infos_mode6.pkl` SHA256
  `45761de4a965c590318987f43af7e7f50b8e043f9a2832a91246f4fd39bb57bb`

The UniAD_SIM client must be pointed at this exact checkpoint file (G2).

## 2026-07-11 22:34 UTC — HUGSIM environment build launched (detached)

- Box facts: NVIDIA L4 (23,034 MiB), driver `580.159.03`, system CUDA toolkit 12.9 at
  `/usr/local/cuda`, system Python 3.10.12, no conda. HUGSIM pins Python 3.11.10 +
  torch 2.4.1 cu118 via **pixi**, so the pixi toolchain was adopted as the README requires.
- Heavy-artifact rule: `PIXI_HOME` and `PIXI_CACHE_DIR` live under
  `/datasets/nuscenes-full/hugsim-envs/`, and `/opt/sentinel-stack/HUGSIM/.pixi` is a symlink
  to `/datasets/nuscenes-full/hugsim-envs/HUGSIM-dot-pixi` — nothing heavy lands on root.
- Script `/tmp/hugsim_env_setup.sh` (log `/var/log/sentinel-hugsim-envsetup.log`), markers:
  `HUGSIM_ENV_SETUP_START`, `HUGSIM_PIXI_STEP1_INSTALL_BEGIN`/`HUGSIM_PIXI_STEP1_RC=`
  (source packages commented, pypi/conda deps), `HUGSIM_PIXI_STEP2_INSTALL_BEGIN`/
  `HUGSIM_PIXI_STEP2_RC=` (pristine `pixi.toml` restored; source builds: hugsim-env,
  simple-knn, gsplat fork, unidepth, trajdata, tinycudann, pytorch3d, nuscenes-devkit fork,
  et al.), `HUGSIM_APEX_BEGIN`/`HUGSIM_APEX_RC=` (`pixi run install-apex`),
  `HUGSIM_ENV_SETUP_DONE`. `TORCH_CUDA_ARCH_LIST=8.9` exported for the L4.
- Known risk, stated up front (named falsifier "environment/CUDA incompatibility"): the
  source-built CUDA extensions (tinycudann, gsplat, pytorch3d, apex `--cuda_ext`) may reject
  the system nvcc 12.9 against torch cu118. If step 2 or apex fails on that mismatch, the
  next honest attempt is pinning a cu118-era nvcc inside the pixi env (conda-forge/nvidia
  `cuda-nvcc 11.8`) or building against the cu121+ torch wheel set; every attempt gets
  logged here before it runs.

## 2026-07-11 22:35-22:42 UTC — asset staging DONE; env build: falsifier probe + fallbacks

- **Assets staged (G1 raw bytes)**: `HUGSIM_ASSETS_RC=0`, `HUGSIM_ASSETS_DONE` 22:35:21 UTC.
  Per-file SHA256/size manifest generation launched detached
  (`/var/log/sentinel-hugsim-manifest.log`, markers `HUGSIM_MANIFEST_START/DONE`, output
  `/tmp/hugsim_asset_manifest.txt`) — to be committed as
  `proof-infra/hugsim_asset_manifest.txt` when done.
- **Smoke-scene staging**: extracted `scenes/nuscenes/scene-0013.zip`, `nusc_map_cache.zip`,
  and `scenarios.zip` to `/datasets/nuscenes-full/hugsim/extracted/` (python `zipfile`, no
  unsafe members possible via extraction API). `scene-0013/` contains
  `cfg.yaml, scene.pth, ground_param.pkl, meta_data.json, dynamic_*.pth, unicycle_*.pth` —
  already in exported simulation format, so no `--ver0` conversion is needed for this scene.
  The scenario's 3DRealCar vehicle `2024_07_05_10_58_02` exists in the staged `3DRealCar/`
  (110 vehicles, already-converted `gs.pth` + `wlh.json` format).
- **Frozen smoke-scenario rule resolves to `scene-0013-easy-00`** (lexicographically first
  nuScenes scenario at the easiest tier, present both in the repo's
  `configs/benchmark/nuscenes/` and the released `scenarios.zip`). Recorded here per the rule.
- **Pixi step 1** (pypi/conda deps, source packages commented): `HUGSIM_PIXI_STEP1_RC=0`.
- **Pixi step 2** (source builds): FAILED — the pre-declared "environment/CUDA
  incompatibility" falsifier probe fired exactly as predicted: gsplat's build calls torch
  `cpp_extension`, which raises `The detected CUDA version (12.9) mismatches the version
  that was used to compile PyTorch (11.8)`. `HUGSIM_PIXI_STEP2_RC=1`, `HUGSIM_APEX_RC=1`
  (same root cause).
- **Fallback attempt A** (22:38, `/tmp/hugsim_env_fix1.sh`, logged in the same file, markers
  `HUGSIM_ENV_FIX1_*`): pin `cuda-toolkit ==11.8.0` from the `nvidia/label/cuda-11.8.0`
  channel inside the pixi env, `CUDA_HOME` at the env prefix. FAILED
  (`HUGSIM_PIXI_FIX1_RC=1`): the env's `nvcc` still resolved to 12.9 — conda-forge's
  `cuda-toolkit` components won over the nvidia label pin, so the mismatch persisted.
- **Fallback attempt B** (22:41, `/tmp/hugsim_env_fix2.sh`, markers `HUGSIM_ENV_FIX2_*`,
  IN FLIGHT): keep torch `2.4.1` but switch the wheel index `cu118 -> cu124`, and pin the
  env-internal `cuda-toolkit = "12.9.*"` with `CUDA_HOME` at the env prefix; torch's
  extension builder accepts matching CUDA majors (12.x vs 12.x). This is a
  dependency-pin edit of the same pinned torch version, recorded here; `pixi.toml.orig`
  remains the pristine upstream file.

## UniAD_SIM client environment — decision pending

Options, in intended order of attempt (G2):

1. Run the client inside the existing sentinel `uniad:latest` Docker image (30.9 GB, on the
   box; it already runs this exact checkpoint under NeuroNCAP): bind-mount
   `/opt/sentinel-stack/UniAD_SIM` (the fork's code/configs), the existing
   `/opt/sentinel-stack/UniAD/ckpts`, and the HUGSIM output/pipe directory; named pipes
   (`mkfifo`) work across bind mounts. `tools/e2e.sh` path edits (its `${UniAD_PATH}`, conda
   activation, zsh shebang) are expected config edits and will be recorded here.
2. A dedicated environment per the UniAD/VAD READMEs (mmcv-era stack) if the Docker route
   fails on dependency or pipe-visibility grounds.

Not attempted yet in this window.

## 2026-07-11 22:55-23:00 UTC — config edits + client wrapper staged (while fix2 compiles)

All three are path/launch config edits of the kind the pre-registration allows and requires
recording; originals preserved with `.orig` suffixes:

- `HUGSIM/configs/sim/nuscenes_base.yaml` (original at `nuscenes_base.yaml.orig`):
  `realcar_path: /datasets/nuscenes-full/hugsim/3DRealCar`,
  `model_base: /datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes`,
  `uniad_path: /opt/sentinel-stack/UniAD_SIM/tools/e2e.sh`,
  `output_dir: /datasets/nuscenes-full/hugsim/outputs/nusc_`,
  `HD_map.path: /datasets/nuscenes-full` (`nusc_trainval`), vad/ltf paths updated for shape
  only (not installed, not used).
- `UniAD_SIM/tools/e2e.sh` (original at `e2e.sh.orig`): replaced the author's
  zsh+conda launcher with a wrapper that runs the UNMODIFIED client
  (`tools/closeloop/e2e.py projects/configs/stage2_e2e/base_e2e.py ckpts/uniad_base_e2e.pth`)
  inside the existing sentinel `uniad:latest` image, mounting `/opt/sentinel-stack/UniAD_SIM`
  as `/model`, the existing `/opt/sentinel-stack/UniAD/ckpts` (SHA receipts above) as
  `/model/ckpts`, and `/datasets/nuscenes-full/hugsim/outputs` at the SAME path inside the
  container so the `mkfifo` pipes are shared host<->container. `CUDA_VISIBLE_DEVICES` passes
  through; container name `hugsim_uniad_client`.
- Host `zsh` installed via apt (HUGSIM's `sim/utils/launch_ad.py` launches the client with
  `zsh <script>`; the wrapper itself is plain bash, which zsh executes via its shebang).

## 2026-07-11 22:53 UTC — G2 client half PASSES (checkpoint-mismatch falsifier did not fire)

Detached probe `/tmp/hugsim_client_probe.sh` (log `/var/log/sentinel-hugsim-clientprobe.log`,
markers `HUGSIM_CLIENT_PROBE_*`): inside `uniad:latest` with the wrapper's mounts, the
UNMODIFIED UniAD_SIM config `projects/configs/stage2_e2e/base_e2e.py` built the model
(plugin import OK) and `load_checkpoint('ckpts/uniad_base_e2e.pth', map_location='cpu')`
succeeded: `CLIENT_LOAD_OK params 131809024`, `HUGSIM_CLIENT_PROBE_RC=0`. First attempt
failed on a missing data file (`data/others/motion_anchor_infos_mode6.pkl`); staged the
box's existing copy (SHA `45761de4…`, receipt above) into `UniAD_SIM/data/others/` and the
retry passed. The GPU inference half of G2/G4 is exercised by the smoke run itself.

Smoke script staged at `/tmp/hugsim_smoke.sh` (log will be
`/var/log/sentinel-hugsim-smoke.log`, markers `HUGSIM_SMOKE_START/RC/DONE`, `timeout 7200`s
per the 120-minute G4 bound): `pixi run python -u closed_loop.py --scenario_path
/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes/scene-0013-easy-00.yaml
--base_path configs/sim/nuscenes_base.yaml --camera_path configs/sim/nuscenes_camera.yaml
--kinematic_path configs/sim/kinematic.yaml --ad uniad --ad_cuda 0`. NOT to be launched
until the pixi env build (fix2) finishes with RC=0 and the hugsim_env import check passes;
never alongside another GPU job.

## 2026-07-11 23:09-23:10 UTC — fix2 verdict: CUDA mismatch RESOLVED; new blocker simple-knn; fix3 launched

- **Fallback attempt B (fix2) result**: `HUGSIM_PIXI_FIX2_RC=1`, but the failure MOVED — no
  CUDA-version mismatch error remains (torch cu124 + env cuda-toolkit 12.9 resolved the
  falsifier's first form; gsplat proceeded past its previous failure point). The new failing
  package is the vendored `submodules/simple-knn`: `error: identifier "FLT_MAX" is
  undefined` — the known CUDA-12 header change (needs `#include <float.h>`).
- **fix3** (23:10, `/tmp/hugsim_env_fix3.sh`, markers `HUGSIM_ENV_FIX3_*`, IN FLIGHT):
  one-line build patch adding `#include <float.h>` to
  `submodules/simple-knn/simple_knn.cu` (original preserved as `simple_knn.cu.orig`), then
  `pixi install` again (cached wheels for already-built packages are reused) and
  `pixi run install-apex` on success. This is a required-to-build compatibility edit to a
  vendored build file, recorded here per the pre-registration; it does not touch simulator
  or client logic.

## 2026-07-11 23:09-23:25 UTC — env build COMPLETE; smoke iterations (G3 achieved; G4 in progress)

- **fix3 result**: `HUGSIM_PIXI_FIX3_RC=0` — the FULL pixi environment built (all source
  packages: gsplat fork, simple-knn, tinycudann, pytorch3d, unidepth, trajdata, hugsim-env,
  nuscenes-devkit fork, et al.). Import check passed:
  `HUGSIM_IMPORT_OK torch 2.4.1+cu124 cuda_avail True gsplat 1.2.0`
  (`/var/log/sentinel-hugsim-importcheck.log`, RC=0; `pip freeze` capture at
  `/tmp/hugsim_pip_freeze.txt`).
- **apex**: `HUGSIM_APEX_RC=1` (apex's own strict CUDA minor-version check, 12.9 vs torch's
  12.4). NOT blocking for this gate: `apex` is imported only under `data/InverseForm/`
  (reconstruction/data-prep toolchain), not by `closed_loop.py`, `sim/`, or `eval_render/`
  (verified by grep). Recorded honestly; a future reconstruction line would need it.
- **Smoke attempt 1** (23:12): fail-fast — host cv2 missing `libGL.so.1`; installed host
  `libgl1`+`libegl1` via apt (env step, recorded).
- **Smoke attempt 2** (23:13): simulator config loaded, client launched; env creation failed
  on the released scene's own `cfg.yaml` baking the author's absolute
  `model_path: /nas/users/...`. Edited the EXTRACTED copy's `model_path` to
  `/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0013` (original preserved
  as `cfg.yaml.orig`; the zip in the manifest is untouched).
- **Smoke attempt 3** (23:14): simulator fully up — `Ready for simulation`, first ego pose
  printed, `ground.ply`/`scene.ply` written (G3: the scenario renders). Client crashed on
  import: `open3d` then `mediapy` missing in `uniad:latest` (visualization imports of
  `tools/closeloop/visualizer.py`). Wrapper now `pip install -q open3d mediapy` into the
  ephemeral container at start; client code untouched.
- **Smoke attempt 4** (23:18:59): FIRST CLOSED-LOOP ROUND TRIPS — client `Ready for
  recieving`, `received`/`sent` for steps 0000 and 0001 with BEV/cam visualizations saved;
  sim advanced 3 ego poses (pipe-deadlock falsifier did NOT fire; the interface works).
  At step ~2 the client's UniAD forward raised `cusolver error:
  CUSOLVER_STATUS_INTERNAL_ERROR when calling cusolverDnCreate(handle)`; the author's
  except-path sets `results=None` and the next line crashes (`NoneType` not subscriptable),
  exiting the client. Killed the then-blocked simulator cleanly.
- **Smoke attempt 5** (23:22:32, IN FLIGHT): plain retry to test transience of the cusolver
  init failure. If it reproduces at the same step, next declared options (in order):
  (a) retry with `PYTORCH_CUDA_ALLOC_CONF` fragmentation guard in the client env;
  (b) an env-level linalg backend preference for the client interpreter (no client code
  edit); (c) if it persists, this is falsifier territory ("environment/CUDA incompatibility"
  applied to the client half) — publish the infrastructure null with the evidence.
  NeuroNCAP context: the same image ran full UniAD inference (incl. planning) for 6,474
  frames on this box/driver, so a hard incompatibility is not the default explanation.

## Resume point (exact — updated 2026-07-11 ~22:45 UTC)

1. Poll `/var/log/sentinel-hugsim-envsetup.log` for `HUGSIM_ENV_FIX2_DONE`; check
   `HUGSIM_PIXI_FIX2_RC` (and `HUGSIM_APEX_RC` — apex `--cuda_ext` may need the same
   CUDA-major logic; if apex alone fails, evaluate whether the simulation path actually
   imports InverseForm/apex before treating it as blocking; it is listed under
   `data/InverseForm`, i.e. the reconstruction/data-prep toolchain, likely NOT needed for
   `closed_loop.py`). If fix2 fails on a NEW package, read the failing package's error in
   the log, log the attempt here, and iterate; remaining declared options include cu121
   wheel set, or `pixi.toml` pin adjustments per package. Every attempt gets a
   `HUGSIM_ENV_FIX<N>_*` marker block in the same log.
2. Poll `/var/log/sentinel-hugsim-manifest.log` for `HUGSIM_MANIFEST_DONE`; fetch
   `/tmp/hugsim_asset_manifest.txt` into `proof-infra/hugsim_asset_manifest.txt` with the
   du/df receipts from that log; commit (G1 evidence).
3. Edit `configs/sim/nuscenes_base.yaml` paths (record the diff here):
   `realcar_path: /datasets/nuscenes-full/hugsim/3DRealCar`,
   `model_base: /datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes`,
   `uniad_path: /opt/sentinel-stack/UniAD_SIM/tools/e2e.sh` (or the docker wrapper),
   `output_dir: /datasets/nuscenes-full/hugsim/outputs/nusc_`,
   `HD_map.path: /datasets/nuscenes-full` (the iter28 official trainval root; note
   `scene-0013-easy-00.yaml` sets `load_HD_map: false`).
4. Verify the HUGSIM env imports (G2 renderer half): `pixi run python -c "import hugsim_env,
   torch; print(torch.cuda.is_available())"` from `/opt/sentinel-stack/HUGSIM`.
5. Set up the UniAD_SIM client per the decision list above (G2 client half): the client must
   load `ckpts/uniad_base_e2e.pth` (SHA receipt above). Inspect
   `UniAD_SIM/tools/closeloop/e2e.py` for its expected obs/plan pipe paths and any nuScenes
   metadata dependency before first launch.
6. Run the single monitor-OFF smoke for the recorded scenario `scene-0013-easy-00`
   (G3/G4) within the 120-minute bound, detached, log `/var/log/sentinel-hugsim-smoke.log`:
   `pixi run python closed_loop.py --scenario_path <scenario yaml> --base_path
   configs/sim/nuscenes_base.yaml --camera_path configs/sim/nuscenes_camera.yaml
   --kinematic_path configs/sim/kinematic.yaml --ad uniad --ad_cuda 0`. Collect
   `eval.json` (HD-Score), per-step logs, `data.pkl` receipts into `proof-infra/`.
7. Publish RESULT.md (pass or infrastructure null) per the pre-registration.

Nothing beyond the pre-registered Stage-0 scope has run: no monitor code touched HUGSIM, no
OFF-vs-ON work, no long GPU eval.
