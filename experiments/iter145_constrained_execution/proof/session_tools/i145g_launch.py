import json,time,shutil
from i145g_ops import P,E,ssh,run,BASE
pre=json.loads((P/'gpu_mount_correction_report.json').read_text());assert pre['client_preflight_v2']['returncode']==0
remaining=json.loads((E/'budget.json').read_text())['deadline_monotonic']-time.monotonic();assert remaining>4980,remaining
r=run('launch_identity',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStartTimestamp)']);assert r.returncode==0
j=json.loads(r.stdout);ready=json.loads((P/'gpu_ready_instance.json').read_text());assert j['id']==ready['id'] and j['status']=='RUNNING' and j['lastStartTimestamp']==ready['lastStartTimestamp']
s='''import json,sys,time,os,subprocess,shutil,hashlib
from pathlib import Path
control=Path('/datasets/nuscenes-full/hugsim/iter145_gpu_20261010');packet=control/'packet';sys.path.insert(0,str(packet))
from experiments.iter145_constrained_execution.resources import HOST,resource_gate
assert hashlib.sha256((control/'execution_manifest.json').read_bytes()).hexdigest()==MANIFEST
obs=dict(HOST,observation_kind='host_readback',state='RUNNING',local_free_gib=LOCALFREE,remote_free_gib=shutil.disk_usage(control).free/2**30)
for k,a in {'containers':['docker','ps','-q'],'gpu_processes':['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']}.items():
 p=subprocess.run(a,capture_output=True,text=True,timeout=30);assert p.returncode==0;obs[k]=p.stdout.splitlines()
assert not obs['containers'] and not obs['gpu_processes']
armed=time.time();p=subprocess.run(['systemd-run','--unit=sentinel-iter145-gpu-execution','--on-active=4950s','/sbin/shutdown','-h','now'],capture_output=True,text=True,timeout=30);assert p.returncode==0
q=subprocess.run(['systemctl','show','sentinel-iter145-gpu-execution.timer','--property=ActiveState,NextElapseUSecMonotonic,TimersMonotonic'],capture_output=True,text=True,timeout=30);assert q.returncode==0 and 'ActiveState=active' in q.stdout
obs.update(observed_epoch=time.time(),owned_shutdown_epoch=armed+4950,shutdown_owner='sentinel.iter145')
envelope=dict(max_output_gib=8,max_seconds=4800,hourly_upper_usd=3,max_cost_usd=4.5,capacity_attempts=1,smoke_attempts=1,source_commit=SOURCE,cleanup_owner='sentinel.iter145',price_source_sha256=PRICE)
resource_gate(obs,envelope,now=time.time())
report=dict(status='supported',observation=obs,envelope=envelope,timer_readback=q.stdout)
(control/'resource_admission.json').write_text(json.dumps(report,indent=2)+'\\n')
py='/opt/sentinel-stack/HUGSIM/.pixi/envs/default/bin/python';env=os.environ.copy();env.update(PYTHONPATH=str(packet)+':/opt/sentinel-stack/HUGSIM',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
a=[py,'-u','-m','experiments.iter145_constrained_execution.gpu_batch','--control',str(control),'--manifest-sha256',MANIFEST]
with (control/'batch_entry.log').open('xb') as log:p=subprocess.Popen(a,cwd='/opt/sentinel-stack/HUGSIM',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
report.update(pid=p.pid,argv=a,started_epoch=time.time());(control/'launch.json').write_text(json.dumps(report,indent=2)+'\\n');print(json.dumps(report,indent=2))
'''.replace('MANIFEST',repr(pre['manifest_sha256'])).replace('LOCALFREE',repr(shutil.disk_usage('/Users/danielwahnich/workspace/sentinel').free/2**30)).replace('SOURCE',repr('1202c067739ede3b301a4fc6d53bf4bdd6bd134f')).replace('PRICE',repr(json.loads((P/'resume_price_binding.json').read_text())['html_sha256']))
r=ssh('batch_launch',s,timeout=90);assert r.returncode==0
(P/'gpu_launch_report.json').write_bytes(r.stdout)
