from pathlib import Path
import json,re,subprocess
R=Path.cwd();D=R/'experiments/iter148_recovery_study';P=D/'proof';parent='21c51ed3ead8d24da410b4913ac1a734507b7c08'
block='''> **Active operator-directed candidate work, 2026-10-11:** Iter148 study admission is
> implemented: 165 focused tests pass; prior 1,104 GPU actions replay; the strengthened
> delayed-pulse prefix matches all ten pre-intervention steps on retained qualification data.
> **New live execution is blocked by Google Cloud reauthentication.** The before-start
> read-only query failed; no VM start command, host command or new episode was issued.
> The unused local watchdog exited143 after intentional cancellation; no automatic restart.
> Current provider state is UNOBSERVED; Iter147's last verified state was TERMINATED.
> Read [result](experiments/iter148_recovery_study/RESULT.md),
> [state](experiments/iter148_recovery_study/STATE.json) and
> [continuation](experiments/iter148_recovery_study/DECISION.md). All112 study slots remain
> without execution evidence. After login, use a fresh first-block10800s/$9 envelope for
> the unchanged first eight slots. No recovery benefit has been established.
> Candidate `research/iter148-recovery-study` is local/unpushed. Master, historical
> HANDOFF/MISSION_STATE, protected root README, unrelated WIP, prior evidence/nulls and
> deferred Iter135 remain preserved.
'''
append='''\n\n## Iter148 local admission closed; provider login required on 2026-10-11

Study admission and full-prefix controls pass165focused tests; existingGPUqualification
replays1104actions and ten delayed-pulse prefix steps. The first provider query failed
credential refresh before any start command. No newcloudcompute or study episode ran.
The unused local watchdog exited143; no automatic restart. Currentprovider state remains
unobserved, with Iter147's prior TERMINATED record preserved. All112slots remain missing.
After account reauthentication, create a fresh bounded first-block envelope; retain the
unchanged population, claims, stopping rules and prior nulls. See Iter148 RESULT/DECISION.
'''
pattern=r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*'
for name in ('CONTINUITY.md','docs/NEXT_PHASE.md'):
 p=R/name;current=p.read_text();b=block.replace('(experiments/','(../experiments/') if name.startswith('docs/') else block
 current=re.sub(pattern,lambda _:b,current,count=1,flags=re.M)
 if name=='CONTINUITY.md':current+=append
 p.write_text(current)
 candidate=subprocess.check_output(['git','show',parent+':'+name],text=True)
 candidate=re.sub(pattern,lambda _:b,candidate,count=1,flags=re.M)
 if name=='CONTINUITY.md':candidate+='\n\n## Iter148 study admission started on 2026-10-11'+current.split('\n\n## Iter148 study admission started on 2026-10-11')[1]
 Path('/tmp/i148_'+p.name).write_text(candidate)
s=subprocess.check_output(['git','show',parent+':README.md'],text=True)
s=re.sub(pattern,lambda _:block,s,count=1,flags=re.M);Path('/tmp/i148_README.md').write_text(s)
for name in ('i148_finish_local.py','i148_update_docs.py'):(P/'session_tools'/name).write_bytes((Path('/tmp')/name).read_bytes())
