"""Connector substitution controls; none execute the four registered cases."""

import copy
import json
import os
from pathlib import Path

import pytest

from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter174_forward_integrated_rrt import adapter, check, contract, runtime
from tests.test_iter169_full_horizon_control import case, OLD
from tests.test_iter172_integrated_rrt import PLAN as PREVIOUS

ROOT = Path(__file__).resolve().parents[1]
PLAN = dict(PREVIOUS, max_proposals=4096)
BASE = Path("experiments/iter174_forward_integrated_rrt")


def collect(budget=12):
    c = case()
    q = query_for(c)
    events = []
    plan = dict(PLAN, attempt_budget=budget, connection_attempt_budget=min(1024, budget))
    edges = adapter.Edges(c["geometry"], OLD, plan, lambda s: summary(q(s)),
                          lambda kind, row: events.append(dict(kind=kind, **row)))
    edges.directed([*c["geometry"]["reset"], 0], [1., .1, .03, 1.2, .02, 3.])
    row = events[-1]
    check.connection_check(row, events[:-1], c, OLD, plan, budget)
    return c, plan, edges, row, events[:-1]


def test_bound_forward_edges_are_admitted_without_optimizer():
    _, _, edges, row, events = collect()
    assert row["result"]["attempts"] == edges.attempts == 12
    assert row["result"]["optimizer"]["started"] is False
    assert row["result"]["optimizer"]["returned"] is False
    requests = [r for r in events if r["kind"] == "request"]
    assert requests[0]["caller"] == "initial"
    assert all(r["caller"] == "forward_proposal" for r in requests[1:])
    assert requests[-1]["stopped"] == "attempt_budget"


def test_insufficient_outer_reservation_runs_no_generator():
    _, _, edges, row, events = collect(2)
    assert not events and edges.attempts == 0 and row["result"] is None
    assert row["stop"] == "attempt_reservation" and edges.stopped()


@pytest.mark.parametrize("mutation", ["caller", "optimizer", "attempts", "phase"])
def test_integration_corruptions_rejected(mutation):
    c, plan, _, row, events = collect()
    row, events = copy.deepcopy(row), copy.deepcopy(events)
    if mutation == "caller":
        events[0]["caller"] = "residual"
    if mutation == "optimizer":
        row["result"]["optimizer"]["started"] = True
    if mutation == "attempts":
        row["result"]["attempts"] -= 1
    if mutation == "phase":
        row["task"]["wait_until"] = 1
    with pytest.raises(ValueError):
        check.connection_check(row, events, c, OLD, plan, plan["attempt_budget"])


@pytest.mark.parametrize("key", ["attempt_budget", "per_run_seconds", "connection_horizon", "seeds"])
def test_preserved_contract_rejects_changed_limits_or_population(key):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    contract.check_contract(ROOT, plan)
    plan[key] = [1, 2, 3, 4] if key == "seeds" else plan[key] + 1
    with pytest.raises(ValueError, match="changed_contract:" + key):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize("mutation", ["sampler", "runtime", "proposal_cap"])
def test_only_connector_substitution_allowed(monkeypatch, mutation):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    original = contract.read

    def altered(root, path):
        data = original(root, path)
        if mutation == "sampler" and str(path) == str(BASE / "adapter.py"):
            return data.replace(b"rng.uniform(-3, 3)", b"rng.uniform(-2, 2)")
        if mutation == "runtime" and str(path) == str(BASE / "RUNTIME.json"):
            return data + b" "
        return data

    monkeypatch.setattr(contract, "read", altered)
    if mutation == "proposal_cap":
        plan["max_proposals"] -= 1
    with pytest.raises(ValueError, match={"sampler": "adapter_scope", "runtime": "unchanged_runtime",
                                         "proposal_cap": "proposal_cap"}[mutation]):
        contract.check_contract(ROOT, plan)


def test_native_forward_completion_respects_absolute_final_checkpoint():
    library = os.environ.get("SENTINEL_RRT172_LIBRARY")
    if not library:
        pytest.skip("retained native sequence bridge unavailable")
    c = case()
    g = c["geometry"]
    g["reset"] = [.5, 0., 0., 2., 0.]
    g["route"] = [[0., i/10] for i in range(11)]
    g["comparators"] = {"final": dict(hazard_time=8., rc=0.)}
    q = query_for(c)
    result = adapter.search(Path(library), g, OLD, PLAN, lambda s: summary(q(s)),
                            lambda *args: None, 17401, start_frame=31)
    assert result["complete"] and result["native_status"] == 2
    assert result["attempts"] == 1 and result["trace"][-1]["frame"] == 32
    assert result["selected_connections"] == [1]


def test_tree_diagnostics_count_distinct_branches_without_calling_them_cases():
    reset = [0.] * 5
    connections = {
        1: dict(before=[*reset, 0], result={}, trace=[dict(frame=0), dict(frame=16)]),
        2: dict(before=[*reset, 16], result={}, trace=[dict(frame=16), dict(frame=32)]),
        3: dict(before=[*reset, 0], result={}, trace=[dict(frame=0), dict(frame=16)]),
        4: dict(before=[*reset, 32], result=None),
    }
    assert check.tree_summary(connections, reset) == dict(max_tree_frame=32,
                                                         checkpoint_crossings=3, root_connections=2)


def test_changed_native_library_rejected_before_execution(monkeypatch, tmp_path):
    library = tmp_path / "wrong.dylib"
    library.write_bytes(b"wrong")
    monkeypatch.setattr(runtime, "read", lambda *args: json.dumps({"bridge_sha256": "0"*64}).encode())
    with pytest.raises(ValueError, match="bridge_identity"):
        runtime.verify(tmp_path, library)
