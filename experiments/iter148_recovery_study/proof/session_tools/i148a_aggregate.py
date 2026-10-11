import json,statistics,sys
from pathlib import Path
from i148a_ops import R,D,P,RAW,ADMISSIONS
sys.path.insert(0,str(R))
from experiments.iter148_recovery_study.aggregate import summarize
from experiments.iter147_full_horizon_execution.coordinator import raw_identity,record
plan=json.loads((D/'STUDY_PLAN.json').read_text())
analyses={int(p.stem.split('_')[1]):json.loads(p.read_text()) for p in ADMISSIONS.glob('pair_*.json')}
accepted=[]
for i,a in sorted(analyses.items()):
 if i!=len(accepted) or a['status']!='supported':break
 accepted.append(a)
result=summarize(plan,accepted)
result.update(source_commit=json.loads((P/'gpu_source_packet.json').read_text())['commit'],raw_commits={},cases=[],block=0,block_status='supported' if len(accepted)==4 else 'invalid',live_study_admitted=True)
controllers=[];loops=[];exchanges=[]
for i,a in sorted(analyses.items()):
 root=RAW/f'pair_{i:03d}';result['raw_commits'][f'pair_{i:03d}']=a['raw_commit'];raw_identity(R,a['raw_commit'],root)
for slot in plan['slots']:
 i=slot['index']//2;root=RAW/f'pair_{i:03d}'/'runs'/slot['id'];a=analyses.get(i)
 row=dict(slot=slot['index'],episode=slot['id'],scenario=slot['scenario'],arm=slot['arm'],replica=slot['replica'],status='missing',steps=None,outcome=None)
 if root.exists():
  row.update(status='supported' if a and a['status']=='supported' else 'invalid',analysis_error=a.get('error') if a else 'analysis_missing')
  if (root/'worker.json').exists():
   w=json.loads((root/'worker.json').read_text());row.update(worker_status=w['status'],worker_stop=w.get('stop_reason'),actor_types=w.get('actor_types'),elapsed_seconds=w.get('elapsed_seconds'))
  if (root/'trace/summary.json').exists():
   s=json.loads((root/'trace/summary.json').read_text());row.update(steps=s['steps'],outcome=s['outcome'],stop_reason=s['stop_reason'],timing_schema=s['schema'])
   lt=[v['full_loop_ns']/1e9 for v in s['timings']];et=[v['exchange_ns']/1e9 for v in s['timings']];loops+=lt;exchanges+=et
   row['loop_seconds']=dict(count=len(lt),median=statistics.median(lt),maximum=max(lt),over_250ms=sum(v>.25 for v in lt)) if lt else None
  if (root/'trace/events.jsonl').exists():
   rows=[];data=(root/'trace/events.jsonl').read_bytes().splitlines()
   for line in data:
    try:rows.append(json.loads(line))
    except ValueError:row['partial_event_line']=True
   ct=[r['result']['complete_call_ns']/1e6 for r in rows if r['event']=='control'];controllers+=ct
   row['controller_ms']=dict(count=len(ct),median=statistics.median(ct),maximum=max(ct),over_50ms=sum(v>50 for v in ct)) if ct else None
   row['recorded_step_events']=sum(r['event']=='step' for r in rows)
   row['largest_event_bytes']=max(map(len,data),default=0)
  if (root/'sentinel_iter48_decisions.jsonl').exists():
   m=[json.loads(l) for l in (root/'sentinel_iter48_decisions.jsonl').read_bytes().splitlines()]
   row['monitor_fired']=sum(r['fired'] for r in m);row['monitor_brake']=sum(r['brake'] for r in m);row['monitor_applied_arm']=slot['arm']=='monitor'
  if a and a['status']=='supported':
   r=next(r for r in a['cases'] if r['episode']==slot['id']);row.update(max_stationarity=r['max_stationarity'],monitor_replay=r['monitor'],camera_calls=r['camera_calls'])
 result['cases'].append(row)
def stats(v):return dict(count=len(v),minimum=min(v),median=statistics.median(v),maximum=max(v)) if v else dict(count=0,minimum=None,median=None,maximum=None)
result['execution_summary']=dict(initialized_slots=sum(r['status']!='missing' for r in result['cases']),missing_slots=sum(r['status']=='missing' for r in result['cases']),recorded_step_events=sum(r.get('recorded_step_events',0) for r in result['cases']),controller_ms={**stats(controllers),'over_50ms':sum(v>50 for v in controllers)},loop_seconds={**stats(loops),'over_250ms':sum(v>.25 for v in loops)},exchange_seconds=stats(exchanges),timing_scope='Summary v2 guard-inclusive step work; reset, summary serialization and worker cleanup outside per-step timing. Observed timings remain descriptive even for invalid cases; validity is explicit per case.')
record(P/'study_aggregate.json',result);print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
