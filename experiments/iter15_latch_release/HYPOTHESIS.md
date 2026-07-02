# Iteration 15 — threat-cleared latch release: pre-registration

Frozen before the run. The full-benchmark split verdict
([`../full14_benchmark/RESULT.md`](../full14_benchmark/RESULT.md)) defines the problem: the union
is decisively benchmark-positive (+0.934 CI [+0.713, +1.155]) but deployment-neutral
(safe-progress −0.170, CI includes 0) because its **committed stop never releases** — on several
unseen scenes the monitor brakes correctly, the threat passes, and the ego sits for the rest of
the episode (0101: 50 → 7 m; 0108: 43 → 7 m driven).

## The change (one mechanism, nothing else)

The latch releases when the threat has verifiably cleared: after braking, if for **K = 4
consecutive frames (2 s)** no tracked object satisfies either union term against the planner's
*current* plan (CPA ≥ 1.5 m and closing-TTC ≥ 2.5 s, the unchanged thresholds), control returns
to the planner. The latch re-arms normally (re-fires if danger returns). Trigger logic, thresholds,
and actuator are untouched — the only new parameter is K.

The iteration-11 asymmetry stays respected: releasing a stop after verified threat clearance
resumes an *in-distribution planner plan*, not an invented maneuver.

## H15 (pre-registered)

Against the committed f14 arms (same episodes, seed-paired; only the new arm is run):

1. **Progress restored where it was lost:** on the over-braked benign-progress pairs
   (stationary 0101/0108, and any pair where union ego < 50% of OFF ego with equal-or-better
   safety), released-union ego distance recovers to > 60% of OFF.
2. **Safety held:** per-class collision rates within noise of the union's (side ≤ 45%, stationary
   ≤ 25% at n=6/pair pooled); the release must not reopen solved cases.
3. **The deployment verdict flips:** pooled safe-progress (released-union − OFF) > 0 with the
   within-pair bootstrap CI excluding 0 — the bar the union itself failed at benchmark scope.
   Benchmark NCAP score stays within noise of the union's 3.09 (no more than −0.15).

## Falsifiers, named up front

- **Release-oscillation:** brake/release cycling (chatter) that degrades both metrics — visible in
  the decision logs as alternating brake/act records; reported if it occurs.
- **Premature release:** if the tracked threat drops out of perception while still dangerous
  (the recall-collapse failure mode from iteration 1b), release re-exposes the ego and side/frontal
  rates rise — that would mean release needs observed-clearance, not just absence-of-detection,
  and the null is reported with that mechanism.
- If safety holds but progress does not recover (the stop was not the binding cost), the
  deployment gap is not calibration — reported as such.

## Protocol

One new arm (`released`, `SENTINEL_RELEASE_K=4`) on all 20 scene-scenario pairs × 6 runs (120
episodes); OFF and union comparators reused from the committed f14 evidence (identical
deterministic episodes). Analysis: `analyze_full14.py` extended three-way; decision logs committed.
