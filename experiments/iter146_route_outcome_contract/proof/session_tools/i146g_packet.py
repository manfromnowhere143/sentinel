from pathlib import Path
import json,subprocess,hashlib,tarfile,io
R=Path('/Users/danielwahnich/workspace/sentinel');D=R/'experiments/iter146_route_outcome_contract';P=D/'proof';E=Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter146-gpu-20261010');E.mkdir(exist_ok=False)
c=subprocess.check_output(['git','rev-parse','research/iter146-route-outcome-contract'],cwd=R).decode().strip();assert c=='9f78e514000f94ab069e846a7b6796009702a223'
old=R/'experiments/iter145_constrained_execution';paths=set(json.loads((old/'proof/simulator_source_packet.json').read_text())['files'])
for d in (old,D):paths.update(str(p.relative_to(R)) for p in d.glob('*.py'))
paths.add('experiments/iter145_constrained_execution/ACTOR_FILES.json')
b=io.BytesIO();records={}
with tarfile.open(fileobj=b,mode='w:gz') as tar:
 for name in sorted(paths):
  raw=subprocess.check_output(['git','show',c+':'+name],cwd=R);assert (R/name).read_bytes()==raw,name
  t=tarfile.TarInfo('packet/'+name);t.size=len(raw);tar.addfile(t,io.BytesIO(raw));records['packet/'+name]=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 for name,raw in [('asset_inventory.json',json.dumps(json.loads((old/'proof/resume_complete_asset_report.json').read_text())['inventory']).encode()),('map_inventory.json',json.dumps(json.loads((old/'proof/resume_full_map_report.json').read_text())['map_inventory']).encode())]:
  t=tarfile.TarInfo(name);t.size=len(raw);tar.addfile(t,io.BytesIO(raw));records[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
raw=b.getvalue();(E/'gpu_packet.tar.gz').write_bytes(raw);(P/'gpu_source_packet.json').write_text(json.dumps(dict(commit=c,files=records,packet_sha256=hashlib.sha256(raw).hexdigest(),packet_bytes=len(raw)),indent=2)+'\n');print(c,len(paths),len(raw))
