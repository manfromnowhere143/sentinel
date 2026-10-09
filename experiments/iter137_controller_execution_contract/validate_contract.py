"""Same-runtime, source-oracle validation before the measured fresh-process blocks."""

import json
from types import SimpleNamespace

import numpy as np

from controller import Controller, load_corpus, load_source, solution_record
from verify import Replay, convert


class Clock:
    def __init__(self, iteration):
        self.iteration = iteration
        self.reads = 0

    def __call__(self):
        self.reads += 1
        return .05 if self.reads > self.iteration else 0.


def main():
    checks = []
    for case in load_corpus()[:2]:
        _, state, reference = convert(case)
        for deadline in (1, 5, 27, 38, 100):
            original, params, _ = load_source(instrument=False)
            original_clock, adapter_clock = Clock(deadline), Clock(deadline)
            original.time = SimpleNamespace(perf_counter=original_clock)
            solver = original.ILQRSolver(params.solver_params, params.warm_start_params)
            expected = solver.solve(state, reference)
            adapter = Controller('timed')
            adapter.solver.clock = adapter_clock
            actual = adapter.solver.solve(state, reference)
            assert [solution_record(s) for s in actual] == [solution_record(s) for s in expected]
            assert original_clock.reads == adapter_clock.reads
            checks.append(dict(dtype=case['dtype'], deadline_iteration=deadline,
                               iterations=len(actual)-1, clock_reads=adapter_clock.reads, status='matched'))
        numerical = Controller('numerical').run(np.array(case['plan'], dtype=case['dtype']), case['velocity'], case['steering'])
        Replay().check(numerical, case, 'numerical')
    print(json.dumps(dict(status='passed', numpy=np.__version__, scripted_clock_checks=checks,
                          independent_numerical_replays=2, benchmark_calls=0), indent=2))


if __name__ == '__main__':
    main()
