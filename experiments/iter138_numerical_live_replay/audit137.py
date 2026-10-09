"""Retrospective arithmetic audit; stdlib only, no original analyzer import."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'iter137_controller_execution_contract'
SCHEDULE = [('numerical', 'idle'), ('timed', 'idle'), ('timed', 'contended'),
            ('numerical', 'contended'), ('numerical', 'contended'), ('timed', 'contended'),
            ('timed', 'idle'), ('numerical', 'idle')]


def encoding(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def quantile(values):
    values = sorted(values)
    return {k: values[(len(values)*p+99)//100-1] for k, p in
            [('p50', 50), ('p95', 95), ('p99', 99), ('max', 100)]}


def audit(root=ROOT):
    expected = json.loads((root/'proof/analysis.json').read_text())
    cases = json.loads((root/'corpus.json').read_text())['cases']
    groups, numerical, controls = {}, {}, {}
    for block, (mode, load) in enumerate(SCHEDULE):
        path = root/f'proof/benchmark/block_{block}.jsonl'
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected['raw_sha256'][path.name]:
            raise ValueError('raw hash')
        rows = [json.loads(line) for line in raw.splitlines()]
        if len(rows) != 114:
            raise ValueError('call count')
        for case, row in zip(cases, rows):
            if (row['block'], row['case_id'], row['mode'], row['load']) != (block, case['id'], mode, load):
                raise ValueError('schedule')
            if row['status'] != 'completed':
                raise ValueError('failed call')
            n, t = row['numerical'], row['timing']
            if hashlib.sha256(encoding(n)).hexdigest() != row['numerical_sha256']:
                raise ValueError('numerical identity')
            if any(t[k+'_miss'] != (t[k+'_ns'] > 50_000_000) for k in ('adapter', 'solver')):
                raise ValueError('deadline account')
            if mode == 'numerical':
                numerical.setdefault(case['id'], []).append(encoding(n))
            else:
                controls.setdefault(case['id'], set()).add(tuple(n['control']))
            groups.setdefault(mode+'/'+load, []).append(row)
    reports = {}
    for key, group in groups.items():
        reports[key] = dict(calls=len(group),
            stop_reasons={s: sum(r['numerical']['stop_reason'] == s for r in group)
                          for s in ('converged', 'deadline', 'iteration_limit')},
            adapter_misses=sum(r['timing']['adapter_ns'] > 50_000_000 for r in group),
            solver_misses=sum(r['timing']['solver_ns'] > 50_000_000 for r in group),
            adapter_ms=quantile([r['timing']['adapter_ns']/1_000_000 for r in group]),
            solver_ms=quantile([r['timing']['solver_ns']/1_000_000 for r in group]),
            iterations=quantile([r['numerical']['iterations'] for r in group]))
    if reports != expected['groups']:
        raise ValueError('reported aggregate differs from raw arithmetic')
    if len(numerical) != 114 or any(len(v) != 4 or len(set(v)) != 1 for v in numerical.values()):
        raise ValueError('numerical repeats')
    return dict(status='supported', audit_scope='retrospective arithmetic and complete-record identity, not new solver execution',
                measured_calls=912, typed_cases=114, source_decisions=57,
                numerical_identical_cases=114, timed_control_variable_cases=sum(len(v)>1 for v in controls.values()),
                all_reported_groups_match=True, groups=reports,
                timing_caveat='50 ms is the configured solver loop budget and declared engineering threshold; no vehicle deadline is established. Adapter includes diagnostic construction; no actuation latency was measured.')


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, sort_keys=True))
