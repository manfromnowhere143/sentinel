# Iteration 148: verified baseline completion; recovery study interrupted

2026-10-11. **Study: inconclusive. Execution block: failed. Evidence recovery and shutdown:
supported.** Four episodes passed independent replay, two strict replica pairs and source-defined
completion. A cloud observation failure stopped the block during the first braking-pulse episode.
Its partial trace is retained and invalid for paired admission. No recovery or harm rate is estimated.

## What ran

The frozen study contains 112 slots: 14 scenarios from three exposed scenes, four arms and two
replicas. Only its first scenario, scene-0013-easy-00, began execution. Seed 144, one reset,
401-action maximum and the registered signed pulses were unchanged.

| Arm in first scenario | Replica 1 | Replica 2 | Accepted evidence |
|---|---|---|---|
| Nominal | 92 actions; source-defined completion | 92 actions; same outcome | Supported pair |
| Responsive monitor | 92 actions; source-defined completion | 92 actions; same outcome | Supported pair |
| One-second pulse at 0 s | 88 recorded actions; no terminal summary | Not initialized | Invalid pair; partial raw retained |
| One-second pulse at 2.5 s | Not initialized | Not initialized | Missing |

The four verified episodes contain 368 actions, no recorded collision or off-route event and no
censoring. Strict replicas agree on states and controls within 1e-9 and on typed plans and image
hashes exactly. The largest independently checked stationarity residual is 9.759011668497575e-7,
below the unchanged 1e-6 bar. There are 2,232 CUDA camera calls including resets.

This is the first independently verified GPU completion in this execution sequence. It uses the
simulator's completion rule, near 90% of sampled route points; the literal final route sample was
not observed. The case has no configured dynamic actors. It is a bounded integration result,
not evidence of recovery from a failure. The monitor never fired or applied braking in any of the
four verified episodes; natural monitor release remains unobserved in these runs.

Overall: **4 admitted slots, 1 initialized incomplete slot and 107 uninitialized slots**. Three pair
parents initialized; only two completed and passed admission. There are zero complete four-arm
scenario comparisons. Every pulse comparison remains missing across all 14 planned scenarios.
The absence of a comparison is not a negative or favorable intervention result.

[Study accounting](proof/block_000_attempt_002/study_aggregate.json),
[scoped metrics](proof/block_000_attempt_002/metrics.json) and [state](STATE.json).

## Why execution stopped

The read-only progress query `auto_002_002` failed while establishing its IAP connection and
returned 255. The fixed supervisor immediately treated this observation failure as a stop condition,
then stopped the exact owned VM. The retained error does not establish a simulator fault or a
Google Cloud outage. Postflight reached the host and observed the worker still running before
shutdown. The transport failure and the supervisor's response must remain separate facts.

That response exposed a weakness in the experiment coordinator: it does not recover from a
lost observation even while the host has its own worker deadline and shutdown timer. The study
was not resumed or silently retried. The first pulse replica has no parent result, worker terminal
receipt or summary. Admission rejected it. Its 88 recorded actions are diagnostic evidence, not an
accepted episode or a completed intervention outcome.

[Progress error](proof/block_000_attempt_002/gpu_progress_auto_002_002.stderr),
[supervisor result](proof/block_000_attempt_002/supervisor_result.json),
[rejected admission](proof/admissions/pair_002.json).

A separate 900-second evidence-recovery envelope started the same stopped VM solely to collect
retained files and verify integrity. No driving worker or container restarted. A cloud API timeout
also affected its first read-only postflight query; one bounded retry succeeded. Both errors remain
retained. No package, model, scientific source, threshold, schedule or outcome rule changed.

## Challenge the timing result

| Verified arm | Controller median | Maximum | Calls over 50 ms | Loop median |
|---|---:|---:|---:|---:|
| Nominal pair | 39.45 ms | 73.98 ms | 2/184 | 1.798 s |
| Monitor pair | 39.94 ms | 56.07 ms | 4/184 | 1.787 s |

**6/368 verified controller calls exceeded 50 ms; all 368 verified loops exceeded 250 ms.**
Loop minimum/median/maximum were 1.712/1.792/24.608 seconds. The partial pulse separately recorded
88 controller calls, one over 50 ms; it has no terminal timing summary. Its missing loop measurements
are not zeros. The raw archive contains 456 recorded step events across accepted and incomplete runs.

