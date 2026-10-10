from pathlib import Path
import json,statistics
R=Path.cwd();P=R/'experiments/iter147_full_horizon_execution/proof';a=json.loads((P/'gpu_aggregate.json').read_text());groups={};candidates=[]
for pair in range(4):
 controllers=[];loops=[];speed=[];dist=[]
 for folder in sorted((P/f'gpu_raw/pair_{pair:03d}/runs').iterdir()):
  s=json.loads((folder/'trace/summary.json').read_text());loops += [t['full_loop_ns']/1e9 for t in s['timings']]
  for line in (folder/'trace/events.jsonl').read_bytes().splitlines():
   r=json.loads(line)
   if r['event']=='control':controllers.append(r['result']['complete_call_ns']/1e6)
   if r['event']=='actor' and r['value'].get('event')=='selection':
    candidates.append(r['value'])
 def stats(v):return dict(count=len(v),minimum=min(v),median=statistics.median(v),maximum=max(v))
 groups[str(pair)]=dict(controller_ms={**stats(controllers),'over_50ms':sum(v>50 for v in controllers)},loop_seconds={**stats(loops),'over_250ms':sum(v>.25 for v in loops)})
result=dict(status='supported',groups=groups,maximum_stationarity=max(r['max_stationarity'] for r in a['cases']),camera_calls=sum(r['camera_calls'] for r in a['cases']),largest_event_bytes=max(r['largest_event_bytes'] for r in a['cases']),monitor_firings_diagnostic=sum(r['monitor_fired'] for r in a['cases'] if r['probe']=='monitor_hold'),monitor_firings_natural_shadow=sum(r['monitor_fired'] for r in a['cases'] if r['probe']=='none'),monitor_braking_decisions_natural_shadow=sum(r['monitor_brake'] for r in a['cases'] if r['probe']=='none'),natural_controller_calls=sum(g['controller_ms']['count'] for k,g in groups.items() if k!='0'),natural_controller_over_50ms=sum(g['controller_ms']['over_50ms'] for k,g in groups.items() if k!='0'),natural_episodes=6,collision_episodes=sum(r['outcome']['collision_observed'] for r in a['cases']),censored_episodes=sum(r['outcome']['censored'] for r in a['cases']),qualified_completion_episodes=sum(r['outcome']['completion_qualified'] for r in a['cases']),resource_output_case_bytes=sum(json.loads((P/f'gpu_pair_{i:03d}_collection_receipt.json').read_text())['output_bytes'] for i in range(4)))
(P/'qualification_metrics.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
