# Iteration 11 — early collision-course detection for frontal prevention (pre-registered, before running)

Iterations 9 and 10 refuted evasive steering for the frontal head-on: both were *worse* than a committed
stop. This iteration re-examines *why* and tests a specific, physically-motivated fix. Pinned before the
run, per the engine.

## Diagnosis: the failure was lead time, not the maneuver

Both prior evasions triggered ~1–2 s before impact, because the trigger keyed off signals that see the
collision late (the planner's optimistic forecast; short-horizon geometry). At a closing speed of
~24 m/s, 1–2 s is below the time needed to *complete* either a stop (~10 m from 11 m/s) or a lane change
(~2–3 s for 3–4 m lateral). So the ego was already committed into the actor's path before it acted.

Two facts make earlier action possible:
1. **The threat's motion is observable.** Multi-frame tracking (iteration 5) gives each actor's true
   world-frame velocity ~1 s after it appears — no dependence on the planner's optimistic forecast.
2. **The adversarial actor is non-reactive.** In this simulator it follows a fixed manipulated path aimed
   at the ego's *original* trajectory; it does not chase the ego. So if the ego leaves that path early,
   the actor's fixed path passes through where the ego *would have been* and misses.

Together these imply: detect the collision course early from observed kinematics, and a maneuver that
would fail late can succeed with lead time.

## Method

**Detector — kinematic closest-approach over a long horizon.** For each tracked agent (observed
world-frame velocity), extrapolate *both* the ego (its current velocity, straight-line) and the agent
over a 4 s horizon, and take the minimum predicted separation and its time `t*`. A collision course is
declared when that minimum falls below a contact margin (~2 m). This differs from every prior trigger in
two ways that matter: it uses the ego's **actual kinematic path** (not the planner's optimistic plan,
which defeated the frontal case in iters 6–7), and a **long** horizon (early detection, not the union's
2.5 s). It stays selective because a benign passing object's extrapolated path does not converge to <2 m.

**Response — time-gated.** Given the time-to-closest-approach `t*`:
- `t* ≥ 1.5 s` (lead time exists) → **evasive lane change**: keep forward progress, ramp ~3.5 m lateral
  to the tracked-clear side over ~2 s (gentle, trackable, and — with early detection — *completed* before
  the actor arrives).
- `t* < 1.5 s` (too late to clear) → **committed stop** (the union's mitigation; the best late response).

The side-impact crossing is subsumed by the same detector (paths cross → small separation) and routed to
the stop, preserving the iteration-8 side result.

## Pre-registered success criterion (H11)

Run OFF vs union[stop] vs early-evade, same seeds, on stationary/frontal/side (≥6 runs each). H11 holds
iff on **frontal**: collision rate **falls below the committed stop's** (≈83%) — i.e. genuine
*prevention*, not just the mitigation the stop already provides — **while** the clean scene stays ≈ OFF
(selectivity) and side stays ≈ 0% (the iteration-8 result is not regressed).

## Falsifiers (stated up front)

- If the long-horizon kinematic detector over-fires and drops clean-scene progress (over-braking
  returns), the early trigger is not selective — reported as a null.
- If early evasion still does not lower the frontal collision rate below the stop, the "lead time was the
  cause" hypothesis is wrong — reported as a third frontal null, and the committed stop stands as the
  established ceiling.
- If evasion succeeds here only because the actor is non-reactive, that limitation is stated explicitly
  (it would not transfer to a reactive adversary without further work).

## Status

Designed and implemented (`server_patch_early_evade.py`, staged); **not yet run** — the run is queued for
the moment GPU access is restored. This document is the pre-registration; the result — win or null — will
be filed against it with the real per-run numbers.
