# Sentinel research direction for information and recoverability

Current status, 2026-10-11: the separately registered execution sequence has reached
[Iter148](../../experiments/iter148_recovery_study/RESULT.md). Four baseline episodes passed
replay and source-defined completion; a progress-observation failure interrupted the first pulse.
The study is inconclusive, with no complete four-arm comparison. Both owned VM starts are
terminated. Iter135 remains deferred. The [current README](../../README.md) and
[architecture](../ARCHITECTURE.md) describe the implemented system and its limits. The dated
recommendation and earlier execution update below are preserved as the original proposal;
their "no new driving outcome" wording describes 9 October, not the current execution record.

Execution update, 2026-10-09: Daniel authorized proceeding. The first bounded implementation is
the separately preregistered [Iteration 136 canary](../../experiments/iter136_hugsim_recoverability_canary/HYPOTHESIS.md).
Its [current status](../../experiments/iter136_hugsim_recoverability_canary/STATUS.md) records local
source and tooling evidence plus the live provider block. The broader research questions below
remain proposed; no new driving outcome or theorem has been established.

Status: **proposed** strategic direction, 2026-10-09. This assessment responds to Daniel's request
to reconsider the route beyond Iteration 135 from first principles. It records an agent-authored
recommendation; it does not amend the frozen experiment, establish a new result, or claim a new
theorem. Iteration 134 remains the last completed science; Iteration 135 remains unrun.

## Recommendation

Make Sentinel answer a precise question:

> What additional information lets a monitor prevent failures that a strong responsive baseline
> misses, while an effective intervention is still available, at an acceptable cost to progress
> and unnecessary intervention?

Measure where that answer survives new scenes, observation faults, and a second planner. This
connects information sufficiency, the time remaining to recover, and actual intervention benefit.
It provides a better research target than assuming that an introspective score, an earlier alarm,
or an improved composite benchmark score must deliver useful protection.

Preserve Iteration 135 as an optional terminal comparison on the existing suite. Recommend
deferring its expensive execution while designing the smallest experiment that can distinguish
missing information from inadequate action or late response. Completion of that terminal test
need not be a scientific prerequisite for a separately preregistered successor. Any retirement,
amendment, or execution decision must be explicit before new evidence; existing results and
accepted publication history remain intact.

## What the repository establishes

- [Iteration 134](../../experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md)
  reproduced a NeuroNCAP benefit over OFF, but union minus placebo was `+0.3683`, with the
  registered 95% interval `[-0.1901,+0.8866]`. Its `PLACEBO_HARM_OR_NULL` verdict leaves semantic
  attribution unresolved.
- [Iteration 135](../../experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md)
  compares a responsive monitor with clock-only policies. Even a favorable result cannot
  separate semantic content from the advantage of responding to the current state. Its
  2,400 episodes reuse 14 source scenes. The [pre-run review](ITER135_PRE_RUN_SCIENTIFIC_DECISION_REVIEW_2026-10-09.md)
  records sensitivity and independent-scene limitations; its retrospective calculations are
  not power guarantees for the new comparator.
- HUGSIM transfer remains null. The [eight-row support-core synthesis](../../experiments/iter121_hugsim_support_core_two_track_synthesis/RESULT.md)
  found that selected fire objects were never supported by the collision actor before collision,
  while other support objects disappeared, drifted, or appeared later. This motivates hypotheses
  about observation and timing; it does not establish their causal role or population prevalence.
- The [released monitor source](../../experiments/iter15_latch_release/server_patch_union_release.py)
  uses decoded objects, scores, track IDs, ego pose and the planned ego trajectory. It estimates
  object velocity from successive detections and applies geometric CPA/TTC rules. Predicted
  `future_trajs` are logged but do not drive this trigger. Calling the current rule introspective
  must not imply demonstrated use of hidden learned representations or independent perception.
- Earlier decoder/activation-steering nulls constrain repeating those particular mechanisms.
  They do not prove that every internal representation is uninformative. Conversely, a new
  representation should earn a new experiment through a specific mechanism and falsifier.

The historical [plan-selection note](../NEXT_FRONTIER_INTROSPECTIVE_PLAN_SELECTION.md) contains
unsupported guarantees that a planner-generated alternative cannot introduce a crash and that
stopping is a safe floor. Those statements must not become design assumptions. A planner can
generate several unsafe options, and stopping can itself be hazardous. Candidate selection and
fallback behavior both require evaluation under specified dynamics and other-agent behavior.

## Current research and the contribution still to establish

Primary sources checked on 2026-10-09 establish substantial adjacent work. Their reported results
have different protocols and are not direct numerical comparisons with Sentinel.

