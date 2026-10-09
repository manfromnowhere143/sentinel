# Iteration 138 live controller replay result

**Status: supported within the registered development scope. Verdict: REPLAY_MATCHED.**
On 2026-10-09, two fresh simulator/client processes produced byte-identical driving traces
on `scene-0411-hard-00` under the numerical controller and single-thread runtime contract.
All 52 controller calls passed independent original-source replay. Both references collided
at **6.5 simulated seconds**, with route completion **0.11557062998555366**. No intervention ran.

The [preregistered hypothesis](HYPOTHESIS.md) passed its replay gate. This establishes one
repeatable development pair; it does not establish collision prevention, useful additional
information, real-time operation, transfer or superiority to an industrial system. The next
scientific question is whether any admissible finite intervention can improve the outcome
while preserving progress. See the [proposed next experiment](NEXT_EXPERIMENT_DESIGN.md).

## Evidence and execution

The [paired analysis](proof/analysis.json) reports:

| Observation | Reference A | Reference B |
| --- | ---: | ---: |
| Complete driving frames and linked controller calls | 26 | 26 |
| Actual planner input dtype | float32 | float32 |
| Solver stopping reason: converged | 26 | 26 |
| Solver stopping reason: iteration limit | 0 | 0 |
| Solver stopping reason: deadline | 0 | 0 |
| Terminal reason | collision | collision |
| Simulated terminal time | 6.5 s | 6.5 s |

The original trace comparator and separate Decimal comparator agree. Complete numerical
controller records, including typed inputs, converted inputs, iterate identities, stopping
reason and returned control, match exactly across corresponding frames. Runtime identity,
effective thread counts and CPU affinity match; process IDs and timing measurements are
excluded from numerical equality. Every controller output is linked to its applied action.
The [A](proof/reference_a_monitor_delivery.stdout) and
[B](proof/reference_b_monitor_delivery.stdout) delivery checks confirm the frozen released
monitor parameters and client-to-simulator trajectory delivery on all frames.
An additional [stdlib recount](proof/arithmetic_recount.stdout) independently matches every
reported live timing quantile, exceedance count, stopping count, outcome and raw equality.

Both driving trace files have SHA-256
`98d197e050f647b5e0406963cbc7c73bcc3ae713cb81937a0c96b24070f49ae0`.
The separate controller logs differ because measured timing differs. Actual live dtype was
captured without coercion. Historical Iter136 dtype and stopping reasons remain unobserved.

This result concerns the explicitly changed numerical controller **and** runtime contract.
It cannot isolate the effect of removing the wall-clock cutoff from fixing numerical-library
thread counts. Iter136 remains closed as `REPLAY_DIVERGED`; its original failed pair is preserved.

## Deadline behavior remains unresolved

All values below are milliseconds, using nearest-rank quantiles over **26 observations per
reference**, including the first frame. With this sample size, p99 equals the maximum.

| Measured boundary | A p50 | A p95 | A p99/max | B p50 | B p95 | B p99/max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full solver | 59.411 | 84.026 | 92.943 | 58.888 | 89.714 | 98.945 |
| Complete adapter call | 62.970 | 89.805 | 99.903 | 62.883 | 96.265 | 105.346 |
| Client roundtrip | 1720.886 | 2234.849 | 33115.658 | 1708.812 | 2113.658 | 15489.515 |

In **each** reference, the full solver exceeded 50 ms on **23/26** calls; the complete adapter
call exceeded it on **24/26**. All solves converged because numerical mode has no wall-time
stopping condition. Convergence therefore says nothing about meeting a deadline.

The [execution binding](EXECUTION_BINDING.md) defines these boundaries. The adapter includes
conversion and diagnostic metadata construction; its external timer excludes controller-log
serialization/write. Client roundtrip includes transport, serialization/deserialization and
client work, so it cannot be called isolated model inference. Startup costs are retained.
The simulator advances in fixed 0.25 s steps regardless of wall time. These traces therefore
do not test the consequences of applying stale actions. The 50 ms threshold is a configured
solver budget and registered engineering comparison, not a validated vehicle actuation deadline.

## Challenge to the earlier numbers

The [independent Iter137 audit](AUDIT137.md) recomputed all 912 retained records and matched
the original counts, repeatability, final-control variation and reported quantiles. No arithmetic
correction was needed. A stricter denominator is **114 scheduled typed cases, 112 unique typed
inputs, 57 dependent source decisions, one disclosed driving scenario**. Repeated execution
does not create additional independent scenes. Full-solver deadline exceedances persist even
when adapter overhead is excluded.

## Retention and validation

- Preregistration commit: `43bc7ff185123e9cb91ef748b54d94f37ea9c343`.
- Executed source commit: `a25e9f09be2a495893c430a3c62bd2da2f4eef8c`.
- Raw A commit before B: `3c98aea4b0053d54b75d07b555ce0d85d6196ffb`.
- Raw B commit before paired interpretation: `ae5dbf0ca4a5388d1af7e9ae1e1e620211683b22`.
- [A inventory](proof/live/reference_a/remote_inventory.json) and
  [B inventory](proof/live/reference_b/remote_inventory.json) bind 11 collected raw files per
  episode and 82 remote-only rendered/scene files per episode, with sizes and hashes.
  Those remote-only bytes remain on the stopped host's persistent disk; they are not in Git.
- [Focused validation](proof/final_focused_validation.stdout): 138 tests passed, comprising
  32 Iter138, 51 Iter137 and 55 Iter136 tests. Implementation/test Ruff passed. Extracted
  committed Iter138 source passed its 32 tests under ambient local Python 3.14/NumPy 2.4.2.
  Host replay used the bound Python 3.11.10/NumPy 1.26.4 environment. No full frozen or hosted
  CI result is claimed for this candidate.
- The initial nonfinite-input known-bad exposed a structured-error logging gap; that failure,
  the correction and passing checks are retained. Initial test lint failures and the corrected
  clean run are retained. Runtime-manifest metadata was corrected before either episode;
  both the draft and correction record remain available. Neither episode was retried.

The local candidate is `research/iter138-live-replay`; it is unpushed. Canonical master remains
accepted F17. The generated historical mission snapshot remains unchanged; current candidate
state and host closure are in [STATE.json](STATE.json) and [STATUS.md](STATUS.md).
