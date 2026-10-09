# Controller execution and measurement contract

## Frozen identities

- Preregistration: `89f83cff2f325bf1a1c76210871bea83fa50da4d`.
- Executed source packet: `3bbf160bc6be02b405d81d80ad2347a0167f9c73`, a descendant of
  Iter136 and accepted F17. The dirty WIP checkout was not the deployment source.
- [binding.json](binding.json) binds the corpus and four retained upstream controller files.
  The upstream HUGSIM commit is `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`.
- [corpus.json](corpus.json): all 57 Iter136 decisions in A/B frame order, each reconstructed
  as float32 and float64; 114 cases. Historical input dtype remains unknown.
- The upstream license is retained at
  [HUGSIM LICENSE](../iter136_hugsim_recoverability_canary/proof/source/HUGSIM/LICENSE.txt)
  and included in the deployed packet.
- GCP project `sunlit-unison-487018-b0`; existing `sentinel-gpu` instance
  `3834622546652649531`, `us-west1-a`, `g2-standard-8`. CPU-only work; the attached L4
  was not used. Installed Python 3.11.10 / NumPy 1.26.4; no dependency installation.

## Numerical and timing semantics

`Controller('numerical')` removes the wall-clock stopping condition. The original dynamics,
constraints, warm start, weights, 100-iteration limit and strict convergence threshold remain.
`Controller('timed')` retains the original 50 ms loop cutoff. Both load exact retained source;
trajectory conversion is extracted from the pinned source without importing the simulator.
The solver instrumentation records the norm and the branch actually taken.

Each successful receipt has typed raw input bytes, converted reference/state, configuration,
per-iterate identities, all convergence norms, final trajectories, control, iteration count,
and a numerical digest. The stopping reason is `converged`, `deadline`, or `iteration_limit`.
Failure receipts have `status: failed`, `stop_reason: failure`, the exception and `control: null`.
A failed receipt is not a usable control command; no fallback policy is invented here.

Convergence is checked first. If it fires, that iteration's deadline reading is null. Deadline
termination can occur on iteration 100; it still takes precedence over exhausting the loop.
The numerical digest excludes timing and process/block identity, but includes the numerical
termination reason and complete iterate identities.

The three timing concepts are deliberately distinct:

| Field | Measurement boundary | Deadline accounting |
|---|---|---|
| `deadline_reads` | Original loop timer, after warm start; last check can be skipped | Original timed branch uses elapsed >= 50 ms |
| `solver_ns` | Immediately around the complete solver call, including warm start/finalization | Miss when strictly > 50,000,000 ns |
| `adapter_ns` | Input validation through conversion, solve, numerical receipt construction and digest | Miss when strictly > 50,000,000 ns |

Final outer receipt packaging, JSON serialization/transport, simulator scheduling and physical
actuation are outside the adapter timestamp. Timings include instrumentation work within these
boundaries. They are not measurements of an uninstrumented controller or end-to-end actuation.
Clock calls in numerical mode are diagnostic and cannot select the returned iterate.

## Runtime controls and replay

Eight fresh workers follow the frozen order in HYPOTHESIS.md. CPU affinity is the lowest allowed
logical CPU (observed CPU 0). Loaded BLAS pools must report one thread. Each contended block has
exactly three arithmetic competitors on the same CPU; readiness, affinity, post-block liveness
and process reaping are retained. Idle means no task-created competitor; ambient load is logged.
No warm-up calls are discarded. File creation is exclusive; existing output refuses a rerun.

`verify.py` does not import the adapter. It imports the original retained upstream files,
reconstructs conversion separately, replays each observed iteration prefix, and checks the
complete numerical receipt. A separate method observer measures input update norms without
changing the original solve method. It checks stopping precedence, skipped readings, exact
repetition, schedule/completeness, loaded thread counts, affinity and deadline counts. It does
not authenticate a hardware clock or prove worst-case timing.

Run the independent check in the recorded Linux/NumPy environment with one BLAS thread and
CPU 0 affinity:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 0 \
  /opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python \
  experiments/iter137_controller_execution_contract/verify.py \
  experiments/iter137_controller_execution_contract/proof/benchmark
```

Cross-version or cross-architecture bit equality is not promised. Local development tests used
Python 3.14 / NumPy 2.4.2. The hosted parity check used the measured environment and compared the
instrumented and original solvers with identical scripted clock readings before the benchmark.

Infrastructure failures and recovery bounds are retained in
[INFRASTRUCTURE_AMENDMENT.md](INFRASTRUCTURE_AMENDMENT.md) and
[CAPACITY_RECOVERY.md](CAPACITY_RECOVERY.md). They change neither the data schedule nor the
scientific decision rules. A source-matching guest preflight armed the shutdown timer before
successful deployment. The failed SSH preflights did not arm a timer.
