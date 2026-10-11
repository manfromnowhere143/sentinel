import sys,json,time,subprocess,traceback,shutil
from pathlib import Path
from i148g_ops import P,E,R,stop
marker=E/'supervisor_started.json'
with marker.open('x') as f:json.dump(dict(started_epoch=time.time(),pairs=[0,1,2,3],initial_pair_already_launched=True),f)
result=dict(status='running',pairs=[])
def call(script,*args,timeout=900):
 print('BEGIN',script,*args,flush=True)
 p=subprocess.run([sys.executable,'/tmp/'+script+'.py',*map(str,args)],cwd=R,capture_output=True,text=True,timeout=timeout)
 print('END',script,p.returncode,p.stdout[-2200:],p.stderr[-1200:],flush=True)
 return p
try:
 for pair in range(4):
  if pair:
   q=call('i148g_launch_pair',pair,timeout=150);assert q.returncode==0,'launch_failed'
  started=time.monotonic()
  for n in range(70):
   label=f'auto_{pair:03d}_{n:03d}'
   q=call('i148g_progress',label,timeout=120);assert q.returncode==0,'progress_transport_failed'
   state=json.loads((P/f'gpu_progress_{label}.stdout').read_text())
   print('PROGRESS',json.dumps({k:v.get('steps') for k,v in state['runs'].items()}),flush=True)
   terminal=state['pairs'].get(f'pair_{pair:03d}_result')
   if terminal:break
   assert time.monotonic()-started<2650,'pair_parent_deadline'
   assert json.loads((E/'budget.json').read_text())['deadline_monotonic']-time.monotonic()>240,'whole_budget_margin'
   time.sleep(40)
  else:raise RuntimeError('pair_poll_limit')
  q=call('i148g_collect',pair,timeout=450);assert q.returncode==0,'collection_failed'
  q=call('i148_commit',f'iter148: retain GPU pair {pair} raw before replay',timeout=300);assert q.returncode==0,'raw_commit_failed'
  q=call('i148g_analyze_pair',pair,timeout=300)
  result['pairs'].append(dict(pair=pair,worker_status=terminal['status'],replay_returncode=q.returncode))
  q2=call('i148_commit',f'iter148: retain independent admission result for GPU pair {pair}',timeout=300);assert q2.returncode==0,'admission_commit_failed'
  if q.returncode or terminal['status']!='completed':
   result.update(status='failed',stopping_reason='fixed study worker/replay gate');break
 else:result['status']='supported'
except Exception as exc:
 result.update(status='failed',error=repr(exc),traceback=traceback.format_exc());print('SUPERVISOR_FAILURE',json.dumps(result),flush=True)
finally:
 try:
  q=call('i148g_postflight',timeout=360);result['postflight_returncode']=q.returncode
 except Exception as exc:result['postflight_error']=repr(exc)
 try:stop('normal_shutdown');result['shutdown_verified']=True
 except Exception as exc:result['shutdown_verified']=False;result['shutdown_error']=repr(exc);print('SHUTDOWN_REQUIRES_ATTENTION',repr(exc),flush=True)
 result['ended_epoch']=time.time();(P/'supervisor_result.json').write_text(json.dumps(result,indent=2)+'\n');print('SUPERVISOR_FINAL',json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='supported' and result.get('shutdown_verified') else 1)
