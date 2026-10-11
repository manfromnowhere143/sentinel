import datetime,json,pathlib,subprocess,time
R=pathlib.Path('/Users/danielwahnich/workspace/sentinel'); D=R/'experiments/iter148_recovery_study'; P=D/'proof/block_000'; E=pathlib.Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter148-block000-20261011')
BASE=['--project','sunlit-unison-487018-b0','--zone','us-west1-a']
def run(name,argv,timeout=60,stdin=None):
 paths=[P/('gpu_'+name+s) for s in ('.stdout','.stderr','.json')]; assert not any(p.exists() for p in paths)
 start=time.monotonic();epoch=time.time()
 try:r=subprocess.run(argv,input=stdin,cwd=R,capture_output=True,timeout=timeout)
 except subprocess.TimeoutExpired as ex:r=subprocess.CompletedProcess(argv,124,ex.stdout or b'',(ex.stderr or b'')+b'CLIENT_TIMEOUT')
 paths[0].write_bytes(r.stdout);paths[1].write_bytes(r.stderr);paths[2].write_text(json.dumps(dict(argv=argv,start_utc=datetime.datetime.fromtimestamp(epoch,datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,returncode=r.returncode),indent=2)+'\n')
 print(name,r.returncode,r.stdout.decode()[-1200:],r.stderr.decode()[-600:],flush=True);return r
def ssh(name,script,timeout=300):
 ready=json.loads((P/'gpu_ready_instance.json').read_text());assert ready['id']=='3834622546652649531' and ready['status']=='RUNNING'
 (P/('gpu_'+name+'.py.txt')).write_text(script)
 return run(name,['gcloud','compute','ssh','sentinel-gpu',*BASE,'--tunnel-through-iap','--command','sudo -n python3 -'],timeout,script.encode())
def stop(prefix):
 ready=json.loads((P/'gpu_ready_instance.json').read_text())
 r=run(prefix+'_identity',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStartTimestamp)']);assert r.returncode==0
 actual=json.loads(r.stdout);assert actual['id']==ready['id'] and actual['lastStartTimestamp']==ready['lastStartTimestamp']
 if actual['status']!='TERMINATED':
  r=run(prefix+'_stop',['gcloud','compute','instances','stop','sentinel-gpu',*BASE,'--quiet','--format=json'],timeout=150);assert r.returncode==0
 r=run(prefix+'_final',['gcloud','compute','instances','describe','sentinel-gpu',*BASE,'--format=json(id,status,lastStartTimestamp,lastStopTimestamp)']);assert r.returncode==0
 actual=json.loads(r.stdout);assert actual['id']==ready['id'] and actual['lastStartTimestamp']==ready['lastStartTimestamp'] and actual['status']=='TERMINATED'
 (P/'gpu_shutdown_verified.json').write_text(json.dumps(actual,indent=2)+'\n');(E/'cleanup_verified.json').write_text(json.dumps(actual)+'\n')

BRANCH='research/iter148-recovery-study'
RAW=D/'proof/study_raw'
ADMISSIONS=D/'proof/admissions'
