"""Unregistered toys and corruption controls; no registered candidate outcomes."""

import copy
import itertools
import json
from pathlib import Path
import time

import numpy as np
import pytest

from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter169_full_horizon_control.shooting import Controls, Evaluator
from experiments.iter169_full_horizon_control.check import accounting
from experiments.iter172_integrated_rrt.check import connection_check
from experiments.iter173_matched_connector_cost import check, forward, worker

ROOT = Path(__file__).resolve().parents[1]
OLD = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())
PLAN = dict(attempt_budget=64, constructive_attempt_budget=64, connection_attempt_budget=1024,
            per_run_seconds=30, max_rss_bytes=2**30, optimizer_max_nfev=100,
            optimizer_tolerance=1e-12, optimizer_diff_step=None, actuator_guidance_scale=1e-6,
            max_proposals=4096, max_actions=96, connection_horizon=8,
            target_tolerance=[.02, .02, .002, .01, .002])


def toy():
    return dict(geometry=dict(reset=[0., 0., 0., 1.3, 0.], route=[[0., i/4] for i in range(81)],
                              ego_dimensions=[1.6, 3., 1.5], obstacles=[], comparators={}),
                task=dict(target=[3., .2, .1, 1.5, .03], terminal_frame=3,
                          tolerance=PLAN["target_tolerance"], wait_until=0, stop_from=None),
                points=[[10., .5, 10.]], ground=np.eye(4)[None].tolist())


def execute(kind, arm):
    c = toy()
    req = None if kind == "constructive" else dict(before=[*c["geometry"]["reset"], 0],
        target=[*c["task"]["target"], 3], task=c["task"], budget=64)
    events = []
    result = worker.execute(c, req, arm, OLD, PLAN, lambda s: summary(query_for(c)(s)),
                            lambda k, r: events.append(dict(kind=k, **r)))
    trace = result.pop("trace")
    result["materialization_queries"] = len(trace)
    return c, req, events, result, trace


@pytest.mark.parametrize("kind", ["constructive", "request"])
@pytest.mark.parametrize("arm", ["forward", "shooting"])
def test_both_arms_share_accounting_and_hard_checks(kind, arm):
    c, req, events, result, trace = execute(kind, arm)
    assert result["attempts"] <= 64
    if arm == "forward":
        check.proposal_check(events, c["geometry"]["reset"], c["task"], 4096, result)
    if kind == "request":
        connection_check(dict(req, result=result, trace=trace, stop=result["stop"]), events,
                         c, OLD, PLAN, 64)
    else:
        requests = copy.deepcopy([r for r in events if r["kind"] == "request"])
        for r in requests:
            if r["caller"] == "forward_proposal":
                r["caller"] = "residual"
        accounting([r for r in events if r["kind"] == "evaluation"], requests, trace, result,
                   c, OLD, PLAN)


@pytest.mark.parametrize("horizon,wait,stop", [(1, 0, None), (7, 2, None), (16, 0, None), (8, 0, 3)])
def test_independent_phase_and_halton_parameters(horizon, wait, stop):
    c = toy(); c["task"].update(terminal_frame=horizon, wait_until=wait, stop_from=stop)
    controls = Controls(c["geometry"]["reset"], c["task"])
    for n, values in enumerate(itertools.islice(forward.proposals(controls), 220)):
        np.testing.assert_allclose(values, check.expected_proposal(controls.reset, c["task"], n),
                                   rtol=0, atol=2e-15)
        assert np.all(np.abs(values) <= 1)


def test_wrong_proposal_and_omitted_generation_rejected():
    c, _, events, result, _ = execute("request", "forward")
    bad = copy.deepcopy(events)
    next(r for r in bad if r["kind"] == "request")["values"][0] += .01
    with pytest.raises(ValueError):
        check.proposal_check(bad, c["geometry"]["reset"], c["task"], 4096, result)
    with pytest.raises(ValueError, match="forward_scope"):
        check.proposal_check(events, c["geometry"]["reset"], c["task"], 1, result)


def test_proposal_limit_fails_closed():
    c = toy(); q = query_for(c)
    ev = Evaluator(c["geometry"], c["task"], OLD, PLAN, lambda s: summary(q(s)), lambda *a: None)
    with pytest.raises(ValueError, match="proposal_generation_limit"):
        forward.solve(ev, False, 1)


