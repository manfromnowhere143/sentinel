# Iter147 result: full-horizon and actor-path qualification

2026-10-10. **Supported within the registered engineering scope:** eight fresh-process
GPU cases, 912 actions and four matching replica pairs. The separate local qualification
supports 890 constructed actions and three replica pairs; 129 focused tests pass.
The GPU source is `7fdb3c5fa9b698e08fedf0f2184dab25a7c495eb`.
Candidate `research/iter147-full-horizon-execution` remains local and unpushed.

## What ran and what happened

| Fixed pair, scene 0013 | Actions per replica | Retained outcome | Monitor decision input |
|---|---:|---|---|
| Easy / monitor hold | 401, 401 | Action cap; both censored | Explicit injected detector object; real model still calculated |
| Extreme / nominal / AttackPlanner | 10, 10 | Foreground collision at 2.50 simulated seconds | Natural model detections; monitor logged in shadow |
| Hard / nominal / IDM | 14, 14 | Foreground collision at 3.50 simulated seconds | Natural model detections; monitor logged in shadow |
| Medium / nominal / ConstantPlanner | 31, 31 | Foreground collision at 7.75 simulated seconds | Natural model detections; monitor logged in shadow |

All runs used seed 144, a single explicit reset and the fixed 401-action maximum.
No initialized retry, replacement, missing slot or outcome-driven change occurred.
A source collision is a validly recorded failure outcome, not a successful driving result.
The six nominal collision runs and two censored diagnostic runs establish **no recovery gain**.
No GPU run reached simulator-defined completion or observed the literal route endpoint.
The diagnostic and qualification cases are excluded from a study recovery denominator.

Every pair passed independent scalar control/transition/outcome checks, CUDA render and
collision receipts, conditional monitor replay, source actor identity and strict replica
comparison. Numerical replica tolerance remained absolute `1e-9`; typed plans and image
hashes matched exactly. The largest projected stationarity residual was
`9.815603583263055e-07`, under the unchanged `1e-6` bar. This is evidence on
these inputs, not a guarantee of convergence on all future plans.

The injected hold produced 802 monitor firings and braking decisions. In the nominal
actor runs the monitor logged 16 firings and 36 braking decisions, but those decisions
were **not applied** in the nominal arm. Their existence does not establish that applying
braking would prevent a collision. GPU monitor release was not observed; the local
source-bound release fixture exercised it. The checker conditions on logged accepted
objects and does not independently establish detector completeness. The actor check
covers recorded geometry/transforms and Attack selection/cost/consumption; it does not
independently reconstruct the entire IDM policy or background point-cloud collision.

## Challenge the timing numbers

The overall controller median of 4.73 ms is dominated by 802 hold actions. It must not
stand in for the harder natural actor cases:

| Pair | Controller median (ms) | Maximum (ms) | Calls over 50 ms | Loop median (s) |
|---|---:|---:|---:|---:|
| Diagnostic hold | 4.70 | 36.12 | 0 / 802 | 1.742 |
| Attack | 40.43 | 62.65 | 3 / 20 | 1.984 |
| IDM | 39.33 | 46.51 | 0 / 28 | 1.881 |
| Constant | 38.23 | 50.57 | 1 / 62 | 1.891 |

**4/110 natural-actor controller calls exceeded 50 ms. All 912 loop measurements
exceeded 250 ms.** Overall loop minimum/median/maximum were 1.713/1.744/23.735 seconds.
The v2 timer includes the final per-step guard and stop decision; reset, summary
serialization and worker cleanup remain outside it. Exchange time includes model/IPC
work, not isolated model inference. The simulator waits synchronously for decisions.
These timings do not demonstrate operation at 4 Hz, and no late-result policy was tested.
This is the actual v2 GPU qualification, separate from the retained Iter146 v1 evidence.

## Storage, runtime and shutdown

The maximum retained GPU event was 329,123 bytes; the largest local
constructed actor event was 1,349,424 bytes. These observations are below the 4 MiB event
bound but do not establish a universal worst-case event size. Finite guards remain
necessary. There were 5,520 CUDA camera calls including reset renders.

Case outputs total 330,201,169 bytes including retained constructor
PLY. All owned control files total 716,310,275 bytes, including
parent logs, source/cache copies and archives. JSON/JSONL/log/config evidence was downloaded;
PLY remains on the stopped host with full hash inventories. The registered aggregate
allocation was 5 GiB, each child had a 1,200-second cap, and the whole envelope was
10,800 seconds / $9 conservative compute. No child deadline was exceeded.

The conservative elapsed interval through local closure was
2541.64 seconds; its $3/hour compute bound is
$2.118. The official-rate prorated estimate is
$0.603, not a billing receipt; existing disk baseline
and taxes are excluded. See [retained pricing](proof/price_binding.json) and Google's
[accelerator pricing](https://cloud.google.com/products/compute/pricing/accelerator-optimized).
No new VM, disk, bucket or package was installed.

Postflight verified 6,074 bound/original files and 20 actor aliases unchanged, no owned
cache-file changes, and no running container/GPU process. Exact instance
`3834622546652649531` is **TERMINATED**; local watchdog and supervisor exited 0.
No owned job or automatic restart remains. [Resource closure](proof/resource_closure.json).

## Evidence and validation

[Hypothesis](HYPOTHESIS.md), [prospective GPU binding](GPU_BINDING.md),
[qualification plan](QUALIFICATION_PLAN.json), [local replay](proof/cpu_analysis.json),
[GPU aggregate](proof/gpu_aggregate.json), [stratified metrics](proof/qualification_metrics.json),
[tested source binding](proof/tested_source_binding.json) and
[129-test receipt](proof/commands/pre_gpu_tests.stdout).
Forty warnings came from unchanged upstream tensor construction; no test failed in the final run.
Earlier lint failures and their corrections remain retained. Tests ran in the ambient local
CPU environment; actual GPU environment imports, client preflight and eight runs are separate
retained evidence. No hosted CI or canonical publication occurred.

Each raw packet was committed before independent aggregate replay and before admission of
the next pair. CPU raw commit: `a9b717b9c1d4e2d007a8f6d2f0dc70abae6da68d`.

| GPU raw packet | Commit before replay |
|---|---|
| pair_000 | `b5c5c7966f6b1f90a75f53b16e4df77262ca938a` |
| pair_001 | `9ab5da0d1001da62b2a848418b334554e4dc3769` |
| pair_002 | `06b88259fd5dfff758331274931c778014e52f7b` |
| pair_003 | `f6c724a2c9706a2511e92aed64f1f2b413b11cf9` |

## Decision

The remaining-path qualification is supported. Proceed with study-specific admission and
finite lifecycle/resource binding for the unchanged proposed 112 slots. The qualification
launcher currently rejects study execution; [STUDY_PLAN.json](STUDY_PLAN.json) is a frozen
population specification, not an admitted live study. Do not quietly remove that distinction.

The scientific question remains whether a constructive, progress-preserving intervention
exists beyond both nominal and responsive-monitor baselines. Only then test a specific
information channel. Preserve the 14 scenarios, three previously exposed scenes, four arms,
two replicas, seed, timing, stopping, missingness and comparator rules. There are zero untouched
holdout scenes. No population generality, physical safety, real-time or state-of-the-art claim
follows. Prior recovery nulls and the deferred Iter135 protocol remain unchanged.
