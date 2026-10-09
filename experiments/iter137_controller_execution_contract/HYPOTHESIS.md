# Iteration 137 controller execution contract

Status: preregistered development benchmark, 2026-10-09. Commit this file alone before
implementing or measuring the new controller adapter. Daniel explicitly authorized reproducible
controller execution, stopping-reason logs and separate deadline measurement before another live
comparison. Descend from Iter136 candidate `16d4b6159203529ecd6cfcdd547b02132e5a0d2b` on a new
local research branch. Preserve Iter136's failed replay and all historical evidence.

## Question and scope

Can a source-bound controller return identical numerical results for identical typed inputs
under declared CPU scheduling conditions, while reporting numerical termination and elapsed-time
deadline behavior as separate measurements? This benchmark includes no simulator construction,
model inference, rendering, driving episode or intervention. It cannot establish live replay,
collision prevention, hard real-time guarantees, transfer or production readiness.

## Frozen development corpus

Use every completed frame of both committed Iter136 reference traces: A has 28 frames and B
29. Preserve all 57 rows and their order, including duplicates. The controller inputs are each
row's executed trajectory, pre-action ego velocity and steering. Evaluate each row as float32
and float64: 114 typed cases. These dtypes are declared reconstructions; historical plan dtype
was not retained. Freeze input and upstream source hashes before benchmark execution.

The source is the already retained HUGSIM controller at upstream commit
`62c690d39fd90020e68a196bd8bcc1c4d4191f2e`. Keep its weights, dynamics, constraints, trajectory
conversion, 100-iteration ceiling and strict `1e-6` convergence threshold. No threshold search.

## Execution modes

- `numerical`: disable wall-clock termination, preserving numerical convergence and the
  100-iteration ceiling. This is a declared research execution mode, not the original timed
  policy and not a real-time guarantee.
- `timed`: preserve the original 50 ms loop budget and branch precedence, with explicit
  instrumentation. Report its instrumentation overhead as part of the measured adapter;
  do not claim uninstrumented deployment latency.

Retain exact input dtype/shape/bytes identity, full converted input state and reference,
configuration/source/environment identity, iteration count, convergence norms, stopping reason
(`converged`, `iteration_limit`, `deadline`, or an explicit failure), control, final solution
and per-iterate numerical identities. Deadline readings skipped by the original convergence
branch remain missing, not zero. Preserve the original convergence-before-deadline precedence.
Measure full solver and adapter duration separately from the loop's own cutoff reading. The
original 50 ms check excludes warm start and finalization; a full-call deadline miss must remain
visible even when termination is labelled converged. Logging transport duration is outside the
adapter measurement and is not claimed as measured actuation latency.

## Frozen measurement schedule

Use the existing Sentinel g2-standard-8 host and installed simulator Python/NumPy environment
if available. Limit BLAS/OpenMP pools to one thread and verify actual loaded pools. Pin the worker
to the lowest allowed logical CPU. `idle` has no task-generated competing worker; record ambient
load without claiming the host is otherwise perfectly idle. `contended` starts exactly three
CPU-only arithmetic workers on that same logical CPU. Record affinity, readiness and liveness.

Run eight fresh worker processes, each covering all 114 typed cases in trace/frame/dtype order:

1. numerical idle
2. timed idle
3. timed contended
4. numerical contended
5. numerical contended
6. timed contended
7. timed idle
8. numerical idle

Total: 912 measured calls. No warm-up solves are discarded. Keep cold-start observations.
Each block has a 180-second process timeout; the whole benchmark has a 30-minute ceiling and
the instance a 60-minute runtime ceiling including preparation and independent validation.
Stop on a failed block or nonfinite/malformed solver result, retain partial proof and mark
remaining calls unobserved. Do not retry a measured call/block or expand the corpus/repetitions.
Pre-benchmark infrastructure failures may be diagnosed within the resource bound. A local
development fixture is not a substitute for the named-host deadline benchmark. No replacement
instance is planned. Stop a task-started host after collection if no unrelated workload appears.

## Decisions and validation

Numerical replay is supported on this corpus/runtime only if all four numerical observations
of every typed case have exactly identical numerical records, including stopping reason,
iteration sequence and result bytes. Timing, process IDs and block labels are excluded from
that identity. Any mismatch is retained as failure; do not relax equality after observation.
Timed-output variability and deadline misses are descriptive outcomes, not admission targets.
Report counts, maxima and nearest-rank p50/p95/p99 by mode/load, with denominators and no
population confidence claim. A miss is observed adapter duration strictly above 50 ms;
also report solver-duration misses and original loop deadline termination counts.

Validate an instrumented solve against the unmodified upstream solver under identical scripted
clock readings before measurement. Use a separately implemented verifier to reconstruct inputs
and replay returned iterates from upstream source without importing the adapter. Retain known-bads
for source/input/configuration mutation, nonfinite or malformed inputs/results, false stopping
reasons, omitted calls, changed output, missed deadline accounting, and repeat divergence. Tests
must cover convergence/deadline/iteration-limit boundaries and verify that numerical mode does
not consult elapsed time to choose its result.

Commit raw benchmark output before interpretation. Keep code, receipts, results, continuity and
memory synchronized. A passing numerical benchmark permits proposing a fresh live comparison;
it does not erase Iter136 or itself execute that comparison.
