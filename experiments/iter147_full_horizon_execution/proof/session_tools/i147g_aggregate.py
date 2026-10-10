import json,statistics,sys
from pathlib import Path
R=Path('/Users/danielwahnich/workspace/sentinel');sys.path.insert(0,str(R))
from experiments.iter147_full_horizon_execution.coordinator import raw_identity,record
P=R/'experiments/iter147_full_horizon_execution/proof';plan=json.loads((P.parent/'QUALIFICATION_PLAN.json').read_text())
analyses={int(p.stem.split('_')[1]):json.loads(p.read_text()) for p in P.glob('pair_*_analysis.json')}
result=dict(status='supported' if len(analyses)==4 and all(a['status']=='supported' for a in analyses.values()) else 'failed',scope='Fixed eight-slot engineering qualification; diagnostic detector hold separated from natural inputs; no study recovery denominator.',source_commit=json.loads((P/'gpu_source_packet.json').read_text())['commit'],raw_commits={},cases=[],live_study_admitted=False)
controllers=[];loops=[];exchanges=[]
for i,a in sorted(analyses.items()):
 root=P/'gpu_raw'/f'pair_{i:03d}';result['raw_commits'][f'pair_{i:03d}']=a['raw_commit'];raw_identity(R,a['raw_commit'],root)
for slot in plan['slots']:
 i=slot['index']//2;root=P/'gpu_raw'/f'pair_{i:03d}'/'runs'/slot['id'];a=analyses.get(i)
 row=dict(slot=slot['index'],episode=slot['id'],scenario=slot['scenario'],arm=slot['arm'],probe=slot['probe'],replica=slot['replica'],status='missing',steps=None,outcome=None)
 if root.exists():
  row.update(status='supported' if a and a['status']=='supported' else 'invalid',analysis_error=a.get('error') if a else 'analysis_missing')
  if (root/'worker.json').exists():
   w=json.loads((root/'worker.json').read_text());row.update(worker_status=w['status'],worker_stop=w.get('stop_reason'),actor_types=w.get('actor_types'),elapsed_seconds=w['elapsed_seconds'])
  if (root/'trace/summary.json').exists():
   s=json.loads((root/'trace/summary.json').read_text());row.update(steps=s['steps'],outcome=s['outcome'],stop_reason=s['stop_reason'],timing_schema=s['schema'])
   loops += [v['full_loop_ns']/1e9 for v in s['timings']];exchanges += [v['exchange_ns']/1e9 for v in s['timings']]
  if (root/'trace/events.jsonl').exists():
   rows=[]
   for l in (root/'trace/events.jsonl').read_bytes().splitlines():
    try:rows.append(json.loads(l))
    except ValueError:row['partial_event_line']=True
   controllers += [r['result']['complete_call_ns']/1e6 for r in rows if r['event']=='control']
   row['recorded_step_events']=sum(r['event']=='step' for r in rows)
   row['largest_event_bytes']=max(map(len,(root/'trace/events.jsonl').read_bytes().splitlines()),default=0)
  if (root/'sentinel_iter48_decisions.jsonl').exists():
   m=[json.loads(l) for l in (root/'sentinel_iter48_decisions.jsonl').read_bytes().splitlines()]
   row['monitor_fired']=sum(r['fired'] for r in m);row['monitor_brake']=sum(r['brake'] for r in m)
  if a and a['status']=='supported':
   r=next(r for r in a['cases'] if r['episode']==slot['id']);row.update(max_stationarity=r['max_stationarity'],monitor_replay=r['monitor'],camera_calls=r['camera_calls'])
 result['cases'].append(row)
def stats(v):return dict(count=len(v),minimum=min(v),median=statistics.median(v),maximum=max(v)) if v else dict(count=0,minimum=None,median=None,maximum=None)
result['summary']=dict(planned_slots=8,initialized=sum(r['status']!='missing' for r in result['cases']),missing=sum(r['status']=='missing' for r in result['cases']),supported_pairs=sum(a['status']=='supported' for a in analyses.values()),supported_steps=sum(r['steps'] for r in result['cases'] if r['status']=='supported'),recorded_step_events=sum(r.get('recorded_step_events',0) for r in result['cases']),controller_ms={**stats(controllers),'over_50ms':sum(v>50 for v in controllers)},loop_seconds={**stats(loops),'over_250ms':sum(v>.25 for v in loops)},exchange_seconds=stats(exchanges),timing_scope='Summary v2 guard-inclusive step work; reset, summary serialization and worker cleanup outside per-step timing. Recorded timing is descriptive even for invalid cases; validity remains per-case explicit.')
record(P/'gpu_aggregate.json',result);print(json.dumps(result,indent=2))
