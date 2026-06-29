# Iteration 1 — Reproduce the NeuroNCAP baseline (the infrastructure gate)

Goal: stand up the public NeuroNCAP closed-loop stack with a **frozen** planner and reproduce the
published baseline collision rate / NCAP score. This sets our starting line on the score tracker.
Per the engine: nothing is built on top until the baseline reproduces.

## The stack (three repos, one parent dir)

```
parent/
  neurad-studio/   # NeuRAD neural renderer (CVPR 2024) — provides PRETRAINED per-scene checkpoints
  NeuroNCAP/       # the closed-loop harness: actor manipulation, scenarios, scoring
  UniAD/           # frozen planner (baseline). VAD as a second baseline later.
```

## What we know (from recon)

- **No NeuRAD training, no full nuScenes.** NeuroNCAP ships **pretrained NeuRAD-L checkpoints** for
  the **14 hand-picked nuScenes sequences** that the scenarios are built on. So we need those 14
  sequences + the checkpoints, not the ~350 GB trainval blob.
- **Scoring:** each scenario (stationary / frontal / side) run 100× with fixed seed, averaged →
  NeuroNCAP score (0–5) and collision rate (%). Published UniAD baseline ≈ **1.84–2.11 score /
  ~60% collision** (stationary 3.50/32.4%, frontal 1.17/77.6%, side 1.67/71.2%).
- **GPU:** RTX 3060 12 GB minimum → an **L4 (24 GB)** is comfortable. Single-machine docker run of
  the full suite is slow (>24 h); we smoke on **1 scenario × few runs** first, then scale.
- **Run:** Docker images per repo; `single_machine_docker_run_eval.sh` (edit vars) → outputs;
  `python3 scripts/aggregate_results.py outputs/<date>` → score table.

## The one gate: nuScenes account

nuScenes requires a free account + license acceptance (nuscenes.org). We need it to pull the 14
sequences (+ metadata). Everything else (NeuRAD ckpts, UniAD ckpt, Docker build) needs no account.

## Steps

1. **Provision** L4 GPU VM (DLVM: CUDA + Docker + nvidia-docker), ~300 GB disk.
2. **Clone** neurad-studio, NeuroNCAP, UniAD into one parent dir.
3. **Download (no account):** NeuRAD pretrained weights (`scripts/downloads/download_neurad_weights.sh`),
   UniAD checkpoint (per UniAD README).
4. **nuScenes (gated):** with the account, pull the 14 NeuroNCAP sequences + metadata.
5. **Build** the Docker images.
6. **Smoke:** 1 scenario, a few runs → confirm a score + collision number come out end-to-end.
7. **Reproduce:** full 100×/scenario (or a powered subset) → compare to the published UniAD baseline.
   Match (within noise) ⇒ baseline reproduced ⇒ iteration 1 done, starting line set.

## Definition of done

Our reproduced UniAD NeuroNCAP score / collision rate matches the published numbers within
run-to-run noise (the eval is stochastic over the 100 seeds). If it does not reproduce, that is
reported honestly — reproducing single-preprint numbers is itself a contribution.

Honest note: this iteration is mostly **systems engineering**, not ML. It is the unglamorous gate
that makes every later iteration measurable. We do it carefully.
