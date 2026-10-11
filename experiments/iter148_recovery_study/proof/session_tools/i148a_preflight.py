import json,time
from i148a_ops import E,P,ssh

for _ in range(120):
 if (P/'gpu_ready_instance.json').exists():break
 time.sleep(1)
else:raise RuntimeError('start identity unavailable')
time.sleep(15)
b=json.loads((E/'budget.json').read_text());remaining=int(b['deadline_monotonic']-time.monotonic()-60);assert remaining>300
s='''import os,json,subprocess,time,shutil
from pathlib import Path
r=dict(hostname=os.uname().nodename,host_epoch=time.time(),free_gib=shutil.disk_usage('/datasets/nuscenes-full').free/2**30,meminfo=Path('/proc/meminfo').read_text())
assert r['hostname'].split('.')[0]=='sentinel-gpu'
for k,a in {'containers':['docker','ps','--format','{{.ID}} {{.Names}}'],'gpu_processes':['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],'gpu':['nvidia-smi','--query-gpu=name,memory.total,memory.free,driver_version','--format=csv,noheader']}.items():
 p=subprocess.run(a,capture_output=True,text=True,timeout=30);r[k]=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr);assert p.returncode==0
assert not r['containers']['stdout'].strip() and not r['gpu_processes']['stdout'].strip() and r['free_gib']>=100
p=subprocess.run(['systemd-run','--unit=sentinel-iter148-block000-attempt002-budget','--on-active=REMAININGs','/sbin/shutdown','-h','now'],capture_output=True,text=True,timeout=30);r['timer']=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr);assert p.returncode==0
p=subprocess.run(['systemctl','show','sentinel-iter148-block000-attempt002-budget.timer','--property=ActiveState,NextElapseUSecMonotonic,TimersMonotonic'],capture_output=True,text=True,timeout=30);r['timer_readback']=p.stdout;assert p.returncode==0 and 'ActiveState=active' in p.stdout
print(json.dumps(r,indent=2))
'''.replace('REMAINING',str(remaining))
for i in range(3):
 r=ssh('preflight_'+str(i),s,timeout=90)
 if r.returncode==0:break
 # Retry boot transport only, never a failed remote assertion or timer setup.
 if r.returncode != 255 or b'Failed to connect to port 22' not in r.stderr:break
 time.sleep(10)
assert r.returncode==0
(P/'gpu_preflight_receipt.json').write_bytes(r.stdout)
