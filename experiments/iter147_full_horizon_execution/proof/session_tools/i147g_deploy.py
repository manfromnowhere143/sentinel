from i147g_ops import R,P,E,ssh
import json,base64
binding=json.loads((P/'gpu_source_packet.json').read_text());raw=(E/'gpu_packet.tar.gz').read_bytes()
s='''import io,tarfile,hashlib,base64,json,os,shutil,subprocess,sys,time
from pathlib import Path
control=Path('/datasets/nuscenes-full/hugsim/iter147_gpu_20261010');control.mkdir(exist_ok=False)
raw=base64.b64decode(PAYLOAD);assert hashlib.sha256(raw).hexdigest()==DIGEST
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as a:
 for t in a.getmembers():assert t.isfile() and not Path(t.name).is_absolute() and '..' not in Path(t.name).parts
 a.extractall(control)
for n,r in RECORDS.items():assert hashlib.sha256((control/n).read_bytes()).hexdigest()==r['sha256'] and (control/n).stat().st_size==r['bytes']
packet=control/'packet';sys.path.insert(0,str(packet))
from experiments.iter145_constrained_execution.resources import file_identity
assets=json.loads((control/'asset_inventory.json').read_text());assert assets['status']=='supported'
files={};aliases={}
for name,row in assets['files'].items():
 if row['role'] in ('actor_model','actor_dimensions'):
  aliases[name]=row;name=row['physical_path']
 files[name]=dict(sha256=row['sha256'],bytes=row['bytes'])
# Source cache remains unchanged; the runtime receives an owned copy.
shutil.copytree('/root/.unified_data_cache',control/'map_cache')
for name,row in list(files.items()):
 if name.startswith('/root/.unified_data_cache/'):
  copy=str(control/'map_cache'/Path(name).relative_to('/root/.unified_data_cache'))
  assert file_identity(Path(copy))==row;files[copy]=row
# Generate the narrow client hook from pinned released bytes.
# Use the runtime interpreter for NumPy-dependent imports below.
py='/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python';env=os.environ.copy();env.update(PYTHONPATH=str(packet)+':/opt/sentinel-stack/HUGSIM',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
code="from pathlib import Path;from experiments.iter147_full_horizon_execution.client import instrument;p=Path("+repr(str(packet))+ ");Path("+repr(str(control/'e2e147.py'))+").write_bytes(instrument((p/'experiments/iter145_constrained_execution/source/released_client.py.txt').read_bytes()))"
p=subprocess.run([py,'-c',code],cwd=packet,env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
base='realcar_path: /datasets/nuscenes-full/hugsim/3DRealCar\\nmodel_base: /datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes\\nHD_map:\\n  path: /datasets/nuscenes-full\\n  version: nusc_trainval\\n'
(control/'nuscenes_base.yaml').write_text(base)
for path in packet.rglob('*'):
 if path.is_file() and '__pycache__' not in path.parts:files[str(path)]=file_identity(path,allow_empty=True)
(control/'plan.json').write_bytes((packet/'experiments/iter147_full_horizon_execution/QUALIFICATION_PLAN.json').read_bytes())
for n in ['plan.json','e2e147.py','nuscenes_base.yaml','asset_inventory.json','map_inventory.json']:files[str(control/n)]=file_identity(control/n)
manifest=dict(source_commit=COMMIT,files=files,actor_aliases=aliases,actor_files=json.loads((packet/'experiments/iter145_constrained_execution/ACTOR_FILES.json').read_text()),cases=sorted(set(s['scenario'] for s in json.loads((control/'plan.json').read_text())['slots'])))
(control/'execution_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
report=dict(control=str(control),source_commit=COMMIT,manifest_sha256=file_identity(control/'execution_manifest.json')['sha256'],file_count=len(files),commands=[])
def run(label,a,timeout):
 start=time.monotonic();r=subprocess.run(a,cwd='/opt/sentinel-stack/HUGSIM',env=env,capture_output=True,text=True,timeout=timeout);record=dict(label=label,argv=a,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed_seconds=time.monotonic()-start);report['commands'].append(record);return r.returncode==0
ok=run('environment_import',[py,'-c','from hugsim_env.envs.hug_sim import HUGSimEnv; from experiments.iter147_full_horizon_execution.gpu import worker; print("ENVIRONMENT_IMPORT_PASSED")'],90)
if ok:ok=run('entrypoint_help',[py,'-m','experiments.iter147_full_horizon_execution.pair','--help'],30)
code="from pathlib import Path;import subprocess;from experiments.iter147_full_horizon_execution.gpu import client_command;from experiments.iter145_constrained_execution.resources import IMAGE;c=Path("+repr(str(control))+");o=c/'preflight_output';o.mkdir();cmd=client_command(c,o,'preflight','nominal');cmd=cmd[:cmd.index(IMAGE)+1]+['-u','tools/closeloop/e2e.py','--help'];raise SystemExit(subprocess.run(cmd,timeout=90).returncode)"
if ok:ok=run('client_preflight',[py,'-c',code],120)
report['status']='supported' if ok else 'failed';(control/'deployment_report.json').write_text(json.dumps(report,indent=2)+'\\n');print(json.dumps(report,indent=2))
'''.replace('PAYLOAD',repr(base64.b64encode(raw).decode())).replace('DIGEST',repr(binding['packet_sha256'])).replace('RECORDS',repr(binding['files'])).replace('COMMIT',repr(binding['commit']))
r=ssh('deployment',s,timeout=600);assert r.returncode==0
j=json.loads(r.stdout);(P/'gpu_deployment_report.json').write_text(json.dumps(j,indent=2)+'\n');print('DEPLOYMENT',j['status'],j['manifest_sha256'])
