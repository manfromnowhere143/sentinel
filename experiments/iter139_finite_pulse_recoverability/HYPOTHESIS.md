# Iteration 139 finite pulse recoverability

Status: preregistered development experiment, 2026-10-09. Commit this hypothesis before
implementation or execution. Parent: Iter138 `f780a98438b4de00d2efa41aae2489e82a276319`.
Daniel directly instructed continuing and challenging our numbers and research design.

## Question and limits

Does any of six finite zero-plan interventions, followed by resumption of the released
planner/monitor, produce useful recovery on the reproducible development collision case?
This tests availability of an action in a finite library, not whether an online monitor
can choose it, which information is missing, physical inevitability or population safety.
The scene and proposed grid were inspected during development; no confirmatory generalization,
p-value or independence claim will be made from these dependent trajectories.

Retain all Iter136/137/138 evidence unchanged. Audit Iter138's arithmetic from its committed
logs before new execution. The earlier validator restricted raw route completion to [0,1],
but the pinned HUGSIM source returns `(nearest_index+1)/(camera_count*0.9)` and terminates
at >=1. The successor accepts the actual [0,10/9] range, with a known-bad outside it and a
successful overshoot fixture. Do not clip values. Actual environment collision flags govern
the endpoint; the aggregate evaluator's planned-trajectory `nc` score is not collision probability.

## Frozen system and schedule

Use `scene-0411-hard-00`, scenario SHA-256
`9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9`, HUGSIM
`62c690d39fd90020e68a196bd8bcc1c4d4191f2e`, UniAD_SIM
`5fb279e39912a5ac7f58e00d56b065cadcd0a749`, released union monitor and the existing prepared
client image `sha256:2fc5cd574b7510c813fecee64d5568fddec8255a4b638dbca758b67696cb1d14`.
Keep simulator/client seeds 136/0, double reset, checkpoint, assets and original terminal logic.
Use unchanged Iter137 numerical controller source
`7784c0a885bba33414a680d2f943f3a701d7ba38bf29996908c6a7bd4089dc03`, actual dtype, single-thread
BLAS/OpenMP and matching runtime identities/available CPU affinity across all episodes.
Simulator PYTHONPATH excludes the client-only Torch shim. No package/image installation.

Exactly eight fresh-process episodes at most, in this order:

| Arm | Onset in simulated seconds | Duration in simulated seconds |
| --- | ---: | ---: |
| reference_a | none | none |
| reference_b | none | none |
| pulse_0_1 | 0 | 1 |
| pulse_0_2 | 0 | 2 |
| pulse_2_1 | 2 | 1 |
| pulse_2_2 | 2 | 2 |
| pulse_4_1 | 4 | 1 |
| pulse_4_2 | 4 | 2 |

References execute the released union. For pulse onset s and duration d, substitute
`zeros_like(incoming_plan)` exactly for decisions with s <= pre-action timestamp < s+d.
With fixed 0.25 s steps these are exactly 4d scheduled frames if reached. At s+d resume
the current incoming released-union plan, without resetting planner, controller or simulation.
The client keeps observing and planning throughout. Preserve dtype, weights, constraints and
conversion; no direct acceleration command, steering change or unregistered fallback.
State/actor reactions after intervention may differ and are part of the treatment response.

## Admission, execution and missingness

Both fresh references must pass equal lengths/terminal reasons, exact observations/discrete
fields, absolute numeric tolerance 1e-6 (zero relative tolerance), exact complete numerical
controller records and a separately implemented Decimal comparison. All calls must pass
independent original-source replay. A divergent pair closes REPLAY_DIVERGED; a matched pair
without collision closes NO_RECOVERABILITY_TARGET. Do not select another case or seed.

Every pulse must match the reference before onset: full trace and numerical controller
records for earlier decisions, plus observation, pre-action state and typed incoming plan at
the onset decision. The executed plan/controller response at onset is allowed to change.
An unreached onset is unobserved. A mismatching prefix, malformed trace, wrong action linkage,
source/config/runtime change or failed numerical replay is invalid and stops later execution.
Missing or partial logs, process failure and wall timeout stop later episodes. Retain all
observed data and leave later arms unobserved; no measured/initialized episode retry.
A correctly recorded simulator/401-frame truncation is a censored outcome and allows the next
scheduled cell; it never counts as prevention. No optional stopping after a useful cell.

