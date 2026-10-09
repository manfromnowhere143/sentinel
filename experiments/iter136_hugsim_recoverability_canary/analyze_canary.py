"""Replay the retained reference and controller-fixture analysis without remote access."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from . import check_monitor_delivery, independent_reference_check, replay_trace
except ImportError:
    import check_monitor_delivery
    import independent_reference_check
    import replay_trace


def analyze(proof):
    paths = {name: proof / 'live_v2' / name / 'scene-0411_hard_00/iter136_trace.jsonl'
             for name in ('reference_a', 'reference_b')}
    traces = {name: replay_trace.load_trace(path) for name, path in paths.items()}
    left, right = traces.values()
    result = {
        'schema': 'sentinel.iter136.analysis.v1',
        'scope': 'one disclosed development case; no intervention or transfer result',
        'primary': replay_trace.compare(left, right),
        'independent': independent_reference_check.check(*paths.values()),
        'references': {},
        'initial_exact_equal': {key: left[1][key] == right[1][key] for key in
                                ('observation_sha256', 'before', 'incoming_plan', 'executed_plan')},
        'initial_controls': {name: trace[1]['control'] for name, trace in traces.items()},
        'initial_control_absolute_difference': [abs(a-b) for a, b in
                                                 zip(left[1]['control'], right[1]['control'])],
        'first_field_divergences': {},
        'input_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                         for name, path in paths.items()},
    }
    if (result['primary']['status'] == 'REPLAY_MATCHED') != result['independent']['matched']:
        raise ValueError('reference comparators disagree')
    for name, trace in traces.items():
        run = paths[name].parent.parent
        receipt = json.loads((run / 'episode.json').read_text())
        if receipt['returncode'] != 0:
            raise ValueError('failed reference process')
        decisions = [json.loads(line) for line in
                     (paths[name].parent / 'sentinel_iter48_decisions.jsonl').read_text().splitlines()]
        markers = [line for line in (run / 'driver.log').read_text().splitlines()
                   if line in ('Collision with foreground', 'Collision with background')]
        result['references'][name] = {
            'frames': len(trace)-2, 'terminal_reason': trace[-1]['reason'],
            'termination_time': trace[-2]['after']['timestamp'],
            'route_completion': trace[-2]['route_completion'],
            'collision_observed': any(row['collision'] for row in trace[1:-1]),
            'collision_log_markers': markers, 'severity': None, 'severity_status': 'not_measured',
            'monitor_delivery': check_monitor_delivery.check(trace, decisions),
        }
    for key in ('observation_sha256', 'before', 'incoming_plan', 'executed_plan',
                'control', 'after', 'collision', 'route_completion'):
        result['first_field_divergences'][key] = None
        for i, (a, b) in enumerate(zip(left[1:-1], right[1:-1])):
            where = replay_trace.difference(a[key], b[key], key)
            if where:
                result['first_field_divergences'][key] = {
                    'frame': i, 'pre_action_time': a['time'], 'path': where}
                break
    probe_path = proof / 'controller_probe_raw.json'
    probe = json.loads(probe_path.read_text())
    if probe['input_trace_sha256'] != result['input_sha256']['reference_a']:
        raise ValueError('controller input binding')
    if len(probe['records']) != 26:
        raise ValueError('registered controller fixture count')
    result['input_sha256']['controller_probe'] = hashlib.sha256(probe_path.read_bytes()).hexdigest()
    result['controller_diagnostic'] = {}
    for dtype in ('float32', 'float64'):
        rows = [row for row in probe['records'] if row['dtype'] == dtype]
        controlled = [row for row in rows if row['clock'] == 'controlled']
        groups = [[row for row in controlled if row['deadline_iteration'] == limit]
                  for limit in (1, 5, 10, 20, 100)]
        if len(rows) != 13 or any(len(group) != 2 for group in groups):
            raise ValueError('registered clock conditions')
        curve = groups[-1][0]['first_control_iterates']
        nearest = {}
        for name, control in result['initial_controls'].items():
            error, index, command = min(
                (max(abs(a-b) for a, b in zip(control, command)), index, command)
                for index, command in enumerate(curve))
            nearest[name] = dict(iteration=index, command=command,
                                 max_absolute_difference=error, exact_equal=control == command)
        result['controller_diagnostic'][dtype] = {
            'live_plan_dtype_retained': False,
            'real_clock': [dict(iterations=row['solution_count']-1, control=row['control'],
                                elapsed_seconds=row['elapsed_seconds'])
                           for row in rows if row['clock'] == 'real'],
            'controlled': [dict(deadline_iteration=group[0]['deadline_iteration'],
                                iterations=group[0]['solution_count']-1,
                                control=group[0]['control'],
                                exact_repeat=group[0]['first_control_iterates'] ==
                                group[1]['first_control_iterates']) for group in groups],
            'nearest_live_commands': nearest,
            'limitation': 'live solver iteration counts and deadlines were not recorded',
        }
    result['live_verdict'] = result['primary']['status']
    result['intervention_episodes'] = 0
    result['intervention_benefit'] = 'unobserved'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proof', type=Path, default=Path(__file__).parent / 'proof')
    args = parser.parse_args()
    print(json.dumps(analyze(args.proof), sort_keys=True, indent=2, allow_nan=False))
