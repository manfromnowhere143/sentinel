"""Linkage checks and independent original-source replay of live controller receipts."""

import argparse
import hashlib
import json
from pathlib import Path

from experiments.iter136_hugsim_recoverability_canary import replay_trace as trace
from experiments.iter136_hugsim_recoverability_canary import independent_reference_check as decimal
from experiments.iter137_controller_execution_contract.verify import Replay, require

CONTROLLER_SHA = '7784c0a885bba33414a680d2f943f3a701d7ba38bf29996908c6a7bd4089dc03'


def read_contract(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file() and path.stat().st_size <= 64*1024*1024, 'controller file')
    raw = path.read_bytes()
    require(raw.endswith(b'\n'), 'truncated controller log')
    rows = [json.loads(line, object_pairs_hook=trace._pairs, parse_constant=trace._bad_constant)
            for line in raw.splitlines()]
    require(3 <= len(rows) <= 403, 'controller record count')
    return rows


def validate_linkage(driving, contract):
    trace.validate(driving)
    header, footer = contract[0], contract[-1]
    require(header['schema'] == 'sentinel.iter138.controller_trace.v1' and header['mode'] == 'numerical', 'controller mode/schema')
    require(header['identity'] == driving[0]['identity'] and header['controller_sha256'] == CONTROLLER_SHA, 'controller identity')
    require(header['threadpools'] and all(p['num_threads'] == 1 for p in header['threadpools']), 'threadpool bound')
    require(footer == dict(end='completed', frames=len(driving)-2) and len(contract) == len(driving), 'missing/unapplied controller call')
    cases = []
    for frame, row in zip(driving[1:-1], contract[1:-1]):
        require(set(row) == {'frame', 'time', 'receipt', 'complete_call_ns', 'client_roundtrip_ns'}, 'controller row fields')
        require(type(row['frame']) is int and row['frame'] == frame['frame'] and row['time'] == frame['time'], 'frame linkage')
        r = row['receipt']
        require(r['status'] == 'completed' and r['mode'] == 'numerical', 'controller failure or wrong mode')
        n = r['numerical']
        plan = n['input']['plan']
        require(plan['dtype'] in ('<f4', '<f8') and plan['shape'] == [6, 2], 'actual plan dtype/shape')
        require(plan['values'] == frame['executed_plan'] == frame['incoming_plan'], 'plan linkage')
        require(n['input']['velocity'] == frame['before']['ego_velo'] and
                n['input']['steering'] == frame['before']['ego_steer'], 'state linkage')
        require(n['control'] == frame['control'], 'applied control linkage')
        require(type(row['complete_call_ns']) is int and row['complete_call_ns'] >= r['timing']['adapter_ns'], 'complete call time')
        require(type(row['client_roundtrip_ns']) is int and row['client_roundtrip_ns'] >= 0, 'client roundtrip time')
        require(hashlib.sha256(trace.canonical(n)).hexdigest() == r['numerical_sha256'], 'numerical digest')
        cases.append(dict(id=str(frame['frame']), dtype=plan['dtype'], plan=frame['executed_plan'],
                          velocity=frame['before']['ego_velo'], steering=frame['before']['ego_steer']))
    return cases


def validate_episode(directory, replay):
    directory = Path(directory)
    driving = trace.load_trace(directory/'iter138_trace.jsonl')
    contract = read_contract(directory/'controller138.jsonl')
    cases = validate_linkage(driving, contract)
    for case, row in zip(cases, contract[1:-1]):
        replay.check(row['receipt'], case, 'numerical')
    rows = contract[1:-1]
    def quantiles(values):
        v = sorted(values)
        return {k: v[(len(v)*p+99)//100-1] for k, p in [('p50', 50), ('p95', 95), ('p99', 99), ('max', 100)]}
    summary = dict(frames=len(cases), terminal_reason=driving[-1]['reason'],
        termination_time=driving[-2]['after']['timestamp'], route_completion=driving[-2]['route_completion'],
        actual_dtypes=sorted({r['receipt']['numerical']['input']['plan']['dtype'] for r in rows}),
        stop_reasons={reason: sum(r['receipt']['numerical']['stop_reason'] == reason for r in rows)
                      for reason in ('converged', 'iteration_limit', 'deadline')},
        complete_call_ms=quantiles([r['complete_call_ns']/1e6 for r in rows]),
        client_roundtrip_ms=quantiles([r['client_roundtrip_ns']/1e6 for r in rows]),
        adapter_ms=quantiles([r['receipt']['timing']['adapter_ns']/1e6 for r in rows]),
        solver_ms=quantiles([r['receipt']['timing']['solver_ns']/1e6 for r in rows]),
        complete_call_over_50ms=sum(r['complete_call_ns'] > 50_000_000 for r in rows),
        solver_over_50ms=sum(r['receipt']['timing']['solver_ns'] > 50_000_000 for r in rows),
        files={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (directory/'iter138_trace.jsonl', directory/'controller138.jsonl')})
    return driving, contract, summary


def compare_controller(left, right):
    if len(left) != len(right):
        return dict(matched=False, reason='length')
    for a, b in zip(left[1:-1], right[1:-1]):
        if trace.canonical(a['receipt']['numerical']) != trace.canonical(b['receipt']['numerical']):
            return dict(matched=False, first_frame=a['frame'], reason='numerical record')
    return dict(matched=True, frames=len(left)-2)


def same_runtime(left, right):
    fields = ('schema', 'identity', 'controller_sha256', 'mode', 'numpy', 'python',
              'platform', 'affinity', 'threadpools')
    return all(left[0][key] == right[0][key] for key in fields)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path, nargs='?')
    args = parser.parse_args()
    replay = Replay()
    a, ca, summary_a = validate_episode(args.reference, replay)
    result = dict(status='validated', reference_a=summary_a, scope='live development reference; no intervention benefit claim')
    if args.candidate:
        b, cb, summary_b = validate_episode(args.candidate, replay)
        primary = trace.compare(a, b)
        independent = decimal.check(args.reference/'iter138_trace.jsonl', args.candidate/'iter138_trace.jsonl')
        numerical = compare_controller(ca, cb)
        runtime_matched = same_runtime(ca, cb)
        matched = primary['status'] == 'REPLAY_MATCHED' and independent['matched'] and numerical['matched'] and runtime_matched
        verdict = 'REPLAY_DIVERGED' if not matched else 'REPLAY_MATCHED' if any(f['collision'] for f in a[1:-1]) else 'NO_RECOVERABILITY_TARGET'
        first = next((dict(frame=x['frame'], field=field) for x, y in zip(a[1:-1], b[1:-1])
                      for field in ('observation_sha256', 'before', 'incoming_plan', 'executed_plan', 'control', 'after')
                      if trace.difference(x[field], y[field])), None)
        result.update(status='supported' if matched else 'failed', verdict=verdict,
                      reference_b=summary_b, primary=primary, independent_decimal=independent,
                      exact_controller=numerical, runtime_matched=runtime_matched, earliest_trace_difference=first)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
