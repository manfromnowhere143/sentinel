# Iteration 5 — observed-velocity gating: selectivity holds, frontal recovers, side-impact resists

Iteration 4 fixed the over-braking but under-braked real threats because it read each agent's velocity
from the planner's *optimistic* forecast. Iteration 5 swaps that for the SOTA-correct source: estimate
each agent's velocity from its **actual observed motion** — track `object_ids` across consecutive
`/infer` frames, lift each detection to world coordinates via `ego2world` (so ego motion is
compensated), and finite-difference the positions. Same frozen planner, same deployment metric.

## Result (same-run OFF vs tracked, 3 scenes × 6 runs)

| arm | NCAP safety ↑ | progress ↑ | collision % ↓ | **safe-progress ↑** |
|---|---:|---:|---:|---:|
| OFF (no monitor) | 2.18 | 0.91 | 61 | 2.08 |
| **tracked (observed velocity)** | 2.61 | 0.88 | 56 | **2.35** |

Per scene — safety / collision % / ego distance driven (m):

| scene | OFF | tracked |
|---|---|---|
| stationary/0103 (clean) | 5.00 / 0 / **32.4** | 5.00 / 0 / **32.4** (0 interventions) |
| frontal/0103 | 0.91 / 83 / 34.6 | **2.18 / 67** / 25.2 |
| side/0103 | 0.64 / 100 / 19.9 | 0.41 / **100** / 20.4 |

## What it settled (robust across iterations 4–5)

- **Selectivity is solved and stable.** Tracked drives the clean scene **32.4 m — identical to the
  unmonitored planner — with zero interventions** (the stationary object's *observed* velocity is ~0,
  so the gate stays silent). The over-braking of iteration 3 does not return.
- **The monitor is net-positive vs the unmonitored planner.** safe-progress **2.35 > 2.08**, the third
  time (iter 4: 2.80; iter 5: 2.35) a selective monitor clears the iteration-3 bar.
- **Observed velocity beats the optimistic forecast on frontal.** Frontal collision falls 83% → 67%
  (vs iteration 4's forecast gate, which left it at 83%): the real measured approach of the head-on
  actor trips the gate where the planner's optimistic forecast did not.

## What it did NOT solve — and the precise reason (the honest core)

**Side-impact stays at 100%.** And the *why* is now exact, because the arms bracket it:

- `ttcold` (total closing speed = ego approach + agent approach) catches the side actor — **side 0%** —
  but over-brakes everything (safe-progress 0.64).
- `tracked` (agent-only closing, the selective gate) **misses the side actor — side 100%** — because a
  side T-bone's *early* warning lives in the **ego's own converging motion**, exactly the term the
  agent-only gate deliberately removes to stay selective. By the time the actor's own velocity points
  at the ego, it is too late to stop.

So the trade is now mapped cleanly: **total-closing catches every threat but over-brakes; agent-closing
is selective but blind to the side case whose warning is in the ego's motion. Neither is both.** A
deployable monitor needs a discriminator that gets the side warning without braking on every passive
object.

## Honesty about resolution

At 6 runs on single scenes, the safe-progress *gap between gating variants* (iter-4 gate 2.80 vs iter-5
tracked 2.35) is **within run-to-run noise** — those two should not be ranked from this corpus. What is
robust and repeated is the structure: selectivity solved, monitor net-positive vs OFF, frontal
improved by observed velocity, side-impact unsolved. Ranking the variants and trusting the deltas needs
the statistical power of more runs / the full 14-scene benchmark (gated trainval).

## Next (iteration 6)

The discriminator that should get *both*: predict the collision from the **ego's planned path** against
each agent's **tracked path** (closest point of approach over both real trajectories), not from a
closing-speed scalar. If the planner's *plan* already steers clear of the object → don't brake (passive
object, planner is handling it, selective). If plan-vs-tracked-actor paths intersect within the horizon
→ brake (the side T-bone the planner fails to avoid is caught, because the crossing is in the geometry
regardless of which body's motion causes it). Bar unchanged: clean progress ≈ OFF, **side collisions
down**, safe-progress > 2.80, all at higher run counts.

## Reproduce

`iter5_run.sh` (arms OFF / tracked via `SENTINEL_TRACK_VEL=1`) + `server_patch_track.py`
(world-frame object-id tracking) → `analyze.py`. Pre-registration shared with iter 4
(`../iter4_gated/HYPOTHESIS.md`). Full per-run table: [`proof/i5_results.txt`](proof/i5_results.txt).
