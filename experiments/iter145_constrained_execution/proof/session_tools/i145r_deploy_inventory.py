from pathlib import Path
import io,tarfile,subprocess,json,hashlib,base64,sys
sys.path.insert(0,'/tmp');from i145r_ops import R as ROOT,P as PROOF,E as EXT,ssh
commit='1d64318392a2e911ea05fee79341ab85801c7857'
paths=['experiments/iter145_constrained_execution/ACTOR_FILES.json','experiments/iter145_constrained_execution/assets.py','experiments/iter145_constrained_execution/resources.py','experiments/iter144_timed_trajectory/trajectory.py','experiments/iter143_model_contract/proof/case_inventory.json']
buf=io.BytesIO();hashes={}
prior=json.loads((ROOT/'experiments/iter142_nominal_continuation_completion/proof/runtime_manifest.json').read_text())
expected={}
for path,digest in prior['files'].items():
 if not path.startswith('/opt/sentinel-stack/'):continue
 if path.endswith('/ckpts/uniad_base_e2e.pth'):role='planner_checkpoint'
 elif path.endswith('/configs/sim/nuscenes_camera.yaml'):role='camera_config'
 elif path.endswith('/configs/sim/kinematic.yaml'):role='kinematic_config'
 else:role='runtime_source'
 expected[path]=dict(role=role,sha256=digest)
with tarfile.open(fileobj=buf,mode='w') as tar:
 for name in paths:
  raw=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT);entry=tarfile.TarInfo(name);entry.size=len(raw);entry.mode=0o644;tar.addfile(entry,io.BytesIO(raw));hashes[name]=hashlib.sha256(raw).hexdigest()
 raw=json.dumps(expected,indent=2).encode();entry=tarfile.TarInfo('expected_runtime.json');entry.size=len(raw);entry.mode=0o644;tar.addfile(entry,io.BytesIO(raw));hashes['expected_runtime.json']=hashlib.sha256(raw).hexdigest()
raw=buf.getvalue();(EXT/'inspection_packet.tar').write_bytes(raw);binding=dict(commit=commit,files=hashes,packet_sha256=hashlib.sha256(raw).hexdigest(),runtime_files=len(expected));(PROOF/'resume_inspection_source_packet.json').write_text(json.dumps(binding,indent=2)+'\n')
s='''import io,tarfile,base64,hashlib,json
from pathlib import Path
raw=base64.b64decode(PAYLOAD);assert hashlib.sha256(raw).hexdigest()==DIGEST
control=Path('/datasets/nuscenes-full/hugsim/iter145_resume_20261010');control.mkdir(exist_ok=False);packet=control/'inspection_packet';packet.mkdir()
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
 for item in archive.getmembers():
  p=Path(item.name);assert not p.is_absolute() and '..' not in p.parts and item.isfile()
 archive.extractall(packet)
for name,digest in HASHES.items():assert hashlib.sha256((packet/name).read_bytes()).hexdigest()==digest
print(json.dumps(dict(control=str(control),packet_sha256=DIGEST,files=len(HASHES))))
'''.replace('PAYLOAD',repr(base64.b64encode(raw).decode())).replace('DIGEST',repr(binding['packet_sha256'])).replace('HASHES',repr(hashes))
r=ssh('inspection_deployment',s,timeout=120);assert r.returncode==0
s='''import subprocess,json,time,shutil
from pathlib import Path
packet=Path('/datasets/nuscenes-full/hugsim/iter145_resume_20261010/inspection_packet')
argv=['/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python','-m','experiments.iter145_constrained_execution.assets','--inventory',str(packet/'experiments/iter143_model_contract/proof/case_inventory.json'),'--runtime-files',str(packet/'expected_runtime.json'),'--actor-files',str(packet/'experiments/iter145_constrained_execution/ACTOR_FILES.json'),'--image-id','sha256:2fc5cd574b7510c813fecee64d5568fddec8255a4b638dbca758b67696cb1d14','--output',str(packet.parent/'asset_inventory.json')]
start=time.time();r=subprocess.run(argv,cwd=packet,capture_output=True,text=True,timeout=600)
report=dict(argv=argv,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed_seconds=time.time()-start)
if (packet.parent/'asset_inventory.json').exists():report['inventory']=json.loads((packet.parent/'asset_inventory.json').read_text())
report['free_gib']=shutil.disk_usage('/datasets/nuscenes-full').free/2**30
print(json.dumps(report,indent=2))
'''
r=ssh('asset_inspection145',s,timeout=660);assert r.returncode==0
report=json.loads(r.stdout);(PROOF/'resume_asset_inspection_report.json').write_text(json.dumps(report,indent=2)+'\n');print('ASSET_STATUS',report.get('inventory',{}).get('status'),report['returncode'])
