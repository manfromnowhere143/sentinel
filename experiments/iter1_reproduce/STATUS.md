# Iteration 1 — live status (the infrastructure gate)

Tracking the NeuroNCAP stack build/download so nothing is lost. Updated as it progresses.

## Compute
- GPU box: **L4 (24 GB)**, `sentinel-gpu` @ us-west1-a (provisioned after an L4 region-wide
  stockout sweep). Docker + GPU-in-Docker **verified** (`GPU 0: NVIDIA L4`).
- Stack cloned to `/opt/sentinel-stack`: `NeuroNCAP/`, `neurad-studio/`, `UniAD/`.

## Docker images (the three the eval needs)
| image | status | size |
|---|---|---|
| `ncap:latest` | **BUILT** | 35 GB |
| `uniad:latest` | **BUILT** | 31 GB |
| `neurad:latest` | rebuilding (see fix below) | — |

**neurad build fix (the engineering insight).** First build failed on the `tiny-cuda-nn` torch
bindings: `ModuleNotFoundError: No module named 'pkg_resources'`. Root cause: pip **build
isolation** spins up a fresh build env with the latest setuptools (which has *removed*
`pkg_resources`), ignoring the Dockerfile's pinned `setuptools<70`. Fix: add
`--no-build-isolation` to the tiny-cuda-nn install (so it uses the pinned setuptools) plus
`wheel ninja` in the env. Patched `neurad-studio/Dockerfile`; rebuilding.

## Downloads
| artifact | needs account? | status |
|---|---|---|
| UniAD checkpoint `uniad_base_e2e.pth` (public GitHub release) | no | **DOWNLOADED** (972 MB) |
| NeuRAD rendering weights (pretrained, 14 NeuroNCAP scenes) | no | pending (locate script/host) |
| UniAD data-infos (`nuscenes_infos_temporal_*.pkl`, HuggingFace OpenDriveLab) | no | pending |
| **nuScenes** v1.0 (14 sequences + CAN-bus + maps) at `/datasets/nuscenes` | **YES** | **gated — needs a free nuScenes account** |

## The one external gate
nuScenes requires a free account + non-commercial license acceptance (nuscenes.org), exactly
like Waymo. Without it the closed-loop run cannot execute. Everything else proceeds without it.

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
