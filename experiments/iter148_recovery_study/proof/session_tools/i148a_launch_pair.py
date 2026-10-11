import json,time,hashlib,sys,subprocess,shutil
from i148a_ops import P,E,R,D,ADMISSIONS,BRANCH,ssh,run,BASE
sys.path.insert(0,str(R))
from experiments.iter147_full_horizon_execution.protocol import identity
from experiments.iter148_recovery_study.admission import committed_file,history,basis,remaining_budget,local_capacity,validate_plan
pair=int(sys.argv[1]);assert 0<=pair<4
arm=f'pair_{pair:03d}'
commit=subprocess.check_output(['git','rev-parse',BRANCH],cwd=R,text=True).strip()
plan=json.loads(committed_file(R,commit,D/'STUDY_PLAN.json'));validate_plan(R,plan)
qualification=basis(R)
for n in ['INPUTS.json','QUALIFICATION.json','GPU_BINDING.md']:
 committed_file(R,commit,D/n)
receipts=[json.loads(committed_file(R,commit,ADMISSIONS/f'pair_{i:03d}.json')) for i in range(pair)]
history(plan,receipts,pair)
local_capacity(shutil.disk_usage(R).free)
# The source frozen before compute must still match every deployed packet entry.
binding=json.loads((P/'gpu_source_packet.json').read_text())
for name,row in binding['files'].items():
 if name.startswith('packet/'):
  raw=(R/name.removeprefix('packet/')).read_bytes()
  assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],name
remaining=json.loads((E/'budget.json').read_text())['deadline_monotonic']-time.monotonic();remaining_budget(remaining)
dep=json.loads((P/'gpu_deployment_report.json').read_text());assert dep['status']=='supported' and dep['qualification_sha256']==qualification
r=run(arm+'_launch_identity',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStartTimestamp)']);assert r.returncode==0
actual=json.loads(r.stdout);ready=json.loads((P/'gpu_ready_instance.json').read_text());assert actual['id']==ready['id'] and actual['lastStartTimestamp']==ready['lastStartTimestamp'] and actual['status']=='RUNNING'
remaining=json.loads((E/'budget.json').read_text())['deadline_monotonic']-time.monotonic();remaining_budget(remaining)
permit=dict(pair=pair,block=0,plan_sha256=identity(plan),manifest_sha256=dep['manifest_sha256'],status='supported',history=receipts,qualification_sha256=qualification,remaining_seconds=remaining)
encoded=json.dumps(permit,sort_keys=True).encode();digest=hashlib.sha256(encoded).hexdigest()
s='''import json,subprocess,os,hashlib,sys,time
from pathlib import Path
c=Path('/datasets/nuscenes-full/hugsim/iter148_study_20261011');raw=PERMIT.encode();assert hashlib.sha256(raw).hexdigest()==CLEARANCE
with (c/(ARM+'_clearance.json')).open('xb') as f:f.write(raw)
assert hashlib.sha256((c/'execution_manifest.json').read_bytes()).hexdigest()==MANIFEST
for argv in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 q=subprocess.run(argv,capture_output=True,text=True,timeout=30);assert q.returncode==0 and not q.stdout.strip()
q=subprocess.run(['systemctl','show','sentinel-iter148-block000-attempt002-budget.timer','--property=ActiveState,TimersMonotonic,NextElapseUSecMonotonic'],capture_output=True,text=True,timeout=30);assert q.returncode==0 and 'ActiveState=active' in q.stdout
argv=['/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python','-u','-m','experiments.iter148_recovery_study.pair','--control',str(c),'--manifest-sha256',MANIFEST,'--clearance-sha256',CLEARANCE,'--pair',str(PAIR)]
env=os.environ.copy();env.update(PYTHONPATH=str(c/'packet')+':/opt/sentinel-stack/HUGSIM',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (c/(ARM+'_entry.log')).open('xb') as log:p=subprocess.Popen(argv,cwd='/opt/sentinel-stack/HUGSIM',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
r=dict(arm=ARM,pid=p.pid,argv=argv,manifest_sha256=MANIFEST,clearance_sha256=CLEARANCE,host_timer=q.stdout,started_epoch=time.time(),remaining_provider_seconds=REMAINING);(c/(ARM+'_launch.json')).write_text(json.dumps(r,indent=2)+'\\n');print(json.dumps(r))
'''.replace('PERMIT',repr(encoded.decode())).replace('CLEARANCE',repr(digest)).replace('MANIFEST',repr(dep['manifest_sha256'])).replace('ARM',repr(arm)).replace('PAIR',str(pair)).replace('REMAINING',repr(remaining))
r=ssh(arm+'_launch',s,timeout=90);assert r.returncode==0
(P/('gpu_'+arm+'_launch_report.json')).write_bytes(r.stdout)
