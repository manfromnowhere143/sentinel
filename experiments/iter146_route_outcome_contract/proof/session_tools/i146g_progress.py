import json,sys
from i146g_ops import ssh
label=sys.argv[1]
s='''import json
from pathlib import Path
c=Path('/datasets/nuscenes-full/hugsim/iter146_gpu_20261010');r=dict(pairs={},runs={})
for p in c.glob('*_pair.json'):r['pairs'][p.stem]=json.loads(p.read_text())
for p in sorted((c/'runs').glob('*')):
 v={}
 for n in ['worker.json','trace/summary.json']:
  if (p/n).exists():
   j=json.loads((p/n).read_text());v[n]={k:j[k] for k in ('status','steps','stop_reason','outcome','elapsed_seconds') if k in j}
 if (p/'trace/events.jsonl').exists():
  lines=(p/'trace/events.jsonl').read_text().splitlines();rows=[]
  for l in lines:
   try:rows.append(json.loads(l))
   except ValueError:pass
  v['steps']=sum(x['event']=='step' for x in rows);v['last_event']=rows[-1]['event'] if rows else None
 v['client_tail']=(p/'client.log').read_text()[-400:] if (p/'client.log').exists() else None
 r['runs'][p.name]=v
for p in c.glob('*_entry.log'):r[p.name]=p.read_text()[-800:]
for p in c.glob('scene*.log'):r[p.name]=p.read_text()[-1200:]
print(json.dumps(r,indent=2))
'''
r=ssh('progress_'+label,s,timeout=90);assert r.returncode==0
