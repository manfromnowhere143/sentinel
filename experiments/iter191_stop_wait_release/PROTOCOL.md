# Iter191 — state-dependent stop, wait and release inside the connector

Preregistered 28 October 2026. Parent
`cde1d294ca687eedaef30ad67c728ffe46d9eed8`. This is connector qualification on
constructed and exposed retained inputs. It is not an integrated four-case trial.
Iter190 is closed; its 16/21 conditional continuations add no integrated credit.

## Single proposal intervention

Keep the Iter189 native binary, sampling, metric, target-derived horizon, physical
rules, uniform timing eligibility, primary ranking and extra-branch rule unchanged.
The original connection has at most eight steps / 128 attempted transitions; case
limits remain 18,000 transitions / 120 seconds. No root-specific tuning is allowed.

Insert exactly one feedback proposal FIRST when the final scheduled checkpoint
lies within the next eight absolute frames, strictly after the current frame.
Use the configured connection horizon for this activation window, not a hardcoded
case ID or frame 32. An actual target may shorten the connection; never lengthen
it to accommodate the proposal. With no checkpoint or outside this window, the
original proposal schedule is unchanged.

Through the final checkpoint, apply `clip(-v/dt, -2, 2)` acceleration and zero
steering rate. This lands at zero speed when a one-step stop is available and
otherwise brakes within the same bound. After that checkpoint, use the frozen
Iter153 route controller at target speed 2 m/s. Compute each command from the
state reached by the existing evaluator; never pre-roll a hidden trajectory,
clamp a physical state, extend the horizon, or bypass a rejection. Existing
post-rejection evaluation semantics remain unchanged and every attempted step
still consumes budget. All physical and collision checks remain decisive.

Represent the new feedback program explicitly in the request log. Its cache
namespace is separate from physical open-loop parameter vectors, so equal numeric
encodings cannot hide work. Then run the unchanged pose-aware initial program,
phase grid and Halton sequence with the remaining allowance. The inserted request
counts toward the existing 4,096-request cap. Preserve first-completion stopping,
deadline precedence, serialization charging and exact native branch transport.

## Complete fixed populations and comparator

Before any new retained-input evaluation, freeze all 23 original outgoing requests
from Iter190's 22 late native node records, including their exact targets, original
tree context, ancestry and attempted work consumed before the request. Also freeze
21 disclosed synthetic goal requests, one per exact retained case/state/frame
root, using the existing native goal construction and target frame 96. These
test connector compatibility from unrequested roots; they are not actual original
requests. Duplicate roots use the later, smaller-budget history and its tree context.

Run the original Iter189 connector and the candidate once for every request.
Alternate arm order by population index. Both get the same original remaining
transition allowance (capped by 128), full original case wall debit and unchanged
target-derived horizon. Setup, queries, proposals, checks and payload serialization
are charged. A result after the remaining deadline is censored; no late branch is
admitted. Offline prefix reconstruction and scalar admission have separate clocks.
No shared warm start, search result or query cache crosses arm executions.

Qualification also runs both native adapters on three constructed fixtures in
separate fresh processes: an untimed straight corridor, a low-speed timed endpoint
and a curved timed endpoint. The latter two use a checkpoint at frame 1 to exercise
schedule-derived activation and release without a frame-32 special case. Retain
all native events and validate actual transport, registration and returned paths.
The untimed candidate must preserve baseline deterministic behavior. Timed cases
must exercise the feedback proposal and complete within their frozen bounds.

## Independent admission and acceptance

Qualify implementation before source freeze using constructed stops, waits,
release, curved steering, infeasible/blocked motion, shortened horizons, off-grid
clocks, exact budget exhaustion, cache aliasing, and expiry before/within/after
evaluation. Retain corruption controls for action/state/clock/ancestry, omitted
work or queries, program ordering, false completion and invalid branch transport.

Separate code reconstructs the feedback actions and original proposal ordering,
replays physical motions, timing eligibility and both selectors, and recomputes
every queried full scalar mask, including rejected/unselected alternatives and
post-rejection queries. Reconstruct the fixed population independently. Verify
all original prefixes and every returned branch join. No favorable missingness.

Primary qualification requires all constructed interface checks to pass, exact
baseline reconstruction on the 23 original requests, preservation of every
baseline full completion on those same requests, and at least one newly complete
original left-bend request within its original remaining budget. Report all
paired gains/losses in full completion, checkpoint crossings, returned progress,
attempts, queries and wall observations. Report the 21 synthetic goal requests
separately. They cannot substitute for a failed primary criterion. Any missing
or malformed evidence is invalid; a relevant censored result is inconclusive;
a complete valid schedule failing the criterion is contradicted.

## Resources and closure

Freeze all source, inputs, runtime, population and qualification controls before
one exclusive raw acquisition. Commit raw before independent admission. No
scientific retry or post-outcome tuning. Producer: 1,200 seconds; checker: 5,400
seconds; external supervisors allow 10 seconds for termination and reap children.
Per native constructed run: 512 transitions / 10 seconds, with a 15-second process
supervisor. Each stage has a 1 GiB RSS ceiling, 256 MiB output cap and 2 GiB free
storage floor. Runtime binds the previously qualified local binary and numerical
stack. No cloud/GPU, simulator driving or provider spending.

If supported, the next step is a separately frozen unchanged-budget all-four
integrated trial with gains/losses against Iter189 and Iter183. No expansion
allocation or metric amendment is part of this qualification. Source comparison
stays closed; actual-history recovery, response delay and superiority remain open.
