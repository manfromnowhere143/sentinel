# Iter193 — preserve intervention history and impose response delay

Preregistered 28 October 2026, before any Iter193 source search. Execution requires
independent admission of Iter192 as supported. No further four-case tuning.

## Question and finite population

Can the exact qualified feedback/retention planner find a complete model-valid
continuation after actual history is preserved, and how does that finding change
with intervention time and an imposed action delay?

Use both retained Iter152 monitor histories already qualified through frame 25 by
Iter164. Verify their controls and states agree through each intervention origin.
They are replicas of one exposed source scene, not independent scenes. Freeze six
conditions, ordered by origin frame then delay: origins 23 and 25 (5.75 and 6.25 s),
each with delays 0, 1 and 2 simulation ticks (0, 0.25 and 0.50 s). Frame 25 is the
recorded first monitor fire. Frame 23 is an explicitly earlier, privileged probe;
it is not a demonstrated trigger improvement. One native process per condition,
seed 20261014 throughout, no retries, replacements or source-case tuning.

Preserve every recorded action through the intervention origin. During each
imposed delay, hold the last applied acceleration and steering-rate command,
propagated through the frozen dynamics. This is a declared counterfactual command
hold, not a recorded post-intervention trajectory or measured hardware delay.
The first new control applies one tick after origin plus delay. If the preserved
or delayed prefix violates a frozen constraint, record `prefix_ineligible` and do
not search from an already rejected prefix. Do not call that a search failure.

## Adapter and budgets

Keep the Iter191 native adapter and proposal bytes unchanged. Translate only the
time origin: replace the reset state by the validated branch state, subtract the
branch time from each original progress deadline, and subtract its frame from the
original 401-action horizon. Keep route, obstacles, background population,
vehicle model and all thresholds unchanged. On output, add the origin back to
every suffix frame and concatenate the preserved history exactly. This
translation applies to this static source model; it is not valid for arbitrarily
time-varying scenes. Qualify translation, no-delay identity, command hold,
deadline preservation, joins and rejection on constructed fixtures first.

Use the full Iter189 planner configuration except the remaining absolute horizon:
18,000 attempted transitions / 120 search seconds per condition, 128 transitions
per connector, eight-frame horizon, 4,096 proposals, unchanged selection and
sampling formulas. No use of reset-time successful controls. Known geometry and
checkpoint schedules are privileged inputs. No information advantage claim.

The search records every request, attempted transition, query summary, branch
choice and native identity. Materialize full masks for the joined selected path
after search; charge those queries/time separately in full worker accounting.
Unlike Iter192, unselected background masks receive producer labels only; no
independent clearance claim is made for unselected branches. This explicit
restriction keeps full-scene replay bounded without altering planner decisions.
Replay every attempted physical/proposal/selection predicate and independently
check full scalar background masks along every returned path and held prefix.

Worker supervisor: 180 s; full producer: 1,800 s; checker: 7,200 s; each process
1 GiB RSS; raw output 512 MiB; minimum free disk 4 GiB. Record actual worker,
search, serialization/replay times and resources. Search expiry cannot become a
completion. Retain an invalid or censored outcome literally. Freeze protocol,
source, bindings and qualification before acquisition; commit raw before replay.

## Comparisons and decision

The six rows are descriptive paired conditions on one exposed source scene.
Report complete model continuations, partial progress, checkpoint checks,
attempts, geometry queries, deadlines, latency and missing/invalid evidence.
Retained Iter164 first-fire exact/24 miss is context only: its larger
60,000-transition / 1,800-second envelope and different search are not an equal-cost
baseline. Do not infer causal delay effects from finite stochastic-search misses,
monotonic recoverability from these rows, or impossibility from search failure.

Supported means at least one complete independently checked continuation at the
actual first-fire origin (frame 25). Earlier-only success is a separate observation.
If no actual-first-fire completion is found, any search wall-time censoring makes
this efficacy hypothesis inconclusive; otherwise it is contradicted for this
registered finite method/population. Invalid evidence never counts as a miss.
The latency observation is separate: compare measured search and full worker time
with the 0.25-second simulation tick; imposed delay is not an allowance to hide
computation. Offline success does not establish an executable online response.

If a complete continuation is admitted, qualify execution in the native simulator
before claiming intervention recovery. If none is admitted, do not tune these six
rows or launch a larger learned-monitor/held-out efficacy study around an
unestablished intervention. Close the negative evidence, identify the mechanism
or timing blocker, and select the next bounded falsification. Product selection
remains a hypothesis: offline recovery qualification first; runtime supervision
requires execution, uncertainty, deadline and transfer evidence.

No new driving episode, live vehicle action, provider/GPU job or spending occurs
in this local source-model test. Native execution is a subsequent conditional
qualification and must not be reported as already performed.
