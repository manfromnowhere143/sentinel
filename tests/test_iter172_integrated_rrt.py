"""Integration contract controls, distinct from the four scientific cases."""

import copy
import json
import os
from pathlib import Path
import time

import pytest

from experiments.iter153_action_feasibility.check import motion
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter172_integrated_rrt import adapter, connection, check
from tests.test_iter169_full_horizon_control import case, OLD, PLAN as LOCAL

PLAN = dict(
    LOCAL,
    attempt_budget=18000,
    per_run_seconds=120,
    max_actions=96,
    connection_horizon=8,
    connection_attempt_budget=1024,
    target_tolerance=[0.02, 0.02, 0.002, 0.01, 0.002],
    optimizer_diff_step=None,
)


def collect(c=None, before=None, target=None, plan=None):
    c = c or case()
    g = c["geometry"]
    before = before or [*g["reset"], 0.0]
    target = target or [1.0, 0.1, 0.03, 1.2, 0.02, 3.0]
    events = []
    q = query_for(c)
    edges = adapter.Edges(
        g,
        OLD,
        plan or PLAN,
        lambda s: summary(q(s)),
        lambda kind, row: events.append(dict(kind=kind, **row)),
    )
    edges.directed(before, target)
    record = events[-1]
    check.connection_check(
        record, events[:-1], c, OLD, plan or PLAN, (plan or PLAN)["attempt_budget"]
    )
    return c, edges, record, events


def evaluator(g=None, start=0, target=None, budget=8, query=None):
    c = case()
    g = g or c["geometry"]
    before = [*g["reset"], float(start)]
    target = target or [20.0, 0.0, 0.0, g["reset"][3], 0.0, float(start + 4)]
    task = connection.task_for(before, target, PLAN)
    events = []
    q = query_for(dict(c, geometry=g))
    e = connection.Evaluator(
        g,
        before,
        target,
        task,
        OLD,
        PLAN,
        budget,
        time.monotonic() + 10,
        query or (lambda s: summary(q(s))),
        lambda kind, row: events.append(dict(kind=kind, **row)),
    )
    return e, events, dict(c, geometry=g)


def test_absolute_checkpoint_and_no_rebased_clock():
    g = case()["geometry"]
    g["comparators"] = {"deadline": dict(hazard_time=4.0, rc=1.0)}
    e, events, c = evaluator(g, start=15, budget=4)
    e.evaluate(e.controls.initial(), "test")
    row = events[-1]
    assert row["trace"][1]["frame"] == 16 and row["trace"][1]["reason"] == "progress"
    assert row["valid_prefix"] == 0
    check.evaluation(row, dict(before=e.before, target=e.target, task=e.task), c, OLD)
    bad = copy.deepcopy(row)
    bad["trace"][1]["frame"] = 1
    with pytest.raises(ValueError, match="absolute_clock"):
        check.evaluation(bad, dict(before=e.before, target=e.target, task=e.task), c, OLD)


def test_premature_completion_rejected_and_final_completion_terminates():
    g = case()["geometry"]
    g["reset"] = [0.5, 0.0, 0.0, 2.0, 0.0]
    g["route"] = [[0.0, i / 10] for i in range(11)]
    g["comparators"] = {"final": dict(hazard_time=8.0, rc=0.0)}
    early, ev, c = evaluator(g, start=1, budget=4)
    early.evaluate(early.controls.initial(), "test")
    assert ev[-1]["trace"][1]["reason"] == "premature_completion" and not ev[-1]["world_complete"]
    late, ev, c = evaluator(g, start=31, budget=4)
    with pytest.raises(connection.StopEvaluation, match="model_complete"):
        late.evaluate(late.controls.initial(), "test")
    assert late.attempts == 1 and ev[-1]["selected_prefix"] == 1 and not ev[-1]["full"]
    check.evaluation(ev[-1], dict(before=late.before, target=late.target, task=late.task), c, OLD)