| Existing work | Consequence for Sentinel |
|---|---|
| [RiskMonitor, v2, 2026-02-08](https://arxiv.org/abs/2503.07425v2) predicts collision risk from planning and motion tokens and evaluates braking in NeuroNCAP. | Internal-token monitoring with a frozen planner is already a direct comparison target. |
| [Argus, 2025-11-12](https://arxiv.org/abs/2511.09032v1) evaluates hazard monitoring and mitigation with TCP, UniAD and VAD. | Runtime takeover and multiple-planner integration alone do not establish novelty. |
| [EvoEye, v2, 2026-07-07](https://arxiv.org/html/2607.03755v2) combines collision prediction from module histories with targeted scenario acquisition on Apollo/CARLA. | Monitor-guided failure discovery and updating are already developed directions. Its stated evaluation questions emphasize prediction and acquisition effectiveness. |
| [Chakraborty et al., 2025-07-30](https://arxiv.org/html/2507.22389v1) use trajectory predictors, reachable-set approximations and conformal calibration to assess plans. | Calibrated prediction and geometric reachability are relevant technical baselines; they do not supply unrestricted safety guarantees under arbitrary shift. |
| [Verified Runtime Validation, 2018-11-15](https://arxiv.org/abs/1811.06502) addresses partial observation and actuator uncertainty in hybrid systems. | Partial observation and verified fallback monitoring have an established mathematical literature. |
| [Runtime Assurance Under Measurement Attack, 2026-09-25](https://arxiv.org/abs/2610.00285v1) studies observability conditions and indistinguishable safe/unsafe trajectories in radio networks. | Even the general observability-limit question has close work outside driving. Its model-specific results cannot be transferred to Sentinel without proof. |
| [Bench2Drive-Robust, 2026-05-18](https://arxiv.org/abs/2605.18059v1) evaluates camera-stream failures, ego-state errors and inference delay in closed loop. | Deployment perturbations belong in the eventual external test. Choosing this implementation still requires a bounded feasibility check. |

The proposed contribution is an experimentally supported account of **which signal changes an
available control decision and its outcome**, with the failure boundary exposed. Novelty of a
specific estimator, theorem, or benchmark remains to be established against the full relevant
literature. Combining existing concepts or naming a new framework is insufficient.

Mobileye's [2026-05-27 description of Meteor and Genario](https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/)
supports the industrial relevance of reproducible failure diagnosis and targeted validation.
It does not establish demand for Sentinel or access to any company's private systems.

## The mathematical target

Let `Z` be the history available through a specified baseline interface, `H` an additional
candidate signal, and `A` the permitted intervention library. Fix an outcome horizon, collision
loss, progress requirement, intervention costs, latency budget and evaluation distribution.
Let `R*(I)` be the lowest expected collision loss attainable by admissible policies using history
`I` under those constraints. The ideal value of the additional signal is

`V(H | Z) = R*(Z) - R*(Z,H)`.

For nested feasible policy classes, optional free access to `H` cannot make the ideal optimum
worse: the policy can ignore it. A trained system can still perform worse, and mandatory signal
acquisition can consume latency or compute. Those are empirical costs, not contradictions of
the ideal statement. The experiment estimates named policy contrasts; it does not observe an
unrestricted optimal value.

Define the information sets carefully. If `Z` contains the full input history and `H` is a
deterministic representation of it, `H` supplies no additional Shannon information. It may make
the relevant computation feasible within the budget. Distinguish an advantage from new
measurements, an advantage from a richer interface, and an advantage from useful computation.

Recoverability supplies the second necessary condition. For a specified simulator state, finite
action library and intervention-time grid, enumerate whether any allowed branch avoids the
collision over the horizon while meeting the other registered constraints. Record successful
times as a set: earlier action need not always be better. Failure of all tested branches means
no successful action was found in that library and grid; it does not prove physical inevitability.
Unknown or invalid branches remain unknown.

An initial impossibility check follows ordinary binary testing. Let `P_hazard` and `P_benign` be
the distributions of all monitor-visible history before a fixed decision deadline in two defined
case families. In the hazard family, the specified intervention is needed and effective; in the
benign family, that intervention is unnecessary. For any randomized binary decision from that
history,

`miss probability + unnecessary intervention probability >= 1 - TV(P_hazard,P_benign)`.

The errors are conditional on their respective families, not a fleet-weighted loss. The bound
follows because the difference between the intervention probabilities is at most total variation.
This is a standard testing result, not a new Sentinel theorem; see [Duchi's Stanford Stats 300b
notes, Winter 2021](https://web.stanford.edu/class/stats300b/Slides/12-testing-asymptotics.pdf).
Its practical use is to ask whether another signal separates cases before the deadline. A weak
classifier or a nonsignificant probe does not establish a small total-variation distance and
cannot prove an information-theoretic limit.

A substantive theory contribution would need new, checked results for the actual sequential
observation/action model, finite samples, resource constraints and specified shift. It should
explain an observed engineering boundary and predict an intervention or information change that
a subsequent experiment can falsify.

## Smallest decisive experimental sequence

### Establish whether intervention can still help

Use the existing HUGSIM support-core cases as disclosed development cases. Stop repeatedly
re-describing the same eight outcomes. First verify that a simulation continuation can reproduce
the original trajectory and outcome before attempting alternative branches. Restore simulator
state, planner history/recurrent state, controller state, monitor history and relevant random
streams. Equal seeds alone do not establish equal counterfactual starting states.

Where snapshots are unavailable, validate deterministic replay of the full prefix. If neither
works, use an explicitly paired full-episode design and narrow the causal claim; do not fabricate
precise branch evidence.

Run a small, preregistered intervention-time sweep with the same permitted actuator. Privileged
simulator state can label opportunities for this diagnostic, but must never enter deployable
monitor inputs. The first deliverable is a case-by-time table showing successful, unsuccessful,
invalid and unobserved branches, with severity and progress. This reveals whether it is useful
to invest in detection for that case and action library.

### Test a specific information hypothesis

Among cases with demonstrated intervention opportunity, compare a competent responsive geometry
baseline with the released union. Freeze their input fields and histories explicitly. Then add
one candidate channel justified by an observed mechanism, such as track continuity/uncertainty,
motion prediction or a specified learned representation. Include a relevant learned monitor
baseline such as RiskMonitor where reproducible implementation and compatible inputs permit.

The HUGSIM support-loss pattern makes persistence and uncertainty an initial hypothesis worth
testing. It is not a reason to blindly retain disappearing objects, which may increase false
braking. Benign counterparts and stale-track cases must be included. A separate sensor or
perception stream is a different intervention on the information supply and must carry its own
cost and common-failure evaluation.

Hold the action library, outcome definitions and latency envelope fixed across the information
ablation. Use equal calibration resources and training/calibration splits by source scene; report
learning capacity and computation differences. Compare prespecified progress/intervention-cost
frontiers. Do not match or adjust the primary effect on realized braking after treatment.

Offline prediction is a screening result. Only subsequent closed-loop policy evaluation tests
whether the additional signal improves outcomes. Perfect prediction of a collision after the
last effective intervention time has no prevention value for that action library.

### Test generalization once the mechanism earns it

Move to source scenes and scene families excluded from development. Keep the current 14
NeuroNCAP scenes and the repeatedly inspected HUGSIM rows out of confirmatory claims of fresh
generalization. Define the independent sampling unit and account for shared locations/scenarios;
more random seeds are not new scenes. Derive sample size from the actual pilot and decision
margins, with uncertainty in the variance estimate.

Lock one held-out evaluation before examining its outcomes. Report collisions and severity,
progress, intervention burden, time available for action, latency, missingness and subgroup
uncertainty. Measure failures of the planner and monitor together. Evaluate observation and
timing faults, then a second planner or simulator after the first mechanism has support.
Scenario mining may search development cases; the frozen evaluation set stays outside that loop.

### Let negative results choose the next investment

| Finding | Decision |
|---|---|
| No successful branch in the registered action/time library | Reconsider that action library or case family before fitting a better detector. Do not claim global unavoidability. |
| Additional signal shows no useful advantage at adequate precision | Stop that signal hypothesis; consider another observation source only with a new mechanism. An imprecise null remains inconclusive. |
| Prediction improves but intervention outcomes do not | Investigate timing, action effectiveness, or costs; withhold prevention claims. |
| Gain disappears against a responsive baseline | Attribute the earlier gain to the bounded policy comparison; close the unsupported mechanism claim. |
| Development gain fails on fresh scenes or faults | Retain the transfer failure and diagnose it before another benchmark tuning cycle. |
| Benefit survives the strong comparator and held-out evaluation | Package the reproducible result and broaden one dimension at a time. |

## Resource and engineering priorities

The next compute request should buy a decision between hypotheses. Set a small fixed canary
budget after verifying actual simulator cost; do not inherit Iteration 135's 110 L4-hour ceiling
as a target. Reserve independent evaluation compute before expanding development searches.

F17 source is published and hosted CI passed, but local R17 receipt generation failed and its
pytest failure cause remains unknown. The [Generation-18 recovery design](ITER135_GENERATION_EIGHTEEN_RECOVERY_DESIGN_2026-10-09.md)
identifies the required output preflight and failure-log retention. Complete bounded repairs
needed for reproducible execution, preserving the accepted lineage. Treat infrastructure success
as infrastructure evidence. Further layers of receipts or another same-row narrative do not
answer the scientific question.

The intended deliverable is a runnable monitor and evaluation system that can tell another team
which failures remain preventable, which signal makes prevention possible, and what costs and
failure boundaries it has measured. Industrial value remains a hypothesis until those results
and an actual user's requirements support it. No current evidence establishes superiority to
Tesla, Mobileye, NVIDIA, SpaceX, or their private systems.
