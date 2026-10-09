# Iteration 136: seeded replay diverged at the controller

**Verdict: `REPLAY_DIVERGED`.** Two fresh-process references completed on the disclosed
`scene-0411-hard-00` development case. Both independent comparison implementations reject
the registered replay condition. The three intervention branches were not run. Recoverability
and intervention benefit remain unobserved.

## Live observations

| Observation | Reference A | Reference B |
|---|---:|---:|
| Completed frames | 28 | 29 |
| Simulated time to collision | 7.00 s | 7.25 s |
| Route completion | 0.145091389 | 0.146347591 |
| Collision log marker | foreground | foreground |
| First acceleration command | 3.0 | 3.0 |
| First steering-rate command | 0.32443532509892165 | 0.3244431296045859 |

The first observation hashes, pre-action states and incoming/executed plan values are
**exactly equal**. The first steering-rate commands differ by approximately `7.804505664e-6`,
exceeding the registered absolute tolerance `1e-6`. Resulting steering states differ on
the first step. Observation hashes and plans differ at the next decision, at 0.25 seconds.
Collision flags differ at the reference-A final step. The sequence is retained in the
[machine-readable analysis](proof/analysis.json).

Both traces pass schema checks. The frozen union's recorded parameters and delivered
trajectories match all 57 recorded decisions. This delivery check does not establish
safety or semantic benefit. Collision severity is unmeasured. One case and two references
do not estimate population failure rates or real-world risk.

## A concrete explanation to investigate

The pinned [controller configuration](proof/controller_source/lqr.py.txt) specifies a
50-millisecond wall-clock solve budget. The [solver](proof/controller_source/lqr_solver.py.txt)
checks `time.perf_counter()` after optimization iterations. Seeding the simulator and
client therefore does not make elapsed compute time part of a reproducible input state.

An explicitly [registered exploratory CPU diagnostic](CONTROLLER_DIAGNOSTIC.md) ran 26
solves on the retained first plan and state. It constructed no simulator and ran no model,
renderer or driving episode. For the float32 reconstruction:

- The live A command matches optimization iterate **38** exactly.
- The live B command matches optimization iterate **27** exactly.
- All five pairs of identical controlled stopping conditions reproduce the same complete
  sequence of first-control iterates exactly. Float64 pairs also repeat exactly.
- Real-clock float32 solves stop after 39, 41 and 41 iterations; controlled runs that allow
  the solver to converge stop after 41 iterations.

This supports clock-dependent controller output as a mechanism in the source fixture and
provides a specific explanation consistent with the live divergence. Actual live solver
iteration counts and stop reasons were not logged, and the original plan dtype was not
retained. The float64 reconstruction was tested too; its nearest commands differ from
the live values by about `2.2e-9`. These limits prevent claiming a complete causal account
of every later difference. No controller change or relaxed tolerance was applied to the
live experiment after this result.

## What this changes about the next step

The next prerequisite is an explicit controller execution contract. A trajectory, vehicle
state and RNG seed are insufficient inputs for repeatable control when optimization stops
according to elapsed machine time.

The successor should first specify and test:

1. **Numerical replay:** record solver inputs, dtype, iterations, stop reason, controls and
   configuration identity. Evaluate a declared deterministic numerical stopping mode in
   isolated CPU fixtures, with known-bads and independently recomputed checks.
2. **Compute constraints:** retain the original timed controller as a named comparator;
   measure deadline misses and output variation under declared CPU load. Removing its
   time limit cannot establish real-time feasibility or benchmark equivalence.
3. **Fresh live validation:** preregister a successor and repeat the complete reference
   comparison before attempting counterfactual interventions. Do not tune seeds or
   tolerances against this failed pair, or reuse it as a passing reference.

The broader mission remains measuring which additional information enables useful, timely
intervention beyond a strong responsive baseline. This result establishes a prerequisite
for interpretable intervention experiments; it establishes neither recoverability nor
state-of-the-art performance.

## Failure history, provenance and resources

The first launch failed before Gym could import the environment class. The agent had
mistakenly applied the client-only shim to the simulator. Its raw failure was committed
before diagnosis, and the [repair record](PRE_INITIALIZATION_REPAIR.md) preserves the bad/good
import check. The record contains **one failed pre-initialization launch, two completed
simulation episodes, zero interventions and 26 CPU diagnostic solves**. No initialized
episode was retried. Original and corrected output directories both remain intact.

Raw reference A and B proof was committed before paired interpretation, at
`892eac240321c68c22ea54849fc1ff96adbc2c3a` and
`c591b613a4b0eba81f8c11a29914ae6595ff84c8`. The CPU diagnostic was registered at
`1812e76f67cf174dc4c756e5e131040cbc86d359`; its raw proof was committed before interpretation
at `254ea05449092291dc036c3bce9f1d6f238c67cf`.

The original L4 instance started on the third attempt. Postflight verified all 409 bound
runtime files, found no running containers or GPU processes, and measured 110.86 GiB
free on the data disk. The host was then stopped within the original 120-minute ceiling.
The [provider readback](proof/provider_final.json) records its final state. That provider
observation does not replace the older Iteration-135 lifecycle controller's `UNKNOWN`.

The focused local suite passes 55 tests and Ruff. The exact committed candidate also passes
the 55 tests and reproduces the analysis byte-for-byte after extraction outside the dirty
checkout; all 115 then-retained proof checksums and new document links verified. See the
[candidate validation receipt](proof/final_candidate_validation.json). No full repository suite, frozen CI,
hosted candidate workflow or production readiness is claimed. This result is retained
on local branch `research/iter136-recoverability`; canonical `master` remains accepted
F17. Iteration 135 remains deferred with its protocol unchanged.

## Recompute

```bash
python3 experiments/iter136_hugsim_recoverability_canary/analyze_canary.py
python3 -m pytest -q tests/test_iter136_recoverability_canary.py
```

The analysis uses retained local proof and needs no provider access. Remote videos,
visualizations and point clouds are inventoried by hash; the committed proof includes
traces, monitor decisions, process logs, evaluation JSON, original data/info pickles,
source identities and raw diagnostic output. Reading the analysis requires no pickle load.
