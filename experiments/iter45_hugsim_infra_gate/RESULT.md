# Iteration 45 - HUGSIM second-benchmark infrastructure gate: pass

Status: `HUGSIM_INFRA_GATE_PASS`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested by standing up the HUGSIM
benchmark stack on `sentinel-gpu` and running the single pre-registered monitor-OFF smoke
scenario once end-to-end. All four completion bars (G1-G4) are met. Every setup step, failed
attempt, and required config/build edit is in [`SETUP_LOG.md`](SETUP_LOG.md); the box-side
logs are committed under [`proof-infra/`](proof-infra/).

Claim boundary (registered, binding): **this gate proves only that the pipeline runs.** It
makes no transfer, benchmark, robustness, deployment, or safety claim. The single scenario's
HD-Score output (`hdscore 0.1677` on `scene-0013-easy-00`, with `nc/dac/ttc/comfort = 1.0`
and `rc = 0.1677`) is reported as evidence that the metric pipeline produces a finite score,
NOT as a UniAD performance number — one scenario supports no performance statement, and its
interpretation belongs to the future Stage-1 monitor-OFF reproduction pre-registration. No
monitor code touched HUGSIM or the client; no OFF-vs-ON work exists; the released union is
unchanged. The iteration-39 wording rules apply.

Primary evidence:

- [`proof-infra/hugsim_asset_manifest.txt`](proof-infra/hugsim_asset_manifest.txt) +
  [`proof-infra/asset_staging_receipts.txt`](proof-infra/asset_staging_receipts.txt) (G1)
- [`proof-infra/i45-envsetup.log`](proof-infra/i45-envsetup.log) (G2: the full environment
  build record — every failure and fix marker, `HUGSIM_ENV_*`/`HUGSIM_PIXI_*`)
- [`proof-infra/hugsim_pip_freeze.txt`](proof-infra/hugsim_pip_freeze.txt) (G2 env freeze)
- [`proof-infra/i45-smoke-run.log`](proof-infra/i45-smoke-run.log) (G3/G4 simulator-side log,
  all six smoke attempts, `HUGSIM_SMOKE_*` markers)
- [`proof-infra/i45-smoke-evidence.tar.gz`](proof-infra/i45-smoke-evidence.tar.gz) (G4:
  `eval.json` with the HD-Score output, client per-step log `output.txt`, per-frame
  `data.pkl`/`infos.pkl`, and the run `video.mp4`; SHA256
  `086b2e095b69c9643ce5b2a04755cd2686e5368b82143ad0c7ef90c2de092233`, verified identical on
  the box and after transfer)

## Verdict

| gate | result |
|---|---|
| S0 provenance | **PASS**: `HYPOTHESIS.md` committed alone (`333b9ce`) before any setup command ran on the box; every state change committed and pushed during execution with CI green (`a9de6b1` … `baf54ad`); box was IDLE throughout except this gate's own work |
| G1 assets staged | **PASS**: the complete `XDimLab/HUGSIM` release (306 files, `61,678,358,667` bytes incl. concurrent extraction) staged at `/datasets/nuscenes-full/hugsim/` with a committed per-file SHA256/size manifest; `hf download` RC=0; data-disk free space receipt `198,079,025,152` bytes after staging |
| G2 environments installed | **PASS**: HUGSIM pixi env built after three recorded attempts (final: torch `2.4.1+cu124`, env-internal `cuda-toolkit 12.9`, one-line `float.h` include patch to vendored `simple-knn`) — import check `HUGSIM_IMPORT_OK torch 2.4.1+cu124 cuda_avail True gsplat 1.2.0`; client half: the UNMODIFIED UniAD_SIM fork (`5fb279e3`) built its model inside the existing `uniad:latest` image and loaded the exact NeuroNCAP checkpoint `uniad_base_e2e.pth` (SHA `0ad0c2f5…`), `CLIENT_LOAD_OK params 131809024` — the checkpoint-mismatch falsifier did NOT fire. `apex` fails its own strict CUDA minor check and is used only by the reconstruction toolchain (`data/InverseForm`), not the simulation path; recorded, non-blocking |
| G3 one scenario renders | **PASS**: `scene-0013` (selected by the frozen lexicographic rule, easy tier) loaded from the staged export — `Ready for simulation`, `ground.ply`/`scene.ply` written, rendered observations produced; no `--ver0` conversion needed for this scene |
| G4 closed-loop smoke, monitor-OFF | **PASS**: the unmodified client drove the scenario end-to-end through the named pipes (16 ego poses / 15 steps, `received`/`sent` round trips logged per step with BEV/cam captures), the run terminated by the benchmark's own rule, and `hugsim_evaluate` produced `eval.json` with a finite HD-Score; wall clock ~2 minutes, far inside the frozen 120-minute bound — the pipe-client-deadlock and VRAM-overflow falsifiers did NOT fire |

## The one real incompatibility found, and its recorded remedy

The environment/CUDA falsifier fired in a narrow, diagnosable form and was resolved at the
environment level with zero client-code changes:

`uniad:latest` ships torch `1.9.1+cu111`; CUDA 11.1's cuSOLVER cannot initialize on the L4
(sm_89) at all — `cusolverDnCreate -> CUSOLVER_STATUS_INTERNAL_ERROR`, proven in isolation
with a 4x4 identity inverse (the NeuroNCAP stack never exercised GPU dense linalg, which is
why this never surfaced in iterations 1-42). The client's UniAD forward hits that op from
step 2 onward. Remedy: an interpreter-level shim (`/opt/sentinel-stack/hugsim-shim/
sitecustomize.py`, mounted read-only into the ephemeral container via `PYTHONPATH`) routes
the cuSOLVER-backed dense linalg ops (`inverse`/`linalg.inv`/`cholesky`/`svd`/`eigh`)
through CPU and returns results on the original device — same math, different execution
provider, client and model code untouched. Recorded in `SETUP_LOG.md`; the future Stage-1
pre-registration must carry this shim (or a properly rebuilt client environment) explicitly.

## Successor authorization (registered boundary)

This pass authorizes ONLY the writing of the Stage-1/2 pre-registration per the launch
packet (`docs/research/SECOND_BENCHMARK_TRANSFER_HUGSIM.md`): Stage 1 = monitor-OFF
reproduction on a frozen scenario subset with published-anchor sanity checks; Stage 2 =
OFF vs released union, seed-paired, with scene-clustered bootstrap CIs and the registered
falsifiers (over-braking/RC collapse, trigger mistuned for splat-rendered tracking noise,
renderer-specific artifacts). No such run, no monitor integration, no scenario sweep, and no
claim about transfer is authorized by iteration 45 itself.
