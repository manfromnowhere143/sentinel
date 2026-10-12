"""Controls that distinguish covered opportunity from search/pruning failure."""

import ast
import copy
import json
import math
from pathlib import Path
import time

import pytest

from experiments.iter158_constraint_aware_search.check import verify_path
from experiments.iter159_route_search_qualification.check import audit_run, witness_loss
from experiments.iter159_route_search_qualification.common import encode
from experiments.iter159_route_search_qualification.guidance import RouteGuidance
from experiments.iter159_route_search_qualification.run import query_for, witness
from experiments.iter159_route_search_qualification.search import search
from experiments.iter158_constraint_aware_search.search import summary

ROOT = Path(__file__).resolve().parents[1]


def control(tmp_path, ranking="route", pruning="speed_groups", budget=500):
    old = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())
    geometry = dict(
        reset=[0.0, 0.0, 0.0, 2.0, 0.0],
        route=[[0.0, i / 10] for i in range(21)],
        ego_dimensions=[1.6, 3.0, 1.5],
        obstacles=[],
        comparators={},
    )
    case = dict(
        geometry=geometry,
        points=[],
        ground=[[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]],
        witness_actions=[[0.0, 0.0]] * 10,
    )
    # Empty shape is explicit in query_for's population contract, so use one
    # far-away finite point for the tiny execution control.
    case["points"] = [[100.0, 0.5, 100.0]]
    plan = dict(
        max_actions=12,
        beam_width=4,
        attempt_budget=budget,
        per_run_seconds=30,
        max_rss_bytes=1024**3,
    )
    query, events = query_for(case), {"attempt": [], "depth": []}
    result = search(
        geometry,
        old,
        plan,
        lambda s: summary(query(s)),
        lambda kind, row: events[kind].append(row),
        ranking,
        pruning,
    )
    trace = result.pop("trace")
    result.update(ranking=ranking, pruning=pruning)
    reference = witness(case, old, query)
    folder = tmp_path / "run"
    folder.mkdir()
    (folder / "selected").mkdir()
    (folder / "selected/trace.json").write_bytes(encode(trace))
    for kind, name in (("attempt", "attempts"), ("depth", "depths")):
        (folder / f"{name}.jsonl").write_bytes(b"".join(encode(r) for r in events[kind]))
    return case, old, plan, result, reference, trace, events, folder


@pytest.mark.parametrize("ranking", ["endpoint", "route"])
@pytest.mark.parametrize("pruning", ["rank", "speed_groups"])
def test_all_four_arms_complete_and_replay(ranking, pruning, tmp_path):
    case, old, plan, result, reference, trace, _, folder = control(tmp_path, ranking, pruning)
    assert result["stop"] == "model_complete"
    audit_run(folder, result, reference, plan)
    metrics = verify_path(
        trace,
        case["geometry"],
        old,
        case["points"],
        case["ground"],
        lambda _: b"\x00",
        True,
        time.monotonic() + 10,
    )
    assert metrics["selected_actions"] > 0


