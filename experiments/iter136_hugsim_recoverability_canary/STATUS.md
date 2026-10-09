# Iteration 136 closed: REPLAY_DIVERGED

Status on 2026-10-09: **failed the registered live replay condition**. Two fresh-process
references completed, with collisions at 7.00 and 7.25 simulated seconds. Both comparison
implementations reject the pair; zero intervention branches ran. The CPU controller-clock
fixture reproduced both first-step control commands at distinct optimization iterates.
Read [RESULT.md](RESULT.md) for the evidence, limits and successor requirements. The GPU
host is stopped, with provider readback `TERMINATED`.

## Registered work and retained evidence

The [hypothesis](HYPOTHESIS.md) was committed alone as
`d46e01672ac8edd1bb4916c1330a3b7765c6bc1c`, a direct child of accepted F17, before the
source probe and provider start. Tooling and raw proof were committed as
`de076aba62020752ea806b92da332873060f07ce` before this interpretation. Both commits use
Daniel's configured author and committer identity. They are on the local research branch
`research/iter136-recoverability`; canonical `master` remains F17. The existing dirty WIP checkout
was preserved. This is a separately registered development canary, not an Iteration-135 retry.

## Source result

The [retained source probe](proof/reset_probe.json) executes the exact pinned HUGSIM reset method
with explicit observation and actor-planner stubs. Repeated reset left steering `0.4`, previous
acceleration `-1.0`, and previous steering rate `0.2` intact. The planner stub's update count
advanced from `1` to `2`. The method does not read its `seed` argument. Python 3.10 and Python
3.14 produced byte-identical probe reports.

This establishes the tested reset method's behavior in that fixture. The pinned actor-planner
source also updates actor state during `plan_traj`, and the historical driver calls reset twice.
A generic call to reset is therefore an unsupported substitute for full simulator/planner state
restoration. The canary preserves the existing startup sequence and uses new processes, followed
by empirical trace equality checks. It does not claim that seeding alone guarantees determinism.

## Implemented tooling

- [instrument_driver.py](instrument_driver.py) produces a separate driver from one exact upstream
  source hash, keeps the two historical startup resets, fixes simulator seeds, isolates output
  directories and records each action boundary. It leaves the upstream file unchanged.
- [replay_trace.py](replay_trace.py) records observations, before/after state, incoming/executed
  plans, control commands and terminal outcomes. It checks the entire reference pair and the
  pre-intervention prefix, including the first intervention observation and incoming plan.
  Missing/non-Boolean collision values are rejected; timeouts and truncations cannot count as
  prevention. Collision severity is explicitly unmeasured by this trace.
- [independent_reference_check.py](independent_reference_check.py) separately compares complete
  reference traces using decimal arithmetic. It complements the primary schema validator; it
  does not validate the full schema or infer intervention benefit.
- [inspect_host.py](inspect_host.py) performs a read-only inventory of the named host, pinned
  assets, free space, repositories, image and running containers/GPU processes. Its report does
  not authorize an episode or establish lifecycle state on its own.

The generated driver is retained at [instrumented_closed_loop.py.txt](proof/instrumented_closed_loop.py.txt),
SHA-256 `8c3b3287a8cd52b392e87c2fc59d87d9dd6db8bbbc6f24658d00652aebc34248`.
The [execution binding](EXECUTION_BINDING.md) and [pre-initialization repair](PRE_INITIALIZATION_REPAIR.md)
record the host inspection and corrected live integration. Two references completed; their
full-trace comparison failed. All 409 bound runtime files also matched at postflight.

## Validation

The initial [test suite](../../tests/test_iter136_recoverability_canary.py) passed **37 tests** under local
Python 3.14.2, including two integrations through the instrumented driver with a stub environment,
source mutation, missing/invalid outcomes, altered observations, missing/reordered frames,
nonfinite values, mismatched identities, prefix divergence, terminal inconsistency and bounded
file reads. Ruff passed. The logs and commands are in [proof](proof/validation_final.json).
The same 37 tests also passed against the exact committed candidate's canary files and project
configuration extracted into an isolated temporary directory, excluding the dirty WIP checkout;
the [candidate validation receipt](proof/committed_candidate_validation.json) binds that source.

The attempted Python 3.10 pytest invocation could not run because that interpreter has no pytest
installed; its failure is retained. The standard-library source probe did run successfully under
Python 3.10. The expanded local suite passes **55 tests** after adding launcher and monitor-delivery
known-bads. The exact committed candidate also passes those 55 tests and reproduces the
analysis outside the dirty checkout; see [validation](proof/final_candidate_validation.json).
Two live references completed under the bound runtime; exact replay failed.
No frozen CI, full repository suite or hosted candidate workflow is claimed.

## Provider and storage evidence

Google Cloud rejected the first two starts for unavailable L4 capacity. The third start
succeeded on the same instance and zone. The scene and checkpoint were present, and two
registered references completed after one retained pre-initialization launch failure.
Postflight observed no running containers or GPU processes and 110.86 GiB free. The
instance was stopped within 26 minutes of provider-reported runtime; final provider
readback is `TERMINATED`. The historical lifecycle-controller record remains `UNKNOWN`.
No replacement instance, new accelerator or disk resize was needed.

Local space was initially below the 15 GiB proof-collection threshold. All 2,631 files in one
redundant clean D16 checkout were hashed against retained Git blobs before that checkout was
removed, recovering about 5.2 GiB. Its receipts and Git objects remain. The detailed cleanup
verification is retained outside Git; the committed summary binds its hash. Local free space
then exceeded 19 GiB. No scientific proof archive was deleted.

## Closed protocol and next research step

Do not resume the intervention grid or retry these references. The preregistered stopping
rule closed the live canary as `REPLAY_DIVERGED`. One failed pre-initialization launch,
two completed episodes, zero intervention episodes and 26 CPU fixture solves are retained.

The successor needs an explicit controller execution contract: deterministic numerical
replay checks, solver iteration/stop-reason/dtype logging, and separate measurement of
real-time deadline behavior under declared compute load. Removing the 50 ms cutoff does
not establish real-time validity. Register and validate that successor before another live
reference pair. Keep the original failed pair and the original timed controller as evidence.

The [result](RESULT.md) and [local analysis command](analyze_canary.py) are the current
entrypoints. Iteration 135 remains deferred and unchanged. Iteration 134 remains the last
completed driving result on canonical master; this Iteration-136 result is a local candidate
on `research/iter136-recoverability`, with canonical master still accepted F17.
