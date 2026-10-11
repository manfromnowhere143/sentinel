import json,tarfile,hashlib,sys
from pathlib import Path
from i148g_ops import P,E,R,RAW,ssh,run,BASE
import shutil
sys.path.insert(0,str(R))
from experiments.iter148_recovery_study.admission import local_capacity
local_capacity(shutil.disk_usage(R).free)
pair=int(sys.argv[1]);assert 0<=pair<4
arm=f'pair_{pair:03d}';attempt=''
s='''import json,hashlib,tarfile,stat,subprocess
from pathlib import Path
c=Path('/datasets/nuscenes-full/hugsim/iter148_study_20261011');arm=ARM
pair=json.loads((c/(arm+'_result.json')).read_text());assert pair['status'] in ('completed','failed')
for a in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 p=subprocess.run(a,capture_output=True,text=True,timeout=30);assert p.returncode==0 and not p.stdout.strip(),p.stdout
records={};selected=[]
plan=json.loads((c/'plan.json').read_text())
for slot in plan['slots'][PAIR*2:PAIR*2+2]:
 folder=c/'runs'/slot['id']
 if not folder.exists():continue
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
 if p.is_file() and (p.name.startswith(arm+'_') or p.name in ('execution_manifest.json','deployment_report.json','plan.json','e2e147.py','nuscenes_base.yaml')):selected.append(str(p.relative_to(c)))
inv=arm+'_output_inventory.json';(c/inv).write_text(json.dumps(dict(files=records,total_bytes=sum(r['bytes'] for r in records.values()),selected_files=selected,derived_content='PLY retained on stopped host with complete hashes; display images disabled prospectively.'),indent=2)+'\\n');selected.append(inv)
assert sum((c/name).stat().st_size for name in selected)<512*1024**2
with tarfile.open(c/(arm+'_raw.tar.gz'),'w:gz') as a:
 for name in selected:a.add(c/name,arcname=name,recursive=False)
raw=(c/(arm+'_raw.tar.gz')).read_bytes();print(json.dumps(dict(pair=pair,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),files=len(selected),output_bytes=sum(r['bytes'] for r in records.values()))))
'''.replace('ARM',repr(arm)).replace('PAIR',str(pair))
r=ssh(arm+'_collect_archive'+attempt,s,timeout=180);assert r.returncode==0
binding=json.loads(r.stdout);assert binding['bytes']<256*1024**2
r=run(arm+'_collect_download'+attempt,['gcloud','compute','scp',*BASE,'--tunnel-through-iap','sentinel-gpu:/datasets/nuscenes-full/hugsim/iter148_study_20261011/'+arm+'_raw.tar.gz',str(E/(arm+'_raw.tar.gz'))],timeout=180);assert r.returncode==0
raw=(E/(arm+'_raw.tar.gz')).read_bytes();assert len(raw)==binding['bytes'] and hashlib.sha256(raw).hexdigest()==binding['sha256']
dest=RAW/arm;dest.mkdir(parents=True,exist_ok=False)
with tarfile.open(E/(arm+'_raw.tar.gz'),'r:gz') as a:
 assert sum(t.size for t in a.getmembers())<512*1024**2
 assert len({t.name for t in a.getmembers()})==len(a.getmembers())
 for t in a.getmembers():assert t.isfile() and not Path(t.name).is_absolute() and '..' not in Path(t.name).parts and t.size<=256*1024**2
 a.extractall(dest)
inv=json.loads((dest/(arm+'_output_inventory.json')).read_text())
for name in inv['selected_files']:
 if name in inv['files']:
  p=dest/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==inv['files'][name]['sha256'] and p.stat().st_size==inv['files'][name]['bytes']
(P/('gpu_'+arm+'_collection_receipt.json')).write_text(json.dumps(binding,indent=2)+'\n');print('COLLECTED',arm,binding['bytes'])
