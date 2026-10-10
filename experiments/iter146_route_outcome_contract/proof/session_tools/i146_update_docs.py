from pathlib import Path
import subprocess,re
R=Path('/Users/danielwahnich/workspace/sentinel');branch='research/iter146-route-outcome-contract'
block='''> **Active operator-directed candidate work, 2026-10-10:** Iter146 completed bounded
> GPU qualification: eight fresh cases / 192 steps / four matching replica pairs.
> All cases were censored at24 actions; monitor fired zero times and source actors
> were empty. No recovery gain or full-horizon GPU completion was established.
> CPU replay supports3,362 synthetic steps. After timing/missingness corrections,
> 96focused tests pass; the corrected timer has local evidence only.
> **1/192 controller calls exceeded50ms; all192 loop-work lower bounds exceeded250ms.**
> Read the [result](PREFIXexperiments/iter146_route_outcome_contract/RESULT.md),
> [state](PREFIXexperiments/iter146_route_outcome_contract/STATE.json) and
> [active handoff](PREFIXexperiments/iter146_route_outcome_contract/DECISION.md).
> Exact owned VM is TERMINATED and its watchdog exited. Cloud compute was used;
> no owned job or automatic restart remains. Next: full-horizon/actor/active-monitor
> qualification and finite resource/runtime binding before the proposed112slots.
> Candidate `research/iter146-route-outcome-contract` is local/unpushed. Master,
> historical HANDOFF/MISSION_STATE, immutable root README and unrelated WIP remain
> preserved. Prior recovery nulls and deferred Iter135 are unchanged.
'''
# Keep prose spacing legible; do not change the factual values.
for old,new in [('at24','at 24'),('supports3,362','supports 3,362'),('96focused','96 focused'),('exceeded50ms','exceeded 50 ms'),('all192','all 192'),('exceeded250ms','exceeded 250 ms'),('proposed112slots','proposed 112 slots')]:block=block.replace(old,new)
started='''\n\n## Iter146 full-horizon contract work started on 2026-10-10

Daniel continued the mission. The separate outcome contract records simulator completion
without hiding collision or off-route outcomes behind reward. Eighteen retained CPU fixtures
passed independent replay: 3,362 steps/eight replica pairs. Sixty-four tests passed. A finite
eight-case GPU qualification is preregistered; the 112-slot study remains proposed.
'''
closed='''\n\n## Iter146 bounded qualification closed on 2026-10-10

Eight fresh-process GPU episodes passed independent replay: 192 steps/four replica pairs,
with both one-second braking pulses and exact plan/image replica agreement. All eight
were censored at 24 actions; monitor activations and configured source actors were zero.
No useful-recovery result follows. One controller call exceeded 50 ms; every recorded
loop-work lower bound exceeded 250 ms. A timing-scope correction preserves raw v1;
new local v2 measures through the final guard/stop decision. Proposed comparison logic
now preserves unknown witness/harm outcomes. Four pre-fix known-bads reproduced the
errors; 96 corrected tests pass. All old CPU/GPU raw replays without changed outcomes.
6,062 bound/original files plus 20 actor aliases were unchanged at postflight. Exact owned
VM is TERMINATED; watchdog exited. Full-horizon/nonempty-actor/active-monitor qualification
and a finite study launcher/resource binding remain before the unchanged proposed 112 slots.
'''
def update(s,prefix):
 pattern=r'^> \*\*Active operator-directed candidate work,[^\n]*\n(?:>[^\n]*\n)*'
 s,n=re.subn(pattern,lambda m:block.replace('PREFIX',prefix),s,count=1,flags=re.M)
 assert n==1
 return s
for name,prefix in [('CONTINUITY.md',''),('docs/NEXT_PHASE.md','../'),('README.md','')]:
 s=subprocess.check_output(['git','show',branch+':'+name],cwd=R,text=True);s=update(s,prefix)
 if name=='CONTINUITY.md':
  if '## Iter146 full-horizon contract work started' not in s:s+=started
  if '## Iter146 bounded qualification closed' not in s:s+=closed
 if name=='README.md':
  old='Iter145 now supports constrained convergence, asset closure and its four-case GPU smoke contract; full-route recovery and real-time operation remain unestablished.'
  assert old in s;s=s.replace(old,'Iter146 adds a bounded four-arm GPU execution qualification and explicit simulator-defined completion; useful recovery and real-time operation remain unestablished.')
 out=Path('/tmp/i146_'+Path(name).name);out.write_text(s)
 if name!='README.md':
  p=R/name;live=update(p.read_text(),prefix)
  if name=='CONTINUITY.md' and '## Iter146 bounded qualification closed' not in live:live+=closed
  p.write_text(live)
print('Candidate docs prepared; root continuity surfaces updated without touching README')
