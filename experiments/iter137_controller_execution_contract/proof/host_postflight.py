import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
root=Path('/datasets/nuscenes-full/hugsim/iter137_controller_20261009')
manifest=json.loads((root/'deployment.json').read_text())
changed=[n for n,h in manifest['files'].items() if hashlib.sha256((root/'packet'/n).read_bytes()).hexdigest()!=h]
active=[]
for p in Path('/proc').glob('[0-9]*/cmdline'):
 try:
  argv=p.read_bytes().split(b'\0')
  if any(x.endswith(b'/benchmark.py') for x in argv): active.append(p.parent.name)
 except (FileNotFoundError,PermissionError,ProcessLookupError): pass
report=dict(host_utc=time.time(),changed_packet_files=changed,bound_file_count=len(manifest['files']),active_benchmark_processes=active,free_gib=shutil.disk_usage(root).free/2**30)
for name,cmd in {'containers':['docker','ps','--format','{{.ID}} {{.Names}}'],'gpu_processes':['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],'processes':['ps','-eo','pid,etimes,pcpu,comm']}.items():
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=20)
 report[name]=dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
assert not changed and not active
assert report['containers']['returncode']==0 and not report['containers']['stdout'].strip()
assert report['gpu_processes']['returncode']==0 and not report['gpu_processes']['stdout'].strip()
r=subprocess.run(['systemctl','stop','sentinel-iter137-budget.timer'],capture_output=True,text=True)
report['cancel_owned_timer']=dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
print(json.dumps(report,indent=2));assert r.returncode==0
