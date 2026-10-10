from pathlib import Path
import json,subprocess,re,shutil
R=Path.cwd();D=R/'experiments/iter147_full_horizon_execution';P=D/'proof';branch='research/iter147-full-horizon-execution'
a=json.loads((P/'gpu_aggregate.json').read_text());m=json.loads((P/'qualification_metrics.json').read_text());c=json.loads((P/'resource_closure.json').read_text())
rawrows='\n'.join(f'| {name} | `{commit}` |' for name,commit in a['raw_commits'].items())
result=f'''# Iter147 result: full-horizon and actor-path qualification

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
`{m['maximum_stationarity']:.16g}`, under the unchanged `1e-6` bar. This is evidence on
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

The maximum retained GPU event was {m['largest_event_bytes']:,} bytes; the largest local
constructed actor event was 1,349,424 bytes. These observations are below the 4 MiB event
bound but do not establish a universal worst-case event size. Finite guards remain
necessary. There were {m['camera_calls']:,} CUDA camera calls including reset renders.

Case outputs total {m['resource_output_case_bytes']:,} bytes including retained constructor
PLY. All owned control files total {c['postflight']['owned_output_bytes']:,} bytes, including
parent logs, source/cache copies and archives. JSON/JSONL/log/config evidence was downloaded;
PLY remains on the stopped host with full hash inventories. The registered aggregate
allocation was 5 GiB, each child had a 1,200-second cap, and the whole envelope was
10,800 seconds / $9 conservative compute. No child deadline was exceeded.

The conservative elapsed interval through local closure was
{c['elapsed_to_local_closure_monotonic_seconds']:.2f} seconds; its $3/hour compute bound is
${c['conservative_compute_upper_usd']:.3f}. The official-rate prorated estimate is
${c['official_rate_prorated_estimate_usd']:.3f}, not a billing receipt; existing disk baseline
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
{rawrows}

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
'''
(D/'RESULT.md').write_text(result)
(D/'DECISION.md').write_text('''# Iter147 continuation handoff — 2026-10-10

## Current state

Read RESULT.md and STATE.json. All eight fixed GPU qualification slots passed: 912 actions,
four strict replica pairs, 802 injected monitor activations and nonempty Attack/IDM/Constant
execution. Six natural nominal episodes collided; two diagnostic hold episodes were censored
at 401 actions. No recovery gain or GPU route completion was established. Four of 110 natural
actor controller calls missed 50 ms; every loop measurement missed 250 ms. CPU evidence remains
separate: 890 constructed actions, three replica pairs, 129 focused tests.

Frozen GPU source: 7fdb3c5fa9b698e08fedf0f2184dab25a7c495eb. All raw commits and replay
receipts are in RESULT.md/proof. No source or threshold was changed after GPU outcomes.
Candidate research/iter147-full-horizon-execution is local/unpushed; no hosted CI ran.

Exact VM sentinel-gpu / ID3834622546652649531 is TERMINATED. Watchdog 54396 and supervisor
64333 exited 0. Closed control: /datasets/nuscenes-full/hugsim/iter147_gpu_20261010.
External evidence: /Users/danielwahnich/sentinel-bootstrap-evidence/iter147-gpu-20261010.
Do not reuse its start identity, budget, timer, clearances or initialized directories.
There is no automatic restart. Scripts in proof/session_tools have closed paths and must not
be executed blindly. All 6,074 bound/original files and 20 actor aliases passed postflight.

## Next authorized work

Daniel's direct mission instruction authorizes continuation without a human ceremony.
The remaining local implementation is a study-specific admission adapter and durable finite
execution lifecycle. Iter147's pair.py deliberately admits qualification only. Its study plan
fixes all 112 slots but is not a complete study launch contract. Do not advertise a proposed
plan as an already admitted executor.

1. Bind the eight-case qualification receipt, exact runtime/source/assets, corrected v2 timer,
   prior four-arm pulse qualification and corrected three-valued comparator to a new prospective
   study manifest. Qualify admission/refusal with retained known-bads. Preserve exact bytes and
   population; no human-created assertion or independent-human ceremony is required.
2. Bind per-case and total time/output/compute limits, original asset inventory, fresh exact
   provider identity, both shutdown guards, collection limits and cleanup. Iter147's measured
   durations/event sizes are observations, not worst-case guarantees. Hard bounds must still
   stop overruns and retain missing later slots. Long horizons with active nonempty actors,
   GPU monitor release and live route completion remain outside observed Iter147 coverage.
3. Implement sequential pair/arm admission from committed raw and independently verified
   results. Retain the full-prefix checks where applicable. No initialized retry, threshold
   relaxation, replacement case, skipped comparator or success-based stopping. Unknown,
   invalid and censored outcomes cannot become favorable labels.
4. Execute the unchanged 14-scenario / four-arm / two-replica plan only after this technical
   binding passes. Measure nominal opportunities, monitor opportunities, their intersection,
   intervention harm and progress separately. Diagnostic hold data is never a study arm.
5. Use an actual constructive recovery witness to select the next information hypothesis.
   Three exposed base scenes are not 14 independent scenes, and none are untouched holdouts.
   The synchronous chain is not a real-time system. Any latency-policy experiment needs its
   own declared late-result behavior, actuation times and outcomes.

## Preservation

Use canonical Sentinel cwd and verify Git identity. Root remains dirty wip-gen17-ci-hardening.
Never checkout, reset, stash or stage unrelated work. Preserve all Iter146 and earlier evidence.
Root README has uchg/deny-delete protection; candidate documentation uses the alternate-index
helper. Master remains 8c118b74c699bf0f139f9bd659192bad06b895f8. Historical HANDOFF/MISSION_STATE
remain untouched; the active CONTINUITY/NEXT_PHASE block and this file describe the new work.
Keep Daniel's Git identity and plain factual messages without generated-by/co-author trailers.
''')
block='''> **Active operator-directed candidate work, 2026-10-10:** Iter147 bounded GPU
> qualification is complete: eight fresh cases / 912 actions / four matching replica pairs.
> Two injected monitor runs reached 401 actions each; six natural nominal actor runs
> reproduced collisions. No recovery gain or GPU route completion was established.
> **4/110 natural-actor controller calls exceeded 50 ms; all 912 loops exceeded 250 ms.**
> Local qualification separately supports 890 constructed actions / three replica pairs;
> 129 focused tests pass. Read the [result](PREFIXexperiments/iter147_full_horizon_execution/RESULT.md),
> [state](PREFIXexperiments/iter147_full_horizon_execution/STATE.json) and
> [active handoff](PREFIXexperiments/iter147_full_horizon_execution/DECISION.md).
> Exact owned VM is TERMINATED; watchdog and supervisor exited. No owned job or restart
> remains. Next: study-specific admission and finite lifecycle/resource binding for the
> unchanged proposed 112 slots. Candidate `research/iter147-full-horizon-execution`
> is local/unpushed. Master, historical HANDOFF/MISSION_STATE, immutable root README,
> unrelated WIP, prior recovery nulls and deferred Iter135 remain preserved.
'''
log='''\n\n## Iter147 bounded qualification closed on 2026-10-10

All eight fixed GPU slots passed independent replay and strict replica comparison: 912 actions,
four pairs. Diagnostic monitor hold reached 401 actions twice with 802 firings; natural nominal
Attack/IDM/Constant pairs reproduced collisions at 2.50/3.50/7.75 simulated seconds. No recovery
or live route completion was established. 4/110 natural-actor controller calls exceeded 50 ms;
all 912 v2 loop timings exceeded 250 ms. Raw was committed before replay and later-pair admission.
Local constructed qualification adds 890 actions / three pairs; 129 focused tests pass.
6,074 bound/original files and 20 actor aliases passed postflight. Owned VM is TERMINATED;
watchdog and supervisor exited. No automatic restart remains. Study-specific admission and
finite lifecycle/resource binding are next for the unchanged proposed 112 slots.
'''
def update(s,prefix):
 s,n=re.subn(r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*',lambda match:block.replace('PREFIX',prefix),s,count=1,flags=re.M);assert n==1;return s
for name,prefix in [('CONTINUITY.md',''),('docs/NEXT_PHASE.md','../'),('README.md','')]:
 s=update(subprocess.check_output(['git','show',branch+':'+name],text=True),prefix)
 if name=='CONTINUITY.md':s+=log
 if name=='README.md':s=s.replace('Iter146 adds a bounded four-arm GPU execution qualification and explicit simulator-defined completion; useful recovery and real-time operation remain unestablished.','Iter147 adds full-horizon diagnostic monitor execution and nonempty actor qualification; useful recovery and real-time operation remain unestablished.')
 Path('/tmp/i147_'+Path(name).name).write_text(s)
 if name!='README.md':
  p=R/name;s=update(p.read_text(),prefix)
  if name=='CONTINUITY.md':s+=log
  p.write_text(s)
memory='''# Sentinel Iter147 recovery — 2026-10-10

Canonical root /Users/danielwahnich/workspace/sentinel. Read CONTINUITY.md top/tail,
HANDOFF.md, MISSION_STATE.json, then experiments/iter147_full_horizon_execution/RESULT.md,
STATE.json and DECISION.md. These are active operator-directed candidate records; old
human-review/NONE clauses do not block Daniel's direct instructions.

Eight fixed GPU cases / 912 actions / four replica pairs passed. Diagnostic hold reached
401 actions twice; six natural nominal actor runs collided. No recovery gain. Four of
110 natural-actor controller calls exceeded 50 ms; all 912 loops exceeded 250 ms. Local
CPU qualification: 890 actions / three pairs; 129 tests. Exact owned VM is TERMINATED;
watchdog and supervisor exited 0, no job or automatic restart. Closed Iter147 budgets,
clearances, source/control directory and slots cannot be reused.

Next: implement study-specific admission and finite resource/lifecycle binding for the
unchanged proposed 112 slots, then technical validation and execution. No human ceremony.
Do not confuse injected detector qualification with natural perception or study recovery.
Prior nulls and deferred Iter135 unchanged. Candidate research/iter147-full-horizon-execution
is local/unpushed. Dirty WIP root, master, old evidence, historical HANDOFF/MISSION_STATE
and immutable root README are preserved. Do not reset, checkout or stage unrelated files.
'''
M=Path('/Users/danielwahnich/.codex/memories');(M/'sentinel-latest.md').write_text(memory);(M/'sentinel-iter147-full-horizon-qualification-2026-10-10.md').write_text(memory)
shutil.copyfile('/tmp/i147_write_results.py',P/'session_tools/i147_write_results.py')
print('Results, active docs, state and memory synchronized; no active compute.')
