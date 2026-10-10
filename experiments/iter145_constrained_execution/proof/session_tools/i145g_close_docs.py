import json,subprocess,shutil,datetime
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');D=R/'experiments/iter145_constrained_execution';P=D/'proof'
a=json.loads((P/'commands/gpu_aggregate_analysis_v2.stdout').read_text());(P/'gpu_aggregate_analysis.json').write_text(json.dumps(a,indent=2)+'\n')
(P/'gpu_watchdog_exit.json').write_text(json.dumps(dict(status='exited',session_id=85149,message='watchdog cancelled after verified cleanup',shutdown_receipt='gpu_shutdown_verified.json'),indent=2)+'\n')
for name in ('i145g_ops.py','i145g_watchdog.py','i145g_progress.py','i145g_collect.py','i145g_postflight.py','i145g_analyze.py','i145g_close_docs.py'):
 src=Path('/tmp')/name
 if src.exists():shutil.copyfile(src,P/'session_tools'/name)
old=(D/'RESULT.md').read_text();old=old.replace('# Iter145 result at the operator stopping point','# Historical stopping-point result (superseded by the resumed result above)',1)
old=old.replace('All 14 frozen scenario YAML hashes matched. The 28 unavailable paths are actor model and\ndimension paths rejected by the no-follow reader at `postprocess/shadow.pth`.','All 14 frozen scenario YAML hashes matched. **Correction recorded on resumption:** the\n28 unavailable entries were 20 actor model/dimension paths for ten actor IDs plus eight\nlegitimate empty runtime files. The earlier statement that all 28 were actor paths was\nincorrect. The actor entries were rejected at `postprocess/shadow.pth`.')
new='''# Iter145: constrained execution and bounded GPU qualification

**2026-10-10 resumed result: supported within the four-case smoke contract.**
The original convergence checks, asset inventory and real simulator smoke now pass.
This is an engineering qualification: no complete-route recovery result or physical
validity claim follows. The proposed 14-scenario / 112-slot study has not started.
Cloud compute was used; the exact owned VM is now **TERMINATED**, its containers were
removed, and the local watchdog exited.

## Resumed measurements

| Check | Result | Evidence |
| --- | --- | --- |
| Asset closure | 5,983 observed file entries; all 14 scenario YAML hashes match | [inventory report](proof/resume_complete_asset_report.json) |
| Original inputs on installed host | 28/28 admitted; 7/28 calls exceeded 50 ms | [host comparison](proof/host_controller_timing_comparison.json) |
| Live GPU smoke | Four fresh nominal cases, 12/12 steps each; one reset each; all stopped at `smoke_step_cap` | [raw batch](proof/gpu_raw/batch.json) |
| Independent execution replay | 48/48 steps supported, including transport bytes, timestamps, controls, actor/render alignment and GEOS foreground overlap | [independent replay](proof/gpu_independent_analysis_v1.json) |
| GPU rendering / actors | 312 camera calls, 48 actor advances, two Attack selections; 48 foreground checks | [aggregate](proof/gpu_aggregate_analysis.json) |
| Maximum live stationarity residual | 9.058617606097497e-7, below unchanged 1e-6 bar | Same aggregate and raw control certificates |
| Complete controller timing | Median 51.305760 ms; maximum 71.016239 ms; **26/48 over 50 ms** | Same aggregate |
| Exchange plus step | Median 2.028208 s; all 48 exceed the .25 s simulation tick | Same aggregate |
| Source/asset preservation | 6,049 original or bound files and 20 actor aliases checked; no changes; owned map-cache copy also unchanged | [postflight](proof/gpu_postflight_integrity_report.json) |
| Focused local tests | 121 passed, 123 warnings | [test log](proof/commands/final_resumed_pytest.stdout) |
| Cleanup | Exact VM observed TERMINATED; watchdog exited | [provider readback](proof/gpu_shutdown_verified.json), [watchdog](proof/gpu_watchdog_exit.json) |

The four cases were `scene-0013-easy-00`, `scene-0038-extreme-00`,
`scene-0013-hard-00` and `scene-0038-medium-01`, in that order. Each ran only
three simulated seconds. The batch took 264.984306 seconds including its file
verification and orchestration. No episode retry or forced-brake outcome occurred.
The fixed seed was 136; the proposed study uses 144 and still needs its own qualification.
No live fresh-process replica comparison was performed in this smoke.

### Timing remains a separate result

Controller convergence passed even when the 50 ms descriptive deadline was missed.
The 28 original inputs had no misses locally and seven on the installed host; the live
48 calls had 26 misses. These are different workloads/environments, not a paired speedup
experiment. Host runtime was Python 3.11.10, NumPy 1.26.4, SciPy 1.17.1,
Torch 2.4.1+cu124 and GEOS/Shapely 2.1.2 as recorded in worker/runtime receipts.
The frozen model container uses its own Torch 1.9.1+cu111 runtime.

Planner exchange alone ranged from 1.502145 to 23.360355 seconds. The four first
exchanges include client readiness; no separate model-startup timer was retained.
After the first exchange in each case, exchange plus step ranged from 1.778705 to
2.653020 seconds (median 2.011067). These sums exclude observation hashing,
serialization and outer-loop overhead, so they are lower bounds on complete loop time.
The synchronous simulator advances by .25 seconds while wall time is longer. Real-time
operation and delay-compensated physical control are unestablished; offline simulated
recoverability can still be studied if this distinction remains explicit.

## Asset and execution corrections

The earlier stopping-point report misclassified 28 unavailable entries. They were
**20 actor files for ten actor IDs plus eight legitimate zero-byte runtime files**.
The [asset amendment](ASSET_CLOSURE_AMENDMENT.md) qualifies the exact historical
`postprocess/shadow.pth -> ..` alias against frozen file hashes, permits only the
registered empty runtime sources, and validates genuinely empty actor populations.
Missing or malformed actor lists remain failures. Full map-loader dependency inventory
added 5,544 files, including nuScenes metadata, vector maps and the complete loader cache.
The runtime writes only to its owned cache copy and outputs.

A Docker import preflight initially failed because a new mount target could not be
created under a read-only model mount. The prospective correction overlays the existing
container `e2e.py` path read-only. The failed and corrected receipts are retained; the
failure preceded any model process, reset or episode, and the budget was not reset.

Raw traces were committed at `7e5976bb9ee4c54dc5f114ca4392d9f16c202510` before
independent aggregate analysis. Base deployment source was
`fc7abe55d5c08338460129fa013b33b0b16dfe27`, with explicit output-guard and mount patches
from `05a550dcc9a09cb657f34c3d82dc9d8215372c19` and
`1202c067739ede3b301a4fc6d53bf4bdd6bd134f`. This is a file-bound patched deployment,
not a claim that the whole packet equals the final commit tree. The active
[execution manifest](proof/gpu_raw/execution_manifest.json) SHA-256 is
`698be5970fb76171b65ca41583eafd92cc260e43724a7709f84c2be38cd23c32`.

The raw driver summary's `gpu_observed: false` is its generic default. Actual GPU
observation is in each worker receipt, with device, model, synchronized render and GEOS
records. Raw bytes remain unchanged. Client exit 137 follows explicit owned-container
removal after the finite cap. Background collision code executed on CUDA points;
independent point-cloud collision/physical fidelity was not established. The map loader
reported a missing route for the Constant actor in the medium case; that actor does not
consume a route. The IDM case loaded its map and completed.

## Resource evidence and next decision

The resumed inspection and GPU qualification used separate prospective 1,800-second /
$1.50 and 5,400-second / $4.50 incremental compute envelopes at a conservative $3/hour.
Official [price evidence](proof/resume_price_binding.json) and both shutdown readbacks
are retained. These are caps, not billing receipts; persistent storage is excluded.
No disk, bucket or hardware was created. The GPU start/stop timestamps were
04:30:58.026 and 04:45:27.673 on the provider's -07:00 clock. Local/provider wall clocks
differed; duration guards used monotonic clocks.

The smoke produced 233,739,383 bytes. Retained JSON, JSONL, logs and configuration were
downloaded and hash-verified; derived PLY and visualization images remain on the stopped
host with complete [hash/size inventory](proof/gpu_raw/output_inventory.json).
Reproduce the analysis with `python3 -m experiments.iter145_constrained_execution.analyze_gpu`.

The [resource projection](proof/gpu_aggregate_analysis.json) is **proposed**, not admitted:
112 x 401 actions at twice the observed maxima gives about 67.88 hours / $203.63 of
compute when first steps are separated, or 591.67 hours / $1,775.00 if every step uses
the slowest observed first-step time. Neither is a measured upper bound. Separating fixed
PLY from linearly growing outputs still gives about 158.75 GiB under the factor-two
assumption, exceeding observed 108.87 GiB free storage even before a reserve. Short
traces in two scenes do not establish bounds for all scenes, arms or late behavior.
The study needs a bounded output policy, full-route runner and outcome replay, explicit
seed/replica qualification, and committed live resource/protocol bindings.

The candidate is local and unpushed; canonical master remains F17. Iter139 remains
null, 0/6 useful recoveries; Iter142 remains null, 0/2. Iter135 remains deferred.
See [DECISION.md](DECISION.md) and [STATE.json](STATE.json) for the current handoff.

---

'''
(D/'RESULT.md').write_text(new+old)
old=(D/'DECISION.md').read_text().replace('# Iter145 stopping point and resume handoff','# Historical pause handoff (tasks below superseded by the current handoff)',1)
new='''# Iter145 current decision and continuation handoff

## Completed after Daniel resumed, 2026-10-10

Asset closure and the four-case GPU smoke are supported in the scope stated in
[RESULT.md](RESULT.md). All 48 control/step records pass independent replay; 26/48
controller calls missed 50 ms. No full-route recovery or real-time result follows.
The cloud VM is verified **TERMINATED**, the watchdog exited, and no owned job remains
active. The study has zero episodes and is not admitted. This is a completed engineering
milestone, not a new operator-requested pause. No automatic restart is scheduled.

## Next concrete work

1. Read current root identity/instructions, active CONTINUITY, this handoff and STATE.
   Keep the dirty root on `wip-gen17-ci-hardening`. Use the candidate through Git or an
   isolated same-repository source packet; preserve unrelated WIP and the immutable README.
2. Implement the full-route 401-action runner and separately implemented outcome checker.
   Keep the Iter145 12-step smoke contract intact. Bind single reset, exact terminal reasons,
   final actor/ego state, collision source, route progress and all missingness explicitly.
   A useful recovery must finish the route collision-free; delay alone does not count.
3. Implement and qualify all four scheduled deliveries: nominal, released monitor,
   one-second brake at t=0 and at t=2.5, preserving signed braking and nominal steering.
   Retain full action/prefix checks and tests that reject mismatched comparisons. Source:
   [case-family protocol](../iter143_model_contract/CASE_FAMILY_PROTOCOL.md),
   [proposed schedule](../iter144_timed_trajectory/study.py),
   [braking correction](ARM_IMPLEMENTATION_CORRECTION.md).
4. Resolve output/storage policy before live execution. The retained projection including
   fixed PLY still exceeds observed free storage; it is not an admitted bound. Qualify any
   prospective visualization/output change without altering evidence needed for replay.
   Measure full-loop time explicitly, including serialization, and keep numerical admission,
   descriptive controller deadlines, simulator time and wall time as separate fields.
5. Bind seed 144, fresh-process replicas, all 14 fixed scenarios / 112 slots, exact source,
   runtime, assets, qualification and a finite total resource envelope. The current four-case
   seed-136 nominal smoke supplies bounded integration evidence, not full study admission.
   Requalify the actual study source and arms under its own finite prospective binding.
6. Then execute the fixed lexical scenario/arm/replica schedule, committing raw before
   analysis and before later arms. Preserve no initialized retry/replacement/seed search,
   stops on invalid replay, successful-comparator cases, missingness and witness criteria.
   Three historically exposed scenes provide development evidence; no untouched holdout
   or population-generalization claim exists. Finite action-library failure is not proof
   that physical recovery is impossible. No independent-human ceremony is required.

## Recovery anchors

- Candidate: `research/iter145-constrained-execution`, local/unpushed. Raw GPU commit:
  `7e5976bb9ee4c54dc5f114ca4392d9f16c202510`. Read current tip with `git rev-parse`.
- Deployed base/patched source identities and manifest are listed in RESULT. All measured
  failures and amendments are retained. Do not rewrite accepted or raw historical bytes.
- Host: `sentinel-gpu`, ID `3834622546652649531`, project `sunlit-unison-487018-b0`,
  zone `us-west1-a`; [latest terminal readback](proof/gpu_shutdown_verified.json).
- Host control/output: `/datasets/nuscenes-full/hugsim/iter145_gpu_20261010/`.
  Raw receipts and JSON/JSONL/log/config files are local in `proof/gpu_raw/`; derived PLY
  and visualization files are retained on host with hashes. All start budgets are closed.
- Resumed inspection cache/source evidence: `proof/resume_*`; GPU evidence: `proof/gpu_*`.
  Reproduce aggregate locally with `python3 -m experiments.iter145_constrained_execution.analyze_gpu`.
- External packet/receipts: `/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-gpu-20261010/`
  and `iter145-resume-20261010/`. Exact session tools are retained under `proof/session_tools/`.
- 121 focused local tests passed with 123 warnings. Prior isolated CPU test receipts remain;
  hosted/frozen Linux CI was not run for this unpushed candidate. No blanket CI-green claim.
- Portable memory: `/Users/danielwahnich/.codex/memories/sentinel-latest.md`.
  Root HANDOFF/MISSION_STATE remain their historical publication snapshot.

---

'''
(D/'DECISION.md').write_text(new+old)
s=json.loads((D/'STATE.json').read_text());s.update(status='supported',phase='bounded_gpu_qualification_complete',latest_source_commit='1202c067739ede3b301a4fc6d53bf4bdd6bd134f',focused_tests=121,provider_state_last_observed='TERMINATED',live_smoke_episodes=4,live_smoke_steps=48,gpu_qualification_status='supported',gpu_raw_commit='7e5976bb9ee4c54dc5f114ca4392d9f16c202510',gpu_controller_over_50ms=26,provider_shutdown_receipt='proof/gpu_shutdown_verified.json',owned_local_watchdog='exited_after_verified_cleanup',owned_active_jobs=0,gpu_envelope='closed',host_inspection_envelope='closed',next_step='Implement and qualify full-route four-arm study runner/outcome replay; bind output limits, seed 144 replicas and finite resources before the proposed 112 slots.',recovery_result=None,study_projection_status='proposed_not_admitted');(D/'STATE.json').write_text(json.dumps(s,indent=2)+'\n')
block='''> **Active operator-directed candidate work, 2026-10-10:** Iter145 resumed and completed
> bounded GPU qualification. Asset closure passed 5,983 file entries. All four nominal
> cases completed 12 steps; independent replay supports 48/48 controls/transitions,
> timestamps, planner transport, rendering and foreground geometry within that scope.
> 121 focused local tests passed. **26/48 live controller calls exceeded 50 ms**;
> exchange plus step exceeded .25 s in all 48 calls. Real-time operation is unestablished.
> Read the [result](PREFIXexperiments/iter145_constrained_execution/RESULT.md),
> [state](PREFIXexperiments/iter145_constrained_execution/STATE.json) and
> [current handoff](PREFIXexperiments/iter145_constrained_execution/DECISION.md).
> VM sentinel-gpu is verified TERMINATED and its watchdog exited; cloud compute was used.
> No full-route study ran. Next: full-route runner/outcome replay, four-arm/seed-144
> qualification and finite storage/runtime bindings for the proposed 112 slots.
> Candidate `research/iter145-constrained-execution` is local/unpushed; master remains F17.
> Prior recovery nulls and deferred Iter135 are unchanged; canonical MISSION_STATE/HANDOFF
> retain their publication snapshot. No owned job or automatic restart remains active.'''
shift='''\n\n## Iter145 resumed GPU qualification on 2026-10-10

Daniel resumed the mission. Exact actor aliases, legitimate empty source files, empty
actor populations and full map-loader inventory were qualified; 5,983 file entries pass.
Four fresh 12-step GPU nominal cases completed. Raw committed before independent replay
at 7e5976bb9ee4c54dc5f114ca4392d9f16c202510; all 48 steps pass the bounded contract.
Controller latency remains a separate negative result: 26/48 calls exceeded 50 ms, and
all exchange-plus-step times exceeded .25 s. No useful-recovery outcome was measured.
The smoke source and 6,049 bound/original files plus 20 actor aliases were unchanged at
postflight. 121 local focused tests passed with 123 warnings. Both resumed VM envelopes
are closed; latest exact VM readback is TERMINATED and watchdog exited. The proposed
112-slot study needs full-route/arm/seed qualification and finite resource/output bindings.
See the Iter145 result and current decision; no live study or canonical publication ran.
'''
def replace_active(text,prefix):
 start=text.index('> **Active operator-directed candidate work, 2026-10-10:**')
 end=text.index('\n\n',start)
 return text[:start]+block.replace('PREFIX',prefix)+text[end:]
for rel,tmp in [('CONTINUITY.md','i145_CONTINUITY.md'),('docs/NEXT_PHASE.md','i145_NEXT_PHASE.md'),('README.md','i145_README.md')]:
 prefix='../' if rel.startswith('docs/') else ''
 candidate=subprocess.check_output(['git','show','research/iter145-constrained-execution:'+rel],cwd=R).decode()
 candidate=replace_active(candidate,prefix)
 if rel=='CONTINUITY.md':candidate+=shift
 if rel=='README.md':candidate=candidate.replace('Iter145 now supports local constrained convergence and simulator CPU wiring; asset closure and full GPU integration remain open.','Iter145 now supports constrained convergence, asset closure and its four-case GPU smoke contract; full-route recovery and real-time operation remain unestablished.')
 (Path('/tmp')/tmp).write_text(candidate)
 if rel!='README.md':
  source=(R/rel).read_text();(Path('/tmp')/('i145_before_final_'+Path(rel).name)).write_text(source)
  updated=replace_active(source,prefix)
  if rel=='CONTINUITY.md':updated+=shift
  (R/rel).write_text(updated)
print('Documentation and state synchronized; candidate README kept out of root worktree.')
