from pathlib import Path
import re,json,subprocess
R=Path.cwd();D=R/'experiments/iter148_recovery_study';B=D/'proof/block_000_attempt_002';branch='research/iter148-recovery-study'
s=json.loads((D/'STATE.json').read_text());ready=json.loads((B/'gpu_ready_instance.json').read_text())
s.update(status='running',phase='first_block_attempt2_host_preflight',cloud_compute_used=True,owned_active_jobs=1,start_command_issued=True,provider_current_state='RUNNING',last_verified_provider_state='RUNNING at attempt2 ready readback',owned_instance=ready,watchdog_session=92679,watchdog_exit_code=None,watchdog_exit_reason=None,next_task='Verify host/runtime/source/timer gates and execute fixed first-block pairs sequentially with committed raw before replay. Close exact owned VM start afterwards.')
(D/'STATE.json').write_text(json.dumps(s,indent=2)+'\n')
block='''> **Active operator-directed candidate work, 2026-10-11:** Iter148 first-block execution
> has resumed after successful Google Cloud reauthentication. The exact owned VM is RUNNING
> under fresh attempt2's 10,800-second / $9 conservative envelope and local watchdog92679.
> Host/runtime/timer admission is in progress; no study result has been accepted yet.
> Scope is the unchanged first eight slots of112; no automatic restart or initialized retry.
> Source dd45ad39b26602ad81626ca55332e7ce6d308e91 remains unchanged. Local165tests and
> replay of1,104priorGPUsteps pass; no new recovery benefit has been established.
> Read [state](experiments/iter148_recovery_study/STATE.json),
> [result](experiments/iter148_recovery_study/RESULT.md) and
> [attempt binding](experiments/iter148_recovery_study/proof/block_000_attempt_002/RESUME_BINDING.json).
> Watch the active attempt receipts for shutdown; do not infer stopped state from the
> earlier credential-failure closure. Candidate `research/iter148-recovery-study` is local.
> Master, historical snapshots, protected root README, unrelated WIP and prior evidence
> remain preserved. Deferred Iter135 and prior recovery nulls remain unchanged.
'''
pattern=r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*'
entry='''\n\n## Iter148 first-block execution resumed on 2026-10-11

Google Cloud login succeeded and a fresh exact-VM readback confirmed TERMINATED before
start. Attempt2 owns start2026-10-10T22:05:46.919-07:00 of VM3834622546652649531 under
10800seconds/$9 bounds. Local watchdog92679 is active. Host/runtime admission proceeds
before the unchanged first eight slots; no new result is accepted at this update.
'''
for name in ('CONTINUITY.md','docs/NEXT_PHASE.md','README.md'):
 b=block.replace('(experiments/','(../experiments/') if name.startswith('docs/') else block
 candidate=subprocess.check_output(['git','show',branch+':'+name],text=True)
 candidate=re.sub(pattern,lambda _:b,candidate,count=1,flags=re.M)
 if name=='CONTINUITY.md':candidate+=entry
 Path('/tmp/i148a_'+Path(name).name).write_text(candidate)
 if name!='README.md':
  p=R/name;root=re.sub(pattern,lambda _:b,p.read_text(),count=1,flags=re.M)
  if name=='CONTINUITY.md':root+=entry
  p.write_text(root)
for name in ['RESULT.md','DECISION.md']:
 p=D/name;p.write_text('> **Live update, 2026-10-11:** Account reauthentication succeeded. Fresh attempt2 is\n> running under its own bounded envelope. Read STATE.json and proof/block_000_attempt_002.\n> The login-block text below is retained history until execution closure.\n\n'+p.read_text())
memory='''# Sentinel Iter148 active attempt2 — 2026-10-11

Exact root /Users/danielwahnich/workspace/sentinel. Read active CONTINUITY and Iter148 STATE.
Operator reauthenticated and requested continuation. Fresh attempt2 owns VM3834622546652649531
start2026-10-10T22:05:46.919-07:00 in sunlit-unison-487018-b0/us-west1-a. It is RUNNING.
Budget10800s/$9 conservative; watchdog tool session92679 active. No study result accepted yet.
Current receipts: experiments/iter148_recovery_study/proof/block_000_attempt_002.
External control: /Users/danielwahnich/sentinel-bootstrap-evidence/iter148-block000-attempt002-20261011.
Hostcontrol planned /datasets/nuscenes-full/hugsim/iter148_study_20261011. Use i148a_* helpers.
Only fixed firstblock pairs0–3/slots0–7. Retain committed raw before replay/admission before nextpair.
Exact frozen source dd45ad39b26602ad81626ca55332e7ce6d308e91. No retry or outcome tuning.
Prior attempt0 credentials failed before start and is closed; its terminated-watchdog record
is not evidence about this active attempt. Do not finish while owned compute remains running.
Dirty root/index/master/old evidence/protectedREADME must remain preserved. Candidate local/unpushed.
'''
Path('/Users/danielwahnich/.codex/memories/sentinel-latest.md').write_text(memory)
(D/'proof/session_tools/i148a_active_docs.py').write_bytes(Path('/tmp/i148a_active_docs.py').read_bytes())
