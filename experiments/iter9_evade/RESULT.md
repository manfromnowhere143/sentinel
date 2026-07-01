# Iteration 9 — evasive steering for the frontal head-on: refuted (a reported negative)

Iteration 8 left one open ceiling: the union *mitigates* the frontal head-on (cuts impact speed) but
does not *prevent* it, because stopping lets the actor ram the stopped ego. The physically-motivated
next step — and the state-of-the-art active-safety move (AEB **+ AES**, automatic evasive steering) —
is to make the response **threat-aware**: keep the committed stop for side crossings, but for a frontal
head-on **steer laterally to dodge** instead of stopping in the actor's path. Iteration 9 implements
that and tests it. **The result refutes the hypothesis: the swerve makes frontal worse, not better.**

## Result (OFF vs union[stop] vs evade, same run, 3 scenes × 6 runs)

| scene | OFF | union (stop) | evade (steer on frontal) |
|---|---|---|---|
| stationary/0103 (clean) | 5.00 / 0% / 32.4 m | 5.00 / 0% / 32.3 m | 5.00 / 0% / 32.3 m |
| frontal/0103 | 0.91 / 83% / 34.6 m | **2.53 / 83%** / 20.8 m | **1.66 / 100%** / 21.2 m |
| side/0103 | 0.64 / 100% / 19.9 m | 5.00 / 0% / 7.1 m | 5.00 / 0% / 6.8 m |

Evade acted as designed — **8 `evade` actions on frontal, `stop` on side, nothing on the clean scene**
(selectivity and the side solution are both preserved: clean 32.3 m = union, side 0%). The change is
entirely on frontal, and it is a regression.

## The finding — steering to dodge is *worse* than stopping here

On frontal the evade arm is **1.66 / 100%** versus the stop-based union's **2.53 / 83%**: more
collisions *and* higher impact (lower score). The lateral swerve (4 m over ~1.5 s while keeping ~85% of
forward speed) does **not** clear the oncoming actor in time, and by not shedding speed it strikes
harder than the committed stop. The intuition "just steer around the head-on" fails in this closed-loop
sim, for reasons that are physically sensible:

- The actor is on an aggressive converging course; a 4 m lateral offset over 1.5 s is not enough to
  leave its swept path before contact, and the ego is still carrying speed *into* the encounter.
- The vehicle dynamics (nuPlan kinematic-bicycle + LQR tracker) cannot execute an arbitrarily hard
  swerve instantly, so the commanded dodge is only partially realized before impact.
- Committing to a stop at least removes the ego's own contribution to the closing speed (hence the
  union's higher score); the swerve keeps that contribution while failing to dodge.

## What this establishes

- **The committed stop (iteration 8's union) remains the best frontal response** — mitigation, not
  prevention, is the current ceiling, and a naive evasive maneuver does not raise it. Reported as a
  null, not buried; the union stays the campaign's best configuration.
- **Frontal head-on *prevention* is a genuine open problem**, not a quick maneuver away. Plausible
  paths that this negative points to — none yet demonstrated: (a) a *braking* evasion (shed speed AND
  steer, rather than steer at speed); (b) steering only into a **verified-clear** gap using the tracked
  free space, rather than a fixed 4 m offset; (c) much earlier detection (longer tracking horizon) so a
  gentle, trackable lane change has time to complete. Each is a real experiment, not a threshold tweak.

## Honesty

Same-run comparison (identical OFF/union baselines to iterations 8), so the frontal regression
(2.53 → 1.66, 83 → 100%) is a clean within-run signal, not cross-run noise. Selectivity and side are
unchanged, confirming the threat-aware routing itself works — it is the *evasive trajectory* that is
inadequate. 6 runs/scene, 2 public-mini scenes, one L4.

## Reproduce

`iter9_run.sh` (arms OFF / union / evade via `SENTINEL_EVADE`) + `server_patch_evade.py` (threat-aware:
CPA→stop, closing-TTC→lateral swerve). Full table: [`proof/i9_results.txt`](proof/i9_results.txt).
