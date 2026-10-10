import sys,json,datetime
sys.path.insert(0,'/tmp');from i145_hostops import run,BASE,EXT,PROOF
budget=json.loads((EXT/'inspection_budget.json').read_text())
r=run('inspection_before_stop',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStartTimestamp)']);assert r.returncode==0;j=json.loads(r.stdout);assert j['id']=='3834622546652649531'
if j['status']!='TERMINATED':
 t=datetime.datetime.fromisoformat(j['lastStartTimestamp']).timestamp();assert budget['start_epoch']-30<=t<=budget['deadline_epoch'],'not our start'
 r=run('inspection_stop',['gcloud','compute','instances','stop','sentinel-gpu',*BASE,'--quiet','--format=json'],timeout=120);assert r.returncode==0
r=run('inspection_final_instance',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,name,status,lastStartTimestamp,lastStopTimestamp)']);assert r.returncode==0;j=json.loads(r.stdout);assert j['id']=='3834622546652649531' and j['status']=='TERMINATED'
with (EXT/'inspection_cleanup_verified.json').open('x') as f:json.dump(j,f,indent=2)
(PROOF/'shutdown_verified.json').write_text(json.dumps(j,indent=2)+'\n')
print('CLEANUP_VERIFIED',flush=True)
