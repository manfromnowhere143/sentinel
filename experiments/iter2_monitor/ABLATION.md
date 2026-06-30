# Iteration 2 — ablation: what is actually doing the work (and the honest boundary)

The engine's ATTRIBUTE step. Two adversarial controls on the same corpus (6 runs/scene), against the
Sentinel TTC monitor and the unmonitored baseline, to answer the two questions a hostile reviewer asks
first: *does your introspective signal earn its keep, and is your monitor better than slamming the
brakes on everything?*

## The four arms

| scene | OFF (no monitor) | naive-proximity (brake if any object < 6 m, **no forecast**) | always-brake (brake every frame) | **Sentinel TTC** (brake if gap/closing-speed < 2.5 s) |
|---|---|---|---|---|
| **frontal/0103 — score** | 1.05 | 2.15 | 3.85 | **4.08** |
| **frontal/0103 — collision %** | 80 | **83** | 50 | **40** |
| **side/0103 — score** | 0.59 | 3.71 | 5.00 | **5.00** |
| **side/0103 — collision %** | 100 | 50 | 0 | **0** |
| **stationary/0103 (clean) — score** | 5.00 | 5.00 | 5.00 | 5.00 |

(Per-run data: `proof/abl_outcomes.tsv`; the TTC and OFF columns are the iter-2 A/B and G1-shadow runs.)

## Finding 1 — the introspective signal is essential, not decoration

A **naive distance brake (6 m, no forecast) is almost useless on the fast approaches**: frontal
collision rate 83% — *no better than the unmonitored 80%* — because at a 13 m/s closing speed a 6 m
trigger fires ~0.46 s before impact, far too late. The **Sentinel TTC trigger**, which reads each
agent's *own forecast displacement* to estimate closing speed and brakes on time-to-collision, cuts
frontal collisions to **40%** and side collisions from 100% to **0%**. The closing-speed / forecast
component is exactly what separates a working brake from a useless one. *The planner's own
introspective signal earns its keep.*

## Finding 2 — the honest boundary: on this corpus the safety score can't separate selective from trivial

**always-brake matches the TTC monitor on the safety score** (frontal 3.85 vs 4.08, side 5.0 vs 5.0,
clean scene 5.0 vs 5.0). The reason is structural and we state it plainly: **every scene in this
corpus is a collision setup where *stopping is the safe action*, and the "clean" scene
(stationary/0103) is also safe when stopped.** So the NeuroNCAP collision-safety metric, on this
collision-only 2-scene corpus, **cannot by itself distinguish a selective monitor from a car that just
refuses to move.**

This does **not** undo the iteration-2 result (a *monitored* frozen planner beats the *unmonitored*
one, pre-registered, CI excludes 0 — that comparison is valid and real). But it bounds the claim
precisely:

- **What is proven:** the planner's own forecast predicts its collisions (G1, AUROC 0.83) and, deployed
  via TTC, prevents/mitigates them (frontal 80→40%, side 100→0%), and this **requires** the
  introspective signal (Finding 1).
- **What is *not* proven here:** that the *selective* monitor beats a trivial always-brake in *net*
  driving value. That requires a **progress-sensitive** evaluation — scenes where the ego must reach a
  goal and always-braking would fail (normal-driving routes, route-completion / comfort metrics, the
  full NeuroNCAP benchmark). The selectivity is visible in the intervention pattern (the TTC monitor
  brakes on the danger scenes and leaves the clean scene alone — it fired on **0** of the clean-scene
  runs in the A/B, vs always-brake's 100%), but quantifying its *value* needs a benchmark that rewards
  progress. That is the explicit next experiment, not a swept-aside caveat.

## Why this is in the repo, prominently

A result that only reports the win and hides the control that matches it is the kind of work the
people we want to impress see through in five minutes. The contribution that survives scrutiny is the
narrow, true one: **a label-free introspective signal from a frozen planner predicts its collisions
(AUROC 0.83) and, with a time-to-collision brake that the signal makes possible, cuts them sharply —
and the naive baselines show the signal is doing the work, while the always-brake control shows
exactly which further benchmark is needed to claim selective value.**
