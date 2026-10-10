from i145g_ops import R,P,ssh
import subprocess,json,base64,hashlib
c=subprocess.check_output(['git','rev-parse','research/iter145-constrained-execution'],cwd=R).decode().strip();updates={}
for n in ('gpu.py','gpu_batch.py'):
 name='experiments/iter145_constrained_execution/'+n;raw=subprocess.check_output(['git','show',c+':'+name],cwd=R);updates[name]=dict(raw=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
s='''import json,hashlib,base64,subprocess,os,shutil
from pathlib import Path
control=Path('/datasets/nuscenes-full/hugsim/iter145_gpu_20261010');packet=control/'packet';before=(control/'execution_manifest.json').read_bytes();manifest=json.loads(before)
archive=control/'before_output_guards';archive.mkdir(exist_ok=False);(archive/'execution_manifest.json').write_bytes(before)
for name,record in UPDATES.items():
 p=packet/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['files'][str(p)]['sha256']
 (archive/p.name).write_bytes(p.read_bytes());raw=base64.b64decode(record['raw']);assert hashlib.sha256(raw).hexdigest()==record['sha256'];p.write_bytes(raw);manifest['files'][str(p)]={k:record[k] for k in ['sha256','bytes']}
manifest['source_patches']=[dict(commit=COMMIT,files={k:{f:r[f] for f in ['sha256','bytes']} for k,r in UPDATES.items()})]
manifest['parent_manifest_sha256']=hashlib.sha256(before).hexdigest();(control/'execution_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
py='/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python';env=os.environ.copy();env.update(PYTHONPATH=str(packet)+':/opt/sentinel-stack/HUGSIM')
code="""import json,subprocess
from pathlib import Path
from experiments.iter145_constrained_execution.gpu import client_command,cleanup_client
c=Path('/datasets/nuscenes-full/hugsim/iter145_gpu_20261010');o=c/'client_preflight';o.mkdir(exist_ok=False)
a=client_command(c,o,'preflight');index=a.index('tools/closeloop/e2e145.py');a=a[:index+1]+['--help']
try:
 p=subprocess.run(a,capture_output=True,text=True,timeout=90);r=dict(argv=a,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
finally: cleanup_client('preflight')
print(json.dumps(r))
"""
p=subprocess.run([py,'-c',code],cwd='/opt/sentinel-stack/HUGSIM',env=env,capture_output=True,text=True,timeout=150)
report=dict(source_patch_commit=COMMIT,manifest_sha256=hashlib.sha256((control/'execution_manifest.json').read_bytes()).hexdigest(),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
if p.returncode==0:report['client_preflight']=json.loads(p.stdout)
(control/'client_preflight.json').write_text(json.dumps(report,indent=2)+'\\n');print(json.dumps(report,indent=2))
'''.replace('UPDATES',repr(updates)).replace('COMMIT',repr(c))
r=ssh('source_patch_and_client_preflight',s,timeout=180);assert r.returncode==0
j=json.loads(r.stdout);(P/'gpu_source_patch_report.json').write_text(json.dumps(j,indent=2)+'\n');print('CLIENT_PREFLIGHT',j['returncode'],j.get('client_preflight',{}).get('returncode'),j['manifest_sha256'])
