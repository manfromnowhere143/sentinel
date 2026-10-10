from pathlib import Path
import subprocess,re,json,sys
R=Path('/Users/danielwahnich/workspace/sentinel');branch='research/iter147-full-horizon-execution';D=R/'experiments/iter147_full_horizon_execution'
phase=sys.argv[1]
cloud='No new cloud start has occurred.' if phase=='preregistered' else 'An owned bounded GPU session is RUNNING; read STATE.json and external budget before any action.'
block='''> **Active operator-directed candidate work, 2026-10-10:** Iter147 local qualification
> supports 890 constructed steps / three replica pairs; 129 focused tests pass.
> Eight full-horizon GPU qualification slots are preregistered: diagnostic monitor hold
> and natural nominal Attack/IDM/Constant cases, two replicas each. The whole envelope
> is 10,800 seconds / $9 conservative compute; each child is capped at 1,200 seconds.
> CLOUD
> Read the [hypothesis](PREFIXexperiments/iter147_full_horizon_execution/HYPOTHESIS.md),
> [binding](PREFIXexperiments/iter147_full_horizon_execution/GPU_BINDING.md),
> [state](PREFIXexperiments/iter147_full_horizon_execution/STATE.json) and
> [active handoff](PREFIXexperiments/iter147_full_horizon_execution/DECISION.md).
> The proposed 112 study slots are not admitted. No recovery, real-time or state-of-the-art
> result follows. Candidate `research/iter147-full-horizon-execution` is local/unpushed.
> Master, historical HANDOFF/MISSION_STATE, immutable root README and unrelated WIP
> remain preserved. Prior recovery nulls and deferred Iter135 are unchanged.
'''.replace('CLOUD',cloud)
def update(s,prefix):
 s,n=re.subn(r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*',lambda m:block.replace('PREFIX',prefix),s,count=1,flags=re.M);assert n==1;return s
log='''\n\n## Iter147 full-horizon path qualification started on 2026-10-10

Local raw was committed at a9b717b9c1d4e2d007a8f6d2f0dc70abae6da68d before
independent replay: 890 constructed steps, three strict replica pairs. Monitor hold
runs execute 401 actions each; monitor release and nonempty actor fixtures also pass.
129 focused tests pass. A separate eight-case GPU binding fixes the diagnostic input,
actor population, 401-action horizon, deadlines, output and compute bounds before live
execution. This is qualification evidence, not a study recovery denominator.
'''
for name,prefix in [('CONTINUITY.md',''),('docs/NEXT_PHASE.md','../'),('README.md','')]:
 s=update(subprocess.check_output(['git','show',branch+':'+name],cwd=R,text=True),prefix)
 if name=='CONTINUITY.md' and '## Iter147 full-horizon path qualification started' not in s:s+=log
 Path('/tmp/i147_'+Path(name).name).write_text(s)
 if name!='README.md':
  p=R/name;s=update(p.read_text(),prefix)
  if name=='CONTINUITY.md' and '## Iter147 full-horizon path qualification started' not in s:s+=log
  p.write_text(s)
state=json.loads((D/'STATE.json').read_text());state.update(status=phase,phase='gpu_qualification_'+phase,cloud_compute_used=phase=='running',owned_active_jobs=int(phase=='running'),local_steps=890,local_replica_pairs=3,focused_tests=129,gpu_slots=8,gpu_source_commit=None,control='/datasets/nuscenes-full/hugsim/iter147_gpu_20261010',external_budget='/Users/danielwahnich/sentinel-bootstrap-evidence/iter147-gpu-20261010/budget.json')
if (D/'proof/gpu_source_packet.json').exists():state['gpu_source_commit']=json.loads((D/'proof/gpu_source_packet.json').read_text())['commit']
if (D/'proof/gpu_ready_instance.json').exists():state['owned_instance']=json.loads((D/'proof/gpu_ready_instance.json').read_text())
(D/'STATE.json').write_text(json.dumps(state,indent=2)+'\n')
(D/'DECISION.md').write_text('# Iter147 active handoff\n\n'+cloud+'\n\nContinue the fixed eight-slot qualification only through committed raw and independently\nvalidated pair admission. No initialized retry or population change. Stop later slots on\nworker failure, invalid replay or replica disagreement. Each child is capped at 1,200 s;\nwhole session 10,800 s / $9 conservative compute, local watchdog plus host shutdown timer.\nBefore closure, collect evidence, check assets, stop exact owned VM, verify TERMINATED\nand watchdog exit. External budget and owned identity are in STATE.json.\n\nLocal-only result: 890 constructed steps / three replica pairs / 129 tests. GPU outcomes\nremain unobserved at this handoff update. The proposed 112 study slots remain unadmitted.\n')
m=Path('/Users/danielwahnich/.codex/memories/sentinel-latest.md')
m.write_text('# Sentinel recovery pointer\n\nCanonical root: '+str(R)+'\n\nIter147 '+phase+'. '+cloud+'\nRead CONTINUITY.md top/tail, HANDOFF.md, MISSION_STATE.json, then\nexperiments/iter147_full_horizon_execution/STATE.json and DECISION.md.\nDirect operator authority permits continuation; no human ceremony.\nCandidate research/iter147-full-horizon-execution is local/unpushed; dirty WIP root\nand immutable README preserved. Never reset/checkout or stage unrelated work.\n')