def test_no_hidden_work_when_expired():
    c = toy(); q = query_for(c)
    ev = Evaluator(c["geometry"], c["task"], OLD, PLAN, lambda s: summary(q(s)), lambda *a: None)
    ev.started = time.monotonic()-31
    r = forward.solve(ev, False, 4096)
    assert r["attempts"] == 0 and r["stop"] == "time_budget"


def test_budget_tamper_and_wrong_absolute_clock_rejected():
    c, req, events, result, trace = execute("request", "forward")
    for field in ["attempts", "queries", "cache_hits"]:
        bad = copy.deepcopy(result); bad[field] += 1
        with pytest.raises(ValueError):
            connection_check(dict(req, result=bad, trace=trace, stop=bad["stop"]), events,
                             c, OLD, PLAN, 64)
    bad = copy.deepcopy(req); bad["before"][5] = 2
    with pytest.raises(ValueError):
        connection_check(dict(bad, result=result, trace=trace, stop=result["stop"]), events,
                         c, OLD, PLAN, 64)


def test_root_only_return_preserves_null_and_false():
    root = dict(state=[0, 0, 0, 1, 0], frame=0, route=dict(rc=.1))
    m = check.request_metrics([root], dict(before=[0,0,0,1,0,0], target=[1,0,0,1,0,3]),
                              dict(comparators={}))
    assert m["distance_gain"] is None and m["route_gain"] is None
    assert not m["improved"] and not m["admissible"]


@pytest.mark.parametrize("failure", ["constructive_complete", "improved_requests", "admissible_requests", "checkpoint_crossings"])
def test_each_scientific_acceptance_condition_fires(failure):
    a = dict(constructive_complete=14, improved_requests=10, admissible_requests=20, checkpoint_crossings=2)
    b = dict(a, improved_requests=11)
    assert check.verdict(dict(shooting=a, forward=b), 14)
    b[failure] = 13 if failure == "constructive_complete" else a[failure]-(failure != "improved_requests")
    assert not check.verdict(dict(shooting=a, forward=b), 14)


def test_cost_curve_excludes_partial_evaluation_work():
    c, req, events, _, trace = execute("request", "forward")
    rows = check.cost_curve(events, req, c["geometry"], [1, 2, 3, 64], trace[:1])
    assert rows[0]["distance_gain"] is None and rows[1]["distance_gain"] is None
    assert rows[0]["cap"] == 1 and rows[-1]["cap"] == 64


def test_retained_request_binding_and_exclusions():
    plan = json.loads((ROOT / "experiments/iter173_matched_connector_cost/PLAN.json").read_text())
    rows = check.bind_requests(ROOT, plan)
    assert len(rows) == 80 and all(r["budget"] >= r["task"]["terminal_frame"] for r in rows)


def test_request_budget_or_population_edit_is_rejected(monkeypatch):
    plan = json.loads((ROOT / "experiments/iter173_matched_connector_cost/PLAN.json").read_text())
    original = check.read
    def changed(root, name, *args):
        raw = original(root, name, *args)
        if str(name).endswith("REQUESTS.json"):
            doc = json.loads(raw)
            doc["requests"][0]["budget"] += 1
            return json.dumps(doc).encode()
        return raw
    monkeypatch.setattr(check, "read", changed)
    with pytest.raises(ValueError, match="request_population"):
        check.bind_requests(ROOT, plan)


def test_scalar_selected_mask_corruption_is_rejected(tmp_path):
    c = toy(); q = query_for(c); state = c["geometry"]["reset"]
    row = dict(state=state, frame=0, action=None, background=summary(q(state)), reason="clear")
    (tmp_path / "mask_000.bin").write_bytes(b"\x00")
    assert check.masks([row], c, tmp_path, OLD, time.monotonic()+10) == (1, 0)
    (tmp_path / "mask_000.bin").write_bytes(b"\x01")
    with pytest.raises(ValueError, match="scalar_mask"):
        check.masks([row], c, tmp_path, OLD, time.monotonic()+10)


def test_outer_time_and_output_reservations_stop_before_worker(tmp_path):
    from experiments.iter173_matched_connector_cost.run import remaining_resources
    plan = dict(search_producer_seconds=30, max_output_bytes=17000010)
    with pytest.raises(ValueError, match="producer_deadline"):
        remaining_resources(tmp_path, plan, time.monotonic()-31)
    (tmp_path / "raw").write_bytes(b"0123456789")
    with pytest.raises(ValueError, match="output_reservation"):
        remaining_resources(tmp_path, plan, time.monotonic())
