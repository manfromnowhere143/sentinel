import json,tarfile,hashlib,sys
from pathlib import Path
from i146g_ops import P,E,ssh,run,BASE
arm=sys.argv[1];assert arm in ('nominal','monitor','brake_t0','brake_t2_5')
s='''import json,hashlib,tarfile,stat,subprocess
from pathlib import Path
c=Path('/datasets/nuscenes-full/hugsim/iter146_gpu_20261010');arm=ARM
pair=json.loads((c/(arm+'_pair.json')).read_text());assert pair['status'] in ('completed','failed')
for a in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 p=subprocess.run(a,capture_output=True,text=True,timeout=30);assert p.returncode==0 and not p.stdout.strip(),p.stdout
records={};selected=[]
for folder in sorted((c/'runs').glob('*__'+arm+'__*')):
 for p in sorted(folder.rglob('*')):
  mode=p.lstat().st_mode
  if stat.S_ISFIFO(mode):continue
  assert not p.is_symlink()
  if not p.is_file():continue
  assert p.stat().st_size<=256*1024**2
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024**2),b''):h.update(b)
  rel=str(p.relative_to(c));records[rel]=dict(sha256=h.hexdigest(),bytes=p.stat().st_size)
  if p.suffix in ('.json','.jsonl','.log','.txt'):selected.append(rel)
for p in sorted(c.glob('*')):
 if p.is_file() and (p.name.startswith(arm+'_') or p.name.startswith('scene-0013-easy-00__'+arm+'__') or p.name in ('execution_manifest.json','deployment_report.json','e2e146.py','nuscenes_base.yaml')):selected.append(str(p.relative_to(c)))
inv=arm+'_output_inventory.json';(c/inv).write_text(json.dumps(dict(files=records,total_bytes=sum(r['bytes'] for r in records.values()),selected_files=selected,derived_content='PLY retained on stopped host with complete hashes; display images disabled prospectively.'),indent=2)+'\\n');selected.append(inv)
assert sum((c/name).stat().st_size for name in selected)<100*1024**2
with tarfile.open(c/(arm+'_raw.tar.gz'),'w:gz') as a:
 for name in selected:a.add(c/name,arcname=name,recursive=False)
raw=(c/(arm+'_raw.tar.gz')).read_bytes();print(json.dumps(dict(pair=pair,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),files=len(selected),output_bytes=sum(r['bytes'] for r in records.values()))))
'''.replace('ARM',repr(arm))
r=ssh(arm+'_collect_archive',s,timeout=180);assert r.returncode==0
binding=json.loads(r.stdout);assert binding['bytes']<100*1024**2
r=run(arm+'_collect_download',['gcloud','compute','scp',*BASE,'--tunnel-through-iap','sentinel-gpu:/datasets/nuscenes-full/hugsim/iter146_gpu_20261010/'+arm+'_raw.tar.gz',str(E/(arm+'_raw.tar.gz'))],timeout=180);assert r.returncode==0
raw=(E/(arm+'_raw.tar.gz')).read_bytes();assert hashlib.sha256(raw).hexdigest()==binding['sha256']
dest=P/'gpu_raw'/arm;dest.mkdir(parents=True,exist_ok=False)
with tarfile.open(E/(arm+'_raw.tar.gz'),'r:gz') as a:
 for t in a.getmembers():assert t.isfile() and not Path(t.name).is_absolute() and '..' not in Path(t.name).parts and t.size<=100*1024**2
 a.extractall(dest)
inv=json.loads((dest/(arm+'_output_inventory.json')).read_text())
for name in inv['selected_files']:
 if name in inv['files']:
  p=dest/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==inv['files'][name]['sha256'] and p.stat().st_size==inv['files'][name]['bytes']
(P/('gpu_'+arm+'_collection_receipt.json')).write_text(json.dumps(binding,indent=2)+'\n');print('COLLECTED',arm,binding['bytes'])
