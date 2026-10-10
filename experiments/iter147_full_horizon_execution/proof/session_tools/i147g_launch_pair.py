import json,time,hashlib,sys
from i147g_ops import P,E,ssh,run,BASE
pair=int(sys.argv[1]);assert 0<=pair<4
arm=f'pair_{pair:03d}'
from pathlib import Path
sys.path.insert(0,str(P.parents[2]))
from experiments.iter147_full_horizon_execution.protocol import identity
plan=json.loads((P.parent/'QUALIFICATION_PLAN.json').read_text())
dep=json.loads((P/'gpu_deployment_report.json').read_text());assert dep['status']=='supported'
remaining=json.loads((E/'budget.json').read_text())['deadline_monotonic']-time.monotonic();assert remaining>2600,remaining
r=run(arm+'_launch_identity',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStartTimestamp)']);assert r.returncode==0
actual=json.loads(r.stdout);ready=json.loads((P/'gpu_ready_instance.json').read_text());assert actual['id']==ready['id'] and actual['lastStartTimestamp']==ready['lastStartTimestamp'] and actual['status']=='RUNNING'
permit=dict(pair=pair,plan_sha256=identity(plan),manifest_sha256=dep['manifest_sha256'],status='supported',previous=None)
if pair:
 path=P/f'pair_{pair-1:03d}_analysis.json';previous=json.loads(path.read_text());assert previous['status']=='supported'
 commit=__import__('subprocess').check_output(['git','rev-parse','research/iter147-full-horizon-execution'],cwd=P.parents[2],text=True).strip()
 assert path.read_bytes()==__import__('subprocess').check_output(['git','show',commit+':'+str(path.relative_to(P.parents[2]))],cwd=P.parents[2])
 permit['previous']=previous
encoded=json.dumps(permit,sort_keys=True).encode();digest=hashlib.sha256(encoded).hexdigest()
s='''import json,subprocess,os,hashlib,sys,time
from pathlib import Path
c=Path('/datasets/nuscenes-full/hugsim/iter147_gpu_20261010');raw=PERMIT.encode();assert hashlib.sha256(raw).hexdigest()==CLEARANCE
with (c/(ARM+'_clearance.json')).open('xb') as f:f.write(raw)
assert hashlib.sha256((c/'execution_manifest.json').read_bytes()).hexdigest()==MANIFEST
for argv in [['docker','ps','-q'],['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']]:
 q=subprocess.run(argv,capture_output=True,text=True,timeout=30);assert q.returncode==0 and not q.stdout.strip()
q=subprocess.run(['systemctl','show','sentinel-iter147-gpu-budget.timer','--property=ActiveState,TimersMonotonic,NextElapseUSecMonotonic'],capture_output=True,text=True,timeout=30);assert q.returncode==0 and 'ActiveState=active' in q.stdout
argv=['/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python','-u','-m','experiments.iter147_full_horizon_execution.pair','--control',str(c),'--manifest-sha256',MANIFEST,'--clearance-sha256',CLEARANCE,'--pair',str(PAIR)]
env=os.environ.copy();env.update(PYTHONPATH=str(c/'packet')+':/opt/sentinel-stack/HUGSIM',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (c/(ARM+'_entry.log')).open('xb') as log:p=subprocess.Popen(argv,cwd='/opt/sentinel-stack/HUGSIM',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
r=dict(arm=ARM,pid=p.pid,argv=argv,manifest_sha256=MANIFEST,clearance_sha256=CLEARANCE,host_timer=q.stdout,started_epoch=time.time(),remaining_provider_seconds=REMAINING);(c/(ARM+'_launch.json')).write_text(json.dumps(r,indent=2)+'\\n');print(json.dumps(r))
'''.replace('PERMIT',repr(encoded.decode())).replace('CLEARANCE',repr(digest)).replace('MANIFEST',repr(dep['manifest_sha256'])).replace('ARM',repr(arm)).replace('PAIR',str(pair)).replace('REMAINING',repr(remaining))
r=ssh(arm+'_launch',s,timeout=90);assert r.returncode==0
(P/('gpu_'+arm+'_launch_report.json')).write_bytes(r.stdout)
