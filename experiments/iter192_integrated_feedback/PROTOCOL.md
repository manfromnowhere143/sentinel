# Iter192 — exact feedback proposal in the complete search

Status: preregistered, 28 October 2026. No Iter192 case has run.

## Question and intervention

Does the exact qualified Iter191 stop/wait/release proposal complete the remaining
left bend while preserving the other three exposed development-case completions?
Use `iter191_stop_wait_release.adapter.search` directly, without changing its bytes
or any imported historical source. The sole planner difference from Iter189 is
the already qualified state-dependent proposal. No allocation, sampling, metric,
target horizon, timing eligibility, native binary, primary/extra selection,
dynamics, collision or completion-rule change is permitted.

The proposal activates only when the final scheduled checkpoint lies strictly
ahead within eight frames. It brakes using the evaluated speed, waits through that
checkpoint, then uses the established route controller at 2 m/s. The remaining
initial, phase-grid and Halton proposals share the original connector allowance.
Known checkpoint times remain privileged model inputs, not online observations.

## Population, comparisons and ceilings

Exactly one candidate acquisition, in this order: bend_left / 20261014,
bend_right / 20261015, chicane_left / 20261016, chicane_right / 20261017. Use the
unchanged Iter161 reflected fixtures and full Iter189 planner configuration:
128 attempted transitions per connector, 18,000 per case, 120 seconds per search,
96 actions, eight-frame connector horizon and 4,096 proposal-request ceiling.
One fresh process per case isolates the native RNG. No retries or replacement
seeds, no outcome-based stopping, no tuning on this trial.

Compare each case to the committed, admitted Iter189 and Iter183 records at
`345495fee70c12a30928353779f3507046484791`. Those are retained controls, not newly
executed arms. All four cases are exposed development cases, not holdouts. Report
each completion, gain, loss, returned frame/progress, checkpoint count, attempts,
queries, calls, primary/extra registrations where available, elapsed search time,
and memory. Missing historical metrics remain null. Used work and wall time need
not match: the intervention changes the tree. Wall-time differences are descriptive
and are not speedup estimates from randomized contemporaneous trials.

The producer retains every queried mask, including rejected/unselected states.
This recording occurs inside the search clock, as in the qualified Iter191 native
worker. Iter189 materialized only registered states after search; report this
instrumentation difference, and do not subtract its cost. Count final serialization
and setup separately in full worker/producer elapsed time. A search that misses its
120-second deadline cannot be credited with a completion. Full workers have a
180-second supervisor ceiling; producer 900 seconds; independent checker 7,200
seconds; each process 1 GiB RSS, all raw output 256 MiB, free disk at least 2 GiB.
Separate process-group supervisors terminate/reap timed-out children. Exhausting a
resource envelope makes the stage invalid, with all existing evidence retained.

## Qualification and immutable evidence

Freeze this protocol before development-case execution. Reuse the exact admitted
Iter191 mechanism and independently implemented replay. Qualify the new wrapper
on constructed native fixtures only, with known-bads for changed budgets/source,
population/seed omissions, raw/source binding, masks, completion and comparisons.
Retain test commands/outcomes, then commit all source, plan, protocol, runtime/input
bindings and qualification record before acquisition. No new planner mechanism is
being qualified; Iter191's six native workers and complete request audit remain
the mechanism qualification. Commit all raw before separate admission. A failed
check cannot be repaired by silently replacing raw or revising the frozen source.

Replay every attempted transition and proposal using Iter191's separate scalar
control/physics/eligibility checker; reconstruct primary/extra choices and native
ancestries; replay all queried masks with scalar point geometry. Check every
returned path, checkpoint and registered sequence, including unused branches.
Native random choices are source/seed/event-bound, not independently regenerated.
Producer and checker are separate implementations executed by the same agent;
this is automated verification, not independent human review.

## Analysis and stopping decision

Supported means all four complete within the frozen search ceilings, with no lost
completion against either retained comparator, and all evidence checks pass.
Otherwise the hypothesis is contradicted if valid uncensored evidence is complete;
any wall-time-censored case makes the scientific comparison inconclusive. Invalid
evidence is never an observed planning failure or a successful completion.
No significance test or population-general improvement is inferred from four
exposed cases. A finite-search miss is unknown feasibility, not physical exclusion.

After success, return to the recorded actual intervention histories and imposed
delays under a separate protocol; cap further four-case tuning. After a miss,
first locate the exact request/evaluation/selection or resource blocker from this
retained tree before selecting any successor. Do not repair Iter192 post-outcome.
Neither outcome demonstrates simulator recovery, a real-time safety intervention,
robustness, competitor superiority, deployment readiness or commercial value.
No new driving episodes, provider/GPU job, spending or live vehicle operation.
