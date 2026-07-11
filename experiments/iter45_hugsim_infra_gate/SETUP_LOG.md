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

## UniAD_SIM client environment — decision pending

Options, in intended order of attempt (G2):

1. Run the client inside the existing sentinel UniAD Docker image (it already runs this
   exact checkpoint under NeuroNCAP); the HUGSIM pipe directory would be bind-mounted.
2. A dedicated environment per the UniAD/VAD READMEs (mmcv-era stack) if the Docker route
   fails on dependency or pipe-visibility grounds.

Not attempted yet in this window.

## Resume point (exact)

1. Poll `/var/log/sentinel-hugsim-assets.log` for `HUGSIM_ASSETS_DONE` and
   `HUGSIM_ASSETS_RC=0`. Then generate the per-file SHA256/size manifest of
   `/datasets/nuscenes-full/hugsim/` into `proof-infra/hugsim_asset_manifest.txt` (exclude
   the `.cache/huggingface` bookkeeping subtree), commit it (G1).
2. Poll `/var/log/sentinel-hugsim-envsetup.log` for `HUGSIM_ENV_SETUP_DONE`; check
   `HUGSIM_PIXI_STEP1_RC` / `HUGSIM_PIXI_STEP2_RC` / `HUGSIM_APEX_RC`. On the CUDA-mismatch
   failure mode, apply the pinning fallback above and relaunch the failed step only
   (`pixi.toml.orig` is the pristine file; the script is idempotent). Log every attempt here.
3. Unzip/stage what the configs expect (`scenes/nuscenes/*.zip`, `nusc_map_cache.zip`,
   `scenarios.zip` — inspect `configs/sim/*_base.yaml` and `configs/benchmark/nuscenes/` in
   the HUGSIM clone for expected layout), still under `/datasets/nuscenes-full/hugsim/`.
4. Set up the UniAD_SIM client env per the decision list above; record checkpoint path +
   SHA receipt in the client config; `tools/e2e.sh` needs `${UniAD_PATH}` set.
5. Apply the frozen smoke-scenario selection rule (lexicographically first supported
   nuScenes scenario, easiest tier), record the choice here, then run the single monitor-OFF
   smoke (G3/G4) within the 120-minute bound, detached, log
   `/var/log/sentinel-hugsim-smoke.log`.
6. Publish RESULT.md (pass or infrastructure null) per the pre-registration.

Nothing beyond the pre-registered Stage-0 scope has run: no monitor code touched HUGSIM, no
OFF-vs-ON work, no long GPU eval.
