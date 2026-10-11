# Iter153: bounded privileged-state maneuver feasibility

11 October 2026. Parent `376184aab2b3eeed1f046e9bf8c35456969b760d`.
Daniel requests autonomous mission continuation. This is a local CPU diagnostic; no provider,
GPU, simulator episode, live controller modification or historical retry belongs to this slice.

The exposed scene-0013-medium-00 nominal and monitor pairs collided in Iter151/152. Two short
brake pulses also collided. Their outcomes, route, reset and stationary logged obstacle are
known development evidence. The new question is whether a finite route-following maneuver
family contains a candidate satisfying this explicit reduced model and useful-progress screen.
A positive answer nominates a maneuver for a new full-scene experiment; it is not a recovery
result, information benefit, road legality, physical guarantee or state-of-the-art ranking.

## Fixed search

Bind the retained nominal and monitor traces, admissions and source in INPUTS.json. Independently
check their existing source dynamics, source foreground collision and route observations before
extracting geometry. Require identical replica route/reset/obstacle dimensions and positions;
reject missing geometry, moving logged obstacles, nonfinite input and changed hashes. The model
holds the logged obstacle fixed beyond its observed interval. That extension is an explicit
assumption, not a newly observed future. Original actor/planner/render behavior is not rerun.

PLAN.json fixes 75 candidates, each executed twice from [0,0,0,1,0]. Three route-center baselines
use target speeds 2, 4, 6 m/s. The other 72 combine those speeds with signed normal offsets
{-4,-3,-2,+2,+3,+4} m, shift starts {0,5} m and shift lengths {10,15} m along original route
arc length. Use q(u)=10u^3-15u^4+6u^5 with u clipped to [0,1]. Offset grows by q over the shift,
holds until station 40 m, then returns by 1-q over 15 m. No outcome-dependent expansion.
Build normal directions from adjacent original route samples; consecutive duplicate geometric
points may be removed for reference construction only. Keep all original samples for outcomes.

At each 0.25 s tick, select the closest reference sample (first on ties); interpolate a target
5 m farther along that reference's arc length. Pure pursuit sets desired curvature to
2*sin(atan2(target_y-y,target_x-x)-heading)/distance, then desired steering atan(2.7*curvature).
Clamp steering command to +/-pi/3 and rate to +/-pi/12 rad/s; speed feedback requests
(target_speed-speed)/0.25 clamped to +/-2 m/s^2. No reverse and no speed above 6 m/s.
This deterministic diagnostic controller is distinct from frozen UniAD/Iter145; comparing it
cannot attribute an effect to monitor information. Retain every actual applied control.

Use the source-matched updated-speed/updated-steering transition with wheelbase 2.7 m, heading
before translation and updated heading after translation. Screen lateral acceleration
abs(v_new^2*tan(steer_new)/2.7)<=4.89 m/s^2 and abs(yaw_rate)<=0.95 rad/s. These two extra
source comfort thresholds are diagnostic restrictions, not validated physical actuator limits.

## Outcomes and independent checking

Run every candidate until source foreground contact, source off-route (>10 m from nearest
original sample), source completion (nearest_index+1 >=0.9*sample_count), a control violation,
or 401 actions. Contact is closed-set rectangle intersection, including touching. Reject a
completion simultaneous with contact. Retain complete partial trajectories and exact stop causes;
a failed candidate does not halt unrelated scheduled candidates, while infrastructure/identity
failure does. Both replicas must agree within 1e-9; execution errors are invalid, never nulls.

Report discrete source foreground contact separately from conservative between-sample clearance.
For each of eight equal subdivisions of linear center/heading interpolation between states,
use the midpoint rectangle and a displacement bound D/2 + 2*r*sin(abs(delta_heading)/4), where
D is that subdivision's center displacement and r is ego half-diagonal. A normalized separating
axis gap must exceed this bound plus 0.25 m against every stationary obstacle. Failure to certify
is unresolved swept clearance, not necessarily collision. This certificate concerns the declared
interpolation only, not a different continuous-time vehicle or curved physical trajectory.

Independently reconstruct transitions, controls/bounds, source route completion, foreground SAT
and the swept separation inequalities. Qualify with actual retained source transition slices,
independent rectangle implementations and known-bads: wrong axes, yaw, dimensions, endpoint-only
collision, touching, missing/nonfinite geometry, excessive controls, altered states, false success,
unknown background converted to false, duplicate/missing candidate or replica and changed inputs.
The independent evaluator must not import the candidate planner, its dynamics or geometry code.

Progress uses the retained comparator failure times 7.75 and 9.0 s and their route-completion
fractions. Require candidate progress at each hazard >= comparator progress-0.05, or earlier
qualified model completion. Keep unknown if a failed/partial candidate has no such observation.
Select only complete, control-valid, swept-clear candidates satisfying both progress screens.
Rank eligible candidates by completion time, absolute offset and lexical candidate ID, in that
order. Retain all 75 outcomes, not only the selected one. Finite failure cannot prove inevitability.

Background point-cloud collision, road compliance, live recovery and information benefit remain
null/unknown in every result. A route-distance bound is not a road boundary. Model success does
not fill those fields. No population rates, confidence intervals or untouched-holdout claims.

## Execution and evidence

Commit protocol before search. Qualify source/geometry and known-bads before freezing the runner.
Then one exclusive search initialization, <=600 wall seconds, 75 candidates x2 replicas x401
maximum actions; no packages, external compute or new scene assets. Preserve partial records if
the budget expires. Commit raw before independent search replay/selection; retain producer and
checker outputs separately. Any post-initialization defect requires a visible amendment/new run,
not overwritten evidence. Preserve Iter145–152, master, pinned authority and unrelated root WIP.
