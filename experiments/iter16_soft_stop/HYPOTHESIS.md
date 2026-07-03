# Iteration 16 — softer than a stop: pre-registration

Frozen before the run. Iteration 15 ([`../iter15_latch_release/RESULT.md`](../iter15_latch_release/RESULT.md))
established that the residual deployment gap against the unmonitored planner is a *cost-of-stopping*
floor, not a triggering flaw: the released-union matches the union's safety exactly and recovers
+0.246 safe-progress, yet released − OFF stays at +0.076 with a CI that includes zero. The
committed decision log quantifies the remaining cost: **69 of 120 episodes intervene; 31 end
still latched at 0 m/s; every one of the 49 releases resumes from a standstill** inside a fixed
episode horizon that cannot refund the spent time.

The named successor mechanism is an intervention softer than a full stop. This iteration tests it.

## The change (one mechanism, nothing else)

While the latch is active, instead of commanding a zero trajectory (full stop), the returned
trajectory is the **planner's own current plan re-parameterized by arc length to a crawl**: waypoint
*k* is placed on the planner's polyline at arc length `min(planned_arclength_k, v_crawl · 0.5 s · k)`
with **v_crawl = 2.0 m/s**. The path geometry is untouched and the profile can only be *slower*
than the planner's — respecting the iteration-11 asymmetry (the ego follows the planner's own
in-distribution path; nothing is invented). Triggers, thresholds, and the iteration-15 release rule
(K = 4 consecutive clear frames against the planner's current plan) are all unchanged. The only
difference from the released-union is the speed commanded while latched: ~2 m/s instead of 0.

### Why 2.0 m/s, fixed before the run

From the committed full-benchmark evidence (`../full14_benchmark/proof/sentinel-full14.log`):
colliding unmonitored episodes impact at class means **16.6 m/s (frontal), 7.9 (side), 8.5
(stationary)**; the union's stop still takes frontal contacts at 10.1 m/s mean. A 2.0 m/s residual
is 12–25% of those observed collision speeds, so any crawl-caused contact sits at the bottom of
NeuroNCAP's impact-speed severity scale, and an unavoidable contact is at most ~2 m/s harder than
under the stop. It is also ordinary walking/creep pace. **No speed sweep will be run**; a sweep
after seeing data would be post-hoc. One value, chosen from committed evidence, fixed here.

## H16 (pre-registered)

Against the committed comparators (full14 OFF and union arms; iter15 released arm — identical
deterministic episodes, seed-paired; only the crawl arm is run):

1. **Safety held.** Pooled NCAP score within 0.15 of the released-union's 3.09; per-class
   collision rates: side ≤ 45%, stationary ≤ 25% (the iteration-15 bars, unchanged); frontal
   class score no worse than unmonitored OFF's 1.32.
2. **The deployment verdict flips (primary).** Pooled safe-progress (crawl − OFF) > 0 with the
   within-pair bootstrap CI excluding 0 — the criterion both the union and the released-union
   failed at benchmark scope.
3. **Dominance over the current best.** Safe-progress (crawl − released) > 0 with the CI
   excluding 0.

H16 is met in full only if all three hold. Criterion 2 alone (with 1) completes the deployment
story; criterion 3 alone (with 1) merely improves the best configuration.

## Falsifiers, named up front

- **Crawl into the crossing actor.** The stop halts short of the T-bone's crossing point; a crawl
  keeps creeping toward it. If side-class collisions exceed **45%**, the null publishes and the
  full stop stands as the correct intervention.
- **Creep into the stationary obstacle.** The stop preserves stationary avoidance (union 17%
  collisions); a crawl may convert avoided obstacles into low-speed taps. If stationary
  collisions exceed **25%** or the stationary class score falls below OFF's 3.52, that is the
  same null with a second mechanism: softness needs threat-class routing (reported, not built
  post-hoc).
- **Frontal severity.** The 2 m/s residual adds to unavoidable head-on contacts. If the frontal
  class score falls below OFF's 1.32, the crawl is worse than no monitor on frontal — reported.
- **The floor is deeper than softness.** If safety holds but crawl − OFF still includes zero, the
  fixed-horizon cost is not recoverable by intervention softness at all — published as the honest
  boundary of what latch calibration can buy.

## Protocol

One new arm (`crawl`: `SENTINEL_CRAWL_V=2.0`, `SENTINEL_RELEASE_K=4`, all other env identical to
iteration 15) on all 20 scene-scenario pairs × 6 runs = 120 episodes. Patch:
[`server_patch_union_crawl.py`](server_patch_union_crawl.py) (git-checkout of `server.py`, then the
iteration-15 patch plus the crawl re-parameterization). Analysis:
[`analyze_iter16.py`](analyze_iter16.py) — four-way per-pair/per-class tables, pooled NCAP and
safe-progress, seed-paired bootstrap CIs for crawl−OFF, crawl−union, crawl−released, and the
decision-log falsifier checks (oscillation; latched-frame speed audit). Decision logs and per-run
evidence committed under `proof/`.
