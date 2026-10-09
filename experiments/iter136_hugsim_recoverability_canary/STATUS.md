# Iteration 136 source probe complete and live canary blocked

Status on 2026-10-09: **blocked at provider start**, with local tooling and source-fixture
validation complete. No live HUGSIM episode ran. No claim about collision prevention, faithful
live replay, or historical-run reproduction follows from these results.

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
Live integration remains unverified. Client patch identity, assets, process ownership, environment
and storage must still be observed on the host before any episode.

## Validation

The [test suite](../../tests/test_iter136_recoverability_canary.py) passed **37 tests** under local
Python 3.14.2, including two integrations through the instrumented driver with a stub environment,
source mutation, missing/invalid outcomes, altered observations, missing/reordered frames,
nonfinite values, mismatched identities, prefix divergence, terminal inconsistency and bounded
file reads. Ruff passed. The logs and commands are in [proof](proof/validation_final.json).

The attempted Python 3.10 pytest invocation could not run because that interpreter has no pytest
installed; its failure is retained. The standard-library source probe did run successfully under
Python 3.10. No frozen CI, full repository suite, hosted workflow or live simulator validation is
claimed for this candidate.

## Provider and storage evidence

Google Cloud rejected two bounded starts of the existing `sentinel-gpu` instance with
`ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS`: a `g2-standard-8` with one L4 was unavailable in
`us-west1-a`. Both failures and subsequent provider readback are retained. The instance remains
`TERMINATED`; no replacement instance, accelerator, disk resize or simulation was started.
Provider termination is a provider observation, not a replacement for the historical lifecycle
controller's `UNKNOWN` record.

Local space was initially below the 15 GiB proof-collection threshold. All 2,631 files in one
redundant clean D16 checkout were hashed against retained Git blobs before that checkout was
removed, recovering about 5.2 GiB. Its receipts and Git objects remain. The detailed cleanup
verification is retained outside Git; the committed summary binds its hash. Local free space
then exceeded 19 GiB. No scientific proof archive was deleted.

## Exact resumption point

The next operation is a bounded start of the same named instance after capacity becomes
available, followed by this read-only inventory from the repository root:

```bash
gcloud compute ssh sentinel-gpu --project sunlit-unison-487018-b0 --zone us-west1-a \
  --tunnel-through-iap --command 'python3 -' \
  < experiments/iter136_hugsim_recoverability_canary/inspect_host.py
```

Retain the output, verify the actual source/assets/client image and free-space requirements,
then bind those runtime identities before installing the new driver into a separate canary
location. Complete the two fresh-process reference episodes and run both comparators. A
divergent pair closes the live replay stage; an agreeing pair without a collision closes the
target stage. Only an agreeing collision pair permits the three registered onset branches.
Historical instance state and historical asset manifests cannot replace this inspection.

The five-episode, per-episode timeout, compute ceiling, no-episode-retry and stopping rules in
the preregistration remain unchanged. Iteration 135 stays deferred and unrun; Iteration 134
remains the last completed driving experiment.
