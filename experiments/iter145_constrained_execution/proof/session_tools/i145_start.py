import json,sys,time
sys.path.insert(0,'/tmp');from i145_hostops import run,BASE,PROOF,EXT
r=run('host_before_start',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,machineType,guestAccelerators)']);assert r.returncode==0;before=json.loads(r.stdout);assert before['id']=='3834622546652649531' and before['status']=='TERMINATED'
r=run('host_start_request',['gcloud','compute','instances','start','sentinel-gpu',*BASE,'--async','--quiet','--format=json']);assert r.returncode==0
op=json.loads(r.stdout)[0]
for i in range(1,31):
 r=run('host_start_poll_'+str(i),['gcloud','compute','operations','describe',op['name'],*BASE,'--format=json']);assert r.returncode==0;op=json.loads(r.stdout)
 if op['status']=='DONE':break
 time.sleep(5)
else:raise RuntimeError('start completion unavailable')
(PROOF/'host_start_operation.json').write_text(json.dumps(op,indent=2)+'\n')
assert 'error' not in op and 'httpErrorStatusCode' not in op,'start failed; no retry'
r=run('host_ready',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,name,status,machineType,zone,lastStartTimestamp,guestAccelerators)']);assert r.returncode==0;j=json.loads(r.stdout);assert j['id']=='3834622546652649531' and j['status']=='RUNNING'
(PROOF/'host_ready_instance.json').write_text(json.dumps(j,indent=2)+'\n')