def test_intermediate_rejection_returns_only_contiguous_prefix():
    calls = []

    def query(state):
        calls.append(state)
        return dict(
            count=101 if len(calls) == 3 else 0,
            certain_inside=101 if len(calls) == 3 else 0,
            possible_inside=101 if len(calls) == 3 else 0,
            decision="collision" if len(calls) == 3 else "clear",
        )

    e, events, c = evaluator(query=query)
    e.evaluate(e.controls.initial(), "test")
    row = events[-1]
    assert (
        row["valid_prefix"] == row["selected_prefix"] == 1 and row["trace"][3]["reason"] == "clear"
    )
    check.evaluation(
        row,
        dict(before=e.before, target=e.target, task=e.task),
        dict(c, points=[[0, 0, 0]] * 101),
        OLD,
    )
    bad = copy.deepcopy(row)
    bad["selected_prefix"] = 3
    with pytest.raises(ValueError, match="prefix_selection"):
        check.evaluation(
            bad,
            dict(before=e.before, target=e.target, task=e.task),
            dict(c, points=[[0, 0, 0]] * 101),
            OLD,
        )


def test_outer_budget_reservation_has_no_hidden_transition():
    c, edges, row, events = collect(plan=dict(PLAN, attempt_budget=2))
    assert edges.attempts == 0 and row["stop"] == "attempt_reservation" and edges.stopped()
    with pytest.raises(ValueError, match="call_after_budget"):
        edges.directed(row["before"], row["target"])


def test_inner_budget_and_derivative_accounting():
    c, edges, row, events = collect(plan=dict(PLAN, connection_attempt_budget=12))
    assert (
        row["result"]["attempts"] == 12
        and edges.attempts == 12
        and row["result"]["requests"] > row["result"]["evaluations"]
    )
    bad = copy.deepcopy(row)
    bad["result"]["attempts"] -= 1
    with pytest.raises(ValueError, match="transition_budget"):
        check.connection_check(
            bad, events[:-1], c, OLD, dict(PLAN, connection_attempt_budget=12), 18000
        )


def test_cached_reuse_and_tampered_identity():
    e, events, c = evaluator()
    values = e.controls.initial()
    e.evaluate(values, "first")
    e.evaluate(values, "repeat")
    assert e.attempts == 4 and e.cache_hits == 1
    c, edges, row, events = collect(plan=dict(PLAN, connection_attempt_budget=12))
    bad = copy.deepcopy(events[:-1])
    cached = next(r for r in bad if r["kind"] == "request" and r["cached"])
    cached["evaluation"] = 999
    with pytest.raises(ValueError, match="cache_identity"):
        check.connection_check(row, bad, c, OLD, dict(PLAN, connection_attempt_budget=12), 18000)


def test_deadline_rejects_without_work():
    e, events, c = evaluator()
    e.deadline = time.monotonic() - 1
    with pytest.raises(connection.StopEvaluation, match="time_budget"):
        e.evaluate(e.controls.initial(), "expired")
    assert e.attempts == 0 and events[-1]["stopped"] == "time_budget"


def test_horizon_target_and_no_invented_phases():
    before = [0.0, 0.0, 0.0, 1.0, 0.0, 95.0]
    target = [10.0, 0.0, 0.0, 0.0, 0.0, 10.0]
    task = connection.task_for(before, target, PLAN)
    assert task["terminal_frame"] == 1 and task["wait_until"] == 0 and task["stop_from"] is None
    check.task_check(before, target, task, PLAN)
    bad = dict(task, wait_until=1)
    with pytest.raises(ValueError, match="target_binding"):
        check.task_check(before, target, bad, PLAN)
    assert connection.task_for([*before[:5], 96.0], target, PLAN) is None
    with pytest.raises(ValueError, match="connection_clock"):
        connection.task_for([*before[:5], 95.5], target, PLAN)


@pytest.mark.parametrize("mutation", ["motion", "reason", "objective", "slacks", "prefix", "world"])
def test_attempt_corruptions_rejected(mutation):
    e, events, c = evaluator()
    e.evaluate(e.controls.initial(), "test")
    row = copy.deepcopy(events[-1])
    if mutation == "motion":
        row["trace"][1]["state"][0] += 0.1
    if mutation == "reason":
        row["trace"][1]["reason"] = "collision"
    if mutation == "objective":
        row["objective"] += 1
    if mutation == "slacks":
        row["constraints"][0] += 1
    if mutation == "prefix":
        row["valid_prefix"] -= 1
    if mutation == "world":
        row["world_complete"] = True
    with pytest.raises(ValueError):
        check.evaluation(row, dict(before=e.before, target=e.target, task=e.task), c, OLD)


