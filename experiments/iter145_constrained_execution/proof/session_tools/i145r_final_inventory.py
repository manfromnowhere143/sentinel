from i145r_ops import ssh,P
import json
s='''import subprocess,json,time,importlib.metadata
from pathlib import Path
control=Path('/datasets/nuscenes-full/hugsim/iter145_resume_20261010');packet=control/'map_packet';py='/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python'
a=[py,'-m','experiments.iter145_constrained_execution.assets','--inventory',str(packet/'experiments/iter143_model_contract/proof/case_inventory.json'),'--runtime-files',str(control/'inspection_packet/expected_runtime.json'),'--actor-files',str(packet/'experiments/iter145_constrained_execution/ACTOR_FILES.json'),'--map-binding',str(control/'map_inventory.json'),'--image-id','sha256:2fc5cd574b7510c813fecee64d5568fddec8255a4b638dbca758b67696cb1d14','--output',str(control/'asset_inventory_complete.json')]
b=time.monotonic();p=subprocess.run(a,cwd=packet,capture_output=True,text=True,timeout=660);r=dict(argv=a,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,elapsed_seconds=time.monotonic()-b)
if (control/'asset_inventory_complete.json').exists():r['inventory']=json.loads((control/'asset_inventory_complete.json').read_text())
v=subprocess.run([py,'-c',"import sys,json,importlib.metadata as m;print(json.dumps(dict(python=sys.version,packages={k:m.version(k) for k in ['numpy','scipy','torch','trajdata','shapely','gymnasium','omegaconf']})))"],capture_output=True,text=True,timeout=30);r['runtime_versions']=dict(returncode=v.returncode,stdout=v.stdout,stderr=v.stderr)
print(json.dumps(r,indent=2))
'''
r=ssh('complete_asset_inventory',s,timeout=720);assert r.returncode==0
j=json.loads(r.stdout);(P/'resume_complete_asset_report.json').write_text(json.dumps(j,indent=2)+'\n');print('ASSET_CLOSURE',j['returncode'],j.get('inventory',{}).get('status'),len(j.get('inventory',{}).get('files',{})))
