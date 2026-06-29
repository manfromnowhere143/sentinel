# Sentinel — Pre-registration (frozen before results)

A runtime introspective safety monitor for a frozen end-to-end driving planner, evaluated in
**closed loop**. The bar below is fixed before any Sentinel result exists, so it cannot move.

## The number we are chasing

**Closed-loop safety on NeuroNCAP** (NeRF/NeuRAD photorealistic closed-loop simulator on public
nuScenes; CVPR 2024, arXiv 2404.07762). Primary metrics: the **NeuroNCAP safety score (0–5)** and
the **collision rate (%)** over the safety-critical scenarios (stationary / frontal / side).

### Published baselines to beat (frozen planners, from NeuroNCAP Table 1)

| planner (frozen) | NCAP score (↑) | collision rate (↓) |
|---|---|---|
| UniAD | 1.84 | 87.8% stationary · 98.4% frontal |
| VAD | 2.75 | 96.2% stationary · 99.6% frontal |

Proof-of-concept for the approach (not a settled SOTA): RiskMonitor / CATPlan (arXiv 2503.07425) —
a frozen-planner introspective monitor + simple braking — reports **+66.5% closed-loop
collision-avoidance** over the unmonitored planner (internal ablation).

## Hypotheses (frozen)

- **H1 (the win).** A Sentinel monitor + intervention on a *frozen* planner raises that planner's
  NeuroNCAP safety score and lowers its collision rate vs the **same unmonitored planner**, by a
  margin whose bootstrap CI excludes zero, on the public NeuroNCAP scenario set.
- **H2 (beat the proof-of-concept).** Sentinel beats a RiskMonitor-style baseline (frozen-planner
  collision-token monitor + braking) on the same scenarios — i.e., a *better* monitor, not just
  *a* monitor.
- **H3 (it generalizes).** The result holds on a second public closed-loop simulator (HUGSIM,
  3DGS, HD-Score) and/or a held-out scenario split — not a single-sim artifact.

## What counts as a win (and what does not)

- **Win:** H1 met with a CI excluding zero on the public NeuroNCAP set, reported honestly
  (per-scenario-class breakdown, no cherry-picking), ideally with H2 and/or H3.
- **Not a win:** an open-loop nuScenes L2/collision improvement (that metric is saturated and
  gameable — explicitly out of scope); a scenario-cherry-picked number presented as full-benchmark
  SOTA (the VaVAM lesson); an internal ablation dressed as a head-to-head.

## Honest risks, named up front

- The binding constraint is **infrastructure**: reproducing NeuroNCAP (NeuRAD rendering) + a frozen
  UniAD/VAD on single-digit GPUs. Iteration 1 is reproduction; if the baseline does not reproduce,
  that is reported.
- The published baselines are single-preprint, author-self-reported, not independently reproduced.
  Reproducing them is itself a contribution and our true starting line.
- A null is a real finding (a monitor that cannot beat the unmonitored planner closed-loop is
  worth knowing) and will be reported, not buried.

## Protocol freeze

Official NeuroNCAP scenarios and scoring; frozen public planner checkpoint (UniAD or VAD), hash
pinned; fixed seeds; drive/scenario-clustered bootstrap CIs; intervention policy and monitor
declared before scoring. `protocol/` pins checkpoints + scenario ids.

*Frozen 2026-06-30. Target chosen from a 110-agent adversarially-verified frontier survey
(23/25 claims confirmed). The bar in this file will not be weakened after results exist.*
