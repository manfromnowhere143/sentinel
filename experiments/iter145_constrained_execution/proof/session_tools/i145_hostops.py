import datetime,json,pathlib,subprocess,time
ROOT=pathlib.Path('/Users/danielwahnich/workspace/sentinel');PROOF=ROOT/'experiments/iter145_constrained_execution/proof';EXT=pathlib.Path('/Users/danielwahnich/sentinel-bootstrap-evidence/iter145-constrained-execution-20261010')
BASE=['--project','sunlit-unison-487018-b0','--zone','us-west1-a']
def run(name,argv,timeout=60,stdin=None):
 paths=[PROOF/(name+s) for s in ['.stdout','.stderr','.json']];assert not any(p.exists() for p in paths)
 start=time.time()
 try:r=subprocess.run(argv,input=stdin,cwd=ROOT,capture_output=True,timeout=timeout)
 except subprocess.TimeoutExpired as e:r=subprocess.CompletedProcess(argv,124,e.stdout or b'',(e.stderr or b'')+b'CLIENT_TIMEOUT')
 paths[0].write_bytes(r.stdout);paths[1].write_bytes(r.stderr);paths[2].write_text(json.dumps(dict(argv=argv,start_utc=datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),elapsed_seconds=time.time()-start,returncode=r.returncode),indent=2)+'\n');print(name,r.returncode,r.stdout.decode()[-1800:],r.stderr.decode()[-1200:],flush=True);return r
def ssh(name,script,timeout=300):
 assert json.loads((PROOF/'host_ready_instance.json').read_text())['id']=='3834622546652649531'
 (PROOF/(name+'.py.txt')).write_text(script)
 return run(name,['gcloud','compute','ssh','sentinel-gpu',*BASE,'--tunnel-through-iap','--command','sudo -n python3 -'],timeout,script.encode())
