# Iteration 138 numerical controller live replay

Status: preregistered development experiment, 2026-10-09. Commit this file alone before
implementation or new execution. Daniel instructed continuing the mission and challenging our
own numbers. Descend from Iter137 `292a65322c5d4a47d501d99566fe156ab37474ed`; preserve Iter136's
failed pair, Iter137's successful CPU replay and deadline misses, accepted F17 and unrelated WIP.

## Question and scope

Do two fresh-process HUGSIM references match under an explicit numerical controller execution
contract? CPU repeatability is necessary but does not establish full-system replay. New evidence
is limited to one disclosed development case and this changed controller policy. No intervention,
new seed, new case, historical-result repair or population safety claim is included.

Before live execution, independently recompute Iter137's counts, exact repeats, final-control
variation and nearest-rank timing quantiles from all 912 retained records. Distinguish all
57 dependent decisions from the 114 dtype reconstructions. Identify the recorded timing
boundaries. The 50 ms value is the configured solver loop budget and our declared engineering
comparison threshold, not an established vehicle actuation deadline. Keep the original numbers
and any corrections equally visible. This is a retrospective audit, not fresh confirmatory data.

## Frozen system and schedule

Case `scene-0411-hard-00`, scenario SHA-256
`9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9`.
Use HUGSIM `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`, UniAD_SIM
`5fb279e39912a5ac7f58e00d56b065cadcd0a749`, the retained Iter136 dependency-prepared client image
`sha256:2fc5cd574b7510c813fecee64d5568fddec8255a4b638dbca758b67696cb1d14`, released union monitor,
checkpoint, double-reset startup and simulator/client seeds **136/0**. Seeds are held for a
fresh protocol, not selected to repair Iter136.

Run exactly two fresh simulator/client processes, reference A then B. No warm model or simulator
reuse. A failed/incomplete/invalid episode stops the experiment with later work unobserved.
Complete A is retained and committed before B. No outcome-dependent scene selection. Even if A
has no collision, B is still required for replay. No intervention branch runs in this iteration.

Use Iter137's source-bound `Controller('numerical')` unchanged: original weights, constraints,
conversion, strict norm <1e-6 and 100-iteration ceiling; wall-clock termination disabled. Preserve
the actual incoming plan dtype rather than reconstructing or coercing it. Reject unsupported,
missing or nonfinite input and failed controller output before actuation. Both runs use single
thread BLAS/OpenMP configuration and the same available CPU affinity; log effective libraries
and thread counts. This runtime contract is explicitly different from the historical timed
controller. Do not attribute a new live result solely to one isolated change.

## Logged quantities and replay gates

Retain all original full-frame observation hashes, pre/post ego and actor state, incoming/executed
plans, actual applied controls, terminal flags and progress. Additionally retain actual typed
controller inputs, converted state/reference, configuration/source identities, complete numerical
iterate identities, norms, iteration count, stopping reason and final controls. Link every
controller receipt one-to-one to its simulator frame and applied action. Missing or unlinked
receipts are invalid. Retain errors; do not substitute zero or a fallback command.

Separate fixed simulation timestamps (0.25 s increments) from measured wall time. Retain solver
and adapter timings, externally measured complete adapter-call time, and client roundtrip time
under explicitly stated boundaries. Timing fields do not participate in numerical replay equality.
Report them descriptively, with denominators; they do not establish real-time feasibility or
control the simulated actuation timestamp. No warm-up frames are discarded.

Require equal episode lengths and terminal reasons, exact observation hashes/discrete fields,
and absolute tolerance 1e-6 with zero relative tolerance on all original numeric trace fields.
Also require exact equality of the complete controller numerical records at corresponding frames,
including input dtype/bytes, converted inputs, iterates, stop reason and returned controls.
Require a separately implemented Decimal trace comparison and original-source numerical replay
of every retained controller call in the bound environment. No relaxed equality after observing
results. A trace/controller divergence closes the pair as REPLAY_DIVERGED; missing or malformed
proof is invalid. Record the earliest disagreement. A matching pair with no collision is
NO_RECOVERABILITY_TARGET, not an invitation to choose another case.

## Validation and resources

Retain known-bads for changed source/config/input, lost dtype, missing or reordered receipts,
wrong frame/action linkage, false stopping reasons, missing/false timing, divergent observations
or controller records, failed predecessors, reused output, unavailable space and insufficient
runtime. Use a stubbed full driver path to test capture-to-actuation linkage before live work.

Use only the existing `sentinel-gpu` in `us-west1-a`. Up to three asynchronous start RPCs within
10 minutes for capacity recovery; inspect completed operation status before SSH. No replacement
VM, hardware change or dependency installation. Overall wall budget is 90 minutes from the first
start request, including preparation, failed capacity requests, two episodes, collection and
independent verification. Use short client timeouts and arm a guest shutdown timer after workload
preflight. Preserve failures without silently resetting the budget. Each episode has a 1,200 s
timeout and needs 1,230 s remaining. Stop owned compute on completion; record final provider state.

Require 15 GiB local free before collection, 100 GiB remote before episodes and 25 GiB remote
reserve after an 8 GiB per-episode projection. Preserve historical source/assets/output. Runtime
files and outputs use new Iter138 paths with exclusive creation. No initialized episode or
measured call retry. Pre-initialization infrastructure may be diagnosed within the same budget;
source/data/claim changes require a recorded pre-evidence amendment.

## Decision and mission connection

A passing pair establishes only reproducible development replay under the declared research
policy. It permits designing a separately preregistered finite intervention/time experiment to
ask whether the case can still be helped. A failure locates an unresolved system boundary and
must constrain the next experiment. The main mission remains demonstrating useful incremental
information beyond a strong responsive baseline under progress, intervention and latency costs.
Workflow success, a small p-value, repeated dependent frames or an attractive score alone cannot
establish that contribution or parity with private industrial systems.
