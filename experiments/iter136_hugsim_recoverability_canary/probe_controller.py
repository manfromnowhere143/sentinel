"""Registered CPU-only diagnostic of the source-bound iLQR stopping clock."""

import ast
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


ROOT = Path('/opt/sentinel-stack/HUGSIM')
CONTROL = Path('/datasets/nuscenes-full/hugsim/iter136_control_20261009_v2')
TRACE = Path('/datasets/nuscenes-full/hugsim/outputs/iter136-20261009-v2/'
             'reference_a/scene-0411_hard_00/iter136_trace.jsonl')


class DeadlineClock:
    def __init__(self, iteration):
        self.iteration = iteration
        self.reads = 0

    def perf_counter(self):
        self.reads += 1
        return 0.05 if self.reads > self.iteration else 0.0


def main():
    manifest = json.loads((CONTROL / 'runtime_manifest.json').read_text())
    sources = {}
    for name in ('sim/ilqr/lqr.py', 'sim/ilqr/lqr_solver.py', 'sim/ilqr/utils.py',
                 'sim/utils/sim_utils.py'):
        path = ROOT / name
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if path.is_symlink() or digest != manifest['files'][str(path)]:
            raise ValueError('source identity')
        sources[name] = digest
    raw = TRACE.read_bytes()
    frame = json.loads(raw.splitlines()[1])
    sys.path.insert(0, str(ROOT))
    from sim.ilqr import lqr, lqr_solver

    tree = ast.parse((ROOT / 'sim/utils/sim_utils.py').read_text())
    node, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'traj2control']
    function = compile(ast.Module(body=[node], type_ignores=[]), '<exact-traj2control>', 'exec')
    conditions = [('real', None, i) for i in range(3)] + [
        ('controlled', limit, repeat) for limit in (1, 5, 10, 20, 100) for repeat in range(2)]
    records = []
    for dtype in ('float32', 'float64'):
        for mode, limit, repeat in conditions:
            clock = time if mode == 'real' else DeadlineClock(limit)
            lqr_solver.time = clock
            solver = lqr_solver.ILQRSolver(lqr.solver_params, lqr.warm_start_params)
            captured = {}

            def convert(plan, state):
                solutions = solver.solve(state, plan)
                captured.update(
                    solution_count=len(solutions),
                    first_control_iterates=[s.input_trajectory[0].tolist() for s in solutions],
                    final_tracking_cost=solutions[-1].tracking_cost,
                )
                return tuple(solutions[-1].input_trajectory[0])

            namespace = {'np': np, 'plan2control': convert}
            exec(function, namespace)
            start = time.perf_counter()
            control = namespace['traj2control'](
                np.array(frame['executed_plan'], dtype=dtype), frame['before'])
            records.append(dict(dtype=dtype, clock=mode, deadline_iteration=limit, repeat=repeat,
                                elapsed_seconds=time.perf_counter()-start,
                                clock_reads=None if mode == 'real' else clock.reads,
                                control=list(control), **captured))
    lqr_solver.time = time
    print(json.dumps(dict(schema='sentinel.iter136.controller_probe.v1',
                          scope='CPU source fixture only; no simulation episode',
                          source_sha256=sources, input_trace_sha256=hashlib.sha256(raw).hexdigest(),
                          input_frame=0, numpy_version=np.__version__, records=records),
                     sort_keys=True, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
