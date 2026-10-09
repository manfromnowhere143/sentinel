"""Independent source replay and benchmark accounting. Does not import the adapter."""

import argparse
from dataclasses import asdict, replace
import hashlib
import importlib.machinery
import importlib.util
import json
import math
from pathlib import Path
import sys
import types

import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'iter136_hugsim_recoverability_canary/proof/controller_source'
HASHES = {
    'lqr.py': 'b32755c32de510e09ac726f5c77731d5f490df6a412e50a4d369d70bdef45faf',
    'lqr_solver.py': '0141d73d0ac38386184e63ce384d2e3cd341130943065b416bdacf4281e57c47',
    'utils.py': '041ed70028c105cfc102978ffddad4e92398d29b2454f1c2be6c81fb765c75fe',
    'sim_utils.py': '36c2ba6a7dee38555f84dde95851ec00be5a699969d53de8906b3e67676792bc',
}
CORPUS_HASH = '58a0095637512152fac6868f1a8d24516fa33f5da96c2429a75e311506804557'
SCHEDULE = [('numerical', 'idle'), ('timed', 'idle'), ('timed', 'contended'),
            ('numerical', 'contended'), ('numerical', 'contended'), ('timed', 'contended'),
            ('timed', 'idle'), ('numerical', 'idle')]


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def array(value):
    value = np.ascontiguousarray(value)
    require(np.isfinite(value).all(), 'nonfinite array')
    raw = value.tobytes()
    return dict(dtype=value.dtype.str, shape=list(value.shape), bytes_hex=raw.hex(),
                sha256=digest(raw), values=value.tolist())


