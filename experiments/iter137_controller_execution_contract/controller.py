"""Source-bound CPU controller adapter; no simulator import or actuation.

Upstream algorithm/trajectory conversion: retained HUGSIM MIT source in Iter136.
Only solve instrumentation and the explicit numerical-mode deadline setting differ.
"""

import ast
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import time
import types

import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'iter136_hugsim_recoverability_canary/proof/controller_source'
SOURCE_HASHES = {
    'lqr.py': 'b32755c32de510e09ac726f5c77731d5f490df6a412e50a4d369d70bdef45faf',
    'lqr_solver.py': '0141d73d0ac38386184e63ce384d2e3cd341130943065b416bdacf4281e57c47',
    'utils.py': '041ed70028c105cfc102978ffddad4e92398d29b2454f1c2be6c81fb765c75fe',
    'sim_utils.py': '36c2ba6a7dee38555f84dde95851ec00be5a699969d53de8906b3e67676792bc',
}
CORPUS_HASH = '58a0095637512152fac6868f1a8d24516fa33f5da96c2429a75e311506804557'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_bound(path, expected):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError('source/input file type or size')
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError('source/input identity')
    return raw


def array_record(value):
    a = np.ascontiguousarray(value)
    if not np.isfinite(a).all():
        raise ValueError('nonfinite array')
    return dict(dtype=a.dtype.str, shape=list(a.shape), bytes_hex=a.tobytes().hex(),
                sha256=sha(a.tobytes()), values=a.tolist())


def solution_record(solution):
    if not np.isfinite(solution.tracking_cost):
        raise ValueError('nonfinite cost')
    a, s = array_record(solution.input_trajectory), array_record(solution.state_trajectory)
    if a['shape'] != [6, 2] or s['shape'] != [7, 5]:
        raise ValueError('malformed solution')
    return dict(input_sha256=sha(canonical(a)), state_sha256=sha(canonical(s)),
                tracking_cost=float(solution.tracking_cost),
                first_control=solution.input_trajectory[0].tolist())


def load_corpus(path=ROOT / 'corpus.json'):
    return json.loads(read_bound(path, CORPUS_HASH))['cases']


def _module(name, tree, bindings=None):
    mod = types.ModuleType(name)
    mod.__dict__.update(bindings or {})
    sys.modules[name] = mod
    exec(compile(tree, f'<{name}>', 'exec'), mod.__dict__)
    return mod


def load_source(source=SOURCE, instrument=True):
    texts = {n: read_bound(source / (n + '.txt'), h).decode() for n, h in SOURCE_HASHES.items()}
    utils = _module('_iter137_utils', ast.parse(texts['utils.py']))
    text = texts['lqr_solver.py']
    if instrument:
        replacements = [
            ('        solve_start_time = time.perf_counter()',
             "        self.execution = dict(stop_reason='iteration_limit', norms=[], deadline_reads=[])\n"
             '        solve_start_time = self.clock()'),
            ('            if input_trajectory_norm_difference < self._solver_params.convergence_threshold:\n                break',
             '            self.execution["norms"].append(float(input_trajectory_norm_difference))\n'
             '            if input_trajectory_norm_difference < self._solver_params.convergence_threshold:\n'
             '                self.execution["deadline_reads"].append(None)\n'
             '                self.execution["stop_reason"] = "converged"\n                break'),
            ('            elapsed_time = time.perf_counter() - solve_start_time',
             '            elapsed_time = self.clock() - solve_start_time\n'
             '            self.execution["deadline_reads"].append(elapsed_time)'),
            ('                and elapsed_time >= self._solver_params.max_solve_time\n            ):\n                break',
             '                and elapsed_time >= self._solver_params.max_solve_time\n            ):\n'
             '                self.execution["stop_reason"] = "deadline"\n                break'),
        ]
        for before, after in replacements:
            if text.count(before) != 1:
                raise ValueError('instrumentation anchor')
            text = text.replace(before, after)
    tree = ast.parse(text)
    tree.body = [n for n in tree.body if not (
        isinstance(n, ast.ImportFrom) and n.module == 'sim.ilqr.utils')]
    solver = _module('_iter137_instrumented' if instrument else '_iter137_original', tree,
                     {k: getattr(utils, k) for k in ('principal_value',
                      'complete_kinematic_state_and_inputs_from_poses', 'compute_steering_angle_feedback')})
    tree = ast.parse(texts['lqr.py'])
    tree.body = [n for n in tree.body if not isinstance(n, (ast.ImportFrom, ast.If))]
    params = _module('_iter137_parameters', tree,
                     {k: getattr(solver, k) for k in ('ILQRSolverParameters',
                      'ILQRWarmStartParameters', 'ILQRSolver')})
    node, = [n for n in ast.parse(texts['sim_utils.py']).body
             if isinstance(n, ast.FunctionDef) and n.name == 'traj2control']
    conversion = compile(ast.Module(body=[node], type_ignores=[]), '<upstream-traj2control>', 'exec')
    return solver, params, conversion


