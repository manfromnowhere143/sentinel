from pathlib import Path
import re,subprocess
R=Path.cwd();D=R/'experiments/iter148_recovery_study';branch='research/iter148-recovery-study'
block='''> **Active operator-directed candidate work, 2026-10-11:** Iter148 execution is closed.
> Nominal and monitor pairs passed: four source-defined completions, 368 verified actions,
> no recorded collision/off-route and zero monitor intervention. An IAP observation failure
> stopped the first pulse run at 88 recorded actions without a terminal summary. Totals:
> four admitted slots, one incomplete and 107 uninitialized; no four-arm comparison or
> recovery/harm rate is available. 6/368 verified controller calls exceeded 50 ms, and all
> 368 loops exceeded 250 ms. Both exact VM starts are TERMINATED; all local controls exited.
> Read [result](experiments/iter148_recovery_study/RESULT.md),
> [state](experiments/iter148_recovery_study/STATE.json) and
> [continuation](experiments/iter148_recovery_study/DECISION.md).
> **Next, by Daniel's explicit order:** review the entire README, relevant diagrams and
> current memories before any next experiment. The interrupted study remains halted;
> no initialized retry or automatic restart. Candidate `research/iter148-recovery-study`
> is local/unpushed. Master, historical snapshots, prior evidence and unrelated WIP remain
> preserved. Deferred Iter135 and prior recovery nulls are unchanged.
'''
entry='''\n\n## Iter148 interrupted block and evidence closure on 2026-10-11

Four baseline episodes passed independent replay and replica checks: 368 actions and source-defined
completion, without collision/off-route or monitor activation. The frozen supervisor stopped the
block after a read-only IAP observation failure. One pulse replica retains 88 actions but no terminal
summary; it is invalid for paired admission. Four slots admitted, one incomplete, 107 uninitialized;
no complete four-arm comparison. No recovery/harm rate is estimated. Six of 368 verified controller
calls exceeded 50 ms and every verified loop exceeded 250 ms.

Evidence recovery restarted no driving job. Final postflight verified 6,101 bound/original files
and 20 actor aliases unchanged, with no active container/GPU process. Both exact VM starts are
TERMINATED and all local controls exited. Combined conservative elapsed cost bound is $1.659,
within the original $9 block allowance. Failures, raw-before-replay commits and closures are retained.
Daniel requested the entire README, relevant diagrams and current research memory be reviewed in
his voice after this closure and before any next experiment. That editorial work is next. The study
remains stopped; a future protocol needs durable, bounded recovery from unavailable observations.
'''
pattern=r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*'
for name in ('CONTINUITY.md','docs/NEXT_PHASE.md','README.md'):
 b=block.replace('(experiments/','(../experiments/') if name.startswith('docs/') else block
 candidate=subprocess.check_output(['git','show',branch+':'+name],text=True)
 candidate=re.sub(pattern,lambda _:b,candidate,count=1,flags=re.M)
 if name=='CONTINUITY.md':candidate+=entry
 Path('/tmp/i148a_final_'+Path(name).name).write_text(candidate)
 if name!='README.md':
  p=R/name;root=re.sub(pattern,lambda _:b,p.read_text(),count=1,flags=re.M)
  if name=='CONTINUITY.md':root+=entry
  p.write_text(root)
for name in ('i148a_final_docs.py','i148a_final_audit.py'):(D/'proof/session_tools'/name).write_bytes((Path('/tmp')/name).read_bytes())
mem='''# Sentinel Iter148 closed; editorial task next — 2026-10-11

Root /Users/danielwahnich/workspace/sentinel. Recover from CONTINUITY and Iter148 RESULT/STATE/DECISION.
Four baseline episodes (nominal and monitor, two replicas each) pass independent replay: 368 actions,
source-defined completion, no collision/off-route, zero monitor intervention. An IAP progress-query
failure caused the frozen supervisor to stop the study during pulse replica1. Partial raw contains
88 actions without terminal summary; invalid paired admission. Four admitted, one incomplete, 107
uninitialized slots. No complete four-arm comparison or recovery/harm rate. Preserve all failures.

No GPU job is active. Both owned starts TERMINATED; latest start2026-10-10T22:31:47.574-07:00,
stop2026-10-10T22:38:08.936-07:00. Primary supervisor40891 exited1, watchdog92679 exited0;
forensic shutdown12123/watchdog32921 exited0. No automatic restart. Postflight6101files/20aliases
unchanged. Source frozen dd45ad39b26602ad81626ca55332e7ce6d308e91. All attempted raw committed
before replay. Six of368 verified controllercalls >50ms; all368 loops >250ms. No real-time claim.

Explicit operator order: BEFORE ANY NEXT EXPERIMENT, review/update the entire README, relevant
research diagrams and current memory, preserving the full story in Daniel's confident, humble,
precise and honest voice. Avoid generic AI prose and unsupported superiority/endorsement claims.
This editorial task is authorized and starts after scientific closure. Do not ask a human ceremony.
The study stays stopped; no initialized retry. Later research requires a prospective durable
observation-recovery design with bounded read-only retries and independent host deadlines.

Candidate research/iter148-recovery-study is local/unpushed. Dirty root wip-gen17-ci-hardening and
index/master/old evidence must remain intact. Root README has uchg and deny-delete; handle the newly
explicitly authorized README task as a separate editorial phase with preserved prior bytes and
restored protections. Do not import historical root WIP into candidate CONTINUITY. Prior nulls and
deferred Iter135 remain. Closed helpers i148a_*/i148f_* embed closed paths; never run blindly.
'''
for name in ('sentinel-latest.md','sentinel-iter148-interrupted-study-2026-10-11.md'):
 Path('/Users/danielwahnich/.codex/memories',name).write_text(mem)
