import json,tarfile,hashlib,subprocess
from pathlib import Path
from i145g_ops import P,E,ssh,run,BASE
s='''import json,hashlib,tarfile,stat,subprocess,os
from pathlib import Path
c=Path('/datasets/nuscenes-full/hugsim/iter145_gpu_20261010');batch=json.loads((c/'batch.json').read_text());assert batch['status'] in ('completed','failed')
for a in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 p=subprocess.run(a,capture_output=True,text=True,timeout=30);assert p.returncode==0 and not p.stdout.strip(),p.stdout
records={};selected=[]
for p in sorted((c/'runs').rglob('*')):
 mode=p.lstat().st_mode
 if stat.S_ISFIFO(mode):continue
 assert not p.is_symlink()
 if not p.is_file():continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 rel=str(p.relative_to(c));records[rel]=dict(sha256=h.hexdigest(),bytes=p.stat().st_size)
 if p.suffix in ('.json','.jsonl','.log','.txt'):selected.append(rel)
for p in sorted(c.glob('*')):
 if p.is_file() and (p.suffix in ('.log',) or p.name in ('batch.json','batch_started.json','execution_manifest.json','launch.json','resource_admission.json','e2e145.py','nuscenes_base.yaml') or p.name.endswith('_process.json')):selected.append(str(p.relative_to(c)))
(c/'output_inventory.json').write_text(json.dumps(dict(files=records,total_bytes=sum(r['bytes'] for r in records.values()),selected_files=selected,excluded_content='Derived PLY and visualization images retained on host; their complete hashes and sizes are above.'),indent=2)+'\\n');selected.append('output_inventory.json')
with tarfile.open(c/'retained_raw.tar.gz','w:gz') as a:
 for name in selected:a.add(c/name,arcname=name,recursive=False)
raw=(c/'retained_raw.tar.gz').read_bytes();print(json.dumps(dict(batch=batch,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),files=len(selected),output_bytes=sum(r['bytes'] for r in records.values()))))
'''
r=ssh('collect_archive',s,timeout=180);assert r.returncode==0
binding=json.loads(r.stdout);assert binding['bytes']<100*1024**2
r=run('collect_download',['gcloud','compute','scp',*BASE,'--tunnel-through-iap','sentinel-gpu:/datasets/nuscenes-full/hugsim/iter145_gpu_20261010/retained_raw.tar.gz',str(E/'retained_raw.tar.gz')],timeout=180);assert r.returncode==0
raw=(E/'retained_raw.tar.gz').read_bytes();assert hashlib.sha256(raw).hexdigest()==binding['sha256']
dest=P/'gpu_raw';dest.mkdir(exist_ok=False)
with tarfile.open(E/'retained_raw.tar.gz','r:gz') as a:
 for t in a.getmembers():assert t.isfile() and not Path(t.name).is_absolute() and '..' not in Path(t.name).parts
 a.extractall(dest)
inv=json.loads((dest/'output_inventory.json').read_text())
for name in inv['selected_files']:
 if name in inv['files']:
  p=dest/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==inv['files'][name]['sha256'] and p.stat().st_size==inv['files'][name]['bytes']
(P/'gpu_collection_receipt.json').write_text(json.dumps(binding,indent=2)+'\n');print('COLLECTED',binding)
