# Iteration 1 — live status (the infrastructure gate)

> **GATE CLEARED (2026-06-30).** The full NeuroNCAP closed loop runs end-to-end on a single L4 and
> emits the real benchmark metric — `render_image → infer → update_actors → score`, frozen UniAD in
> the loop. Closed-loop smoke on **scene-0103 / stationary / 2 runs** → `ncap_score 5.0`,
> `any_collide=false`, `recall@5-35m=1.0` on both runs, per-run `metrics.json` written. Full proof +
> the eight integration blockers cleared (durable engine insights): [`PROOF_smoke_0103.md`](PROOF_smoke_0103.md).
> This retires the engineering risk the pre-reg named as the binding constraint. It is **not** the
> full averaged baseline (14 scenes × 100 runs) — that is now compute + the gated trainval blobs,
> not unknowns. No baseline claim is made from a single smoke point.

Tracking the NeuroNCAP stack build/download so nothing is lost. Updated as it progresses.

## Compute
- GPU box: **L4 (24 GB)**, `sentinel-gpu` @ us-west1-a (provisioned after an L4 region-wide
  stockout sweep). Docker + GPU-in-Docker **verified** (`GPU 0: NVIDIA L4`).
- Stack cloned to `/opt/sentinel-stack`: `NeuroNCAP/`, `neurad-studio/`, `UniAD/`.

## Docker images (the three the eval needs) — ALL BUILT
| image | status | size |
|---|---|---|
| `ncap:latest` | **BUILT** | 35 GB |
| `uniad:latest` | **BUILT** | 31 GB |
| `neurad:latest` | **BUILT** | 86 GB |

**neurad build — two fixes (the engineering insight).** The `neurad-studio` Dockerfile fought us:
1. **tiny-cuda-nn** failed `ModuleNotFoundError: No module named 'pkg_resources'`. Root cause: pip
   **build isolation** spins up a fresh build env with the latest setuptools (which *removed*
   `pkg_resources`), ignoring the pinned `setuptools<70`. Fix: `--no-build-isolation` (use the
   pinned setuptools) + `wheel ninja` in the env. → tiny-cuda-nn then compiled.
2. **The SfM source-build cascade** (pycolmap → hloc → pyceres → pixel-perfect-sfm) all failed on
   CMake/dependency configure. Key realization: these are **Structure-from-Motion / reconstruction**
   tools — used to *train* NeuRAD from raw images by estimating camera poses. We render from
   **pretrained checkpoints** on nuScenes (already calibrated), so none are needed at inference.
   Fix: skip all four (replaced with no-ops). → neurad image built.

The lesson, logged for the engine: when a research Dockerfile chains optional training-time deps,
an inference-only deployment can skip them — don't grind CMake deps you'll never call.

## Downloads
| artifact | needs account? | status |
|---|---|---|
| UniAD checkpoint `uniad_base_e2e.pth` (public GitHub release) | no | **DOWNLOADED** (972 MB) |
| NeuRAD rendering weights (pretrained, 14 NeuroNCAP scenes, public Dropbox) | no | **DOWNLOADED + EXTRACTED** (13 GB, 14 scene dirs) |
| UniAD data-infos (`nuscenes_infos_temporal_*.pkl`, HuggingFace OpenDriveLab) | no | pending |
| **nuScenes** v1.0 (14 sequences + CAN-bus + maps) at `/datasets/nuscenes` | **YES** | **THE remaining gate — needs a free nuScenes account** |

## The external gate — CLEARED
nuScenes account registered (license accepted). The three needed pieces — **trainval metadata
(0.43 GB), CAN-bus (0.73 GB), map expansion v1.3 (0.37 GB)** — were downloaded, routed through a
GCS bucket, and staged on the box at `/datasets/nuscenes/` (`v1.0-trainval/` 13 JSONs, `can_bus/`
per-scene pose/IMU, `maps/` basemaps + `expansion/`). The 290 GB sensor blobs were **not** pulled
— NeuRAD renders the images, so they are not needed (and would not fit). Extraction needed Python
`zipfile` (the box lacks `unzip`) — logged. **All run inputs are now on the box.**

## Remaining steps to the starting line
1. neurad image rebuild completes (3/3 images).
2. Download NeuRAD weights + UniAD data-infos (no account).
3. nuScenes data (gated).
4. Edit `single_machine_docker_run_eval.sh` vars (BASE_DIR, NUSCENES_PATH, checkpoints).
5. **Smoke:** one scenario, few runs → confirm a NeuroNCAP score + collision rate come out.
6. **Reproduce:** the published UniAD baseline (~1.84 score / ~60% collision) within run noise.

## Definition of done
Our reproduced UniAD NeuroNCAP score / collision rate matches the published numbers within the
stochastic 100-seed run noise → baseline reproduced → starting line set on the score tracker.
