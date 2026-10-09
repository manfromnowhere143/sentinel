import json
import os
import pathlib
import shutil
import subprocess
import time
import hashlib
root=pathlib.Path('/opt/sentinel-stack/HUGSIM')
commands={
 'hugsim_commit':['git','-C',str(root),'rev-parse','HEAD'],
 'containers':['docker','ps','--format','{{.ID}} {{.Names}}'],
 'gpu_processes':['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],
 'processes':['ps','-eo','pid,etimes,pcpu,comm'],
 'python':[str(root/'.pixi/envs/default/bin/python'),'-c',"import sys,numpy,importlib.util; print(sys.version); print(numpy.__version__); print('pytest',importlib.util.find_spec('pytest')); print('threadpoolctl',importlib.util.find_spec('threadpoolctl'))"]}
report=dict(host_utc=time.time(),hostname=os.uname().nodename,affinity=sorted(os.sched_getaffinity(0)),free_gib=shutil.disk_usage('/datasets/nuscenes-full').free/2**30)
for name,cmd in commands.items():
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=30);report[name]=dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
assert report['hugsim_commit']['stdout'].strip()=='62c690d39fd90020e68a196bd8bcc1c4d4191f2e'
assert report['containers']['returncode']==0 and not report['containers']['stdout'].strip()
assert report['gpu_processes']['returncode']==0 and not report['gpu_processes']['stdout'].strip()
assert report['free_gib']>15
source={}
for n in ['sim/ilqr/lqr.py','sim/ilqr/lqr_solver.py','sim/ilqr/utils.py','sim/utils/sim_utils.py']:
 source[n]=hashlib.sha256((root/n).read_bytes()).hexdigest()
report['source_sha256']=source
r=subprocess.run(['systemd-run','--unit=sentinel-iter137-budget','--on-active='+str(max(1, min(3240, int(1791554138.290096-time.time()-60))))+'s','/sbin/shutdown','-h','now'],capture_output=True,text=True)
report['shutdown_timer']=dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
print(json.dumps(report,indent=2));assert r.returncode==0
