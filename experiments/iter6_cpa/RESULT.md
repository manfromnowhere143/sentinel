# Iteration 6 — plan-vs-tracked-path CPA solves the side-impact case (at a selectivity cost)

Iteration 5 left one sharp open problem: the side T-bone, whose early warning lives in the ego's
converging motion, which the selective agent-closing gate deliberately removed — so side-impact stayed
at 100%. Iteration 6 replaces the closing-speed scalar with a real geometric test: predict the collision
from the **ego's planned path** against each agent's **tracked path** (closest point of approach over
both real trajectories, world frame). Brake if that closest approach falls below a collision margin.

## Result (OFF vs cpa, 3 scenes × 8 runs — higher count to cut noise)

| scene | OFF | cpa |
|---|---|---|
| stationary/0103 (clean) | 5.00 / 0% / 33.0 m | 5.00 / 0% / **22.3 m** |
| frontal/0103 | 1.31 / 75% / 36.1 m | **2.95** / 88% / 19.9 m |
| **side/0103** | 0.65 / **100%** / 20.3 m | **5.00 / 0%** / 6.1 m |
| **pooled safe-progress** | **2.32** | 2.17 |

## The win — the side-impact case is solved

**side-impact collapses from 100% to 0% (8/8 avoided), score 0.65 → 5.00.** This is the scene that
resisted every earlier monitor except the trivial over-braking one, and it is now solved *from the
geometry*: the side actor's tracked path crosses where the ego's plan will be, the CPA drops below the
margin, and the brake fires in time. At n=8 with a 100% → 0% swing this is a clean signal, not noise.
The plan-vs-tracked-path formulation is the right shape — it catches a threat regardless of which body's
motion causes the crossing, which is exactly what the ego-motion-dependent side case needed.

Frontal also improves in *severity*: score 1.31 → 2.95 (impact strongly mitigated), though the collision
*rate* (88% vs 75%) is within noise at n=8 — CPA softens the frontal crashes rather than preventing them.

## The honest cost — it over-brakes, so it is not net-positive here

CPA is **less selective** than iteration 5. On the benign clean scene the ego drives **22.3 m vs OFF's
33.0** — the 2.5 m CPA margin also flags the ego's *safe close pass* of the stationary object (the plan
legitimately passes it at ~2–3 m), so the monitor brakes when it shouldn't. Combined with the frontal
progress loss, **pooled safe-progress 2.17 < OFF 2.32** — at this margin CPA does not beat the
unmonitored planner on the deployment metric. It trades selectivity for catching the side case.

So across the campaign the two live approaches are now complementary, not combined:
- **iter 5 (agent-closing):** selective (clean = OFF exactly) but blind to the side case.
- **iter 6 (plan-vs-tracked-path CPA):** catches the side case (0%) but over-brakes benign close passes.

## Root cause and the next step — margin, not method

The clean-scene over-braking is a **margin calibration** problem, not a flaw in the CPA idea. A true
collision converges to ~0 m; a safe close pass of the stationary object stays at ~2–3 m; the side
T-bone's paths cross to <1 m. A 2.5 m margin cannot separate the 2–3 m pass from the <1 m crossing. The
fix (iteration 7) is a **tighter margin (~1.0–1.5 m = actual contact, not near-miss)** so CPA fires on
real crossings (side, frontal) but not on the benign pass — which should keep iteration 6's side win
*and* restore iteration 5's clean-scene selectivity. Equivalently: gate the CPA brake so it ignores a
static object the plan is smoothly passing. Bar unchanged: side collisions ≈ 0, clean progress ≈ OFF,
safe-progress > OFF (2.32 here), at n ≥ 8.

## Honesty about the metric

OFF's pooled safe-progress here is 2.32 (vs 2.08 in the iter-3/4 6-run baseline) — the baseline itself
moves with seeds and run count, so cross-iteration safe-progress numbers are not directly comparable;
only same-run arm-vs-arm deltas are. The robust, same-run facts of iteration 6 are: **side 100 → 0%
(large, clean)** and **clean progress 33 → 22 m (real over-braking)**. Those two, not the 0.15
pooled gap, are the result.

## Reproduce

`iter6_run.sh` (arms OFF / cpa) + `server_patch_cpa.py` (world-frame object-id tracking + plan-vs-path
CPA) → per-run table [`proof/i6_results.txt`](proof/i6_results.txt).
