# Iter144 explicit trajectory execution qualification

Status at registration: preregistered, 2026-10-10. Local software qualification only.
Parent: closed Iter143 18ca7e2000c22c7cd1d00f31ab81854a25fa2698.
Daniel directly requested implementation, execution qualification, and progress toward
its proposed 14-scenario study. No cloud access or driving episode in this iteration.

## New regime: sentinel.timed_trajectory.v1

Use absolute simulation seconds, an explicit episode identity and plan origin, SI
units, positions in HUGSIM local (a,b) metres and heading measured from +a toward +b.
Actor native yaw maps to heading yaw+pi/2; ego native theta maps to pi/2-theta.
These differ deliberately. Retain source branch and original time channel. Never
reinterpret historical outcomes as results under this regime.

At a planning origin t, compare candidates, ego and neighbors on t+i*.25, i=0..19.
Generate spline/low-speed candidates with tf=5 and N=20; spline support ends5,
low-speed support4.75. Preserve the measured initial state at t and interpolate
positions and signed speed linearly, heading by the shortest angular increment.
No extrapolation. Interpolated source speed is a state label, not a guaranteed
position derivative on accelerating/curved paths. Exact straight constant-speed
fixtures must agree. Retain original source rows alongside aligned trajectories.

Reset returns the initial state without consuming a future point. Apply actions and
actor motion over [t,t+.25], first consumption at .25. Replan after ten completed
steps at 2.5,5,... from the state at that time. Generate forecasts from the same
pre-step observation. Reject nonmonotone/nonfinite/dropped/shifted time channels,
wrong frame/units/episode, stale plans, state discontinuities, repeated or skipped
execution ticks and queries beyond support. Invalid admission cannot replace a
valid active plan. Invalid execution stops with an explicit reason, never fallback
success. Empty candidate generation alone selects a timestamped constant-motion
fallback. Deterministic lowest-cost selection, stable index ties, replaces random
top-k; this is a named policy change. No attempt to reproduce legacy driving results.

Use the source simulator's updated-speed/updated-steering transition for ego
prediction, .25 s, wheelbase2.7. Project requested acceleration to +/-2 and steering
rate to +/-pi/12; constrain steering angle to +/-pi/3 by adjusting rate. Log requested
and applied control. Signed ego velocity is allowed; braking moves it toward zero
without crossing zero. Source actor generation requires nonnegative initial speed
because its generator clamps negative speed; reverse actor replans stop explicitly.
Use analytic piecewise Jacobians, independently checked by centered finite differences
away from clamp boundaries, and exercise the actual instrumented iLQR solver.
Numerical mode has no wall deadline; log stopping reasons and solver/complete-call
latencies separately. No real-time or late-result qualification is inferred.

## Frozen qualification envelope

Before diagnostic measurement commit tested source. Execute from committed source.
Commit raw artifacts before independent analysis. Retain failed attempts separately.
Known-bad tests exercise every admission condition, including mutations of whole raw
records. Independent replay must not call adapter transition/interpolation/cost code.

Execute straight constant-speed fixtures for spline v4, low-speed v1, fallback v4,
headings -.4,0,.4, each for 21 timestamps0..5 (20 steps). Source spline and forward
sampler functions, including actual generation/filtering, must run on CPU. Restricted
straight sampler grids are disclosed in these fixtures. Also exercise the full
default source sampler at v0,1,4 and the same three headings through adaptation and
cost selection. Probe the new transition on the prior 32 state/control fixtures,
including clipped inputs; check Jacobians on interior and strictly saturated controls.
Run the actual instrumented iLQR on straight and curved timestamped references with
v0 and4, two numerical repetitions. No outcome-based fixture replacement. Integrate
reset/actor dispatch and applied ego controls with the retained environment step
prefix for a bounded 20-step CPU execution; renderer/collision/assets are excluded.

Pass requires all finite schemas/admission checks, exact straight-motion timing within
1e-5, frame round trips and reset, independent cost/ego replay within1e-8, Jacobians
within1e-5, and repeatable numerical solver results within1e-10. A software failure
is failed/invalid with retained evidence and a dated correction before new measurement.
A pass is supported only for this CPU source/fixture contract, never physical fidelity,
safety, state of the art, full simulator operation or useful recoverability.

## Study progression

Generate a machine-readable 112-slot schedule from the unchanged Iter143 inventory:
14 scenarios /3 historically exposed base scenes, four arms, two replicas. Retain
all other inventory rows and exclusions. Freeze proposed single reset, fixed seeds,
explicit control policy and missingness fields. Add executable admission requirements
for source/runtime/assets, bounded integration smoke and resource budget. Missing
bindings remain null and prevent live admission. Do not invent asset availability,
runtime estimates, cloud status or study outcomes. Study remains proposed until the
actual live protocol and resource envelope are separately bound. No new scene0411
search, no extra parameter/seed/outcome search, no packages installed.
