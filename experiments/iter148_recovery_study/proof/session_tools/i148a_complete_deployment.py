import json,ast
from i148a_ops import P,E,R,BASE,run
ready=json.loads((P/'gpu_ready_instance.json').read_text());assert ready['status']=='RUNNING' and ready['id']=='3834622546652649531'
binding=json.loads((P/'gpu_source_packet.json').read_text())
# Reuse the retained, substituted deployment body after verified archive extraction.
original=(P/'gpu_deployment.py.txt').read_text()
continuation=original[original.index('from experiments.iter145_constrained_execution.resources import file_identity'):]
prefix='''import io,tarfile,hashlib,base64,json,os,shutil,subprocess,sys,time
from pathlib import Path
control=Path('/datasets/nuscenes-full/hugsim/iter148_study_20261011');packet=control/'packet'
assert control.is_dir() and not control.is_symlink() and packet.is_dir()
assert not list(control.glob('pair_*'))
for n in ('runs','map_cache','e2e147.py','nuscenes_base.yaml','plan.json','execution_manifest.json','deployment_report.json','deployment_continuation_started.json'):
 assert not (control/n).exists(),n
for name,row in RECORDS.items():
 p=control/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],name
with (control/'deployment_continuation_started.json').open('x') as f:json.dump(dict(reason='host interpreter missing scipy; use existing qualified simulator interpreter before any study initialization',source_commit=COMMIT),f)
sys.path.insert(0,str(packet))
'''.replace('RECORDS',repr(binding['files'])).replace('COMMIT',repr(binding['commit']))
s=prefix+continuation;ast.parse(s)
(P/'gpu_deployment_continuation.py.txt').write_text(s)
r=run('deployment_continuation',['gcloud','compute','ssh','sentinel-gpu',*BASE,'--tunnel-through-iap','--command','sudo -n /opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python -'],600,s.encode());assert r.returncode==0
j=json.loads(r.stdout);(P/'gpu_deployment_report.json').write_text(json.dumps(j,indent=2)+'\n');assert j['status']=='supported'
print('DEPLOYMENT',j['status'],j['manifest_sha256'])
