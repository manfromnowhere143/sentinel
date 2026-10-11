# Iter148: study admission implemented; cloud launch blocked before start

2026-10-11. Local engineering checks are **supported**. Live study execution is **blocked**
by Google Cloud reauthentication. The failed operation was a read-only instance description;
**no VM start command, host command or new GPU episode was issued**. No new recovery result
is established. All 112 study slots remain without supported execution evidence.

## What changed

The study keeps the original 14 scenarios, three exposed scenes, four arms, two replicas,
seed 144, 401-action maximum and unchanged outcomes and intervention rules. New study-only
admission code requires the bound qualification receipt, exact population, an unbroken chain
of committed earlier receipts, and exclusive started markers. The parent must report two
completed workers without deadline or cleanup failures. Raw evidence is committed before
independent replay and before the next pair can start. Complete scenario comparison is required
before leaving a scenario. No initialized retry, skipped arm or outcome-driven replacement.

The existing pre-intervention equality check omitted timestamps, nominal controls, progress
and RGB hashes. Four constructed corruptions reproduced those gaps in the prior comparator;
the new check rejects them. Replaying the previously committed Iter146 GPU traces passes the
stronger check, including all ten pre-onset steps for the 2.5-second pulse. This is replay of
existing qualification data. Both pulse comparisons remain unknown because the runs were
censored at 24 actions; neither is a new recovery witness.

The accounting explicitly distinguishes true, false, observed unknown and missing results.
With no Iter148 execution, each pulse has 14 missing scenario comparisons, zero measured
comparisons and no estimated recovery rate. Supported engineering checks never substitute
for successful driving outcomes.

## Evidence and validation

| Check | Retained result |
|---|---|
| Prior Iter147 GPU qualification replay | 912 actions / four strict replica pairs |
| Prior Iter146 four-arm GPU qualification replay | 192 actions / four strict replica pairs |
| Focused local tests | 165 passed; 40 unchanged upstream tensor warnings |
| Local lint | Passed for seven implementation modules and the test file |
| Exact frozen packet | Imports, full 112-slot plan and qualification binding passed locally |
| Strengthened prefix check on prior GPU evidence | Passed; delayed-pulse prefix contains ten steps |
| New study executions | 0 / 112 |
| Fresh provider/runtime validation | Unobserved after credential refresh failed |

Source frozen at `dd45ad39b26602ad81626ca55332e7ce6d308e91`; the source packet contains 113
repository files plus two asset inventory files. The input manifest binds 101 previous source
and evidence files to the Iter147 parent. Local tests use the ambient CPU environment, and the
packet import check used Python 3.14. New study admission has not yet executed in the hosted
GPU environment. No hosted CI or canonical publication ran. Candidate
`research/iter148-recovery-study` is local and unpushed.

[Qualification receipt](QUALIFICATION.json), [test output](proof/commands/final_local_tests.stdout),
[frozen-packet check](proof/commands/frozen_packet_check.stdout),
[prior GPU prefix replay](proof/prior_gpu_prefix_replay.json),
[source packet](proof/block_000/gpu_source_packet.json) and
[empty study accounting](proof/study_accounting.json).

## Finite execution and unused envelope

Before new outcomes, the preregistration divided the same 112 slots into 14 fixed scenario
blocks. Each block permits 10,800 seconds and $9 at a conservative $3/hour compute rate:
151,200 seconds / $126 maximum across all blocks. This prospectively replaces the proposed
single-start overhead allowance; it does not alter the scientific schedule. Only the first
block's eight slots are eligible for initial launch validation.

Each worker retains a 1,200-second deadline; a pair requires more than 2,600 seconds remaining.
The full control directory is bounded at 57 GiB, with 448 MiB per-case stop, a 25 GiB host reserve,
256 MiB file/trace and 4 MiB event bounds. First start requires 100 GiB host free; local collection
requires 17 GiB free and is bounded to 512 MiB expanded / 256 MiB compressed per pair. Both a local
watchdog and a fresh host shutdown timer are required. These are limits, not measured worst cases.

The first attempted envelope stopped at the before-start provider query with:
`Reauthentication failed. cannot prompt during non-interactive execution.`
The local unused watchdog was deliberately terminated and exited 143. No supervisor, host timer,
container or study process was created. No new compute was started; this does not assert that
existing persistent storage has no charges. Current provider state is **unobserved** because
the query failed. The last successful observation, from Iter147 closure, was TERMINATED.
No automatic restart is scheduled. [Failure receipt](proof/block_000/gpu_before_start.json),
[provider error](proof/block_000/gpu_before_start.stderr),
[unused-envelope closure](proof/block_000/resource_closure.json).

## Decision and limits

After account reauthentication, create a fresh first-block envelope and run the retained
provider, resource, runtime, timer and admission checks before slots 0–7. The failed attempt's
paths and budget are closed. It initialized no study slot and permits no inference about one.
Read [DECISION.md](DECISION.md) for exact continuation instructions.

The research target remains constructive, progress-preserving recovery beyond both nominal
and responsive-monitor baselines. Establish that witness before choosing a new information
channel. Source-defined completion is near 90% of route samples, not the literal route endpoint.
The three scenes are previously exposed, with zero untouched holdout scenes. GPU monitor release
and route completion remain unobserved. Prior latency failures and recovery nulls are preserved;
this work does not establish real-time operation, safety, generalization, state of the art or
commercial value. Deferred Iter135 remains unchanged.

Master, prior evidence, the root Git index, unrelated WIP, historical HANDOFF/MISSION_STATE and
protected root README are preserved. An intermediate local candidate commit included historical
working-tree CONTINUITY additions; a forward correction restored the parent candidate prose and
kept only the active Iter148 update. The root worktree history was preserved, and no source or
outcome changed. [Correction record](proof/candidate_doc_correction.json).
