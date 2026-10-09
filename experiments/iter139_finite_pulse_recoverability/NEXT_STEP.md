# Next step after the finite pulse null

Status: **proposed**, informed by the closed Iter139 development result. This is an
agent-authored research decision, not a new preregistration, a proof of inevitability or a
claim to the best possible algorithm. The live grid is closed; do not extend or retry it.

## The decision that the next work must resolve

The first question is whether the available intervention can change the encounter enough to
avoid collision and continue driving. Iter139 found no such action among its six zero-plan
pulses. A more accurate alarm has no demonstrated recovery opportunity in that tested library.
This leaves richer actions, other onset times, other case families and information value open.

The [post hoc actuation recount](proof/actuation_recount.stdout) shows that the commands were
applied and slowed the vehicle. Every pulse frame has negative acceleration; terminal ego
speed ranges from about 0.046 to 0.325 m/s across the pulses. All eight environment logs report
foreground collision. Those facts motivate a contact and other-actor diagnostic; they do not
identify the actor, explain relative impact speed or establish that braking caused the crash.
The controller also changes steering while tracking a zero plan. Calling this action simply
"braking" can hide part of its dynamics.

## One bounded diagnostic, using the new evidence

Before another GPU run, freeze a small CPU analysis of these eight new trajectories:

1. Reconstruct the environment's foreground rectangle intersections at every recorded step
   from the logged ego and actor boxes. Independently check polygon geometry and coordinate
   conventions against the pinned source, including rotated, touching and non-overlap fixtures.
   Report ambiguous or inconsistent geometry explicitly; do not fill gaps with actor labels.
2. Reconstruct the delivered acceleration, steering and speed histories. Separate the command
   interval, the physical deceleration and post-release replanning. Compare observed paths at
   fixed times without treating post-treatment speed or dose as a repaired causal comparator.
3. Check how the pinned scenario's actor planner uses ego state and whether the observed actor
   paths change across branches. Report actor correspondence only if evidence identifies it;
   list order or nearest position alone does not prove persistent identity. Replaying the
   reference actor path against a new ego path is a geometric diagnostic, not a closed-loop
   counterfactual if the actor responds to ego behavior.
4. Produce one action-selection memo with a concrete decision: a justified new action family,
   a different preregistered development case family, or an identified missing measurement.
   End the diagnostic there. Do not begin another chain of same-case descriptive taxonomies.

This uses new numerical-controller interventions. The earlier
[eight-row support-core synthesis](../iter121_hugsim_support_core_two_track_synthesis/RESULT.md)
already closed its descriptive object-support question; repeating that audit is not the next
investment. Privileged geometry may label this diagnostic but cannot silently enter the inputs
of a deployable monitor or its baseline.

## Choose the successor from the diagnosis

| Finding | Consequence for a separately preregistered successor |
| --- | --- |
| Action delivery, coordinate or state-linkage inconsistency | Repair and validate the execution contract, retaining the failed evidence, before comparing policies. |
| Delivered slowing still leaves the foreground contact in all tested branches | Justify a bounded alternative action family from contact geometry and feasible dynamics, or move to a specified case family with a plausible braking opportunity. Do not assume longer braking is safe. |
| A proposed alternative works only against a frozen reference actor path | Treat it as a screening proposal; require reactive closed-loop validation before claiming recovery. |
| No justified feasible alternative emerges | Record the limit for this case/library and change the development search under an explicit finite budget. Do not infer physical impossibility or keep searching until a win. |
| A new frozen action library contains a successful recovery | Freeze that opportunity and compare information policies with matched permitted actions, constraints and calibration resources. |

The next canary needs a fixed candidate set, objective, budget, prefix/replay checks, explicit
missingness, full-route outcomes and all failures retained. A wider action family changes the
research scope and must have its own protocol. Future outcome-dependent development choices
must remain visible; this heavily inspected scene cannot become a fresh validation scene.

## Preserve the broader mission

The target remains useful incremental information: which signal changes an available decision
early enough to improve collision/progress/intervention outcomes against a strong responsive
baseline? Distinguish new measurement, richer interface and faster useful computation. A hidden
representation of an already available history need not add Shannon information to add practical
value under a compute limit. Estimate named policy contrasts; do not label them the unrestricted
optimal value of information.

Keep timing as a separate obligation. All 206 numerical calls converged, yet 166 complete calls
and 137 full solver calls exceeded 50 ms, and client roundtrips are much longer. A future
performance change must preserve a declared numerical error/control contract and measure both
solver and complete pipeline behavior. Restoring wall-clock solver truncation would change the
policy; it cannot silently stand in for the matched numerical controller. A later delay-aware
experiment must evaluate observation age and action timing in the closed loop.

After a useful action opportunity and a specific information advantage survive their frozen
comparisons, test source scenes excluded from development, benign/stale-track counterparts,
observation faults and a second planner or simulator. Account for source-scene dependence and
joint planner/monitor failures. Preserve collision, progress, intervention burden, severity,
latency, subgroup uncertainty and missingness separately. No result here establishes fleet
safety, industrial demand or superiority to a private engineering system.

Iter135 remains deferred and unchanged. Iter136, Iter137, Iter138 and Iter139 remain closed.
The cloud host is stopped; the next proposed diagnostic requires no new cloud launch.
