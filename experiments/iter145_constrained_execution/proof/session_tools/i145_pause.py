from pathlib import Path
import json, subprocess, re, shutil
R=Path('/Users/danielwahnich/workspace/sentinel'); D=R/'experiments/iter145_constrained_execution'; P=D/'proof'; E=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010')
stop=json.loads((P/'shutdown_verified.json').read_text()); assert stop['status']=='TERMINATED' and stop['id']=='3834622546652649531'
s=json.loads((D/'STATE.json').read_text());s.update(status='paused',phase='paused_before_asset_gate_completion',pause_reason='operator_requested_machine_shutdown_for_about_one_hour',provider_state_last_observed='TERMINATED',provider_shutdown_receipt='proof/shutdown_verified.json',asset_status='blocked',asset_verdict='ASSET_CLOSURE_UNAVAILABLE',cloud_compute_used=True,owned_local_watchdog='exited_after_verified_cleanup',owned_active_jobs=0,automatic_resume_scheduled=False,host_inspection_envelope='closed',next_step='verify historical actor path aliases, empty actor lists, and HD-map dependencies before a new bounded GPU qualification')
s.pop('owned_shutdown_deadline_epoch',None)
(D/'STATE.json').write_text(json.dumps(s,indent=2)+'\n')
(D/'RESULT.md').write_text('''# Iter145 result at the operator stopping point

**2026-10-10: paused at Daniel's request before machine shutdown.** Controller
qualification and simulator CPU wiring are supported within the scopes below.
Asset closure is blocked; full GPU integration and live execution remain unqualified.
Cloud compute was used for inspection. No live smoke or study episode ran.

## Retained measurements

| Check | Result | Evidence |
| --- | --- | --- |
| Original controller inputs | 28/28 admitted; four replica pairs | [independent analysis](proof/optimizer_analysis_v3.json) |
| Maximum stationarity residual | 9.548826324229376e-7, below unchanged 1e-6 bar | [raw controller records](proof/optimizer_raw_v3.json) |
| Constraint violation | 0; maximum complementarity 7.863774333754186e-16 | Same controller analysis |
| From-rest straight / curved iterations | 15 / 34, within the unchanged 100-iteration cap | Same controller analysis |
| Simulator CPU wiring | 96 steps, 384 actor advances, 16 selections, four replica pairs | [independent analysis](proof/integration_analysis.json) |
| Short-horizon maximum stationarity | 9.53344077181395e-7 | Same integration analysis |
| Corrupted full artifacts | 30/30 rejected: 15 controller and 15 integration | [known-bad results](proof/known_bad_validations.json) |
| Focused tests | 71 on isolated committed source; 76 after five brake-pulse tests | [isolated log](proof/commands/committed_simulator_pytest.stdout), [later log](proof/commands/brake_branch_pytest.stdout) |
| Cloud asset inspection | 411/439 file entries observed; 28 unavailable; closure blocked | [host report](proof/asset_inspection_report.json) |
| Cloud shutdown | Exact owned VM observed TERMINATED; local watchdog exited | [provider readback](proof/shutdown_verified.json) |

Controller complete-call times were 2.374959–25.150209 ms on the original inputs and
1.284666–18.591459 ms in the CPU integration fixtures. These are ambient local
measurements, not a GPU deadline or vehicle timing qualification. Runtime was local
Python 3.14.2, NumPy 2.4.2, SciPy 1.17.1 and CPU Torch 2.10. Ruff passed. The retained
pytest logs include warnings; frozen Linux and hosted CI were not run for this candidate.

## Failures and corrections preserved

The first SLSQP design failed stationarity on 20/28 inputs. A prospective bounded
Gauss-Newton refinement amendment retained the population, thresholds, 100 total
major-iteration cap and eight-refinement limit. A checker incorrectly treated the last
SLSQP callback as the returned solution; the correction retains both values explicitly.
A shorter-horizon fixture then failed at 2.8796812003850647e-6. The diagnostic traced a
zero admissible step to outward roundoff in an active-bound KKT direction. The
[prospective nullspace amendment](NULLSPACE_AMENDMENT.md) changed the equality-constrained
subproblem solve before the final measurements. Failed records remain in proof.
Stationarity is a local necessary condition; global nonlinear optimality is unclaimed.

The [braking correction](ARM_IMPLEMENTATION_CORRECTION.md) restores the registered
one-second signed pulse, caps braking at zero speed, preserves nominal steering and
resumes nominal control. Only nominal CPU traces were measured; no brake-arm episode ran.

## What the integration evidence covers

The fixtures execute retained HUGSIM environment methods, explicit trajectory timing,
reset, control consumption, render transforms and Attack/Constant/IDM/Unicycle updates.
Named substitutions include constructed CPU state, identity CUDA transfer, deterministic
small camera outputs, background collision false, SAT polygon overlap in place of GEOS,
and synthetic nominal delivery. Actual asset construction, CUDA rendering, GEOS and
planner transport require GPU qualification. The bounded driver core exists; standalone
GPU orchestration remains to be completed. Physical fidelity and recovery are unestablished.

## Inspection and shutdown

One g2-standard-8 / L4 VM start was used under the [inspection binding](HOST_INSPECTION_BINDING.md):
1,800 seconds maximum, $1.50 incremental compute cap and zero live episodes. Official
pricing evidence and the conservative $3/hour bound are retained in
[price binding](proof/price_binding.json). This is a prospective budget, not a billing receipt;
existing persistent disk costs are excluded. No new disk or bucket was created.
The host was idle, with about 109.25 GiB free storage. These observations must be refreshed
before another execution; no permanent resource admission follows from this inspection.

All 14 frozen scenario YAML hashes matched. The 28 unavailable paths are actor model and
dimension paths rejected by the no-follow reader at `postprocess/shadow.pth`.
[Iter46's amendment](../iter46_hugsim_off_baseline/HYPOTHESIS.md) documents a historical
compatibility symlink from that path to the flat actor directory. That is a plausible
explanation, not verified current link identity and not proof that the models are missing.
Two scenarios still require HD-map/route-cache inventories. Three easy scenarios have
valid empty actor lists, which the current asset gate incorrectly rejects. These defects
were identified and saved for resumption; no asset gate was waived.

VM `sentinel-gpu`, ID `3834622546652649531`, in `us-west1-a`, project
`sunlit-unison-487018-b0`, was stopped and observed TERMINATED. The local watchdog exited
after verified cleanup. The inspection envelope is closed and must not be reused.

Tested CPU source: `8b8fa4239f95482d8419a0d5afc09b18248feb43`.
Raw committed before analysis: `f0ccefca87981bf4c02acf58e7bd1bc7dada5f60`.
Later brake correction and inspection source: `ae29d5f83f7b021c735bdf0af914bfc4bd132ee6`.
The candidate remains local and unpushed. Canonical master remains F17.
Iter139 remains null, 0/6 useful recoveries; Iter142 remains null, 0/2.
Iter135 stays deferred. The proposed 14-scenario / 112-slot study has not started.

See the [resume handoff](DECISION.md) and [machine-readable state](STATE.json).
''')
(D/'DECISION.md').write_text('''# Iter145 stopping point and resume handoff

## Stopped at Daniel's request, 2026-10-10

The machine is about to be closed for approximately one hour. Work is paused; no automatic
restart is scheduled. Cloud VM `sentinel-gpu` (ID `3834622546652649531`, project
`sunlit-unison-487018-b0`, zone `us-west1-a`) is **TERMINATED** according to the
[retained readback](proof/shutdown_verified.json). The owned local watchdog exited.
No owned job remains active. Cloud compute was used for asset inspection; zero live
smoke/study episodes ran. Read [RESULT.md](RESULT.md) and [STATE.json](STATE.json).

## First actions when Daniel resumes

1. Verify Sentinel cwd/root/remote and read AGENTS.md, the active CONTINUITY block,
   this handoff and STATE.json. Inspect `research/iter145-constrained-execution` through
   Git without checking out over the dirty WIP root. No human acceptance ceremony is needed.
2. Correct and qualify asset inventory locally. Preserve all scenario YAML bytes.
   Iter46 HYPOTHESIS.md (historical section around lines 262–294) records the approved
   `<car>/postprocess/shadow.pth -> ..` compatibility alias over flat released
   `<car>/{gs.pth,wlh.json}`. Inspect that exact historical evidence and the Iter45
   `proof-infra/hugsim_asset_manifest.txt`. Implement an explicit, bounded logical-to-physical
   mapping; verify actual link text, target ownership and canonical regular-file hashes.
   Do not generally relax no-follow reads or substitute actor assets. Current link identity
   was not read back in this inspection. Retain known-bads for escape, wrong alias and hashes.
3. Accept a validated empty `plan_list` for the three easy scenarios, with a known-bad for
   missing/malformed lists. Complete HD-map and route-cache dependency discovery for
   `scene-0013-hard-00.yaml` and `scene-0038-medium-01.yaml`. Base config uses
   `/datasets/nuscenes-full`, `nusc_trainval`; inspect actual loader dependencies.
4. Prepare and commit a fresh finite inspection/qualification binding before any new VM
   start. The previous single-start, 1,800-second inspection envelope is closed. Refresh
   cloud identity, credentials, price bound, disk/RAM/GPU headroom, idle state and clock
   basis; stale receipts do not admit execution. Arm cleanup and retain terminal evidence.
   Authentication recovered this session and is not currently a known blocker.
5. Finish source-bound GPU assembly around the bounded driver and planner pipe. Qualify
   actual asset construction, rendering, CUDA, GEOS, transport, actor/ego consumption,
   resets, stop reasons, wall-clock limits and cleanup with a finite preregistered smoke.
   Record complete-call deadlines separately from numerical convergence. No smoke was
   authorized by the now-closed inspection binding, and no smoke was run.
6. Only after those checks, finalize live bindings for the proposed 14-scenario / 112-slot
   study. Preserve frozen populations, schedules, outcomes, missingness, retries and stops.
   These are historically exposed development scenarios across three scenes, not an
   independent generalization population. Do not relabel collision delay as useful recovery.

## Evidence and preservation

- CPU: original 28/28 inputs pass unchanged constrained checks; 96 CPU integration steps,
  384 actor advances; independent replay and 30 corrupted-artifact rejections retained.
- 71 focused tests passed on the isolated 56-file source packet; 76 passed locally after
  five brake-branch tests. Real GPU/GEOS/model transport and physical validity remain open.
- Source `8b8fa4239f95482d8419a0d5afc09b18248feb43`; raw-before-analysis
  `f0ccefca87981bf4c02acf58e7bd1bc7dada5f60`; brake/inspection correction
  `ae29d5f83f7b021c735bdf0af914bfc4bd132ee6`. No brake-arm outcome measured.
- All failed optimizer, replay and development attempts remain retained. Inspect amendments
  before interpreting results. Never use callback values as a substitute for SLSQP result.x.
- Host packet/output remains at `/datasets/nuscenes-full/hugsim/iter145_control_20261010/`;
  all relevant inspection output is also in local `proof/`. No remote process remains running.
- External evidence: `/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010/`.
  Frozen source packet is `simulator_source_v4/`. Retained tooling is `proof/session_tools/`.
- Root stays `wip-gen17-ci-hardening`. Preserve unrelated WIP, staged state, immutable README,
  canonical HANDOFF.md and MISSION_STATE.json. The active blocks in CONTINUITY/NEXT_PHASE
  carry the current candidate state. Candidate README was updated through an alternate index;
  root README was not edited. No checkout, stash, master move, push or publication was used.
- Latest portable memory is `/Users/danielwahnich/.codex/memories/sentinel-latest.md`.
  The previous snapshot is `sentinel-through-iter144-closure-2026-10-10.md`.
''')
block='''> **Active operator-directed candidate work, 2026-10-10:** Iter145 is **paused**
> at Daniel's request for machine shutdown. Constrained controller qualification passed
> 28/28 original inputs; simulator CPU wiring passed 96 steps / 384 actor advances.
> 76 focused local tests passed; 30 corrupted full artifacts were rejected.
> Read the [result]({prefix}experiments/iter145_constrained_execution/RESULT.md),
> [state]({prefix}experiments/iter145_constrained_execution/STATE.json) and
> [resume handoff]({prefix}experiments/iter145_constrained_execution/DECISION.md).
> Cloud inspection found unresolved actor aliases, HD-map dependencies and an empty-actor
> gate defect. VM sentinel-gpu is verified TERMINATED; the local watchdog exited.
> No live smoke or study ran. Actual GPU/GEOS/model transport remains unqualified.
> The 14-scenario / 112-slot study is proposed, not admitted. Resume with asset closure
> and a new bounded GPU qualification envelope. No automatic restart is scheduled.
> Candidate `research/iter145-constrained-execution` is local/unpushed; master remains F17.
> Prior recovery nulls and deferred Iter135 remain unchanged; canonical MISSION_STATE/HANDOFF
> retain their publication snapshot.'''
entry='''\n\n## Iter145 operator stopping point on 2026-10-10

Daniel requested a pause before closing the machine for approximately one hour.
The constrained controller now passes 28/28 original inputs and the retained simulator
CPU wiring passes 96 steps. Failures and prospective amendments remain visible in the
Iter145 result. Thirty corrupted full artifacts were rejected; 76 focused local tests
passed (71 also passed on the isolated committed source packet).
One bounded cloud asset inspection ran; no live episode ran. Asset closure remains blocked:
actor compatibility aliases require verified mapping, two HD-map dependencies need inventories,
and valid empty actor lists need a gate correction. The exact owned VM is TERMINATED and
the local watchdog exited. Resume instructions and all receipts are retained under
experiments/iter145_constrained_execution. No automatic restart is scheduled.
'''
for rel in ['CONTINUITY.md','docs/NEXT_PHASE.md','README.md']:
 prefix='../' if rel.startswith('docs/') else ''
 def update(t):
  t,n=re.subn(r'> \*\*Active operator-directed candidate work, 2026-10-10:.*?(?=\n\n)',lambda _:block.format(prefix=prefix),t,count=1,flags=re.S);assert n==1
  if rel=='CONTINUITY.md':t+=entry
  if rel=='README.md':
   old='Iter144 now qualifies the explicit timing interface locally; from-rest convergence and full simulator integration remain open.'
   assert old in t;t=t.replace(old,'Iter145 now supports local constrained convergence and simulator CPU wiring; asset closure and full GPU integration remain open.')
  return t
 candidate=subprocess.check_output(['git','show','research/iter145-constrained-execution:'+rel],cwd=R,text=True)
 Path('/tmp/i145_'+Path(rel).name).write_text(update(candidate))
 if rel!='README.md':
  before=(R/rel).read_bytes();(E/('pause_before_'+Path(rel).name)).write_bytes(before);(R/rel).write_text(update(before.decode()))
T=P/'session_tools';T.mkdir(exist_ok=True)
names=['sentinel_i145_commit.py','i145_run.py','i145_init.py','i145_packet.py','i145_packet_v2.py','i145_packet_v3.py','i145_packet_v4.py','i145_diagnose_replay.py','i145_price.py','i145_hostops.py','i145_watchdog.py','i145_start.py','i145_preflight.py','i145_preflight_retry1.py','i145_deploy_inventory.py','i145_asset_diagnose.py','i145_stop.py','i145_pause.py']
for n in names:
 p=Path('/tmp')/n
 if p.exists():shutil.copy2(p,T/n)
(P/'pause_cleanup.json').write_text(json.dumps(dict(operator_requested_pause=True,cloud_final_state=stop,local_watchdog_exit_code=0,local_watchdog_terminal_output='watchdog cancelled after verified cleanup',active_owned_jobs=0,automatic_resume_scheduled=False),indent=2)+'\n')
print('PAUSE_REPORTS_WRITTEN')
