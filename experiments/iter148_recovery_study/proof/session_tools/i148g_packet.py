from pathlib import Path
import json,subprocess,hashlib,tarfile,io
from i148g_ops import R,D,P,E,BRANCH
E.mkdir(exist_ok=False)
c=subprocess.check_output(['git','rev-parse',BRANCH],cwd=R,text=True).strip()
paths=set(json.loads((D/'INPUTS.json').read_text())['files'])
paths.update(str(p.relative_to(R)) for p in D.glob('*.py'))
paths.update('experiments/iter148_recovery_study/'+n for n in ['INPUTS.json','QUALIFICATION.json','STUDY_PLAN.json','HYPOTHESIS.md','GPU_BINDING.md'])
b=io.BytesIO();records={}
with tarfile.open(fileobj=b,mode='w:gz') as tar:
 for name in sorted(paths):
  raw=subprocess.check_output(['git','show',c+':'+name],cwd=R);assert (R/name).read_bytes()==raw,name
  t=tarfile.TarInfo('packet/'+name);t.size=len(raw);tar.addfile(t,io.BytesIO(raw));records['packet/'+name]=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 old=R/'experiments/iter145_constrained_execution'
 for name,raw in [('asset_inventory.json',json.dumps(json.loads((old/'proof/resume_complete_asset_report.json').read_text())['inventory']).encode()),('map_inventory.json',json.dumps(json.loads((old/'proof/resume_full_map_report.json').read_text())['map_inventory']).encode())]:
  t=tarfile.TarInfo(name);t.size=len(raw);tar.addfile(t,io.BytesIO(raw));records[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
raw=b.getvalue();assert sum(v['bytes'] for v in records.values())<32*1024**2
(E/'gpu_packet.tar.gz').write_bytes(raw);(P/'gpu_source_packet.json').write_text(json.dumps(dict(commit=c,files=records,packet_sha256=hashlib.sha256(raw).hexdigest(),packet_bytes=len(raw)),indent=2)+'\n');print(c,len(paths),len(raw))
