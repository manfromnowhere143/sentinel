# Full-horizon control qualification

Freeze PLAN, runtime fingerprints, upstream source inventory, controller, checker,
tests and all bound inputs before initializing the scientific schedule. Execute
all twelve unchanged Iter168 cases once in their recorded order. The retained
Iter168 depth2 arm is the comparator; it is not rerun. Its raw/admission identities
and selected paths are source-bound, and its selected masks are replayed again.
Do not make a contemporaneous wall-time or population-superiority claim.

The controller receives only geometry, task state/time targets and the background
query callback. It receives no witness controls or case identifier. It optimizes
one complete open-loop sequence over the task's terminal frame, at dt 0.25. No new
integration model, route-completion waiver or intermediate interpolation replaces
Sentinel's semi-implicit transition, foreground sweep, point-count predicate,
actuator limits, route constraints or absolute progress checkpoints.

Parameterization: independent controls are normalized to [-1,1], mapping to
acceleration ±2 and steering rate ±pi/12. Wait frames have both controls fixed to zero.
At the task's stop frame, acceleration is computed as -current_speed/0.25; later
acceleration is zero. This enforces an explicit task phase, not a speed clamp;
computed braking outside the acceleration limit is rejected. All other non-wait
steering rates and pre-stop/non-stop accelerations remain optimization variables.
The initial guess is constant acceleration toward the specified terminal speed
(or zero at the stop deadline) and constant rate toward terminal steering, clipped
to bounds. It is derived from task inputs, never the constructive controls.

Optimizer: SciPy 1.17.1 least_squares, method trf, exact dense trust-region solver,
2-point finite differences, x_scale=jac, linear loss, max_nfev=100, diff_step=1e-6,
ftol/xtol/gtol=1e-12. The first five residuals are wrapped terminal state errors divided
by unchanged coordinate tolerances. Append the negative part of every actuator
slack divided by 1e-6. These residuals guide search only; the unchanged hard predicates
alone decide eligibility. Background counts and nearest-route progress are not
silently replaced by differentiable surrogates.

Every unique parameter vector is fully propagated, even if an intermediate state
is rejected, so endpoint fitting remains defined. Each attempted transition is
charged. Query background only after other hard checks pass for that state.
Exact IEEE754 parameter bytes key a per-case cache; log every request and hit.
Reserve enough remaining transitions for a full rollout before starting one;
a transition-cap stop may leave fewer than one horizon's steps unused. Check time
between transitions; retain an incomplete timed-out evaluation without making it
eligible. Root queries and selected-mask materialization are separately counted.

Stop immediately at the first complete, hard-admissible candidate, including an
initial guess or derivative probe. This is a feasible-task return, not optimizer
convergence. Otherwise stop at a resource cap or optimizer return and retain the
eligible full candidate with minimum squared normalized terminal error, breaking
ties by evaluation ID; retain only reset if none exists. Preserve solver status,
function/gradient counters and unknown convergence on early interruption. Never
substitute max_nfev or solver iteration counts for actual propagated work.

Independent admission checks every evaluated transition, decoded action, phase,
actuator slack, objective and request/cache/budget accounting. It reconstructs full
scalar masks on witnesses, selected new paths and retained comparator paths.
Unselected background labels remain producer evidence. Recheck their count/decision
consistency without claiming independent geometry for them. Twelve of twelve new
completions supports local qualification; any valid miss contradicts it. Invalid
witnesses or evidence invalidate admission. Source qualification remains false.

Run from the owned repository with full frozen commit hashes:

```bash
python3 -m experiments.iter169_full_horizon_control.run --root "$PWD" --source-commit SOURCE
python3 -m experiments.iter169_full_horizon_control.check --root "$PWD" --raw-commit RAW
```

Use owned external process-group supervisors with 310-second limits. Retain process
exit and reaping evidence. No initialized retry, native driving, provider use or
source-scene comparison. Runtime fingerprints bind selected observed files and
versions; they do not certify a hermetic build or full OS dependency closure.
