import json,sys,subprocess,traceback,statistics
from i148g_ops import R,D,RAW,ADMISSIONS,BRANCH
sys.path.insert(0,str(R))
from experiments.iter148_recovery_study.replay import admit
from experiments.iter148_recovery_study.admission import committed_file
from experiments.iter147_full_horizon_execution.coordinator import record
pair=int(sys.argv[1]);root=RAW/f'pair_{pair:03d}'
commit=subprocess.check_output(['git','rev-parse',BRANCH],cwd=R,text=True).strip()
plan=json.loads((D/'STUDY_PLAN.json').read_text())
result=dict(pair=pair,raw_commit=commit,status='invalid',live_study_admitted=True)
try:
 receipts=[json.loads(committed_file(R,commit,ADMISSIONS/f'pair_{i:03d}.json')) for i in range(pair)]
 result=admit(R,root,plan,pair,commit,receipts,RAW)
 controllers=[];loops=[];exchanges=[]
 for folder in sorted((root/'runs').iterdir()):
  s=json.loads((folder/'trace/summary.json').read_text());loops.extend(v['full_loop_ns']/1e9 for v in s['timings']);exchanges.extend(v['exchange_ns']/1e9 for v in s['timings'])
  rows=[json.loads(l) for l in (folder/'trace/events.jsonl').read_text().splitlines()];controllers.extend(r['result']['complete_call_ns']/1e6 for r in rows if r['event']=='control')
 result['timing']=dict(controller_ms=dict(median=statistics.median(controllers),maximum=max(controllers),over_50ms=sum(t>50 for t in controllers)),full_loop_seconds=dict(median=statistics.median(loops),maximum=max(loops),over_250ms=sum(t>.25 for t in loops)),exchange_seconds=dict(median=statistics.median(exchanges),maximum=max(exchanges)))
except Exception as exc:result.update(status='invalid',error=repr(exc),traceback=traceback.format_exc())
ADMISSIONS.mkdir(exist_ok=True)
record(ADMISSIONS/f'pair_{pair:03d}.json',result);print(json.dumps(result))
raise SystemExit(0 if result['status']=='supported' else 1)
