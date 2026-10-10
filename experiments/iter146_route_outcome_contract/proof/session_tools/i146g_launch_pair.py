import json,time,hashlib,sys
from i146g_ops import P,E,ssh,run,BASE
arm=sys.argv[1];assert arm in ('nominal','monitor','brake_t0','brake_t2_5')
dep=json.loads((P/'gpu_deployment_report.json').read_text());assert dep['status']=='supported'
remaining=json.loads((E/'budget.json').read_text())['deadline_monotonic']-time.monotonic();assert remaining>1300,remaining
r=run(arm+'_launch_identity',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStartTimestamp)']);assert r.returncode==0
actual=json.loads(r.stdout);ready=json.loads((P/'gpu_ready_instance.json').read_text());assert actual['id']==ready['id'] and actual['lastStartTimestamp']==ready['lastStartTimestamp'] and actual['status']=='RUNNING'
permit=dict(arm=arm,manifest_sha256=dep['manifest_sha256'],status='supported')
if arm!='nominal':
 previous=('nominal','monitor','brake_t0','brake_t2_5')[('nominal','monitor','brake_t0','brake_t2_5').index(arm)-1]
 result=json.loads((P/(previous+'_pair_analysis.json')).read_text());assert result['status']=='supported'
 permit.update(prior_arm=previous,raw_commit=result['raw_commit'],replay_sha256=hashlib.sha256((P/(previous+'_pair_analysis.json')).read_bytes()).hexdigest())
encoded=json.dumps(permit,sort_keys=True).encode();digest=hashlib.sha256(encoded).hexdigest()
s='''import json,subprocess,os,hashlib,sys,time
from pathlib import Path
c=Path('/datasets/nuscenes-full/hugsim/iter146_gpu_20261010');raw=PERMIT.encode();assert hashlib.sha256(raw).hexdigest()==CLEARANCE
with (c/(ARM+'_clearance.json')).open('xb') as f:f.write(raw)
assert hashlib.sha256((c/'execution_manifest.json').read_bytes()).hexdigest()==MANIFEST
for argv in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 q=subprocess.run(argv,capture_output=True,text=True,timeout=30);assert q.returncode==0 and not q.stdout.strip()
q=subprocess.run(['systemctl','show','sentinel-iter146-gpu-budget.timer','--property=ActiveState,TimersMonotonic,NextElapseUSecMonotonic'],capture_output=True,text=True,timeout=30);assert q.returncode==0 and 'ActiveState=active' in q.stdout
argv=['/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python','-u','-m','experiments.iter146_route_outcome_contract.gpu_pair','--control',str(c),'--manifest-sha256',MANIFEST,'--clearance-sha256',CLEARANCE,'--arm',ARM]
env=os.environ.copy();env.update(PYTHONPATH=str(c/'packet')+':/opt/sentinel-stack/HUGSIM',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (c/(ARM+'_entry.log')).open('xb') as log:p=subprocess.Popen(argv,cwd='/opt/sentinel-stack/HUGSIM',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
r=dict(arm=ARM,pid=p.pid,argv=argv,manifest_sha256=MANIFEST,clearance_sha256=CLEARANCE,host_timer=q.stdout,started_epoch=time.time(),remaining_provider_seconds=REMAINING);(c/(ARM+'_launch.json')).write_text(json.dumps(r,indent=2)+'\\n');print(json.dumps(r))
'''.replace('PERMIT',repr(encoded.decode())).replace('CLEARANCE',repr(digest)).replace('MANIFEST',repr(dep['manifest_sha256'])).replace('ARM',repr(arm)).replace('REMAINING',repr(remaining))
r=ssh(arm+'_launch',s,timeout=90);assert r.returncode==0
(P/('gpu_'+arm+'_launch_report.json')).write_bytes(r.stdout)
