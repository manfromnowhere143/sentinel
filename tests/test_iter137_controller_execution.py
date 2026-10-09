"""Known-bads, branch boundaries, and source-oracle parity for the CPU contract."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.iter137_controller_execution_contract import controller as c
from experiments.iter137_controller_execution_contract import verify as v
from experiments.iter137_controller_execution_contract import benchmark as b


@pytest.fixture(scope='module')
def case():
    return c.load_corpus()[0]


@pytest.fixture(scope='module')
def receipt(case):
    return c.Controller('numerical').run(np.array(case['plan'], dtype=case['dtype']), case['velocity'], case['steering'])


@pytest.fixture(scope='module')
def oracle():
    return v.Replay()


class Clock:
    def __init__(self, values):
        self.values = iter(values)
        self.reads = 0

    def __call__(self):
        self.reads += 1
        return next(self.values)


@pytest.mark.parametrize('dtype', ['float32', 'float64'])
@pytest.mark.parametrize('deadline', [1, 5, 27, 38, 100])
def test_scripted_clock_parity_with_unmodified_source(case, dtype, deadline):
    case = {**case, 'dtype': dtype}
    _, state, ref = v.convert(case)
    original, params, _ = c.load_source(instrument=False)
    adapter = c.Controller('timed')
    values = [0.0] + [0.0] * (deadline-1) + [.05] * 100
    a, z = Clock(values), Clock(values)
    adapter.solver.clock = a
    original.time = SimpleNamespace(perf_counter=z)
    expected = original.ILQRSolver(params.solver_params, params.warm_start_params).solve(state, ref)
    actual = adapter.solver.solve(state, ref)
    assert a.reads == z.reads
    assert len(actual) == len(expected)
    assert [c.solution_record(s) for s in actual] == [c.solution_record(s) for s in expected]
    assert c.array_record(actual[-1].input_trajectory) == c.array_record(expected[-1].input_trajectory)


def test_numerical_outputs_ignore_clock(case):
    _, state, ref = v.convert(case)
    rows = []
    for value in (0., 10_000.):
        adapter = c.Controller('numerical')
        adapter.solver.clock = Clock([0.] + [value] * 100)
        rows.append([c.solution_record(s) for s in adapter.solver.solve(state, ref)])
    assert rows[0] == rows[1]


@pytest.mark.parametrize('norm,elapsed,limit,mode,reason,reads', [
    (0., .05, 100, 'timed', 'converged', [None]),
    (1e-6, .05, 100, 'timed', 'deadline', [.05]),
    (1e-6, .049999999, 1, 'timed', 'iteration_limit', [.049999999]),
    (1e-6, .05, 1, 'timed', 'deadline', [.05]),
    (1e-6, 1000., 1, 'numerical', 'iteration_limit', [1000.]),
    (0., 1000., 1, 'timed', 'converged', [None]),
])
def test_actual_solver_branch_precedence(norm, elapsed, limit, mode, reason, reads):
    adapter = c.Controller(mode)
    solver = adapter.solver
    solver._solver_params = replace(solver._solver_params, max_ilqr_iterations=limit)
    initial = np.zeros((6, 2))
    updated = initial.copy()
    updated[0, 0] = norm
    def iterate(inputs):
        return SimpleNamespace(input_trajectory=inputs, state_trajectory=np.zeros((7, 5)))
    solver._input_warm_start = lambda *args: iterate(initial)
    solver._compute_tracking_cost = lambda **kwargs: 0.
    solver._run_lqr_backward_recursion = lambda **kwargs: None
    solver._update_inputs_with_policy = lambda **kwargs: updated
    solver._run_forward_dynamics = lambda state, inputs: iterate(inputs)
    solver.clock = Clock([0., elapsed])
    solver.solve(np.zeros(5), np.zeros((7, 5)))
    assert solver.execution['stop_reason'] == reason
    assert solver.execution['deadline_reads'] == reads


@pytest.mark.parametrize('bad', ['source', 'symlink', 'corpus'])
def test_rejects_source_and_corpus_mutation(tmp_path, bad):
    if bad == 'corpus':
        path = tmp_path / 'corpus.json'
        data = json.loads((c.ROOT / 'corpus.json').read_text())
        data['cases'][0]['velocity'] += .1
        path.write_text(json.dumps(data))
        with pytest.raises(ValueError):
            c.load_corpus(path)
    else:
        shutil.copytree(c.SOURCE, tmp_path / 'source')
        target = tmp_path / 'source/lqr.py.txt'
        if bad == 'source':
            target.write_text(target.read_text() + '\n# mutation\n')
        else:
            target.unlink()
            target.symlink_to(c.SOURCE / 'lqr.py.txt')
        with pytest.raises(ValueError):
            c.Controller('numerical', tmp_path / 'source')
        with pytest.raises(ValueError):
            v.Replay(tmp_path / 'source')


@pytest.mark.parametrize('plan,velocity,steering', [
    ([[0., 1.]]*6, 1., 0.), (np.zeros((6, 2), dtype=np.float16), 1., 0.),
    (np.zeros((5, 2)), 1., 0.), (np.full((6, 2), np.nan), 1., 0.),
    (np.zeros((6, 2)), float('inf'), 0.), (np.zeros((6, 2)), True, 0.),
    (np.zeros((6, 2)), 1., float('nan')),
])
def test_invalid_input_is_explicit_failure(plan, velocity, steering):
    result = c.Controller('numerical').run(plan, velocity, steering)
    assert result['status'] == 'failed' and result['control'] is None
    assert result['stop_reason'] == 'failure'


@pytest.mark.parametrize('kind', ['nonfinite', 'shape'])
def test_invalid_solver_output_is_explicit_failure(case, kind):
    adapter = c.Controller('numerical')
    result = SimpleNamespace(input_trajectory=np.full((6, 2), np.nan) if kind == 'nonfinite' else np.zeros((5, 2)),
                             state_trajectory=np.zeros((7, 5)), tracking_cost=0.)
    adapter.solver.solve = lambda *args: [result, result]
    adapter.solver.execution = dict(norms=[0.], stop_reason='converged', deadline_reads=[None])
    row = adapter.run(np.array(case['plan']), case['velocity'], case['steering'])
    assert row['status'] == 'failed' and row['control'] is None


def test_independent_replay_matches(case, receipt, oracle):
    assert oracle.check(receipt, case, 'numerical') == receipt['numerical_sha256']


@pytest.mark.parametrize('mutation', ['input', 'config', 'output', 'norm', 'reason', 'source',
                                     'adapter_miss', 'solver_miss', 'skipped_read', 'duration', 'digest'])
def test_independent_replay_rejects_known_bads(case, receipt, oracle, mutation):
    row = deepcopy(receipt)
    if mutation == 'input':
        row['numerical']['input']['velocity'] += .1
    elif mutation == 'config':
        row['configuration']['solver']['max_ilqr_iterations'] = 99
    elif mutation == 'output':
        row['numerical']['control'][0] += .001
    elif mutation == 'norm':
        row['numerical']['norms'][-1] = 1.
    elif mutation == 'reason':
        row['numerical']['stop_reason'] = 'deadline'
    elif mutation == 'source':
        row['source_sha256']['lqr.py'] = '0'*64
    elif mutation in ('adapter_miss', 'solver_miss'):
        row['timing'][mutation] = not row['timing'][mutation]
    elif mutation == 'skipped_read':
        row['timing']['deadline_reads'][-1] = 0.
    elif mutation == 'duration':
        row['timing']['adapter_ns'] = -1
    row['numerical_sha256'] = c.sha(c.canonical(row['numerical'])) if mutation != 'digest' else '0'*64
    with pytest.raises(ValueError):
        oracle.check(row, case, 'numerical')


@pytest.mark.parametrize('duration,miss', [(49_999_999, False), (50_000_000, False), (50_000_001, True)])
def test_deadline_accounting_strict_boundary(duration, miss):
    v.check_termination(dict(iterations=1, norms=[0.], stop_reason='converged'),
                        dict(deadline_reads=[None], adapter_ns=duration, solver_ns=duration,
                             adapter_miss=miss, solver_miss=miss), 'numerical')


@pytest.mark.parametrize('mutation', ['missing', 'reorder', 'repeat', None])
def test_full_schedule_and_exact_repeat_gate(mutation):
    cases = [dict(id='fixture')]
    rows = [dict(block=i, case_id='fixture', load=load, numerical_sha256='same',
                 numerical=dict(stop_reason='converged', iterations=1),
                 timing=dict(adapter_ns=1, solver_ns=1, adapter_miss=False, solver_miss=False))
            for i, (mode, load) in enumerate(v.SCHEDULE)]
    replay = SimpleNamespace(check=lambda row, case, mode: row['numerical_sha256'])
    if mutation == 'missing':
        rows.pop()
    elif mutation == 'reorder':
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == 'repeat':
        rows[-1]['numerical_sha256'] = 'changed'
    if mutation:
        with pytest.raises(ValueError):
            v.verify_rows(rows, cases, replay)
    else:
        report = v.verify_rows(rows, cases, replay)
        assert report['numerical_identical_cases'] == 1
        assert report['groups']['numerical/idle']['calls'] == 2
        assert report['groups']['timed/idle']['adapter_ms']['p99'] == 1e-6


def test_benchmark_refuses_existing_output(tmp_path):
    with pytest.raises(ValueError, match='retries forbidden'):
        b.run(SimpleNamespace(output=tmp_path))


def test_benchmark_refuses_insufficient_instance_budget(tmp_path):
    with pytest.raises(ValueError, match='budget'):
        b.run(SimpleNamespace(output=tmp_path/'new', instance_deadline=0))
    assert not (tmp_path/'new').exists()


def test_registered_corpus_and_schedule():
    assert len(c.load_corpus()) == 114
    assert b.SCHEDULE == v.SCHEDULE
    assert [x['id'] for x in c.load_corpus()][:2] == ['a:00:float32', 'a:00:float64']
    assert c.load_corpus()[-1]['id'] == 'b:28:float64'
    assert not any('controller' in n for n in v.__dict__ if not n.startswith('__'))
    assert Path(v.__file__).is_file()
