# Iter151 result: nominal pair admitted; comparison inconclusive

11 October 2026. **The canary is closed and inconclusive.** Both nominal replicas on
`scene-0013-medium-00.yaml` passed independent execution and replica checks and recorded a
collision at **7.75 simulated seconds**, after 31 actions each. The registered comparison
did not complete: **2 admitted, 0 incomplete, 14 uninitialized; 62 verified actions**.
No monitor-arm or braking-pulse outcome, recovery rate or harm rate is available.

The scientific baseline failure is a valid observed outcome. It repeats the selected prior
collision opportunity in this exposed development case; it does not show that any intervention
can prevent it, and it adds no independent source scene. Do not pool it with Iter148, which
remains closed at 4 admitted / 1 incomplete / 107 uninitialized.

## Why execution stopped

The first pair completed, its durable evidence reconciled through IAP, and its raw archive
downloaded. The local commit helper then ran a repository whitespace check on captured evidence.
That check rejected trailing whitespace in the **unchanged captured client source** `e2e147.py`.
The supervisor halted the schedule, retained the files, verified postflight integrity, stopped
the exact owned VM start and exited. The live execution result remains **failed**.

The error concerns the scope of a publication check. It is not a worker failure, a simulator
failure, a failed replica check or a favorable scientific outcome. Captured source must retain
its exact bytes, including existing formatting. The raw packet and failure were committed at
`95db0f680f6319fb33454ee0b5531bfd30d3b8da` before scientific replay. Both replicas then passed
the unchanged scientific checks. No initialized episode was retried and no result was erased.

[Original execution failure](proof/block_000/result.json) ·
[raw-before-replay admission](proof/admissions/pair_000.json) ·
[finite accounting](proof/aggregate.json) · [metrics](proof/metrics.json) ·
[272 raw files verified unchanged](proof/preservation.json).

The corrected helper admits only evidence paths under this iteration's proof directory,
rejects symlink trees and unrelated staged work, and preserves captured bytes. Authored code
still receives source/style checks. A real temporary Git repository now exercises the entire
archive → exact-byte commit → scientific replay → committed receipt path on these same two
retained episodes. It reproduced the whitespace rejection from the old check, preserved the
client bytes, and recovered the identical raw inventory and 62 verified actions. This local
rehearsal adds **zero new scientific outcomes**. The corrected coordinator has not run in the cloud.

[Correction and validation](proof/postrun_correction.json) ·
[retention rehearsal](proof/retention_rehearsal.json) · [rehearsal source](rehearse_retention.py).
The first rehearsal encountered macOS's `/var` versus `/private/var` alias; its caller now uses
a resolved root. The failed invocation is retained and the historical checker was not weakened.

## Engineering evidence

The [protocol](HYPOTHESIS.md) was committed at `bb416e9` before implementation or new data.
The exact 16-slot plan preserved the proposed scenarios, arm order, replicas, seed, horizons,
outcomes, stopping and missingness rules. Live source was frozen at
`35fcf9a7904feab0e7022f7db3e8fc9b70403d2c`; the [packet receipt](proof/block_000/source_packet.json)
binds all 142 deployed files. Historical controller, monitor, worker and replay sources remain
unchanged. The post-run bookkeeping correction is distinct from that live source.

| Check | Observation |
|---|---|
| Pre-live focused Iter146–151 regression | 308 passed; 40 retained upstream warnings |
| Final pre-live integration checks | 56 passed, including the extracted-byte collection bound |
| Actual Linux ownership qualification | PID birth, exact command, executable, directory and boot checked; five substitutions rejected |
| Duplicate host fixture initialization | Rejected; existing records unchanged |
| Independent short systemd deadline | `Result=timeout`, `MainPID=0`, at about 2.016 s |
| Scientific pair service | Exclusive service; 2,500 s configured RuntimeMaxSec and control-group kill policy |
| Active scientific observation | Seven running observations, then reconciled completion; no live scientific observation loss occurred |
| Separate host receipt audit | Eight corrupted records rejected |
| Independent scientific replay | 2 replicas / 62 actions admitted; replica agreement passed |
| Post-run focused checks | 57 passed, including actual Git preservation of whitespace-bearing evidence |
| Captured evidence preservation | All 272 committed raw files still match the raw commit |

[Pre-live regression](proof/final_local_tests.stdout) ·
[pre-live collection correction](proof/prelive_review.json) ·
[Linux qualification](proof/block_000/host_qualification.json) ·
[independent host audit](proof/host_independent_audit_final.json) ·
[audit source](proof/audit_host.py.txt) ·
[scientific observation trace](proof/block_000/pair_000_trace.json) ·
[final focused output](proof/postrun_retention_tests.stdout).

Local tests used ambient macOS Python 3.14.2; the cloud used the existing simulator environment.
The short deadline actually expired; the scientific 2,500-second deadline and VM shutdown timer
did not need to expire. Their configured presence is not evidence of a full-duration expiry.
Temporary boot reachability failures were retried read-only. The live scientific observations
were successful, so resilience to observation loss still relies on the prior constructed faults.

## Scientific detail and limits

The source-defined collision was observed in both replicas, without off-route, completion or
censoring. Actor type was ConstantPlanner. Maximum checked controller stationarity residual:
`9.815603583263055e-7`, below the fixed `1e-6` bar. The nominal-arm monitor log contains two
firings and six braking-flag frames per replica; these logged flags do **not** measure the
effect of executing the monitor arm. That arm remains unrun.

Controller calls had median 37.726 ms and maximum 75.550 ms; **1/62 exceeded 50 ms**.
Full loops had median 1.882 s and maximum 34.728 s; **62/62 exceeded 250 ms**. The simulator
waits synchronously. No 4 Hz wall-clock execution, late-result policy, physical safety,
population generality, causal information benefit or industrial superiority is established.
Historical `live_study_admitted:false` fields inside reused component reports retain those
components' original scope; this study's explicit permit, parent and pair admission establish
the new operational admission. They are not independent human or institutional acceptance.

## Closure and continuation

VM `sentinel-gpu`, ID `3834622546652649531`, g2-standard-8/one L4, in
`sunlit-unison-487018-b0/us-west1-a`:

- Owned start: `2026-10-11T00:32:53.429-07:00`.
- Verified stop: `2026-10-11T00:41:31.285-07:00`, state `TERMINATED`.
- Full envelope: 532.104 s, within 10,800 s; local watchdog exited 0.
- Conservative compute estimate: **$0.443**, within $9, using the $3/hour planning rate.
- Postflight: 11,645 file bindings and 20 actor aliases checked; no bound original or owned
  cache change, no active container or GPU process; 114,122,719,232 remote bytes free.

[Closure](proof/block_000/closure.json) · [postflight](proof/block_000/postflight.json) ·
[dated price binding](proof/price_binding.json). This is an incremental compute estimate,
not an invoice; persistent storage and taxes are excluded. The second envelope did not start.
There is no remaining owned job, no silent schedule resume and no new infrastructure.

The [next decision](DECISION.md) is a separately registered continuation of the unrun comparisons,
with the admitted nominal pair explicitly treated as retained prior evidence. Preserve this
closed 16-slot accounting. Before more GPU work, qualify the full retention/admission pipeline
on representative captured artifacts, including their original source formatting. Whole-repository
CI remains unresolved; current local lint scope is recorded separately, and no green hosted
result or master integration is claimed.
