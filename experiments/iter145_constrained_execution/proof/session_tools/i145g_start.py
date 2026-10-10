import time,json,shutil
from i145g_ops import run,P,E,BASE
assert shutil.disk_usage('/Users/danielwahnich/workspace/sentinel').free/2**30>=15
r=run('before_start',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,machineType,guestAccelerators)']);assert r.returncode==0
j=json.loads(r.stdout);assert j['id']=='3834622546652649531' and j['status']=='TERMINATED' and j['machineType'].endswith('/g2-standard-8') and len(j['guestAccelerators'])==1 and j['guestAccelerators'][0]['acceleratorCount']==1 and j['guestAccelerators'][0]['acceleratorType'].endswith('/nvidia-l4')
r=run('start',['gcloud','compute','instances','start','sentinel-gpu',*BASE,'--async','--quiet','--format=json']);assert r.returncode==0
op=json.loads(r.stdout)[0]
for i in range(30):
 r=run('start_poll_'+str(i),['gcloud','compute','operations','describe',op['name'],*BASE,'--format=json']);assert r.returncode==0;op=json.loads(r.stdout)
 if op['status']=='DONE':break
 time.sleep(5)
assert op['status']=='DONE' and 'error' not in op
r=run('ready',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,name,status,machineType,zone,lastStartTimestamp,guestAccelerators)']);assert r.returncode==0
j=json.loads(r.stdout);assert j['id']=='3834622546652649531' and j['status']=='RUNNING'
(P/'gpu_ready_instance.json').write_text(json.dumps(j,indent=2)+'\n')
