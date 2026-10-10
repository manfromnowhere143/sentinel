import json,sys
sys.path.insert(0,'/tmp');from i145_hostops import EXT,ssh,PROOF
budget=json.loads((EXT/'inspection_budget.json').read_text())
s='''import os,json,subprocess,time,shutil
r=dict(hostname=os.uname().nodename,epoch=time.time(),free_gib=shutil.disk_usage('/datasets/nuscenes-full').free/2**30)
assert r['hostname'].split('.')[0]=='sentinel-gpu'
for name,argv in {'containers':['docker','ps','--format','{{.ID}} {{.Names}}'],'gpu_processes':['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],'processes':['ps','-eo','pid,etimes,pcpu,comm'],'gpu':['nvidia-smi','--query-gpu=name,memory.total,memory.free,driver_version','--format=csv,noheader']}.items():
 p=subprocess.run(argv,capture_output=True,text=True,timeout=30);r[name]=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
assert r['containers']['returncode']==0 and not r['containers']['stdout'].strip()
assert r['gpu_processes']['returncode']==0 and not r['gpu_processes']['stdout'].strip()
assert r['free_gib']>=100 and r['free_gib']-1>=25
remaining=int(DEADLINE-time.time()-60);assert remaining>300
p=subprocess.run(['systemd-run','--unit=sentinel-iter145-budget','--on-active='+str(remaining)+'s','/sbin/shutdown','-h','now'],capture_output=True,text=True,timeout=30);r['shutdown_timer']=dict(returncode=p.returncode,seconds=remaining,stdout=p.stdout,stderr=p.stderr);assert p.returncode==0
p=subprocess.run(['systemctl','show','sentinel-iter145-budget.timer','--property=ActiveState,NextElapseUSecMonotonic,TimersMonotonic'],capture_output=True,text=True,timeout=30);r['timer_readback']=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr);assert p.returncode==0 and 'ActiveState=active' in p.stdout
print(json.dumps(r,indent=2))
'''.replace('DEADLINE',repr(budget['deadline_epoch']))
r=ssh('host_preflight145',s,timeout=120);assert r.returncode==0
(PROOF/'host_preflight145_receipt.json').write_text(r.stdout.decode())
