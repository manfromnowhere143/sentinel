"""Descriptive short-run qualification; no recovery estimand is calculated."""
import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path

R = Path('/Users/danielwahnich/workspace/sentinel')
sys.path.insert(0, str(R))
from experiments.iter146_route_outcome_contract.gpu_check import verify_case
from experiments.iter146_route_outcome_contract.compare import replicas
from experiments.iter145_constrained_execution.independent import close

P = R / 'experiments/iter146_route_outcome_contract/proof'
arms = ('nominal', 'monitor', 'brake_t0', 'brake_t2_5')
result = dict(status='supported', scope='Eight fixed 24-action seed-144 GPU qualification episodes on scene-0013-easy-00; descriptive engineering evidence only.', source_commit='9f78e514000f94ab069e846a7b6796009702a223', live_study_admitted=False, raw_commits={}, cases=[], arms={}, timing_scope_correction='Raw full_loop_ns is a loop-work lower bound: its endpoint precedes the post-step resource guard, deadline check and stop dispatch. It includes the initial guard, observation hashing, exchange, control, simulator, outcome calculation and trace flush. elapsed_ns encloses reset, loop guards and finalization but excludes summary serialization and worker cleanup. Raw bytes are unchanged.')
reports = {}
all_controller, all_loop, all_exchange, all_simulator = [], [], [], []
for arm in arms:
    admission = json.loads((P / (arm + '_pair_analysis.json')).read_text())
    assert admission['status'] == 'supported'
    commit = admission['raw_commit']; result['raw_commits'][arm] = commit
    root = P / 'gpu_raw' / arm
    for path in root.rglob('*'):
        if path.is_file():
            assert path.read_bytes() == subprocess.check_output(['git','show',commit + ':' + str(path.relative_to(R))], cwd=R)
    pair = []
    arm_controller, arm_loop, arm_exchange, arm_simulator = [], [], [], []
    for replica in (1,2):
        folder = root / 'runs' / f'scene-0013-easy-00__{arm}__{replica}'
        report = verify_case(folder); pair.append(report)
        s = json.loads((folder / 'trace/summary.json').read_text())
        rows = [json.loads(line) for line in (folder / 'trace/events.jsonl').read_text().splitlines()]
        controls = [r for r in rows if r['event'] == 'control']
        monitors = [json.loads(r['raw']) for r in rows if r['event'] == 'monitor']
        steps = [r for r in rows if r['event'] == 'step']
        controller = [r['result']['complete_call_ns']/1e6 for r in controls]
        loops = [r['full_loop_ns']/1e9 for r in s['timings']]
        exchanges = [r['exchange_ns']/1e9 for r in s['timings']]
        simulator = [r['simulator_ns']/1e9 for r in steps]
        arm_controller += controller; arm_loop += loops; arm_exchange += exchanges; arm_simulator += simulator
        out = dict(episode=s['episode'],arm=arm,replica=replica,steps=s['steps'],stop_reason=s['stop_reason'],outcome=s['outcome'],monitor_fired=sum(r['fired'] for r in monitors),monitor_brake=sum(r['brake'] for r in monitors),max_monitor_objects=max(len(r['objs']) for r in monitors),max_stationarity=report['max_stationarity'],controller_stop_reasons=sorted(set(r['result']['stop_reason'] for r in controls)),camera_calls=report['camera_calls'],loop_lower_bound_sum_seconds=sum(loops),enclosing_episode_seconds=s['elapsed_ns']/1e9,enclosing_episode_average_upper_bound_seconds=s['elapsed_ns']/1e9/s['steps'],configured_actor_counts=sorted(set(len(r['info']['obj_boxes']) for r in steps)),events_sha256=report['events_sha256'])
        if arm.startswith('brake_'):
            onset = 0 if arm=='brake_t0' else 2.5
            pulse = [r for r in report['scientific'] if onset <= r['time']-.25 < onset+1]
            out['pulse'] = dict(observation_times=[r['time']-.25 for r in pulse],application_times=[r['time'] for r in pulse],applied_acceleration=[r['action'][0] for r in pulse],nominal_acceleration=[r['nominal_action'][0] for r in pulse],contrasted_steps=sum(abs(r['action'][0]-r['nominal_action'][0])>1e-9 for r in pulse))
        result['cases'].append(out)
    replicas(pair); reports[arm] = pair
    def stats(values):
        return dict(count=len(values),minimum=min(values),median=statistics.median(values),maximum=max(values))
    result['arms'][arm] = dict(controller_ms={**stats(arm_controller),'over_50ms':sum(x>50 for x in arm_controller)},loop_work_lower_bound_seconds={**stats(arm_loop),'over_250ms':sum(x>.25 for x in arm_loop)},exchange_seconds=stats(arm_exchange),simulator_seconds=stats(arm_simulator))
    all_controller += arm_controller; all_loop += arm_loop; all_exchange += arm_exchange; all_simulator += arm_simulator
# Descriptive preregistered late-pulse prefix check over both fresh replicas.
prefixes=[]
for i in range(2):
    a,b=reports['nominal'][i],reports['brake_t2_5'][i]
    count=0
    for x,y in zip(a['scientific'],b['scientific']):
        if x['time'] > 2.5: break
        for field in ('time','state','action','nominal_action','rc'):close(x[field],y[field],1e-9)
        for field in ('nominal','delivered','collision','off_route','rgb','actors'):assert x[field]==y[field],field
        count+=1
    prefixes.append(count)
result['late_pulse_equal_prefix_steps_per_replica']=prefixes
result['summary']=dict(episodes=len(result['cases']),steps=sum(x['steps'] for x in result['cases']),replica_pairs=len(reports),camera_calls=sum(x['camera_calls'] for x in result['cases']),max_stationarity=max(x['max_stationarity'] for x in result['cases']),monitor_fired=sum(x['monitor_fired'] for x in result['cases']),monitor_brake=sum(x['monitor_brake'] for x in result['cases']),censored=sum(x['outcome']['censored'] for x in result['cases']),completion=sum(x['outcome']['completion_qualified'] for x in result['cases']),collision_observed=sum(x['outcome']['collision_observed'] is True for x in result['cases']),off_route_observed=sum(x['outcome']['off_route_observed'] is True for x in result['cases']),controller_ms={**stats(all_controller),'over_50ms':sum(x>50 for x in all_controller)},loop_work_lower_bound_seconds={**stats(all_loop),'over_250ms':sum(x>.25 for x in all_loop)},exchange_seconds=stats(all_exchange),simulator_seconds=stats(all_simulator),output_bytes=sum(json.loads((P/f'gpu_{arm}_collection_receipt.json').read_text())['output_bytes'] for arm in arms))
(P/'gpu_aggregate.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps(result['summary'],indent=2))
