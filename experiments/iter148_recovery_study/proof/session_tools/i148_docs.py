from pathlib import Path
import json,re,subprocess
R=Path.cwd();D=R/'experiments/iter148_recovery_study';P=D/'proof'
text='''> **Active operator-directed candidate work, 2026-10-11:** Iter148 has preregistered
> the unchanged 112-slot recovery study in 14 fixed operational blocks. The first block
> binds eight slots / one scenario, a fresh three-hour/$9 conservative compute envelope,
> exclusive pair starts, committed raw before independent replay, complete receipt history
> and full pre-intervention prefix checks. Prior qualification replays 1,104 GPU actions;
> 165 focused tests pass. Read the [study protocol](experiments/iter148_recovery_study/HYPOTHESIS.md),
> [execution binding](experiments/iter148_recovery_study/GPU_BINDING.md) and
> [state](experiments/iter148_recovery_study/STATE.json) for current execution status.
> No Iter148 study outcome is available at source freeze. Only block 0 is admitted for
> initial launch; remaining blocks require fresh automated lifecycle checks.
> Candidate `research/iter148-recovery-study` is local/unpushed. Master, historical
> HANDOFF/MISSION_STATE, immutable root README, unrelated WIP, all prior evidence,
> previous recovery nulls and deferred Iter135 remain preserved.
'''
for name in ('CONTINUITY.md','docs/NEXT_PHASE.md'):
 p=R/name;s=p.read_text();block=text.replace('(experiments/','(../experiments/') if name.startswith('docs/') else text
 s=re.sub(r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*',lambda _:block,s,count=1,flags=re.M)
 if name=='CONTINUITY.md':s+='\n\n## Iter148 study admission started on 2026-10-11\n\nThe original112slots are preregistered in14fixed scenario blocks; first-block envelope\nis10800seconds/$9conservative. PriorGPUqualification1104steps replays;165focused tests pass.\nNew controls bind committed prior receipts, prevent duplicate initialized work and check\nfull pre-intervention prefixes. No newstudy outcome exists at sourcefreeze.\n'
 p.write_text(s);Path('/tmp/i148_'+p.name).write_text(s)
base=subprocess.check_output(['git','show','research/iter147-full-horizon-execution:README.md'],text=True)
base=re.sub(r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*',lambda _:text,base,count=1,flags=re.M)
Path('/tmp/i148_README.md').write_text(base)
s=json.loads((D/'STATE.json').read_text());s.update(status='preregistered',phase='first_block_source_freeze',focused_tests=165,prior_gpu_steps_replayed=1104,planned_slots=112,initial_block_slots=8,study_outcomes_observed=0,automatic_restart=False,next_task='Freeze source, arm a fresh bounded envelope and execute fixed block 0 after provider/resource/runtime validation.')
(D/'STATE.json').write_text(json.dumps(s,indent=2)+'\n')