def test_fixed_expansion_cap_refuses_partial_depth(tmp_path):
    _, _, plan, result, reference, _, events, folder = control(tmp_path, budget=1)
    assert result["stop"] == "attempt_budget" and result["selected"] is None
    assert events["depth"][-1]["complete"] is False
    audit_run(folder, result, reference, plan)


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("beam", "beam_replay"),
        ("queries", "query_count"),
        ("count", "attempt_count"),
        ("complete", "selected_identity"),
        ("trace", "trace_binding"),
        ("survivors", "survivor_count"),
        ("depth", "depth_sequence"),
        ("parent", "parent_order"),
        ("false_empty", "false_completion"),
    ],
)
def test_changed_search_records_fail(mutation, reason, tmp_path):
    _, _, plan, result, reference, trace, events, folder = control(tmp_path)
    if mutation == "beam":
        events["depth"][0]["beam"] = [999]
    elif mutation == "queries":
        result["queries"] += 1
    elif mutation == "count":
        result["attempts"] += 1
    elif mutation == "complete":
        result["selected"] = 999
    elif mutation == "trace":
        changed = copy.deepcopy(trace)
        changed[-1]["state"][0] += 1
        (folder / "selected/trace.json").write_bytes(encode(changed))
    elif mutation == "survivors":
        events["depth"][0]["survivors"] += 1
    elif mutation == "depth":
        events["depth"][0]["frame"] = 99
    elif mutation == "parent":
        events["attempt"][1]["parent"] = 999
    elif mutation == "false_empty":
        result.update(stop="beam_empty", selected=None)
    for kind, name in (("attempt", "attempts"), ("depth", "depths")):
        (folder / f"{name}.jsonl").write_bytes(b"".join(encode(r) for r in events[kind]))
    with pytest.raises(ValueError, match=reason):
        audit_run(folder, result, reference, plan)


def toy_loss():
    row = dict(
        id=1,
        parent=0,
        frame=1,
        action=[0.0, 0.0],
        state=[0.5, 0, 0, 2, 0],
        reason="clear",
        route=dict(rc=0.1, nearest=2, distance=0),
        guide_distance=10,
        effort=0,
    )
    return [dict(id=0, frame=0), row], [dict(id=0, frame=0), row], [dict(frame=1, complete=True, beam=[])]


def test_covered_witness_can_be_lost_by_width():
    reference, attempts, depths = toy_loss()
    assert witness_loss(reference, attempts, depths)["cause"] == "beam_width"


def test_covered_witness_can_be_lost_to_cell_representative():
    reference, attempts, depths = toy_loss()
    replacement = copy.deepcopy(attempts[1])
    replacement.update(id=2, guide_distance=9, action=[0, 0.01])
    replacement["state"][4] = 0.0025
    attempts.append(replacement)
    depths[0]["beam"] = [2]
    assert witness_loss(reference, attempts, depths)["cause"] == "cell_representative"


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("uncovered", "witness_proposal_coverage"),
        ("missing", "covered_witness_action_missing"),
        ("rejected", "feasible_witness_rejected"),
        ("state", "witness_state"),
    ],
)
def test_coverage_and_hard_rejection_cannot_be_hidden(mutation, reason):
    reference, attempts, depths = copy.deepcopy(toy_loss())
    reference = copy.deepcopy(reference)
    if mutation == "uncovered":
        reference[1]["action"] = [0.3, 0.0]
    elif mutation == "missing":
        attempts.pop()
    elif mutation == "rejected":
        attempts[1]["reason"] = "collision"
    else:
        attempts[1]["state"][0] += 1
    with pytest.raises(ValueError, match=reason):
        witness_loss(reference, attempts, depths)


def test_route_guidance_changes_local_heading_without_changing_goal():
    geometry = dict(route=[[0, 0], [0, 3], [0, 6], [3, 6], [6, 6], [9, 6]])
    guide = RouteGuidance(geometry)
    aligned = guide.distance([6, 3, math.pi / 2, 2, 0])
    opposed = guide.distance([6, 3, -math.pi / 2, 2, 0])
    assert aligned < opposed and math.isclose(opposed - aligned, 2.7 * math.pi)


def test_checker_does_not_import_producer_and_search_cannot_accept_witness():
    checker = ROOT / "experiments/iter159_route_search_qualification/check.py"
    modules = [
        n.module for n in ast.walk(ast.parse(checker.read_text())) if isinstance(n, ast.ImportFrom)
    ]
    assert not any(
        m
        and (
            m.endswith("search")
            or m.endswith("guidance")
            or m.endswith("run")
            or m.endswith("background")
        )
        for m in modules
    )
    import inspect

    assert "witness" not in inspect.signature(search).parameters
    assert "case" not in inspect.signature(search).parameters
