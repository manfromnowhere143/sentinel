"""Mechanical optimizer/accounting regressions; registered twelve cases are not run."""

import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.iter153_action_feasibility.check import motion
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter168_control_connector.check import verify_trace
from experiments.iter169_full_horizon_control import runtime, shooting
from experiments.iter169_full_horizon_control.check import accounting, evaluation_check

ROOT = Path(__file__).resolve().parents[1]
OLD = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())
PLAN = dict(
    attempt_budget=8192,
    per_run_seconds=30,
    max_rss_bytes=2**30,
    optimizer_max_nfev=100,
    optimizer_tolerance=1e-12,
    optimizer_diff_step=1e-6,
    actuator_guidance_scale=1e-6,
)


def case():
    return dict(
        geometry=dict(
            reset=[0.0, 0.0, 0.0, 1.3, 0.0],
            route=[[0.0, i / 4] for i in range(81)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators={},
        ),
        task=dict(
            target=[4.0, 0.2, 0.1, 1.5, 0.0],
            terminal_frame=3,
            tolerance=[0.02, 0.02, 0.002, 0.01, 0.002],
            wait_until=0,
            stop_from=None,
        ),
        points=[[10.0, 0.5, 10.0]],
        ground=np.eye(4)[None].tolist(),
    )


def execute(c, plan=None):
    q = query_for(c)
    ev = []
    req = []
    result = shooting.search(
        c["geometry"],
        c["task"],
        OLD,
        plan or PLAN,
        lambda s: summary(q(s)),
        lambda kind, row: (req if kind == "request" else ev).append(row),
    )
    trace = result.pop("trace")
    result["materialization_queries"] = len(trace)
    return ev, req, trace, result, q


def test_explicit_stop_and_wait_parameterization():
    c = case()
    c["geometry"]["reset"] = [0.0, 0.0, 0.0, 0.37, 0.0]
    c["task"].update(terminal_frame=3, stop_from=1, target=[0.0, 0.0, 0.0, 0.0, 0.0])
    ev, req, trace, result, q = execute(c)
    assert result["complete"] and result["attempts"] == 3 and not result["optimizer"]["started"]
    assert trace[1]["action"] == [-1.48, 0.0] and all(r["state"][3] == 0 for r in trace[1:])
    accounting(ev, req, trace, result, c, OLD, PLAN)
    verify_trace(
        trace,
        c,
        OLD,
        lambda f: np.packbits(q(trace[f]["state"]).mask, bitorder="little").tobytes(),
        True,
    )
    c["geometry"]["reset"] = [0.0, 0.0, 0.0, 0.0, 0.07]
    c["task"].update(wait_until=3, stop_from=None, target=c["geometry"]["reset"])
    ev, req, trace, result, q = execute(c)
    assert result["complete"] and result["attempts"] == 3 and not result["optimizer"]["started"]
    accounting(ev, req, trace, result, c, OLD, PLAN)


def test_optimizer_uses_terminal_state_on_separate_three_frame_toy():
    c = case()
    state = c["geometry"]["reset"]
    for action in ([0.3, 0.05], [0.2, -0.04], [0.4, 0.02]):
        state = motion(state, action)
    c["task"].update(target=state, tolerance=[1e-4] * 5)
    ev, req, trace, result, q = execute(c)
    assert result["optimizer"]["started"] and result["complete"]
    assert result["attempts"] > 3 and result["stop"] == "qualified_candidate"
    assert result["optimizer"]["success"] is None  # Early valid path is not convergence.
    accounting(ev, req, trace, result, c, OLD, PLAN)
    verify_trace(
        trace,
        c,
        OLD,
        lambda f: np.packbits(q(trace[f]["state"]).mask, bitorder="little").tobytes(),
        True,
    )


def test_optimizer_success_is_not_task_completion(monkeypatch):
    def fake(fun, x, **kwargs):
        fun(x)
        return SimpleNamespace(
            x=x, success=True, status=1, message="mock converged", nit=1, nfev=1, njev=0
        )

    monkeypatch.setattr(shooting, "least_squares", fake)
    c = case()
    ev, req, trace, result, q = execute(c)
    assert result["optimizer"]["success"] and not result["complete"]
    accounting(ev, req, trace, result, c, OLD, PLAN)
    bad = copy.deepcopy(result)
    bad["complete"] = True
    with pytest.raises(ValueError, match="result_complete"):
        accounting(ev, req, trace, bad, c, OLD, PLAN)


def test_full_rollout_reservation_and_accounted_budget():
    c = case()
    plan = dict(PLAN, attempt_budget=2)
    ev, req, trace, result, q = execute(c, plan)
    assert result["attempts"] == 0 and result["unused_attempt_budget"] == 2
    assert result["stop"] == "attempt_budget" and len(trace) == 1
    accounting(ev, req, trace, result, c, OLD, plan)
    bad = dict(result, attempts=1)
    with pytest.raises(ValueError, match="transition_budget"):
        accounting(ev, req, trace, bad, c, OLD, plan)


def test_exact_cache_and_rejected_cache_identity(monkeypatch):
    def fake(fun, x, **kwargs):
        fun(x)
        fun(x)
        fun(x)
        return SimpleNamespace(
            x=x, success=False, status=0, message="mock limit", nit=1, nfev=2, njev=0
        )

    monkeypatch.setattr(shooting, "least_squares", fake)
    c = case()
    ev, req, trace, result, q = execute(c)
    assert result["evaluations"] == 1 and result["attempts"] == 3 and result["cache_hits"] == 4
    accounting(ev, req, trace, result, c, OLD, PLAN)
    bad = copy.deepcopy(req)
    bad[1]["values"][0] += 0.01
    with pytest.raises(ValueError, match="cache_identity"):
        accounting(ev, bad, trace, result, c, OLD, PLAN)


def test_analytic_phase_does_not_hide_out_of_bound_braking(monkeypatch):
    monkeypatch.setattr(
        shooting,
        "least_squares",
        lambda fun, x, **kw: SimpleNamespace(
            x=x, success=False, status=0, message="mock fail", nit=1, nfev=1, njev=0
        ),
    )
    c = case()
    c["geometry"]["reset"][3] = 6.0
    c["task"].update(terminal_frame=1, stop_from=1, target=[0.0, 0.0, 0.0, 0.0, 0.0])
    ev, req, trace, result, q = execute(c)
    assert ev[0]["trace"][1]["action"][0] == -24 and ev[0]["trace"][1]["reason"] == "controls"
    assert not ev[0]["eligible"] and not result["complete"] and len(trace) == 1
    accounting(ev, req, trace, result, c, OLD, PLAN)
    bad = copy.deepcopy(ev[0])
    bad["eligible"] = True
    with pytest.raises(ValueError, match="evaluation_eligible"):
        evaluation_check(bad, c, OLD, trace[0])


def test_nonfinite_parameters_rejected():
    c = case()
    controls = shooting.Controls(c["geometry"]["reset"], c["task"])
    v = controls.initial()
    v[0] = math.nan
    with pytest.raises(ValueError, match="parameter_domain"):
        controls.table(v)


def test_invalid_task_clock_rejected():
    c = case()
    c["task"]["terminal_frame"] = 1.5
    with pytest.raises(ValueError, match="task_horizon"):
        shooting.Controls(c["geometry"]["reset"], c["task"])


def test_deadline_before_evaluation_has_no_hidden_work():
    c = case()
    q = query_for(c)
    rows = []
    e = shooting.Evaluator(
        c["geometry"],
        c["task"],
        OLD,
        PLAN,
        lambda s: summary(q(s)),
        lambda kind, row: rows.append((kind, row)),
    )
    e.started -= 31
    with pytest.raises(shooting.StopEvaluation, match="time_budget"):
        e.evaluate(e.controls.initial(), "initial")
    assert e.attempts == e.evaluations == 0 and rows[-1][1]["stopped"] == "time_budget"


def test_false_background_label_and_objective_rejected(monkeypatch):
    monkeypatch.setattr(
        shooting,
        "least_squares",
        lambda fun, x, **kw: SimpleNamespace(
            x=x, success=False, status=0, message="mock limit", nit=1, nfev=1, njev=0
        ),
    )
    c = case()
    ev, req, trace, result, q = execute(c)
    bad = copy.deepcopy(ev[0])
    bad["trace"][1]["background"]["decision"] = "collision"
    with pytest.raises(ValueError, match="background_label"):
        evaluation_check(bad, c, OLD, trace[0])
    bad = copy.deepcopy(ev[0])
    bad["objective"] += 1
    with pytest.raises(ValueError, match="numeric_replay"):
        evaluation_check(bad, c, OLD, trace[0])
    bad = copy.deepcopy(ev[0])
    bad["constraints"][0] += 1
    with pytest.raises(ValueError, match="numeric_replay"):
        evaluation_check(bad, c, OLD, trace[0])


def test_runtime_mismatch_rejected(monkeypatch):
    monkeypatch.setattr(runtime, "read", lambda *a: json.dumps({"version": 1}).encode())
    monkeypatch.setattr(runtime, "identity", lambda: {"version": 2})
    with pytest.raises(ValueError, match="runtime_identity"):
        runtime.verify(ROOT)


def test_invalid_tolerance_cannot_change_units_silently():
    c = case()
    c["task"]["tolerance"][0] = 0
    with pytest.raises(ValueError, match="tolerance_domain"):
        shooting.Controls(c["geometry"]["reset"], c["task"])


def test_intermediate_background_rejection_blocks_terminal_candidate(monkeypatch):
    c = case()
    q = query_for(c)
    initial = summary(q(c["geometry"]["reset"]))
    calls = []

    def query(state):
        calls.append(state)
        if len(calls) == 1:
            return initial
        return dict(
            initial, count=101, certain_inside=101, possible_inside=101, decision="collision"
        )

    monkeypatch.setattr(
        shooting,
        "least_squares",
        lambda fun, x, **kw: SimpleNamespace(
            x=x, success=False, status=0, message="mock cap", nfev=1, njev=0
        ),
    )
    state = c["geometry"]["reset"]
    for _ in range(3):
        state = motion(state, [0.0, 0.0])
    c["task"]["target"] = state
    result = shooting.search(c["geometry"], c["task"], OLD, PLAN, query, lambda kind, row: None)
    assert not result["complete"] and result["selected_evaluation"] is None
    assert len(result["trace"]) == 1


def test_unobserved_clock_and_optimizer_flags_rejected(monkeypatch):
    monkeypatch.setattr(
        shooting,
        "least_squares",
        lambda fun, x, **kw: SimpleNamespace(
            x=x, success=False, status=0, message="mock cap", nfev=1, njev=0
        ),
    )
    c = case()
    ev, req, trace, result, q = execute(c)
    bad = copy.deepcopy(ev[0])
    bad["trace"][1]["frame"] = 2
    with pytest.raises(ValueError, match="evaluation_clock"):
        evaluation_check(bad, c, OLD, trace[0])
    bad = copy.deepcopy(result)
    bad["optimizer"].update(returned=False, success=True)
    with pytest.raises(ValueError, match="unobserved_optimizer_status"):
        accounting(ev, req, trace, bad, c, OLD, PLAN)
