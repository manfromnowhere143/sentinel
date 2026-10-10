# Iter146: bounded execution supported; recovery remains unmeasured

2026-10-10. Status: **supported within the registered engineering scope**. Eight
fresh-process GPU episodes, 192 steps and four replica pairs passed independent
replay. All episodes stopped at the 24-action cap (six simulated seconds). These
are censored short episodes, not eight successful drives or a recovery experiment.
The proposed 14-scenario / 112-slot study has not run and is not admitted.

## What changed

- Added a finite single-reset runner over the retained Iter145 constrained controller
  and timed simulator adapter, with streamed events, explicit stop reasons, bounded
  parsing/output and a separate scalar execution/outcome checker.
- Defined completion exactly: retained HUGSIM terminates at rc >= 1, where
  rc=(nearest route index+1)/(0.9*N). This is approximately 90% of recorded samples,
  not literal route-end traversal. Literal final-sample observation is separate.
- Kept collision and off-route failure visible when source reward is overwritten
  by +1000 on simultaneous completion. Reward cannot establish success.
- Removed only display-image process creation from the actual client, with an exact
  AST delta check. Planner, monitor and constructor PLY output remain.

The outcome clarification preceded these outcomes in [HYPOTHESIS.md](HYPOTHESIS.md).
The separate [GPU binding](GPU_QUALIFICATION_BINDING.md) fixed the eight cases,
source, seed 144, arm order, stopping, replica tolerance and resource envelope.

## GPU execution evidence

Exact deployed source: `9f78e514000f94ab069e846a7b6796009702a223`; one 75-file
Git source packet. Fixed `scene-0013-easy-00.yaml`, one reset per fresh process.

| Arm | Episodes / steps | Controller median ms | Controller max ms | >50 ms | Loop-work lower-bound median s |
| --- | --- | --- | --- | --- | --- |
| nominal | 2 / 48 | 38.579 | 70.379 | 1/48 | 1.583813 |
| monitor | 2 / 48 | 38.152 | 49.133 | 0/48 | 1.586298 |
| brake_t0 | 2 / 48 | 39.287 | 49.440 | 0/48 | 1.591452 |
| brake_t2_5 | 2 / 48 | 39.271 | 48.706 | 0/48 | 1.585190 |

All **192/192** controls met the declared numerical admission checks; maximum
stationarity residual was **9.0990645607e-07** under the unchanged
1e-6 bar. This is a bounded numerical/KKT result, not a global-optimum proof.
All four replica pairs matched typed plan bytes and input image hashes exactly;
state/action/actor values agreed at absolute tolerance 1e-9.

The late pulse matched the nominal trajectory for ten pre-intervention steps in
both replicas. Pulse observation times were 0/.25/.5/.75 s and 2.5/2.75/3/3.25 s;
application endpoints were .25/.5/.75/1 s and 2.75/3/3.25/3.5 s. All four pulse
steps per replica differed from the computed nominal acceleration. Early braking
reached zero forward speed; its last two pulse accelerations were zero, as specified.

There were **1,200 CUDA camera calls**. All eight runs recorded no collision or
off-route event during observation, no simulator completion, and `censored=true`.
All ended with `action_cap`; all controller stop reasons were `kkt_converged`.
The monitor fired **0/192** times. There were **zero configured source actors**.
Thus active monitor intervention and nonempty actor execution remain unobserved
in this GPU population. CPU substitutions cannot fill those GPU coverage gaps.
Background point-cloud collision outcomes were retained from the source and bound
to device receipts; they were not independently reconstructed from the point cloud.

The GPU runs used the actual installed renderer, model, monitor and collision code
with the named controller/actor adapter and display-output change. The generic
pair-report phrase “source execution with declared substitutions” comes from the
shared checker; it does not mean these GPU runs used the CPU fixture substitutions.
See [aggregate](proof/gpu_aggregate.json) and each arm's raw packet and pair analysis.

## Timing: a negative result and a corrected label

Controller median was **38.637 ms**; maximum
**70.379 ms**; **1/192 exceeded 50 ms**. This is a
separate sample from Iter145's retained 26/48 misses, with changed output policy
and population; no controlled speedup estimate is claimed.

All **192/192 loop-work lower bounds exceeded 250 ms**. Median was
**1.585938 s**, minimum
**1.520346 s**, maximum
**22.039466 s**. Exchange median was
**1.308980 s**; simulator median
**0.212040 s**. Cold-start calls remain included.
The measured chain does not meet a 4 Hz wall-clock deadline in these runs.

Review found that frozen `full_loop_ns` ends before the final resource guard and
stop decision. Raw bytes and original analysis field names are preserved. The
[correction](TIMING_CORRECTION.md) explicitly interprets them as lower bounds;
this does not weaken the observed deadline failure. Episode `elapsed_ns` is an
enclosing scope, not an individual loop latency or complete worker lifetime.

After closing the frozen qualification, summary schema v2 now records explicit
elapsed-clock boundaries through the final guard/stop decision, while retaining
the loop-work interval. Its exclusion of timing-list append, loop dispatch and
summary writing is explicit. A synthetic 200-second guard delay reproduced the
old undercount and passes the corrected test. **The v2 timer has local evidence
only; no v2 GPU timing is claimed.**

