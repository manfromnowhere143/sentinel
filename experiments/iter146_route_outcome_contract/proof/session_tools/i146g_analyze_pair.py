import json,sys,subprocess,traceback,statistics,hashlib
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');sys.path.insert(0,str(R))
from experiments.iter146_route_outcome_contract.gpu_check import verify_case
from experiments.iter146_route_outcome_contract.compare import replicas
arm=sys.argv[1];P=R/'experiments/iter146_route_outcome_contract/proof';root=P/'gpu_raw'/arm
commit=subprocess.check_output(['git','rev-parse','research/iter146-route-outcome-contract'],cwd=R,text=True).strip()
for p in root.rglob('*'):
 if p.is_file():assert p.read_bytes()==subprocess.check_output(['git','show',commit+':'+str(p.relative_to(R))],cwd=R)
reports=[];result=dict(arm=arm,raw_commit=commit,status='invalid',live_study_admitted=False)
try:
 for replica in (1,2):
  directory=root/'runs'/('scene-0013-easy-00__'+arm+'__'+str(replica));report=verify_case(directory)
  assert report['steps']==24 and report['arm']==arm
  reports.append(report)
 replicas(reports)
 result.update(status='supported',replica_pairs=1,steps=48,cases=[{k:v for k,v in r.items() if k not in ('scientific','route')} for r in reports])
 controllers=[];loops=[];exchanges=[]
 for folder in sorted((root/'runs').iterdir()):
  s=json.loads((folder/'trace/summary.json').read_text());loops.extend(v['full_loop_ns']/1e9 for v in s['timings']);exchanges.extend(v['exchange_ns']/1e9 for v in s['timings'])
  rows=[json.loads(l) for l in (folder/'trace/events.jsonl').read_text().splitlines()];controllers.extend(r['result']['complete_call_ns']/1e6 for r in rows if r['event']=='control')
 result['timing']=dict(controller_ms=dict(median=statistics.median(controllers),maximum=max(controllers),over_50ms=sum(t>50 for t in controllers)),full_loop_seconds=dict(median=statistics.median(loops),maximum=max(loops),over_250ms=sum(t>.25 for t in loops)),exchange_seconds=dict(median=statistics.median(exchanges),maximum=max(exchanges)))
except Exception as exc:
 result.update(error=repr(exc),traceback=traceback.format_exc(),cases_verified=len(reports))
(P/(arm+'_pair_analysis.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
raise SystemExit(0 if result['status']=='supported' else 1)
