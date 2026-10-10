import json,hashlib,traceback,sys
from pathlib import Path
sys.path.insert(0,'/Users/danielwahnich/workspace/sentinel')
from experiments.iter145_constrained_execution.gpu_check import verify
p=Path('experiments/iter145_constrained_execution/proof');reports=[]
for case in sorted((p/'gpu_raw/runs').iterdir()):
 try:r=verify(case)
 except Exception as e:r=dict(status='failed',episode=case.name,error=repr(e),traceback=traceback.format_exc())
 r['events_sha256']=hashlib.sha256((case/'trace/events.jsonl').read_bytes()).hexdigest();reports.append(r)
 print(case.name,r['status'],r.get('error',''),flush=True)
result=dict(raw_commit='7e5976bb9ee4c54dc5f114ca4392d9f16c202510',status='supported' if all(r['status']=='supported' for r in reports) else 'failed',cases=reports)
(p/'gpu_independent_analysis_v1.json').write_text(json.dumps(result,indent=2)+'\n')