class Controller:
    def __init__(self, mode, source=SOURCE):
        if mode not in ('numerical', 'timed'):
            raise ValueError('unknown mode')
        module, params, self.conversion = load_source(source)
        self.mode = mode
        self.params = replace(params.solver_params, max_solve_time=None) if mode == 'numerical' else params.solver_params
        self.warm = params.warm_start_params
        self.solver = module.ILQRSolver(self.params, self.warm)
        self.solver.clock = time.perf_counter
        self.configuration = dict(solver=asdict(self.params), warm_start=asdict(self.warm))

    def run(self, plan, velocity, steering):
        start = time.perf_counter_ns()
        try:
            if not isinstance(plan, np.ndarray) or plan.dtype not in (np.dtype('float32'), np.dtype('float64')):
                raise ValueError('plan must have explicit float32/float64 dtype')
            if plan.shape != (6, 2) or not np.isfinite(plan).all():
                raise ValueError('malformed/nonfinite input')
            if any(isinstance(v, (bool, np.bool_)) or not np.isscalar(v) or not np.isfinite(v)
                   for v in (velocity, steering)):
                raise ValueError('malformed/nonfinite state')
            captured = {}

            def solve(reference, state):
                captured['reference'], captured['state'] = reference, state
                solver_start = time.perf_counter_ns()
                solutions = self.solver.solve(state, reference)
                captured['solver_ns'] = time.perf_counter_ns() - solver_start
                captured['solutions'] = solutions
                return tuple(solutions[-1].input_trajectory[0])

            ns = {'np': np, 'plan2control': solve}
            exec(self.conversion, ns)
            control = ns['traj2control'](plan, dict(ego_velo=velocity, ego_steer=steering))
            solutions = captured['solutions']
            # Include receipt construction in adapter latency; JSON transport is outside it.
            numerical = dict(input=dict(plan=array_record(plan), velocity=float(velocity), steering=float(steering)),
                             state=array_record(captured['state']), reference=array_record(captured['reference']),
                             iterations=len(solutions)-1, stop_reason=self.solver.execution['stop_reason'],
                             norms=self.solver.execution['norms'], control=list(control),
                             iterates=[solution_record(s) for s in solutions],
                             final_input=array_record(solutions[-1].input_trajectory),
                             final_state=array_record(solutions[-1].state_trajectory))
            if not np.isfinite(numerical['norms']).all():
                raise ValueError('nonfinite norm')
            digest = sha(canonical(numerical))
            adapter_ns = time.perf_counter_ns() - start
            return dict(schema='sentinel.iter137.execution.v1', status='completed', mode=self.mode,
                        source_sha256=SOURCE_HASHES, configuration=self.configuration,
                        numerical=numerical, numerical_sha256=digest,
                        timing=dict(solver_ns=captured['solver_ns'], adapter_ns=adapter_ns,
                                    deadline_reads=self.solver.execution['deadline_reads'],
                                    solver_miss=captured['solver_ns'] > 50_000_000,
                                    adapter_miss=adapter_ns > 50_000_000))
        except Exception as exc:
            return dict(schema='sentinel.iter137.execution.v1', status='failed', mode=self.mode,
                        stop_reason='failure', error_type=type(exc).__name__, error=str(exc),
                        control=None, adapter_ns=time.perf_counter_ns()-start)
