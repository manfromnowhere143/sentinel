import json,sys,time,datetime
sys.path.insert(0,'/tmp');from i145_hostops import EXT,BASE,run
budget=json.loads((EXT/'inspection_budget.json').read_text())
while time.time()<budget['deadline_epoch']:
 if (EXT/'inspection_cleanup_verified.json').exists():print('watchdog cancelled after verified cleanup',flush=True);sys.exit(0)
 time.sleep(min(5.,max(.1,budget['deadline_epoch']-time.time())))
r=run('watchdog_instance',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStartTimestamp)']);assert r.returncode==0
state=json.loads(r.stdout);assert state['id']=='3834622546652649531'
if state['status']=='TERMINATED':sys.exit(0)
started=datetime.datetime.fromisoformat(state['lastStartTimestamp']).timestamp();assert budget['start_epoch']-30<=started<=budget['deadline_epoch'],'not owned start'
r=run('watchdog_stop',['gcloud','compute','instances','stop','sentinel-gpu',*BASE,'--quiet','--format=json'],timeout=120);assert r.returncode==0
r=run('watchdog_stopped',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStopTimestamp)']);assert r.returncode==0 and json.loads(r.stdout)['status']=='TERMINATED'
(EXT/'inspection_cleanup_verified.json').write_text(r.stdout.decode());print('watchdog verified stopped',flush=True)