def load_original(source=SOURCE):
    for name, expected in HASHES.items():
        path = source / (name + '.txt')
        require(not path.is_symlink() and digest(path.read_bytes()) == expected, 'source identity')
    # Import unmodified retained files with their original absolute package names.
    # This verifier runs in its own process; it never imports a simulator package.
    for name in ('sim', 'sim.ilqr'):
        module = types.ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    for name in ('utils', 'lqr_solver', 'lqr'):
        full = 'sim.ilqr.' + name
        loader = importlib.machinery.SourceFileLoader(full, str(source / (name + '.py.txt')))
        spec = importlib.util.spec_from_loader(full, loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[full] = module
        loader.exec_module(module)
    return sys.modules['sim.ilqr.lqr_solver'], sys.modules['sim.ilqr.lqr']


def convert(case):
    plan = np.array(case['plan'], dtype=case['dtype'])
    require(plan.shape == (6, 2) and np.isfinite(plan).all(), 'case input')
    ref = np.zeros((7, 5))
    ref[1:, :2] = plan[:, [1, 0]]
    previous_x, previous_y = 0.0, 0.0
    for index, (x, y) in enumerate(plan):
        angle = np.arctan2(y - previous_y, x - previous_x)
        angle = np.where(angle > np.pi / 2, angle - np.pi, angle)
        angle = np.where(angle < -np.pi / 2, angle + np.pi, angle)
        ref[index + 1, 2] = angle
        previous_x, previous_y = x, y
    state = np.array([0.0, 0.0, 0.0, case['velocity'], case['steering']])
    return plan, state, ref


class Replay:
    def __init__(self, source=SOURCE):
        self.module, self.params = load_original(source)
        self.cache = {}

    def expected(self, case, iterations):
        key = (digest(encoded(case)), iterations)
        if key in self.cache:
            return self.cache[key]
        plan, state, ref = convert(case)
        solver = self.module.ILQRSolver(replace(self.params.solver_params,
                    max_ilqr_iterations=iterations, max_solve_time=None), self.params.warm_start_params)
        norms = []
        update = solver._update_inputs_with_policy

        def observe(current_iterate, lqr_input_policy):
            next_input = update(current_iterate, lqr_input_policy)
            norms.append(float(np.linalg.norm(next_input - current_iterate.input_trajectory)))
            return next_input

        solver._update_inputs_with_policy = observe
        solutions = solver.solve(state, ref)
        require(len(solutions) == iterations + 1, 'replayed iteration count')
        records = []
        for s in solutions:
            records.append(dict(input_sha256=digest(encoded(array(s.input_trajectory))),
                                state_sha256=digest(encoded(array(s.state_trajectory))),
                                tracking_cost=float(s.tracking_cost),
                                first_control=s.input_trajectory[0].tolist()))
        result = dict(input=dict(plan=array(plan), velocity=float(case['velocity']), steering=float(case['steering'])),
                      state=array(state), reference=array(ref), iterations=iterations, norms=norms,
                      control=solutions[-1].input_trajectory[0].tolist(), iterates=records,
                      final_input=array(solutions[-1].input_trajectory), final_state=array(solutions[-1].state_trajectory))
        self.cache[key] = result
        return result

    def check(self, receipt, case, mode):
        require(receipt['schema'] == 'sentinel.iter137.execution.v1' and receipt['status'] == 'completed', 'failed/schema')
        require(receipt['mode'] == mode and receipt['source_sha256'] == HASHES, 'mode/source identity')
        params = replace(self.params.solver_params, max_solve_time=None) if mode == 'numerical' else self.params.solver_params
        require(receipt['configuration'] == dict(solver=asdict(params), warm_start=asdict(self.params.warm_start_params)), 'configuration identity')
        n = receipt['numerical']
        require(type(n['iterations']) is int and 1 <= n['iterations'] <= 100, 'iteration bounds')
        require(digest(encoded(n)) == receipt['numerical_sha256'], 'numerical digest')
        expected = self.expected(case, n['iterations'])
        require(encoded({k: v for k, v in n.items() if k != 'stop_reason'}) == encoded(expected), 'numerical replay')
        check_termination(n, receipt['timing'], mode)
        return receipt['numerical_sha256']


def check_termination(n, timing, mode):
    count = n['iterations']
    reads, norms = timing['deadline_reads'], n['norms']
    require(len(reads) == len(norms) == count, 'stopping record length')
    previous = 0.0
    for i, (norm, elapsed) in enumerate(zip(norms, reads)):
        require(math.isfinite(norm) and norm >= 0, 'norm')
        converged = norm < 1e-6
        if converged:
            require(i == count - 1 and elapsed is None, 'convergence precedence/skipped clock')
        else:
            require(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= previous, 'clock readings')
            previous = elapsed
            if mode == 'timed' and elapsed >= .05:
                require(i == count - 1, 'continued after deadline')
    if norms[-1] < 1e-6:
        reason = 'converged'
    elif mode == 'timed' and reads[-1] >= .05:
        reason = 'deadline'
    else:
        require(count == 100, 'premature iteration limit')
        reason = 'iteration_limit'
    require(n['stop_reason'] == reason, 'false stopping reason')
    a, s = timing['adapter_ns'], timing['solver_ns']
    require(type(a) is int and type(s) is int and a >= s >= 0, 'elapsed duration')
    require(previous * 1e9 <= s + 1000, 'loop duration exceeds full solver')
    require(type(timing['adapter_miss']) is bool and timing['adapter_miss'] == (a > 50_000_000), 'adapter deadline accounting')
    require(type(timing['solver_miss']) is bool and timing['solver_miss'] == (s > 50_000_000), 'solver deadline accounting')


def verify_rows(rows, cases, replay):
    require(len(rows) == len(cases) * 8, 'missing calls')
    numerical = {c['id']: [] for c in cases}
    timed = {c['id']: [] for c in cases}
    groups = {}
    for index, row in enumerate(rows):
        block, offset = divmod(index, len(cases))
        mode, load = SCHEDULE[block]
        case = cases[offset]
        require((row['block'], row['case_id'], row['load']) == (block, case['id'], load), 'schedule/order')
        h = replay.check(row, case, mode)
        (numerical if mode == 'numerical' else timed)[case['id']].append(h)
        groups.setdefault(mode + '/' + load, []).append(row)
    mismatches = [k for k, values in numerical.items() if len(set(values)) != 1]
    require(not mismatches, 'numerical repeat divergence: ' + ','.join(mismatches))

    def percentiles(values):
        values = sorted(values)
        return {label: values[math.ceil(len(values)*fraction)-1]
                for label, fraction in [('p50', .5), ('p95', .95), ('p99', .99), ('max', 1)]}

    summaries = {}
    for key, group in groups.items():
        reasons = {k: sum(r['numerical']['stop_reason'] == k for r in group)
                   for k in ('converged', 'deadline', 'iteration_limit')}
        summaries[key] = dict(calls=len(group), stop_reasons=reasons,
            adapter_misses=sum(r['timing']['adapter_miss'] for r in group),
            solver_misses=sum(r['timing']['solver_miss'] for r in group),
            adapter_ms=percentiles([r['timing']['adapter_ns']/1e6 for r in group]),
            solver_ms=percentiles([r['timing']['solver_ns']/1e6 for r in group]),
            iterations=percentiles([r['numerical']['iterations'] for r in group]))
    return dict(status='supported', scope='114 reconstructed inputs, one bound CPU/runtime, four numerical observations each',
                measured_calls=len(rows), numerical_identical_cases=len(cases), numerical_repeat_mismatches=mismatches,
                timed_variable_cases=sum(len(set(h)) > 1 for h in timed.values()), groups=summaries)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    corpus_raw = (ROOT / 'corpus.json').read_bytes()
    require(digest(corpus_raw) == CORPUS_HASH, 'corpus identity')
    cases = json.loads(corpus_raw)['cases']
    manifest = json.loads((args.output / 'run.json').read_text())
    require(manifest['status'] == 'completed' and len(manifest['blocks']) == 8, 'incomplete run')
    rows = []
    for i, block in enumerate(manifest['blocks']):
        require(block['block'] == i and block['returncode'] == 0, 'failed block')
        meta = json.loads((args.output / f'block_{i}.meta.json').read_text())
        require(meta['calls'] == 114 and meta['status'] == 'completed', 'block calls/status')
        require(meta['affinity'] == [manifest['cpu']], 'worker affinity')
        require(meta['threadpools'] and all(p['num_threads'] == 1 for p in meta['threadpools']), 'threadpool bound')
        expected = 0 if SCHEDULE[i][1] == 'idle' else 3
        require(len(block['competitors']) == expected, 'competitor count')
        require(all(c['affinity'] == [manifest['cpu']] for c in block['competitors']), 'competitor affinity')
        require(block['competitors_alive_after'] == expected, 'competitor liveness')
        rows.extend(json.loads(line) for line in (args.output / f'block_{i}.jsonl').read_text().splitlines())
    result = verify_rows(rows, cases, Replay())
    result['numpy_version'] = np.__version__
    result['raw_sha256'] = {p.name: digest(p.read_bytes()) for p in sorted(args.output.iterdir()) if p.is_file()}
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