@pytest.mark.parametrize("mutation", ["token", "parent", "endpoint", "duration"])
def test_sequence_token_corruptions_rejected(mutation):
    c, edges, row, events = collect(plan=dict(PLAN, connection_attempt_budget=12))
    trace = row["trace"]
    end = trace[-1]
    rows = [
        [*trace[0]["state"], trace[0]["frame"], 0.0, 0.0, 0.0],
        [*end["state"], end["frame"], float(row["call"]), 0.0, (len(trace) - 1) * 0.25],
    ]
    adapter.expand_path(rows, edges.accepted, c["geometry"]["reset"], 0, OLD)
    bad = copy.deepcopy(rows)
    accepted = copy.deepcopy(edges.accepted)
    if mutation == "token":
        bad[1][6] = 1000
    if mutation == "parent":
        accepted[row["call"]]["before"][0] += 0.1
    if mutation == "endpoint":
        bad[1][0] += 0.1
    if mutation == "duration":
        bad[1][8] += 0.25
    with pytest.raises(ValueError, match="native_"):
        adapter.expand_path(bad, accepted, c["geometry"]["reset"], 0, OLD)


def test_native_varying_control_sequence_transport(monkeypatch):
    library = os.environ.get("SENTINEL_RRT172_LIBRARY")
    if not library:
        pytest.skip("new native sequence bridge unavailable")
    c = case()
    g = c["geometry"]
    g["reset"] = [0.0, 0.0, 0.0, 2.0, 0.0]
    g["route"] = [[0.0, i / 10] for i in range(11)]
    actions = [[0.4, 0.05], [-0.4, -0.05]]

    class ScriptedEdges:
        def __init__(self, *args):
            self.started = time.monotonic()
            self.attempts = self.queries = self.calls = 0
            self.exception = None
            self.reservation_stop = False
            self.accepted = {}

        def stopped(self):
            return self.calls > 0

        def directed(self, before, target):
            self.calls += 1
            trace = [dict(id=0, parent=None, frame=0, action=None, state=before[:5])]
            state = before[:5]
            for i, action in enumerate(actions, 1):
                state = motion(state, action)
                trace.append(dict(id=i, parent=i - 1, frame=i, action=action, state=state))
            self.attempts = 2
            record = dict(call=1, before=before, trace=trace)
            self.accepted[1] = record
            return record

    monkeypatch.setattr(adapter, "Edges", ScriptedEdges)
    result = adapter.search(
        Path(library), g, OLD, PLAN, lambda s: dict(decision="clear"), lambda *args: None, 8921
    )
    assert (
        result["complete"]
        and len(result["trace"]) == 3
        and [r["action"] for r in result["trace"][1:]] == actions
    )


def test_native_approximate_path_is_not_completion():
    library = os.environ.get("SENTINEL_RRT172_LIBRARY")
    if not library:
        pytest.skip("new native sequence bridge unavailable")
    c = case()
    g = c["geometry"]
    q = query_for(c)
    result = adapter.search(
        Path(library),
        g,
        OLD,
        dict(PLAN, attempt_budget=1, connection_horizon=1),
        lambda s: summary(q(s)),
        lambda *args: None,
        8922,
    )
    assert not result["complete"] and result["native_status"] in (0, 1) and result["attempts"] == 1


def test_runtime_identity_rejects_changed_bridge(monkeypatch, tmp_path):
    from experiments.iter172_integrated_rrt import runtime

    library = tmp_path / "wrong.dylib"
    library.write_bytes(b"wrong")
    monkeypatch.setattr(
        runtime, "read", lambda *args: json.dumps({"bridge_sha256": "0" * 64}).encode()
    )
    with pytest.raises(ValueError, match="bridge_identity"):
        runtime.verify(tmp_path, library)
