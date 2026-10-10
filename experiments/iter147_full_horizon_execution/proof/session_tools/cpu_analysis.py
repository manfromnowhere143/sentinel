import json,sys,subprocess
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');sys.path.insert(0,str(R));P=R/'experiments/iter147_full_horizon_execution/proof'
from experiments.iter147_full_horizon_execution.coordinator import raw_identity
from experiments.iter147_full_horizon_execution.monitor import replay
from experiments.iter146_route_outcome_contract.check import read,verify
from experiments.iter146_route_outcome_contract.compare import replicas
commit=subprocess.check_output(['git','rev-parse','research/iter147-full-horizon-execution'],cwd=R,text=True).strip()
raw_sha=raw_identity(R,commit,P/'cpu_raw');reports={};out=[];maxevent=0;maxcandidates=0
for name in ('hold','release','actors'):
 pair=[]
 for i in (1,2):
  directory=P/'cpu_raw'/f'{name}__{i}';events,s=read(directory/'trace');report=verify(events,s);pair.append(report)
  monitors=[json.loads(r['raw']) for r in events if r['event']=='monitor'];monitor=replay(monitors)
  raw=(directory/'trace/events.jsonl').read_bytes();largest=max(map(len,raw.splitlines()));maxevent=max(maxevent,largest)
  candidates=[len(r['value']['candidates']) for r in events if r['event']=='actor' and r['value']['event']=='select'];maxcandidates=max([maxcandidates,*candidates])
  out.append(dict(name=directory.name,steps=report['steps'],max_stationarity=report['max_stationarity'],actor_selections=report['attack_selections'],actor_types=['AttackPlanner','ConstantPlanner','IDM'] if name=='actors' else [],monitor=monitor,trace_bytes=len(raw),largest_event_bytes=largest,candidates_per_selection=candidates))
 replicas(pair)
result=dict(status='supported',raw_commit=commit,raw_inventory_sha256=raw_sha,cases=out,steps=sum(x['steps'] for x in out),replica_pairs=3,max_event_bytes=maxevent,max_candidates=maxcandidates,gpu_observed=False,live_study_admitted=False)
(P/'cpu_analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
