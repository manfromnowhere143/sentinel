# Iteration 8 — the union: one config that is selective, net-positive, and solves the side case

Iteration 7 showed the two danger cases need different detectors and that no single margin holds all
four properties. Iteration 8 tests the obvious synthesis: brake on the **union** of the two
individually-selective detectors —

```
brake if  (plan-vs-tracked-path CPA < 1.5 m)   OR   (observed agent-closing TTC < 2.5 s)
```

the CPA term for the side crossing, the observed-closing term for the optimistic-plan frontal. Because
neither fires on the passive stationary object, the union should stay selective.

## Result (OFF vs union, 3 scenes × 8 runs)

| scene | OFF | union |
|---|---|---|
| stationary/0103 (clean) | 5.00 / 0% / 33.0 m | 5.00 / 0% / **30.2 m** |
| frontal/0103 | 1.31 / 75% / 36.1 m | **2.43** / 88% / 21.2 m |
| side/0103 | 0.65 / **100%** / 20.3 m | **5.00 / 0%** / 6.4 m |
| **pooled safe-progress** | **2.32** | **2.53** |

## What the union achieves — three of four fully, the fourth mitigated

**For the first time in the campaign, one configuration holds these at once:**
- **Selective** — clean scene 30.2 m ≈ OFF's 33.0 (the union brakes only lightly on the benign scene;
  no freezing).
- **Net-positive** on the deployment metric — **safe-progress 2.53 > OFF 2.32**. The gain is real and
  structural: it comes from solving the side case (which OFF loses 100%) while barely touching
  clean-scene progress.
- **Side-impact solved** — 100% → 0% (the CPA term catches the crossing, unaffected by planner
  optimism).
- **Frontal — strongly mitigated, not fully prevented.** Score 1.31 → 2.43 (impact speed cut hard by
  the closing-TTC brake), but the collision *rate* stays ≈ OFF (88% vs 75%, within noise). This is the
  one property not fully closed.

So the union is the best monitor of the eight iterations: it is the only one that is simultaneously
selective, net-positive, and side-solving, and it makes frontal crashes low-speed instead of lethal.

## The one honest remaining gap — fully preventing frontal head-on

The union does not *prevent* frontal collisions, it *softens* them. The reason is the same planner
optimism that iteration 7 isolated: in a head-on the ego is committed into the actor's path, and even a
correct brake triggered ~1–2 s out cannot fully stop from ~11 m/s before contact — it only cuts the
impact speed (hence the score jump without the rate drop). Across the whole campaign the *only* arm that
drove frontal collision rate down (to 50%) was the trivial over-braking one, and it did so by freezing
the car everywhere (safe-progress 0.64). Fully preventing the head-on without over-braking is a genuine
open problem — it likely needs earlier detection (longer tracking horizon) or an evasive maneuver rather
than a straight-line stop, not a threshold change.

## Where the campaign lands (eight iterations)

Every property of a deployable frozen-planner safety monitor is now demonstrated, and the best single
configuration — the union — holds three of the four at once with the fourth mitigated, **net-positive
over the unmonitored planner on a progress-aware metric**, all label-free on a frozen planner, single
L4, public data. The honest ceiling is named: frontal-head-on *prevention* (vs mitigation), limited by
planner optimism and stopping distance.

## Honesty about scope and noise

2 public-mini scenes, 8 runs/scene, one L4 — a method-development loop, not the full 14-scene published
benchmark (gated trainval). The robust same-run facts are the large, clean swings: **side 100 → 0%**,
**clean ≈ OFF (30.2 vs 33)**, **frontal score 1.31 → 2.43**, **pooled 2.53 > 2.32**. The frontal
collision-*rate* difference (88 vs 75) is within noise and is *not* claimed as an improvement.

## Reproduce

`iter8_run.sh` (arms OFF / union) + `server_patch_union.py` (world-frame object-id tracking; brake on
CPA-OR-closing-TTC). Full table: [`proof/i8_results.txt`](proof/i8_results.txt).