## Local qualification and missingness correction

Original CPU raw: **18 constructed fixtures / 3,362 steps / eight replica pairs**,
including all four arms through 401-action censoring, completion/collision
coincidence and off-route failure. Maximum stationarity was
6.478487035721514e-7. CPU replicas use fresh environments within one process,
not fresh processes. Substitutions: constructed assets, identity CUDA transfer,
2x2 deterministic images, synthetic planner/monitor, no actors, SAT foreground
and controlled background. These are engineering fixtures, not driving evidence.
Raw commit `4c36188c813c68aab2f16ebd5b281ea96de02300` preceded aggregate analysis.

**64 pre-GPU tests passed**. Subsequent review found three missingness bugs in the
unused proposed comparison logic: unknown intersection becoming False, censored
nominal becoming no harm, and censored intervention becoming failed recovery.
Three-valued conjunction now preserves unknowns and distinguishes observed failure
from incomplete execution; absent contrast is unknown when the pulse end was not
observed. Completion, action law, prefix and hazard-progress margin are unchanged.
No study claim had used that comparator. Positive witnesses, separate comparators,
intersection, harm, missing hazard, earlier completion and no-effect cases now have
constructed truth-table tests; they are not simulator recovery results.

The retained pre-fix run has **4 failing / 2 passing** targeted tests, demonstrating
the timing error plus three missingness bugs. Corrected source has **96 passing
focused tests, 38 warnings**, and passes Ruff. Seven corrupt v2 timing variants
are rejected. The corrected checker also replays all 3,362 old CPU steps and all
192 old GPU steps with unchanged outcomes. Local Python/package provenance and
source hashes are in [test binding](proof/corrected_source_test_binding.json).
These were ambient local tests; hosted CI and v2 frozen GPU execution were not run.

## Resources and closure

Eight case outputs total **315,348,267 bytes**. Complete file hashes and
sizes are retained; JSON/JSONL/log/config evidence is local, while derived PLY
files remain on the stopped host. Postflight rechecked **6,062 original/bound
files and 20 actor aliases**: unchanged. Owned map-cache files were also unchanged.
The host had 115,948,425,216 free bytes after execution. No GPU process or container
remained at postflight. No new VM, disk, bucket or package installation was needed.

The 512 MiB per-case allocation, 448 MiB polling stop, 256 MiB per-file cap and
25 GiB host reserve held in this population. These do not establish an instantaneous
aggregate quota. Parent entry logs sit outside the per-case directory; a future
study must include every owned output in its allocation. The proposed 56 GiB
112-slot allocation is arithmetic, not observed full-study consumption; nonempty
actor candidate logging and full-horizon runtime still need measurement.

One read-only collection attempt ran before the early-pulse pair marker existed
and failed. Its receipt is retained. Collection subsequently succeeded after the
same pair completed; no episode was restarted, retried or replaced.

VM `sentinel-gpu`, ID `3834622546652649531`, project
`sunlit-unison-487018-b0`, zone `us-west1-a`: **TERMINATED**, exact owned start
`2026-10-10T05:28:35.902-07:00`, stop metadata
`2026-10-10T05:53:16.661-07:00`. Local watchdog exited 0 after verified cleanup.
No owned job or automatic restart remains. Cloud compute was used.

Provider start-to-stop metadata spans **1480.759 s**;
the local budget-to-terminated-readback span is **1503.277 s**.
Each interval uses one clock; provider and local wall clocks differ. The refreshed
listed compute estimate is **$0.351**, and the conservative
$3/hour estimate is **$1.253**, below the registered
5,400-second / $4.50 ceiling. These are estimates, not a billing invoice; persistent
disk baseline is excluded. See [resource closure](proof/resource_closure.json)
and [price evidence](proof/price_binding.json).

## Evidence lineage and remaining limits

Raw entered the local candidate branch before independent replay and later-arm admission:

| Arm | Raw commit |
| --- | --- |
| nominal | `38dbc586c25af02cdd5ec26fa9d21ef9ec0e4081` |
| monitor | `5f17011e9f842fdcdccb3261586c3100c4816e13` |
| brake_t0 | `a6503f97b34757c1f025e284ef06b3cdce8145ee` |
| brake_t2_5 | `277f13455d6feac0f54b55a57ce6e8064b6f6cc5` |

Candidate `research/iter146-route-outcome-contract` is local and unpushed. Canonical
master, immutable root README, root index, historical HANDOFF/MISSION_STATE and
unrelated WIP are preserved. No canonical publication occurred. Prior Iter139
0/6 and Iter142 0/2 recovery nulls remain unchanged; Iter135 stays deferred.

The next step is full-horizon and actor/active-monitor qualification with the corrected
measurement source, then an executable finite 112-slot schedule and prospective
runtime/resource binding. Keep all three historically exposed scene families and
all fourteen scenarios, including successful comparators and harmful interventions.
There are no untouched holdouts here. No state-of-the-art, physical safety, transfer,
real-time, population or useful-recovery claim follows from this qualification.
