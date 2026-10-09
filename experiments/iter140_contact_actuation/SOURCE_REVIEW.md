# Source contract for the contact diagnostic

This review covers hash-bound configuration and source already retained before Iter140.
It does not replace the forthcoming check of observed states and contact flags.

## Configuration and identity

The [scenario bytes](proof/scenario.yaml.txt) were recovered from the retained Iter136 host
readback. Their SHA-256 matches both the original receipt and Iter139's runtime manifest:
`9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9`.
There is one plan-list entry: AttackPlanner, pred_steps 20 and ATTACK_FREQ 10. It starts with
plan coordinates a=0, b=-20, yaw=0 and speed=3; ego starts at a=b=0 and speed=1.
Reset and initial planning advance actor state, so these configuration values must not be
substituted for the actual first logged observation.

The pinned [planner source](../iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/utils/plan.py.txt)
creates the keyed dictionaries once with `agent_0` for this single entry, updates values under
that key, and returns the keyed planning transforms. The environment's `objs_list` reads that
same planning dictionary. If every recorded state contains one box, its correspondence is
source-inferred agent_0, not a logged actor ID and not a perception track assignment. More than
one box or a missing box removes that simple correspondence argument.

## Sequence and actor response

In the pinned [environment](../iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/hugsim_env/envs/hug_sim.py.txt),
each step increments the simulation timestamp, asks the actor planner to plan from the current
ego state, then integrates ego speed/steering/position/heading. Foreground collision is checked
using the resulting ego box and current planned actor boxes; observations and info follow.
The collision routine checks closed 2D rectangles and ignores vertical extent.

The planner includes ego state as row zero of its constant-heading prediction and passes that
prediction to AttackPlanner as `attacked_states`. In the pinned
[actor controller](../iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/utils/agent_controller.py.txt),
the attack cost contains the minimum distance between candidate actor positions and those ego
predictions. Candidate selection can depend on ego motion. This source dependency licenses a
specific hypothesis; the independent trace comparison will determine whether paths differ in
the observed pulses. Freezing a reference actor path would remove this feedback.

## Model scope and clocks

The environment and constant-heading predictor use dt=0.25 seconds. The AttackPlanner call
passes dt=0.1, generates its candidate horizon from that interval, and advances a stored plan
index on environment calls. The prediction arrays therefore have different nominal intervals
despite their index-wise distance comparison. ATTACK_FREQ 10 gives a scheduled replan test at
multiples of 2.5 environment seconds; an exhausted or missing stored plan may also replan.
These are source facts, not proof of the actual internal replan times in an episode.

Keep the simulator unchanged for this audit. The two clocks limit a physical interpretation of
actor prediction and motion. Relative center velocity from successive logged states is a
0.25-second finite difference, not a validated physical collision speed or injury measure.
This diagnostic can establish consistency with the declared simulator implementation without
establishing that implementation's physical fidelity.

The kinematic configuration also declares an acceleration action space of [-2,2] m/s², while
the environment step directly integrates supplied acceleration without clipping it to that
space. Iter139's retained pulse commands include -3 m/s². Thus a match to the step equations
does not establish compliance with the declared action-space bounds or a vehicle's actuator
limits. A future action family must specify and validate its admissible control envelope.

## Validation before new calculations

37 focused tests pass, including rotated/touching/contained boxes, a dimension swap, 200
deterministic random rectangle pairs, changed bytes, symlinks, missing input, malformed JSON,
broken state continuity, altered contact/area/distance/velocity reports and unsupported actor
identity. Two initial synthetic tests failed because independently computed zero velocity had
integer representation while the primary computation returned a float. Changing the independent
velocity calculation to explicit floating arithmetic resolved this without relaxing numerical
thresholds. The initial E731 lint finding was also corrected. Failure logs are retained.

The independent implementation supplements the registered separating-axis Boolean check with
convex clipping for overlap area and point-to-edge distances. These auxiliary numerical values
must match the primary output within absolute 1e-9 in their respective units. This validation
clarification is fixed before the first real-corpus analysis, alongside the registered 1e-9 m
ambiguity band and 1e-9 state-residual threshold; no outcome-dependent tolerance choice is made.
Area/distance disagreement is retained as independent-replay disagreement. The environment is
isolated locally; the complete installed versions are in [environment_freeze.stdout](proof/environment_freeze.stdout).
