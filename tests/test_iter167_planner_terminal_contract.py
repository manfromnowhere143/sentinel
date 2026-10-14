"""Regression for the actual early-completion qualification defect."""

import copy
import json
from pathlib import Path

import pytest

from experiments.iter166_independent_planner.adapter import Edges as OriginalEdges
from experiments.iter167_planner_terminal_contract.adapter import Edges, terminal_frame

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    old = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())
    geometry = dict(
        reset=[0.0, 0.0, 0.0, 2.0, 0.0],
        route=[[0.0, i / 10] for i in range(11)],
        ego_dimensions=[1.6, 3.0, 1.5],
        obstacles=[],
        comparators={"a": dict(hazard_time=4.0, rc=0.0), "b": dict(hazard_time=8.0, rc=0.0)},
    )
    plan = dict(attempt_budget=100, per_run_seconds=10, max_actions=96, max_rss_bytes=1024**3)
    return geometry, old, plan


def test_actual_early_completion_defect_is_rejected():
    geometry, old, plan = fixture()
    args = (geometry, old, plan, lambda s: dict(decision="clear"), lambda *a: None)
    before = [0.5, 0.0, 0.0, 2.0, 0.0, 1.0]
    assert OriginalEdges(*args).edge(before, [0.0, 0.0])["reason"] == "clear"
    corrected = Edges(*args)
    row = corrected.edge(before, [0.0, 0.0])
    assert row["route"]["rc"] >= 1 and row["reason"] == "premature_completion"
    assert corrected.attempts == 1 and corrected.queries == 0


def test_original_final_checkpoint_can_complete():
    geometry, old, plan = fixture()
    edges = Edges(geometry, old, plan, lambda s: dict(decision="clear"), lambda *a: None)
    row = edges.edge([0.5, 0.0, 0.0, 2.0, 0.0, 31.0], [0.0, 0.0])
    assert row["reason"] == "clear" and row["frame"] == 32 and row["route"]["rc"] >= 1


def test_source_deadline_remains_frame_36():
    geometry, old, _ = fixture()
    geometry = copy.deepcopy(geometry)
    geometry["comparators"] = {
        "a": dict(hazard_time=7.75, rc=0.32925097621583244),
        "b": dict(hazard_time=9.0, rc=0.32215122470713525),
    }
    assert terminal_frame(geometry, old) == 36


def test_off_grid_checkpoint_fails_closed():
    geometry, old, _ = fixture()
    geometry["comparators"]["a"]["hazard_time"] = 7.76
    with pytest.raises(ValueError, match="checkpoint_off_grid"):
        terminal_frame(geometry, old)
