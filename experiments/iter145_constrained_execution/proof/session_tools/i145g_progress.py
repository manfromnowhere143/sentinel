import sys,json
from i145g_ops import P,ssh
label='progress_'+sys.argv[1]
s='''import json,os
from pathlib import Path
c=Path('/datasets/nuscenes-full/hugsim/iter145_gpu_20261010');r={}
for name in ['batch.json','batch_entry.log']:
 p=c/name
 if p.exists():r[name]=p.read_text()[-5000:]
r['cases']={}
for p in sorted((c/'runs').glob('*')) if (c/'runs').exists() else []:
 row={}
 for n in ['worker.json','trace/summary.json','client.log']:
  q=p/n
  if q.exists():row[n]=q.read_text()[-4000:]
 q=p/'trace/events.jsonl'
 if q.exists():
  rows=[json.loads(x) for x in q.read_text().splitlines()];row['steps']=sum(x['event']=='step' for x in rows);row['last_event']=rows[-1]['event'] if rows else None
 r['cases'][p.name]=row
for p in c.glob('scene-*.log'):r[p.name]=p.read_text()[-4000:]
print(json.dumps(r,indent=2))
'''
r=ssh(label,s,timeout=60);assert r.returncode==0
j=json.loads(r.stdout);print('STATE',j.get('batch.json'),{k:{'steps':v.get('steps'),'summary':v.get('trace/summary.json'),'worker':v.get('worker.json','')[-500:]} for k,v in j['cases'].items()})
