import json
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');D=R/'experiments/iter146_route_outcome_contract';P=D/'proof'
a=json.loads((P/'gpu_aggregate.json').read_text());s=a['summary'];c=json.loads((P/'resource_closure.json').read_text())
rows=[]
for arm,v in a['arms'].items():
 rows.append(f"| {arm} | 2 / 48 | {v['controller_ms']['median']:.3f} | {v['controller_ms']['maximum']:.3f} | {v['controller_ms']['over_50ms']}/48 | {v['loop_work_lower_bound_seconds']['median']:.6f} |")
(D/'RESULT.md').write_text('''# Iter146: bounded execution supported; recovery remains unmeasured

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
'''+ '\n'.join(rows) + f'''

All **192/192** controls met the declared numerical admission checks; maximum
stationarity residual was **{s['max_stationarity']:.12g}** under the unchanged
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

Controller median was **{s['controller_ms']['median']:.3f} ms**; maximum
**{s['controller_ms']['maximum']:.3f} ms**; **1/192 exceeded 50 ms**. This is a
separate sample from Iter145's retained 26/48 misses, with changed output policy
and population; no controlled speedup estimate is claimed.

All **192/192 loop-work lower bounds exceeded 250 ms**. Median was
**{s['loop_work_lower_bound_seconds']['median']:.6f} s**, minimum
**{s['loop_work_lower_bound_seconds']['minimum']:.6f} s**, maximum
**{s['loop_work_lower_bound_seconds']['maximum']:.6f} s**. Exchange median was
**{s['exchange_seconds']['median']:.6f} s**; simulator median
**{s['simulator_seconds']['median']:.6f} s**. Cold-start calls remain included.
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

Eight case outputs total **{s['output_bytes']:,} bytes**. Complete file hashes and
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

Provider start-to-stop metadata spans **{c['provider_start_to_stop_metadata_seconds']:.3f} s**;
the local budget-to-terminated-readback span is **{c['local_envelope_to_terminated_readback_seconds']:.3f} s**.
Each interval uses one clock; provider and local wall clocks differ. The refreshed
listed compute estimate is **${c['listed_compute_estimate_usd']:.3f}**, and the conservative
$3/hour estimate is **${c['conservative_compute_estimate_usd']:.3f}**, below the registered
5,400-second / $4.50 ceiling. These are estimates, not a billing invoice; persistent
disk baseline is excluded. See [resource closure](proof/resource_closure.json)
and [price evidence](proof/price_binding.json).

## Evidence lineage and remaining limits

Raw entered the local candidate branch before independent replay and later-arm admission:

| Arm | Raw commit |
| --- | --- |
'''+ '\n'.join(f'| {arm} | `{commit}` |' for arm,commit in a['raw_commits'].items()) + '''

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
''')
(D/'DECISION.md').write_text('''# Iter146 continuation handoff — 2026-10-10

## Current state

Bounded GPU qualification is closed: eight fresh-process cases, 192 steps, four
replica pairs, all supported under the registered contract. All cases were censored
at 24 actions; no recovery/completion outcome was established. Monitor fired zero
times and source actors were empty. Read RESULT.md and TIMING_CORRECTION.md first.

Candidate: research/iter146-route-outcome-contract, local/unpushed. Frozen GPU source:
9f78e514000f94ab069e846a7b6796009702a223. Current local runner summary v2 and corrected
three-valued comparator were added after GPU qualification; 96 focused tests pass.
They are not a new GPU regime result. Raw v1 remains immutable and passes the updated
checker. Every arm's raw commit is listed in RESULT.md and proof/gpu_aggregate.json.

VM sentinel-gpu is verified TERMINATED; watchdog3763 exited0. The closed control
is /datasets/nuscenes-full/hugsim/iter146_gpu_20261010. Local external receipts:
/Users/danielwahnich/sentinel-bootstrap-evidence/iter146-gpu-20261010/.
Do not reuse its budget, start identity, manifest, clearance files or initialized
case directories. No automatic restart or owned active job remains.

## Next authorized work

Daniel's mission instruction authorizes continuing without a human ceremony.
Preserve the proposed 14 scenarios, four arms, two replicas, seed144, single reset,
401-action horizon, lexical scenario/arm order, no initialized retry or replacement,
raw-before-analysis ordering, and all missing/invalid/censored outcomes.

1. Build the full-horizon GPU worker and finite study coordinator as a new named
   regime, reusing qualified source components. The current gpu.py/gpu_pair.py are
   intentionally a 24-action/eight-case qualification path, not a study launcher.
   Bind all 112 slots before outcomes and prevent skipping successful comparators.
2. Close concrete coverage gaps with a separately registered bounded qualification:
   corrected v2 guard-inclusive timing, 401-action execution/runtime, nonempty
   Attack/Constant/IDM actor paths, and monitor-active transport/actuation. Choose
   fixtures/cases before outcomes. Explicit injected monitor fixtures qualify only
   that injected integration path; do not label them spontaneous model detections.
   The fourteen-case source inventory contains no Unicycle actor requirement.
3. Measure actor candidate/event sizes and include parent logs, archives, source/cache
   copies and all owned output in resource accounting. The 56GiB allocation and
   24-action empty-actor costs alone do not bind worst-case full-study consumption.
   Freeze total host time/cost, per-case deadline, resource-stop behavior, complete
   inventory, exact source/assets, fresh provider identity and both shutdown guards.
4. Once automated qualifications and admission pass, execute the unchanged finite
   schedule, retaining raw before replay and later-arm admission. Any invalid replay
   stops later work; missing slots remain missing. Producer verification is operational
   evidence, never independent human review. Never make Daniel hash or attest files.
5. Use the corrected comparator only on independently verified matching replicas.
   Report nominal and monitor opportunities separately, their intersection, harm,
   progress, invalidity and censoring. Three exposed base scenes are the independent
   scene count; no population p-value/CI or physical-unavoidability inference.

The strategic question remains whether an effective action actually exists beyond
both responsive comparators. Only after a constructive recovery witness should we
freeze a signal selector, availability times and information ablations. Real-time
operation additionally needs a separately declared late-result policy and deadline
experiment; the current synchronous measured chain misses250ms on every step.

## Local recovery and preservation

Use canonical cwd and verify Git identity. Root is dirty wip-gen17-ci-hardening;
never checkout/reset/stash/stage unrelated work. Root README has uchg/deny-delete
protection. Edit candidate documentation through the alternate-index commit helper,
not by unprotecting root README. Master remains8c118b74c699bf0f139f9bd659192bad06b895f8.
Root HANDOFF/MISSION_STATE are historical publication snapshots; direct operator
instructions supersede their older human-review/NONE clauses. Read the active
CONTINUITY/NEXT_PHASE block and this handoff for the resumed mission.

proof/session_tools retains packaging, command capture, GPU lifecycle, collection,
analysis and alternate-index tools. Old scripts have hardcoded closed control paths;
read and adapt them under a new finite binding rather than executing them blindly.
Preserve all Iter145 bytes and all committed CPU/GPU raw. Final source/tests, evidence,
resource closure and state must agree before any new launch or claim.
''')
state=dict(iteration=146,status='supported',phase='bounded_qualification_closed_local_corrections_supported',source_commit='9f78e514000f94ab069e846a7b6796009702a223',source_commit_scope='frozen GPU v1 source; current local timer-v2/comparator correction not GPU-executed',cpu_raw_commit='4c36188c813c68aab2f16ebd5b281ea96de02300',cpu_steps=3362,cpu_replica_pairs=8,pre_gpu_tests=64,focused_tests=96,test_warnings=38,gpu_qualification_episodes=8,gpu_steps_replayed=192,gpu_replica_pairs_supported=4,gpu_camera_calls=1200,gpu_monitor_firings=0,gpu_configured_actor_count=0,gpu_qualification_censored_episodes=8,live_study_episodes=0,live_study_admitted=False,recovery_claim='unmeasured in Iter146',provider_state_last_observed='TERMINATED',owned_active_jobs=0,cloud_compute_used=True,owned_local_watchdog_session=None,watchdog_exited=True,automatic_restart=False,provider_cleanup_receipt='proof/resource_closure.json',gpu_manifest_sha256='829454a169fcf6a43eba7a36c77bc4976f05573bc178e907ccd8b981f40e331f',candidate_branch='research/iter146-route-outcome-contract',canonical_publication=False,candidate_pushed=False,next_work='New full-horizon worker/coordinator; finite actor/monitor/timer/runtime qualification and study admission without changing the 14-case schedule.',limitations=['All eight GPU cases censored at24 actions; no recovery evidence','Active monitor and nonempty actor GPU paths unobserved','Frozen full_loop_ns lower bounds exclude final guard/stop handling; v2 local only','No physical/transfer/population/real-time claim'])
(D/'STATE.json').write_text(json.dumps(state,indent=2)+'\n')
with (D/'TIMING_CORRECTION.md').open('a') as f:f.write('''
## Prospective correction completed locally

After the eight fixed GPU episodes closed, runner summary v2 adds start/work-end/end
elapsed-clock boundaries and measures through the post-step guard and stop decision.
It explicitly excludes timing-list append, Python loop dispatch and summary writing.
The independent checker validates ordering, differences, nesting and nonoverlap;
seven corrupted boundary fixtures are rejected. A 200-second synthetic guard delay
fails against v1 and passes against v2. All96focused tests pass; raw v1 replay remains
unchanged. No corrected v2 GPU measurement has been observed. See RESULT.md.
''')
print('Wrote result, decision, state and correction note')
