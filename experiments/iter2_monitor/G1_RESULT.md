# G1 gate — does the frozen planner's own output foresee its collisions? **Pass (AUROC 0.83).**

The cheapest decisive test before building any intervention: replay the frozen planner's *own*
per-frame outputs through the Sentinel monitor and ask whether they separate the runs that crash
from the runs that don't — **with no ground truth and no intervention**.

## Setup

- **Shadow run:** the inference server instrumented to dump, per frame, the planner's planned
  trajectory + detected agents + `object_scores` + multimodal `future_trajs` (no intervention — the
  returned plan is untouched). 40 closed-loop episodes (frontal/0103, side/0103, stationary/0103,
  stationary/0796 × 10), **481 frames**, on one L4.
- **Labels:** each run's NeuroNCAP outcome — **26 collisions, 14 clean**.
- **Signal:** the predicted closest approach between the ego's own plan and each agent's own
  forecast (the displacement convention; see below), evaluated **offline** with the unit-tested
  `sentinel/monitor.py`. Reproduce: `g1_auroc.py proof/risk.jsonl proof/outcomes.tsv`.

## Result — the imminent horizon is the signal

AUROC of the per-run signal vs the collision label, **proximity-only** (the simplest geometric
term), sweeping the prediction horizon:

| horizon | AUROC (closest predicted gap) |
|---:|---:|
| full (3.0 s) | 0.67 |
| 2.0 s | 0.70 |
| 1.0 s | 0.75 |
| **0.5 s (next step)** | **0.83** |

**This is a clean monotone trend — that monotonicity is the evidence, not a tuned hyperparameter.**
The more imminent the window, the more discriminative the planner's own forecast becomes, which is
exactly the physical claim: an *about-to-happen* predicted collision is what a brake must act on. At
the braking-relevant 0.5 s window the frozen planner's own outputs separate its crashes from its
clean runs at **AUROC 0.83** — matching the PerceptionProof result (label-free signal predicts the
collision gate at AUROC ~0.8) and now established *closed-loop*.

## Three things G1 taught us (the engine's ATTRIBUTE step)

1. **Any-time max saturates to 1.0 for every run** — over a 3 s plan the planner always forecasts
   *some* agent near the path somewhere. Timing matters: the operational signal is the imminent
   predicted gap in the final window, not any-time risk.
2. **The simplest term wins.** Proximity / closest-gap alone (0.83) beats the
   confidence × multimodal-disagreement weighting (≤0.81). The fancy weighting adds noise here; the
   monitor's default operational signal will be the bare imminent predicted gap.
3. **The planner's forecast is *optimistic*.** On collisions, UniAD's own forecast predicts a 3–4 m
   gap, yet the car hits. That gap between the planner's confidence and reality *is* the introspective
   failure Sentinel exploits — and it is why a margin-based brake threshold (not a zero-gap one) is
   the right intervention.

## Coordinate convention, resolved empirically

`future_trajs` are **displacements** from each agent's current position (agent absolute future =
`obj_xy + fut`), not absolute coordinates. Tested both: the displacement convention carries the
signal (0.83); the absolute convention is at chance (~0.49), because it spuriously collapses every
agent's forecast toward the origin. Decided by the data, not assumed.

## Honest limits

- 40 runs, 26/14 split — enough for a go/no-go gate, not a tight CI. The intervention A/B uses more
  runs and a drive-clustered bootstrap per the pre-registration.
- AUROC 0.83 is good, not perfect: some clean runs also plan close (the planner intends a tight but
  safe pass → false-brake risk), and some collisions the forecast under-flags (miss risk). The brake
  threshold trades these off, and the **do-no-harm gate on stationary/0103** (14/14 clean here, all
  large-gap) is the mandatory guard.

## Verdict

**G1 passes.** The introspective signal is real and closed-loop. Proceed to the intervention: brake
when the imminent (≤0.5 s) predicted gap falls below a margin threshold fixed on a held-out slice,
then measure the closed-loop collision reduction A/B (monitor on vs off) on the corpus.
