import io,tarfile,subprocess,hashlib,json,base64
from i145r_ops import R,P,E,ssh
c=subprocess.check_output(['git','rev-parse','research/iter145-constrained-execution'],cwd=R).decode().strip(); paths=['experiments/iter145_constrained_execution/'+n for n in ('assets.py','maps.py','resources.py','ACTOR_FILES.json')]+['experiments/iter144_timed_trajectory/trajectory.py','experiments/iter143_model_contract/proof/case_inventory.json'];b=io.BytesIO();files={}
with tarfile.open(fileobj=b,mode='w') as a:
 for n in paths:
  raw=subprocess.check_output(['git','show',c+':'+n],cwd=R);t=tarfile.TarInfo(n);t.size=len(raw);a.addfile(t,io.BytesIO(raw));files[n]=hashlib.sha256(raw).hexdigest()
raw=b.getvalue();binding=dict(commit=c,files=files,sha256=hashlib.sha256(raw).hexdigest());(P/'resume_map_packet.json').write_text(json.dumps(binding,indent=2)+'\n');(E/'map_packet.tar').write_bytes(raw)
s='''import io,tarfile,base64,hashlib,json,subprocess,time
from pathlib import Path
raw=base64.b64decode(PAYLOAD);assert hashlib.sha256(raw).hexdigest()==HASH
control=Path('/datasets/nuscenes-full/hugsim/iter145_resume_20261010');packet=control/'map_packet';packet.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(raw)) as a:
 for t in a.getmembers():assert t.isfile() and not Path(t.name).is_absolute() and '..' not in Path(t.name).parts
 a.extractall(packet)
for n,h in FILES.items():assert hashlib.sha256((packet/n).read_bytes()).hexdigest()==h
py='/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python'
p=subprocess.run([py,'-m','experiments.iter145_constrained_execution.maps','--output',str(control/'map_inventory.json')],cwd=packet,capture_output=True,text=True,timeout=630)
r=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
if (control/'map_inventory.json').exists():r['map_inventory']=json.loads((control/'map_inventory.json').read_text())
print(json.dumps(r,indent=2))
'''.replace('PAYLOAD',repr(base64.b64encode(raw).decode())).replace('HASH',repr(binding['sha256'])).replace('FILES',repr(files))
r=ssh('full_map_inventory',s,timeout=660);assert r.returncode==0
j=json.loads(r.stdout);(P/'resume_full_map_report.json').write_text(json.dumps(j,indent=2)+'\n');print('MAP_RESULT',j['returncode'],j.get('map_inventory',{}).get('status'),j.get('map_inventory',{}).get('file_count'))
