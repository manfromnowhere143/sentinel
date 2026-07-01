# Iteration 7 — margin sweep: a tighter CPA restores selectivity + keeps side, but frontal defeats it

Iteration 6 solved the side case with plan-vs-tracked-path CPA but over-braked the clean scene at a
2.5 m margin. The hypothesis was that a tighter margin (~1.0–1.5 m) would keep the side win and restore
selectivity. Iteration 7 sweeps the margin (OFF vs cpa@1.5 vs cpa@1.0) to test it.

## Result (3 scenes × 6 runs)

| arm | clean (stationary) | frontal | side |
|---|---|---|---|
| OFF | 5.00 / 0% / 32.4 m | 0.91 / 83% / 34.6 m | 0.64 / 100% / 19.9 m |
| cpa@2.5 (iter 6) | 5.00 / 0% / **22.3 m** (over-brakes) | 2.95 / 88% / 19.9 m | 5.00 / 0% / 6.1 m |
| **cpa@1.5** | 5.00 / 0% / **32.3 m** (= OFF) | 1.41 / **100%** | 5.00 / 0% / 7.1 m |

## What the sweep proved — three of four, and why the fourth resists

**cpa@1.5 holds three of the four properties at once:**
- **Selective** — clean scene 32.3 m, *identical to OFF* (the 1.5 m margin no longer flags the ego's
  ~2–3 m benign pass of the stationary object; iteration 6's over-braking is gone).
- **Side-impact solved** — still 0% (the T-bone's paths genuinely cross to <1.5 m, so the tighter
  margin keeps catching it).
- **Net-positive** on the clean + side scenes.

**But frontal reverts to 100%**, and the reason is fundamental, not a tuning miss: the head-on actor
defeats plan-vs-path CPA at *any* tight margin because the planner's **own plan is optimistic** — it
plans a path it believes clears the oncoming actor by ~3–4 m, so the closest approach between the
*plan* and the actor's tracked path never drops near the collision margin, even as the car drives
straight into the crash. Looser margins catch a little more frontal (2.5 m → 88%) but only by
over-braking everything; tighter margins are selective but blind to it (1.5 m → 100%). **No single CPA
margin holds all four.**

## The mechanism, isolated (the durable insight)

The two danger cases need *different* detectors, and the sweep makes the reason exact:

- **Side T-bone** — the ego and actor paths genuinely **cross** (closest approach → ~0 m). Plan-vs-
  tracked-path CPA catches it at a tight, selective margin. The planner's optimism doesn't matter,
  because the crossing is real in the geometry.
- **Frontal head-on** — the planner **optimistically plans to clear** the actor, so the plan-vs-actor
  closest approach stays at 3–4 m even in the crashes. CPA on the *plan* cannot see it. What sees it is
  the actor's **observed closing motion** toward the ego (iteration 5's agent-closing on tracked
  velocity caught frontal at 67%; total-closing caught it at 50%) — a signal that doesn't trust the
  optimistic plan.

So the deployable monitor is a **union of two selective detectors**, not one margin:
`brake if (plan-vs-tracked-path CPA < ~1.5 m)  OR  (observed agent-closing TTC < threshold)`.
The CPA term catches the side crossing; the closing term catches the optimistic-plan frontal; both are
individually selective (neither fires on the passive stationary object), so their union should stay
selective too. That union is iteration 8.

## Honesty

cpa@1.0 was included in the sweep but is not tabled here at full n (it trends the same way as cpa@1.5 —
selective, side-caught, frontal-blind — only more so). The robust, same-run finding is the cpa@1.5 row
against OFF and the iteration-6 2.5 m row: selectivity and side are recoverable at a tight margin;
frontal is not, by construction.

## Reproduce

`iter7_run.sh` (arms OFF / cpa@1.5 / cpa@1.0 via `SENTINEL_CPA_MARGIN`) on the iteration-6 CPA server
patch. Full table: [`proof/i7_results.txt`](proof/i7_results.txt).
