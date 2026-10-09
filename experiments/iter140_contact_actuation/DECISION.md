# Next action decision after contact reconstruction

Decision: propose one bounded **nominal-continuation canary** in the current numerical runtime,
before any stronger-braking or steering search. The candidate action is to continue the frozen
planner's current nominal plan while the released monitor records shadow decisions. This is a
proposal for a separate protocol; Iter140 is complete and launches no live experiment.

## Why this is the next discriminating comparison

[Iter140](RESULT.md) reconstructed all eight terminal foreground contacts. The actor's center
was behind the ego at each contact, with positive center-distance closing over the last recorded
interval. Every pulse delivered slowing. Every pulse also changed the actor path relative to
the reference at common observed times. A stronger alarm followed by more braking therefore
has no demonstrated useful action opportunity on this case.

The action library tested so far contains additional zero-plan pulses on top of the released
monitor. It does not contain a branch that consistently declines the released monitor's
zero-plan replacement and continues nominal planning. The next comparison asks whether the
available nominal action can recover under this exact execution contract. It does not assume
that continuing, accelerating or stopping is safe.

Testing a more elaborate evasive controller now would add action generation and feasibility
assumptions before resolving this simpler branch. A continuation canary can distinguish a
useful action already present in the nominal plan from failure of both the current nominal
planner and the zero-plan family. Even a successful continuation would leave the safety of an
online choice between actions and the value of additional information untested.

## Historical evidence lowers the prior expectation

This is not the first OFF comparison in Sentinel. The earlier
[Iter49 transfer experiment](../iter49_hugsim_hard_tier_gate/RESULT.md) already includes this
case. Its two OFF evaluator reports have clipped maximum route completion about 0.178 and 0.167;
neither reports completed-route progress. Those results weigh against assuming that disabling
the monitor will solve the encounter. The [retained context](proof/historical_comparator_context.json)
binds the exact old files and distinguishes their planned-trajectory nc aggregates from actual
episode collision flags. They do not contain the current numerical-controller execution and
matched-prefix evidence. This proposal closes that specific gap once; it does not reopen a
large OFF-versus-ON benchmark or claim novelty for monitor ablation.

## Proposed bounded design

Freeze four fresh-process episodes in a successor protocol: two released-union references,
then two nominal-continuation episodes. Require the references to reproduce the current case
and their numerical/observation/state records to match before proceeding. In continuation,
run the same monitor in shadow and return the typed nominal plan unchanged even when its
braking latch fires. Keep planner observations/history, seeds, reset behavior, numerical
controller, solver policy, assets and original loop horizon fixed. Two continuation episodes
must agree under the declared replay contract; no seed search or initialized-episode retry.

Validate the full common prefix through the observation and typed nominal plan at the first
decision where the released monitor would change the plan. Record nominal, monitor-proposed
and delivered plans separately, with controller linkage and actual environment outcomes.
An unchanged nominal plan and a zero replacement are action choices, not matched braking
doses. Do not select a favorable cutoff or substitute a recorded nominal-plan sequence for a
planner that continues reacting to new observations.

The proposed primary recovery requirement remains collision-free route completion within
the original horizon and progress at the reference hazard time within the frozen allowance.
Keep reference-horizon diagnostics separate from final outcomes, with explicit censoring,
invalidity, missingness and latency. Preserve the actor's live feedback in every branch.
Freeze the exact resource and failure rules before execution; no new GPU run is part of this
memo. A maximum of four episodes bounds the scientific comparison, not its eventual compute
budget, which still needs a concrete preflight allocation.

## Resolve model semantics before that launch

The [source review](SOURCE_REVIEW.md) identifies two scope limits: actor candidate planning
uses a 0.1-second interval against a 0.25-second environment step, and the step integrator
accepts accelerations outside the declared Gym action space. The current canary may study
the unchanged released simulator, but it must name these dynamics and the effective control
limits explicitly. It cannot claim physical actuator admissibility or calibrated attack timing.
Add checks for the exact delivered control envelope and retain violations rather than silently
clipping. The effective numerical-controller bounds must be verified from the pinned controller
before finalizing that envelope.

If the successor instead changes actor timing or enforces a different actuator envelope,
that is a new simulator/control contract. It requires its own reference validation and a
distinct result; historical outcomes cannot be reinterpreted under the repair. No model repair
is authorized by finding a convenient result in a changed environment.

## Decision rules after the canary

| Observed result | Next investment |
| --- | --- |
| Repeated nominal continuation achieves useful recovery | There is an available continuation action in this model. Freeze the opportunity, then test a responsive action-selection baseline and a specified additional signal, including cases where declining braking is harmful. |
| Both continuation episodes also collide or fail progress | Close this case/action comparison. Change the development case-family design under a finite budget; do not begin a larger clock/strength search on this case. A richer action family would need a separate feasibility argument. |
| Continuation remains collision-free but is truncated | Inconclusive for recovery. Preserve the frozen horizon and censoring; do not extend until success. |
| Replay, prefix, action linkage or control-contract checks fail | Retain the failed run and repair the identified execution problem under a new protocol. No performance claim. |

The broader target remains information that changes a useful decision before its deadline,
against a strong responsive baseline, then independent-scene and fault evaluation. Ground-truth
contact labels used here cannot enter that monitor unnoticed. Low ego speed is not low impact
severity; one development scene does not establish safety, generalization or industrial value.
Iter135 stays deferred. Iter136–140 remain closed after their recorded outcomes.
