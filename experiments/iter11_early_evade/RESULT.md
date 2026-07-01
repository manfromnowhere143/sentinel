# Iteration 11 — early collision-course detection + evasion: refuted (the third frontal null, and the decisive one)

The pre-registered hypothesis ([HYPOTHESIS.md](HYPOTHESIS.md)) was that the iter 9/10 evasion failures were
caused by **lead time** — the trigger fired too late for a maneuver to complete — and that detecting the
collision course *early* from observed kinematics (a 4 s closest-approach over the ego's actual path and
the agent's tracked path) would let a lane change succeed. It is **refuted**, on both the detector and the
maneuver, and it exposes why the committed stop is the right answer.

> **Correction (2026-07-02, verification pass).** The published table was a mid-run snapshot. The
> complete log (committed:
> [`../verification/evidence/logs/sentinel-i11.log`](../verification/evidence/logs/sentinel-i11.log))
> changes two cells, both making the null **stronger**: frontal evade is **1.71 / 83%** on all 6 runs
> (the published 2.06 / 80% was computed on the 5 finished at snapshot time), and the evade arm's side
> runs — which had not finished — show **5/6 collisions**: the early-evade design also breaks the side
> case the stop-based union had solved. Corrected in the table; conclusions unchanged (reinforced).
> See [`../VERIFICATION.md`](../VERIFICATION.md) §3.3.

## Result (OFF vs early-stop vs early-evade, same run, 3 scenes × 6 runs)

| arm | clean (stationary) | frontal | side |
|---|---|---|---|
| OFF | 5.00 / 0% / 32.4 m | 0.91 / 83% | 0.64 / 100% |
| early-detector → **stop** | 5.00 / 0% / **17.3 m** | 2.03 / **83%** | 5.00 / 0% |
| early-detector → **evade** | 3.07 / **50%** / 21.8 m | 1.71 / **83%** | 1.24 / **83%** |

22 `evade_early` actions fired, so the maneuver ran. The pre-registered H11 bar — frontal collision
*below* the stop's ~83% while clean stays ≈ OFF — fails on every clause.

## What it establishes (three findings, all negative, all useful)

**1. Early detection does not prevent the head-on.** The early-detector + committed stop holds frontal
collision at **83%** — identical to the late-triggered union. Stopping 4 s earlier does not help, because
the ego remains *in its lane*, which is exactly where the non-reactive actor is aimed. The lead-time
hypothesis is wrong: for a stop, more warning time does not convert to prevention.

**2. Early detection is less selective.** The 4 s kinematic horizon fires on the ego merely *approaching*
the parked car (its straight-line path passes within the 2 m margin), so the clean scene is over-braked
(17.3 m vs OFF's 32.4 m). The long horizon trades precision for early warning — the wrong trade here.

**3. Evasion on a false alarm is actively dangerous — the decisive lesson.** Coupling the same
lower-precision detector with a *lane change* makes the **clean scene collide 50% of the time**: the ego
swerves into the parked car it should have passed. This is the asymmetry that kills evasion as a strategy
here — **a committed stop is safe when the trigger is wrong; a swerve when the trigger is wrong causes the
crash it was meant to avoid.** Evasion demands near-perfect precision, which a label-free monitor does not
have. And even when it fired correctly on the frontal, it did not prevent it (83% = the stop's 83%).
The complete side-scene data sharpens this further: under the evade response the side case — which the
stop-based union solves — collides 5/6 times. Evasion does not merely fail to add safety; it *removes*
safety the stop already delivers.

## The settled conclusion of the frontal-prevention line

Three independent designs — steer-at-speed (iter 9), brake-and-steer (iter 10), early-detect-and-evade
(iter 11) — have now been tested and refuted. The committed stop is not merely the best frontal response
found; it is the **safe** one, because it degrades gracefully under the false positives that any real
monitor produces. Frontal head-on *prevention* is not achievable with a single evasive maneuver on a
label-free monitor in this closed-loop sim, and pursuing it trades away the selectivity and safety the
iteration-8 union already has. **The union remains the definitive configuration; this line of inquiry is
closed with a clear, honest reason.**

## Honesty

Same-run OFF baseline identical to every prior iteration (frontal 83%). The originally-published
numbers were a mid-run snapshot; the complete-data correction above (frontal 1.71/83%, side 1.24/83%)
strengthens the refutation. 6 runs/scene, 2 public-mini scenes, one L4.
A **reported null**, filed with the same weight as the wins — and the pre-registered falsifier ("evasion
succeeds only if the trigger is precise") is the one that fired.

## Reproduce

[`iter11_run.sh`](iter11_run.sh) (OFF / stop / evade via `SENTINEL_EVADE`) +
[`server_patch_early_evade.py`](server_patch_early_evade.py). Full table:
[`proof/i11_results.txt`](proof/i11_results.txt).