Use the original loop limit: at most 401 actions (100.25 simulated seconds), with earlier
collision, route completion or other environment termination preserved. Log every original
observation hash, state, incoming/executed plan, control, outcome, raw progress, typed incoming
plan, typed executed input, conversion, numerical iterates, norms, stop reason, runtime identity
and wall duration. Reject missing, unsupported or nonfinite input before actuation.
Validate delivered monitor parameters/plans. Count scheduled overrides, actual overrides,
frames that changed the incoming plan, and released-monitor brake requests separately.

Commit complete raw proof for each episode before outcome interpretation or the next episode.
Preserve errors and partial files when an episode fails. Independently replay every controller
call in the bound environment and independently recompute pulse timing, prefix and outcomes
with a separate implementation. Known-bads cover onset/release off-by-one, invalid range,
continued override after release, dtype loss, wrong action, missing/reordered receipts, prefix
divergence, false success, missing/censored endpoints and resource/predecessor failures.
Test the complete capture-to-actuation path with a multiple-frame stub before live execution.

## Outcomes and decision rules

Let T be the first actual reference collision time and R its route completion at termination.
For each valid branch report:

1. Actual collision and first collision time; terminal reason and observed horizon. Report
   collision-free observation through T as a bounded diagnostic only. Early successful route
   completion satisfies this horizon rule; early other termination or missing T does not.
2. Progress at T (the state after the action reaching T), or successful terminal progress if
   the route completes earlier; final raw progress, time, override duration and changed-plan
   frames. The fixed progress bar is progress at T >= R-0.05.
3. **Useful recovery** requires no actual collision anywhere in the completed branch,
   successful route completion by the original loop horizon, the progress-at-T bar, a fully
   observed assigned pulse and resumption, and no more than two seconds of override. This
   endpoint is fixed before data. Censored/off-route/failed/incomplete outcomes cannot qualify.

Report every cell, including collision-free-but-censored and progress failures. Full-route
success and hazard-horizon diagnostics remain separate. For a complete valid six-cell grid,
at least one useful recovery yields `FINITE_PULSE_RECOVERY_SUPPORTED`; no useful cells and
no censored outcomes yields `FINITE_PULSE_RECOVERY_NULL`; no useful cells with censoring yields
`FINITE_PULSE_RECOVERY_INCONCLUSIVE`. An incomplete/invalid grid cannot receive an overall
supported or null verdict; report the reason and any observed cell outcomes without imputing
unobserved cells. These verdicts concern only this finite grid and this disclosed case.

## Timing and resources

Keep fixed simulation time and measured wall time distinct. Retain full solver, internal
adapter, complete adapter-call and client-roundtrip boundaries from Iter138. Report nearest-rank
p50/p95/p99/max and >50 ms counts with denominators; retain startup observations. These do not
establish an end-to-end vehicle deadline or simulate stale-action effects. Do not remove
diagnostics or change numerical policy to improve latency within this experiment.

Use only existing `sentinel-gpu` in us-west1-a. Up to three asynchronous start requests within
ten minutes for capacity recovery; no replacement VM/hardware change. Inspect completed provider
operation before SSH. Overall budget: **180 minutes from the first start request**, including
preparation, eight bounded episodes, collection/replay and cleanup. Arm an owned shutdown timer
with a margin; each episode has 1,200 s wall timeout and requires >=1,230 s remaining. Enforce
15 GiB local free for collection, 100 GiB remote free before an episode and 25 GiB reserve
after an 8 GiB per-episode projection. Exclusive new paths; preserve historical files/assets.
Pre-initialization infrastructure diagnosis is permitted within the same budget, preserving
failures; source/data/claim changes need a recorded pre-evidence amendment. Stop owned compute
on completion or closure and retain final provider state. No automatic budget/grid expansion.

If a useful cell exists, the next research step is a separately frozen information comparison
against a strong responsive baseline with matched actions/resources, then independent scenes.
A null is evidence about the specified action library, not permission to tune this experiment.
