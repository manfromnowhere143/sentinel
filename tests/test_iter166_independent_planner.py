"""Physical-contract and budget known-bads, plus an optional installed native smoke."""

import ctypes as C
import math
import os
from pathlib import Path

import pytest

from experiments.iter153_action_feasibility.check import motion
from experiments.iter166_independent_planner.adapter import Edges, distance, search

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    import json

    old = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())
    geometry = dict(
        reset=[0.0, 0.0, 0.0, 2.0, 0.0],
        route=[[0.0, i / 10] for i in range(101)],
        ego_dimensions=[1.6, 3.0, 1.5],
        obstacles=[],
        comparators={},
    )
    plan = dict(attempt_budget=1000, per_run_seconds=10, max_actions=96, max_rss_bytes=2 * 1024**3)
    return geometry, old, plan


def query(state):
    return dict(decision="clear")


def test_stop_and_restart_match_independent_motion():
    geometry, old, plan = fixture()
    edges = Edges(geometry, old, plan, query, lambda *a: None)
    state = [*geometry["reset"], 25.0]
    speeds = []
    for action in [[-2.0, 0.0]] * 4 + [[0.0, 0.0]] * 4 + [[2.0, 0.0]] * 4:
        row = edges.edge(state, action)
        assert row["state"] == pytest.approx(motion(state[:5], action), abs=1e-13)
        assert row["reason"] == "clear" and row["frame"] == int(state[-1]) + 1
        state = [*row["state"], float(row["frame"])]
        speeds.append(state[3])
    assert speeds[3:8] == [0] * 5 and speeds[-1] == 2
    assert edges.attempts == edges.queries == 12


def test_budget_counts_rejected_edges():
    geometry, old, plan = fixture()
    plan["attempt_budget"] = 1
    edges = Edges(geometry, old, plan, query, lambda *a: None)
    row = edges.edge([*geometry["reset"], 0.0], [200.0, 0.0])
    assert row["reason"] == "controls" and edges.attempts == 1 and edges.queries == 0
    with pytest.raises(ValueError, match="attempt_after_budget"):
        edges.edge([*geometry["reset"], 0.0], [0.0, 0.0])


def test_checkpoint_uses_absolute_clock():
    geometry, old, plan = fixture()
    geometry["comparators"] = {"source": dict(hazard_time=7.75, rc=1.0)}
    edges = Edges(geometry, old, plan, query, lambda *a: None)
    row = edges.edge([*geometry["reset"], 30.0], [0.0, 0.0])
    assert row["reason"] == "progress" and edges.queries == 0


def test_horizon_cannot_rebase():
    geometry, old, plan = fixture()
    edges = Edges(geometry, old, plan, query, lambda *a: None)
    assert edges.edge([*geometry["reset"], 96.0], [0.0, 0.0])["reason"] == "horizon"
    assert edges.queries == 0


def test_background_ambiguity_rejected():
    geometry, old, plan = fixture()
    edges = Edges(
        geometry, old, plan, lambda _: dict(decision="numerically_ambiguous"), lambda *a: None
    )
    assert edges.edge([*geometry["reset"], 0.0], [0.0, 0.0])["reason"] == "numerically_ambiguous"


def test_foreground_sweep_checked_before_background():
    geometry, old, plan = fixture()
    geometry["reset"] = [0.0, 0.0, 0.0, 6.0, 0.0]
    geometry["ego_dimensions"] = [0.01, 0.01, 0.01]
    geometry["obstacles"] = [[0.75, 0.0, 0.0, 0.01, 0.01, 0.01, 0.0]]
    edges = Edges(geometry, old, plan, query, lambda *a: None)
    assert edges.edge([*geometry["reset"], 0.0], [0.0, 0.0])["reason"] == "foreground_sweep"
    assert edges.queries == 0


def test_distance_wraps_heading_and_accounts_clock():
    a = [0, 0, math.pi, 0, 0, 25]
    b = [0, 0, -math.pi, 0, 0, 26]
    assert distance(a, b) == pytest.approx(0.01)


def test_native_bridge_contract():
    library = os.environ.get("SENTINEL_OMPL_LIBRARY")
    if not library:
        pytest.skip("isolated OMPL runtime not installed in this test environment")
    geometry, old, plan = fixture()
    geometry["route"] = geometry["route"][:11]
    events = []
    result = search(
        Path(library),
        geometry,
        old,
        plan,
        query,
        lambda kind, row: events.append((kind, row)),
        20261014,
    )
    assert result["complete"] and result["native_status"] == 2
    assert len(result["trace"]) > 1
    for a, b in zip(result["trace"], result["trace"][1:]):
        assert b["state"] == pytest.approx(motion(a["state"], b["action"]), abs=1e-12)
    assert result["attempts"] == sum(k == "attempt" for k, _ in events)
    native = C.CDLL(library)
    native.sentinel_distance.argtypes = [C.POINTER(C.c_double)] * 2
    native.sentinel_distance.restype = C.c_double
    for a, b in [([0, 1, math.pi, 2, 0.3, 25], [2, 3, -math.pi, 3, 0.4, 26]), ([0] * 6, [1] * 6)]:
        assert native.sentinel_distance(
            (C.c_double * 6)(*a), (C.c_double * 6)(*b)
        ) == pytest.approx(distance(a, b), abs=1e-13)


def test_native_approximation_remains_incomplete():
    library = os.environ.get("SENTINEL_OMPL_LIBRARY")
    if not library:
        pytest.skip("isolated OMPL runtime not installed in this test environment")
    geometry, old, plan = fixture()
    plan["attempt_budget"] = 1
    result = search(Path(library), geometry, old, plan, query, lambda *args: None, 20261015)
    assert result["attempts"] == 1 and result["stop"] == "attempt_budget"
    assert result["complete"] is False and result["native_status"] != 2
    assert result["trace"][-1]["route"]["rc"] < 1


def test_runtime_hash_rejects_changed_bridge(tmp_path):
    from experiments.iter166_independent_planner.runtime import verify

    changed = tmp_path / "libsentinel_ompl.dylib"
    changed.write_bytes(b"not the bound adapter")
    with pytest.raises(ValueError, match="bridge_identity"):
        verify(ROOT, changed)
