# Next steps after explicit trajectory qualification

The Iter144 timing contract is supported on its registered CPU fixtures. The next
live comparison remains unadmitted. Preserve all old null results and the new
from-rest convergence failures.

## Resolve optimizer behavior before driving

Register a bounded successor using the two retained from-rest references and their
exact source/parameter identities. Inspect objective and input-change histories to
distinguish cycling, poor warm starts and constraint-boundary behavior; the observed
iteration cap alone does not identify a cause. The retained solver lacks a line
search. A projected step with objective-decrease acceptance is a candidate, not yet
an established remedy. Do not silently change the cap, convergence tolerance, cost
weights or fixture population to make this result green. Retain the existing output
as the comparison and report control/trajectory changes under any new policy.

Require explicit handling of iteration limits and nonfinite results. Test analytic
Jacobians again if the dynamics/projection changes. Log numerical stop reasons and
measure wall time separately. A returned control and a repeatable result are both
insufficient to claim convergence or a vehicle deadline.

## Complete simulator integration

Use the new timestamped interface throughout the actual nominal planner, actor dispatch,
controller, observation, action, collision and rendering boundaries. The Iter144 bridge
returns CPU native actor states, not CUDA scene transforms. Build transforms from the
same consumed timestamped state and log the times used by collision/rendering. Verify
all actor types present in the pilot; the present generation qualification covers
AttackPlanner-style spline/forward candidates and its fallback.

Bind nominal reference knot times from the planner protocol before resampling. Do not
infer them from array position. Verify reset of every state component, including ego
steering and actor clocks, once per new episode. Enforce actual environment dt,
wheelbase and limits against the selected predictor at runtime. Test simultaneous
multiple actors and the ego/actor frame boundary with actual scenario configurations.
Keep the prior regime identity and changed difficulty visible.

## Bind the finite study

The machine-readable [schedule](proof/study_schedule.json) and its
[audit](proof/study_schedule_audit.json) establish 112 proposed slots, all 14 selected
scenarios, three development scenes and all retained exclusions. The original
[scientific design](../iter143_model_contract/CASE_FAMILY_PROTOCOL.md) remains proposed.
The new single-reset and seed-144 choices are preparation, not a live preregistration.

Verify actual YAML hashes, scene/model/checkpoint assets and runtime identities for
every selected row. Missing assets stay unavailable; no substitution or scene0411
search. Run a separately bounded integration smoke, measure time/storage, then bind
a feasible total host/cost ceiling, per-episode cutoff and shutdown ownership before
registering the live schedule. Do not extrapolate local CPU fixture times into a GPU
rendering budget. No new human acceptance ceremony is needed; the agent can perform
these bindings under Daniel's instruction.

All comparator-success cases stay in the intervention schedule to expose harm.
Report nominal and monitor recovery opportunities separately and their intersection.
Only after a repeated complete-route action witness exists should an added-information
selector be tested, with signal availability and action deadlines explicitly recorded.