The v2 loop timer includes the final guard and stop decision. Reset, summary serialization and
worker cleanup are outside it. Model/IPC exchange time is not isolated inference time. The
simulation waits synchronously; these results do not establish 4 Hz operation or a late-result policy.

## Admission, deployment and retained failures

Before this execution, 165 focused local tests passed with 40 unchanged upstream tensor warnings.
Prior qualification replay reproduced 1,104 GPU actions across eight pairs. Four constructed
corruptions demonstrated gaps in the older pre-intervention prefix check; the new check rejects
them. Existing delayed-pulse qualification passes all ten pre-onset steps including images and
timestamps. Those old 24-action runs remain censored qualification data, not new study outcomes.

The first attempt failed credential refresh before any VM start. After the operator reauthenticated,
attempt 2 used the exact frozen source `dd45ad39b26602ad81626ca55332e7ce6d308e91`.
Deployment initially imported qualification code through system Python, which lacked SciPy. Before
any study initialized, a retained prospective correction routed one completion of the verified
partial deployment through the existing simulator interpreter. No package was installed. Seven
constructed invalid deployment states were rejected, and the corrected runtime imports, entrypoint
and client preflight passed. The original failure was preserved.

[Tests](proof/commands/final_local_tests.stdout), [qualification](QUALIFICATION.json),
[source packet](proof/block_000_attempt_002/gpu_source_packet.json),
[deployment correction](proof/block_000_attempt_002/DEPLOYMENT_CORRECTION.md),
[deployment checks](proof/block_000_attempt_002/deployment_completion_known_bads.json).

| Raw packet, committed before replay | Commit |
|---|---|
| Nominal pair | `ad1066ea9e5fdbd795a7f2fa43c3f63a6cac1058` |
| Monitor pair | `c94c47c7bdbfad77250b7807cc5fa478b2c4de5f` |
| Interrupted pulse pair | `841ba8d4dcec4b5cded70783c7494345b4a835f5` |

## Resource closure

The original block limit remains 10,800 seconds / $9 at a conservative $3/hour. The primary envelope
closed at 1,528.58 local monotonic seconds; evidence recovery added 462.28 seconds. Their conservative
sum is 1,990.86 seconds: **$1.659 upper estimate**, with an official-rate prorated estimate of $0.472.
These are estimates, not invoices; existing persistent storage and taxes are excluded. No subtraction
across provider, host and local absolute clocks was used. The combined intervals remain within the
original block allowance. [Combined closure](proof/block_000_attempt_002/combined_resource_closure.json).

Postflight verified 6,101 bound/original files and 20 actor aliases unchanged, with no owned cache
changes or active container/GPU process. Owned control files total 599,293,135 bytes, including
source/cache copies and archives. Full constructor PLY hashes are retained; those PLY files remain
on the stopped host. JSON/JSONL/log/config evidence was collected without display images.
[Final integrity](proof/block_000_forensic/gpu_postflight_integrity_report.json).

Both exact owned starts of VM `3834622546652649531` are **TERMINATED**. The last start was
`2026-10-10T22:31:47.574-07:00`, stopped at `2026-10-10T22:38:08.936-07:00`.
Primary supervisor 40891 exited 1 on the recorded transport stop; watchdog 92679 exited 0. The
forensic shutdown command 12123 and watchdog 32921 both exited 0. No owned job or automatic restart
remains. [Evidence-recovery closure](proof/block_000_forensic/resource_closure.json).

## Decision

The operator requested a full README, diagram and current-memory review after this task and before
any next experiment. Complete that editorial work next, using the verified results and failures above.
Then design and qualify durable observation recovery before another study launch: distinguish an
unavailable observation from a failed worker, retain host deadlines and immutable initialization
records, and permit bounded read-only retries without duplicate execution. This is future work;
the interrupted study remains stopped under its original rule. Do not overwrite or rerun its slots.

The scientific question remains constructive recovery beyond both nominal and a responsive monitor,
followed by a specific information hypothesis. No new recovery witness, population generality,
physical safety, real-time behavior or state-of-the-art claim is established here. Prior recovery
nulls and deferred Iter135 remain intact. [Continuation](DECISION.md).
