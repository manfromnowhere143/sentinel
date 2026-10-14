"""Mechanical positive controls and retained known-bads; no study outcomes asserted."""

import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest

from experiments.iter153_action_feasibility.planner import reference, transition
from experiments.iter153_action_feasibility.check import motion
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter168_control_connector.check import (
    physical,
    verify_trace,
    coverage_check,
    accounting,
)
from experiments.iter168_control_connector.controls import proposals
from experiments.iter168_control_connector.connector import reached, search

ROOT = Path(__file__).resolve().parents[1]
OLD = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())


def case():
    return dict(
        geometry=dict(
            reset=[0.0, 0.0, 0.0, 0.0, 0.0],
            route=[[0.0, k / 4] for k in range(81)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators={},
        ),
        task=dict(
            target=[0.0, 0.0, 0.0, 0.0, 0.0],
            terminal_frame=3,
            tolerance=[0.02, 0.02, 0.002, 0.01, 0.002],
            wait_until=3,
            stop_from=None,
        ),
        points=[[10.0, 0.5, 10.0]],
        ground=np.eye(4)[None].tolist(),
    )


def execute(depth=1, budget=1000):
    c = case()
    q = query_for(c)
    plan = dict(attempt_budget=budget, max_actions=16, per_run_seconds=20, max_rss_bytes=2**30)
    attempts, calls = [], []
    result = search(
        c["geometry"],
        c["task"],
        OLD,
        plan,
        lambda s: summary(q(s)),
        lambda kind, row: (attempts if kind == "attempt" else calls).append(row),
        depth,
    )
    trace = result.pop("trace")
    result.update(depth=depth, materialization_queries=len(trace))
    return c, q, plan, attempts, calls, trace, result


def test_scalar_and_producer_motion_for_fractional_braking():
    path, arc = reference([[0, 0], [0, 20]], dict(offset=0, start=0, length=10), OLD)
    for v in (0.007, 0.4999, 0.5001, 3.17, 6.0):
        state = [0.0, 0.0, 0.12, v, 0.0]
        choices = proposals(state, path, arc, OLD)
        braking = [-min(2.0, v * 4), 0.0]
        assert braking in choices
        assert len(choices) == len({tuple(a) for a in choices})
        assert transition(state, braking, OLD) == pytest.approx(motion(state, braking))
        assert motion(state, braking)[3] == max(0.0, v - 0.5)


@pytest.mark.parametrize("speed", [-1e-9, 6.001, float("nan"), float("inf"), True])
def test_bad_proposal_states_rejected(speed):
    with pytest.raises(ValueError, match="proposal_state_domain"):
        proposals([0.0, 0.0, 0.0, speed, 0.0], None, None, OLD)


def test_wait_trace_and_budget_accounting():
    c, q, plan, attempts, calls, trace, result = execute(2)
    assert result["complete"] and result["attempts"] > len(trace) - 1
    accounting(attempts, calls, trace, result, c, OLD, plan)
    assert (
        verify_trace(
            trace,
            c,
            OLD,
            lambda f: np.packbits(q(trace[f]["state"]).mask, bitorder="little").tobytes(),
            True,
        )["verified_states"]
        == 4
    )
    bad = copy.deepcopy(attempts)
    bad[-1]["frame"] += 1
    with pytest.raises(ValueError, match="attempt_clock"):
        accounting(bad, calls, trace, result, c, OLD, plan)
    with pytest.raises(ValueError, match="scalar_mask"):
        verify_trace(trace, c, OLD, lambda f: b"\xff", True)


def test_partial_expansion_cannot_be_used():
    c, q, plan, attempts, calls, trace, result = execute(2, 1)
    assert result["stop"] == "attempt_budget" and len(trace) == 1 and not result["complete"]
    accounting(attempts, calls, trace, result, c, OLD, plan)
    calls[0]["selected"] = 1
    with pytest.raises(ValueError, match="partial_expansion_used"):
        accounting(attempts, calls, trace, result, c, OLD, plan)


def test_early_target_is_not_a_verified_wait():
    c, q, plan, attempts, calls, trace, result = execute()
    assert not reached(trace[0]["state"], 0, c["task"])
    with pytest.raises(ValueError, match="false_completion"):
        verify_trace(trace[:1], c, OLD, lambda f: b"\x00", True)


def test_wait_stop_and_physical_known_bads():
    c = case()
    start = c["geometry"]["reset"]
    assert physical(start, motion(start, [2, 0]), [2, 0], 1, c, OLD) == "wait_contract"
    c["task"].update(wait_until=0, stop_from=1)
    assert physical(start, motion(start, [2, 0]), [2, 0], 1, c, OLD) == "stop_contract"
    assert physical(start, motion(start, [3, 0]), [3, 0], 1, c, OLD) == "controls"
    c["task"]["stop_from"] = None
    c["geometry"]["obstacles"] = [[0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]]
    assert physical(start, start, [0, 0], 1, c, OLD) == "foreground"
    c["geometry"]["obstacles"] = [[0.0, -1.6, 0.0, 0.1, 0.1, 1.0, 0.0]]
    # Endpoint boxes do not intersect, but the required .25 m swept margin does.
    c["geometry"]["obstacles"][0][1] = -0.95
    assert physical(start, start, [0, 0], 1, c, OLD) == "foreground_sweep"
    c["geometry"]["obstacles"] = []
    c["geometry"]["comparators"] = {"1": dict(hazard_time=0.25, rc=0.5)}
    assert physical(start, start, [0, 0], 1, c, OLD) == "progress"


def test_background_collision_rejected_even_with_matching_mask():
    c, q, plan, attempts, calls, trace, result = execute()
    c["points"] = [[0.0, 0.5, 0.0] for _ in range(101)]
    q = query_for(c)
    for row in trace:
        row["background"] = summary(q(row["state"]))
    with pytest.raises(ValueError, match="background_rejected"):
        verify_trace(
            trace,
            c,
            OLD,
            lambda f: np.packbits(q(trace[f]["state"]).mask, bitorder="little").tobytes(),
            True,
        )


def test_missing_braking_coverage_is_rejected():
    v = 0.2
    legacy = [[a, r * math.pi / 12] for a in (-2.0, 0.0, 2.0) for r in (-1, -0.5, 0, 0.5, 1)]
    rows = [
        dict(
            speed=v,
            legacy=legacy,
            successor=[dict(action=a, state=motion([0.0, 0.0, 0.0, v, 0.0], a)) for a in legacy],
        )
    ]
    with pytest.raises(ValueError, match="successor_population"):
        coverage_check(rows, dict(coverage_speeds=[v]))
