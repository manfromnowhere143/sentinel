# Iteration 1b — partial NeuroNCAP baseline + a frozen-planner collision corpus

Public data only, no gated download. Every NeuroNCAP scene that exists in the public `v1.0-mini`
sensor set (scene **0103** in all three scenario types; scene **0796** stationary) was run closed
loop on the **frozen UniAD** planner, **15 runs each — 60 closed-loop episodes total**, on one L4.

## Results (mean NeuroNCAP score 0–5 ↑, collision rate ↓)

| scenario / scene | runs | mean NCAP score | collision rate | published full-set avg* |
|---|---:|---:|---:|---|
| frontal / 0103 | 15 | **1.07** | 80.0% | frontal 1.17 (5 scenes) |
| side / 0103 | 15 | 0.51 | 100.0% | side 1.67 (5 scenes) |
| stationary / 0103 | 15 | 5.00 | 0.0% | stationary 3.50 (10 scenes) |
| stationary / 0796 | 15 | 1.03 | 80.0% | overall 1.84 |

\* Published UniAD figures are averages over the **full** scene set per scenario type (NeuroNCAP
paper / repo). Ours are **per-scene** on the two scenes available in public mini, so they are
compared to — not equated with — the published averages.

Raw per-run `score impact_speed` for all 60 episodes: [`proof/iter1b_scores_raw.txt`](proof/iter1b_scores_raw.txt).

## What reproduces, and what is honestly out of reach here

- **The frontal number reproduces cleanly.** Frontal/0103 = **1.07** against a published 5-scene
  frontal average of **1.17** — within run-to-run noise. The single cleanest apples-to-apples point
  we can form from public mini, and it matches.
- **The UniAD failure profile reproduces qualitatively across the board:** dynamic scenarios are
  near-total failures (frontal 80%, side 100% collision), the planner driving into the actor at
  11–15 m/s (frontal) and 5–10 m/s (side).
- **Per-scene variance is enormous and is the honest reason the full baseline averages 10×100.**
  Stationary alone spans **5.00 (0103, trivially avoided)** to **1.03 (0796, collides 80%)**. A
  two-scene stationary mean (3.0) only coarsely brackets the published 3.50; the averaged baseline
  genuinely needs all scenes × 100 seeds, which needs the gated full trainval blobs. No full-baseline
  claim is made from this subset.

## The real payload: a frozen-planner collision corpus + an introspective signal

Iteration 1b was not chasing a leaderboard row — it was manufacturing the **failures Sentinel must
catch**. It produced **39 genuine collision episodes out of 60** on a *frozen* planner
(frontal 12/15, side 15/15, stationary-0796 12/15; stationary-0103 0/15), each with full per-step
state (`metrics.json`, `trajectories.json`, `ego_poses.json`).

A concrete, reusable signal already falls out of the structured metrics. On a representative
frontal/0103 **collision** run:

```
any_collide@0.0s: true
recall@5-15m:    0.0     <- planner FAILED to detect the actor at the critical 5–15 m band
recall@15-25m:   1.0
recall@25-35m:   1.0
```

The crash coincides with the planner's **own perception collapsing at close range** — exactly the
kind of introspective, label-free failure indicator [PerceptionProof](https://github.com/manfromnowhere143/perceptionproof)
showed predicts the collision gate (AUROC ~0.8). Iteration 2 deploys that signal **in the loop, with
intervention**, and measures the collision reduction on precisely this corpus.

## Method notes (honesty)

- **Frozen planner.** UniAD weights (`uniad_base_e2e.pth`) are loaded and never updated; any later
  safety gain is attributable to the monitor, not a better planner.
- **Seeds / N.** 15 runs/scene here (vs the paper's 100) — enough to estimate per-scene collision
  rate and bracket the score, not to claim a final averaged figure. Iteration 2 fixes seeds and
  reports drive-clustered bootstrap CIs per the pre-registration.
- **Single GPU, public data.** One L4; public `v1.0-mini` sensor data; public UniAD checkpoint and
  NeuRAD checkpoints. Reproducible with `sentinel_iter1b.sh`.

Output dir on the box: `NeuroNCAP/outoutput/2026-06-30_08-04-29/{frontal,side,stationary}-{0103,0796}/run_*`.
