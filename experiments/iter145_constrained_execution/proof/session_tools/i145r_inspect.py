from i145r_ops import ssh,P
s='''import os,json,glob
from pathlib import Path
r={'cache':{},'metadata':{},'source':{},'aliases':{}}
for root in ['/root/.unified_data_cache','/home/danielwahnich/.unified_data_cache']:
 p=Path(root);entries=[]
 if p.exists():
  for base,dirs,files in os.walk(p,followlinks=False):
   for f in sorted(files):
    q=Path(base)/f;entries.append(dict(path=str(q),size=q.lstat().st_size,symlink=q.is_symlink()))
    if len(entries)>5000:raise RuntimeError('cache inventory cap')
 r['cache'][root]=dict(exists=p.exists(),entries=entries)
for root in ['/datasets/nuscenes-full/v1.0-trainval','/datasets/nuscenes-full/v1.0-mini','/datasets/nuscenes-full/maps']:
 p=Path(root);r['metadata'][root]=[dict(path=str(q),bytes=q.lstat().st_size,symlink=q.is_symlink()) for q in sorted(p.rglob('*')) if q.is_file()] if p.exists() else None
for name in ['dataset.py','maps/map_api.py','caching/df_cache.py','data_structures/scene.py','dataset_specific/nusc/nusc_dataset.py']:
 for lib in glob.glob('/opt/sentinel-stack/HUGSIM/.pixi/envs/default/lib/python*/site-packages/trajdata'):
  p=Path(lib)/name
  if p.exists() and p.stat().st_size<300000:r['source'][str(p)]=p.read_text()
for p in sorted(Path('/datasets/nuscenes-full/hugsim/3DRealCar').glob('*/postprocess/shadow.pth')):
 r['aliases'][str(p)]=os.readlink(p) if p.is_symlink() else 'NOT_A_LINK'
print(json.dumps(r,indent=2))
'''
r=ssh('map_loader_discovery',s,timeout=180);assert r.returncode==0
import json
j=json.loads(r.stdout)
(P/'resume_map_discovery.json').write_text(json.dumps(j,indent=2)+'\n')
S=P/'resume_loader_source';S.mkdir(exist_ok=False)
for path,raw in j['source'].items():(S/path.split('/trajdata/')[1].replace('/','__')).write_text(raw)
print('CACHE',[(k,v['exists'],len(v['entries'])) for k,v in j['cache'].items()]);print('METADATA',[(k,None if v is None else len(v)) for k,v in j['metadata'].items()]);print('SOURCE',list(j['source']))
