"""Constructive control and corruptions before exposed-scene acquisition."""

import copy
import json
from pathlib import Path
import time
import subprocess

import numpy as np
import pytest

from experiments.iter153_action_feasibility.check import motion
from experiments.iter153_action_feasibility.geometry import obstacles
from experiments.iter155_background_witness.geometry import count_points, vertices
from experiments.iter156_background_calibration.background import (
    BackgroundPopulation,
    box_for_state,
)
from experiments.iter158_constraint_aware_search.check import verify_path
from experiments.iter158_constraint_aware_search.common import sha
from experiments.iter158_constraint_aware_search.common import BASE, source_check, raw_check
from experiments.iter158_constraint_aware_search.search import prior_reason, search, summary

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    old = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())
    old["max_actions"] = 12
    geometry = dict(
        reset=[0.0, 0.0, 0.0, 1.0, 0.0],
        route=[[0.0, i / 20] for i in range(41)],
        ego_dimensions=[1.6, 3.0, 1.5],
        obstacles=[],
        comparators={},
    )
    plan = dict(
        producer_seconds=60,
        finalization_reserve_seconds=1,
        beam_width=4,
        maximum_search_queries=1000,
        max_rss_bytes=2 * 1024**3,
    )
    points = np.empty((0, 3), dtype="<f4")
    ground = np.eye(4)[None, :, :]
    population = BackgroundPopulation(points, sha(points.tobytes()))
    events = []

    def query(state):
        box, _, _ = box_for_state(state, ground)
        return summary(population.query(box))

    return old, geometry, plan, points, ground, events, query


def run_fixture():
    old, geometry, plan, points, ground, events, query = fixture()
    result = search(
        geometry, old, plan, query, lambda k, r: events.append((k, r)), time.monotonic()
    )
    return old, geometry, plan, points, ground, events, result


def replay(old, geometry, points, ground, trace, complete=True, masks=lambda _: b""):
    return verify_path(
        trace,
        geometry,
        old,
        points.tolist(),
        ground.tolist(),
        masks,
        complete,
        time.monotonic() + 15,
    )


def test_constructed_completion_survives_independent_replay():
    old, geometry, _, points, ground, _, result = run_fixture()
    assert result["stop"] == "model_complete"
    admitted = replay(old, geometry, points, ground, result["trace"])
    assert admitted["verified_states"] > 1


def detour_fixture():
    old, geometry, plan, points, ground, _, query = fixture()
    old["max_actions"] = 100
    plan.update(beam_width=24, maximum_search_queries=60000, producer_seconds=120)
    geometry.update(
        route=[[0.0, i / 10] for i in range(201)], obstacles=[[7.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]]
    )
    result = search(geometry, old, plan, query, lambda *_: None, time.monotonic())
    return result, old, geometry, points, ground


def test_constructed_detour_survives_independent_replay():
    result, old, geometry, points, ground = detour_fixture()
    assert result["stop"] == "model_complete"
    assert max(abs(row["state"][1]) for row in result["trace"]) > 1
    replay(old, geometry, points, ground, result["trace"])


def test_immediate_progress_ranking_is_a_retained_bad_control(monkeypatch):
    import importlib

    module = importlib.import_module("experiments.iter158_constraint_aware_search.search")

    def progress_score(node):
        return (
            -node["route"]["nearest"],
            node["route"]["distance"],
            abs(node["state"][4]),
            node["effort"],
            node["id"],
        )

    def greedy(rows, width):
        seen, selected = set(), []
        for row in sorted(rows, key=progress_score):
            key = module.cell(row["state"])
            if key not in seen:
                seen.add(key)
                selected.append(row)
                if len(selected) == width:
                    break
        return selected

    monkeypatch.setattr(module, "score", progress_score)
    monkeypatch.setattr(module, "choose", greedy)
    result, *_ = detour_fixture()
    assert result["stop"] == "beam_empty" and result["selected"] is None


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("state", "numeric_replay"),
        ("parent", "parent_chain"),
        ("frame", "frame_sequence"),
        ("mask", "scalar_mask"),
        ("count", "scalar_counts"),
        ("mask_identity", "mask_identity"),
        ("missing", "missing_background"),
        ("decision", "background_clear"),
        ("route", "route_index"),
        ("nonfinite", "state_domain"),
    ],
)
def test_corruptions_cannot_be_admitted(mutation, reason):
    old, geometry, _, points, ground, _, result = run_fixture()
    trace = copy.deepcopy(result["trace"])

    def masks(_):
        return b"\x01" if mutation == "mask" else b""

    if mutation == "state":
        trace[1]["state"][0] += 0.1
    elif mutation == "parent":
        trace[1]["parent"] = 999
    elif mutation == "frame":
        trace[1]["frame"] = 3
    elif mutation == "mask":
        pass
    elif mutation == "count":
        trace[0]["background"]["count"] = 1
    elif mutation == "mask_identity":
        trace[0]["background"]["mask_sha256"] = "0" * 64
    elif mutation == "missing":
        trace[0]["background"] = None
    elif mutation == "decision":
        trace[0]["background"]["decision"] = "numerically_ambiguous"
    elif mutation == "route":
        trace[0]["route"]["nearest"] += 1
    elif mutation == "nonfinite":
        trace[1]["state"][0] = float("nan")
    with pytest.raises(ValueError, match=reason):
        replay(old, geometry, points, ground, trace, masks=masks)


def test_partial_path_cannot_claim_completion():
    old, geometry, _, points, ground, _, result = run_fixture()
    with pytest.raises(ValueError, match="false_completion"):
        replay(old, geometry, points, ground, result["trace"][:2])
    assert (
        replay(old, geometry, points, ground, result["trace"][:2], complete=False)[
            "selected_actions"
        ]
        == 1
    )


def test_progress_requirement_cannot_be_bought_with_collision_clearance():
    old, geometry, _, points, ground, _, result = run_fixture()
    geometry["comparators"] = {"required": dict(hazard_time=0.25, rc=1.0)}
    trace = result["trace"]
    assert (
        prior_reason(
            trace[0]["state"], trace[1]["state"], trace[1]["action"], 1, geometry, old, []
        )[0]
        == "progress"
    )
    with pytest.raises(ValueError, match="progress"):
        replay(old, geometry, points, ground, trace)


def test_over_limit_control_fails_both_layers():
    old, geometry, _, points, ground, _, result = run_fixture()
    trace = copy.deepcopy(result["trace"][:2])
    trace[1]["action"] = [3.0, 0.0]
    trace[1]["state"] = motion(trace[0]["state"], trace[1]["action"])
    assert (
        prior_reason(
            trace[0]["state"], trace[1]["state"], trace[1]["action"], 1, geometry, old, []
        )[0]
        == "controls"
    )
    with pytest.raises(ValueError, match="controls"):
        replay(old, geometry, points, ground, trace)


def test_foreground_blocks_proposal_and_replay():
    old, geometry, _, points, ground, _, result = run_fixture()
    geometry["obstacles"] = [[0.0, 0.0, 0.0, 2.0, 4.0, 1.0, 0.0]]
    trace = result["trace"]
    assert (
        prior_reason(
            trace[0]["state"],
            trace[1]["state"],
            trace[1]["action"],
            1,
            geometry,
            old,
            obstacles(geometry),
        )[0]
        == "foreground"
    )
    with pytest.raises(ValueError, match="foreground"):
        replay(old, geometry, points, ground, trace)


def test_false_background_clearance_rejected_by_scalar_population():
    old, geometry, _, _, ground, _, result = run_fixture()
    trace = copy.deepcopy(result["trace"][:1])
    points = np.tile([0.1, 0.5, 0.1], (101, 1)).astype("<f4")
    actual = count_points(points.tolist(), vertices([0, 0, 0], 0))
    mask = np.packbits(actual["mask"], bitorder="little").tobytes()
    trace[0]["background"].update(
        count=101, certain_inside=101, possible_inside=101, mask_sha256=sha(mask)
    )
    with pytest.raises(ValueError, match="background_clear"):
        replay(old, geometry, points, ground, trace, complete=False, masks=lambda _: mask)


def test_query_budget_does_not_admit_unfinished_depth():
    old, geometry, plan, _, _, events, query = fixture()
    plan["maximum_search_queries"] = 2
    result = search(
        geometry, old, plan, query, lambda k, r: events.append((k, r)), time.monotonic()
    )
    assert result["stop"] == "query_budget" and result["selected"] is None
    assert result["completed_depth"] == 0 and len(result["trace"]) == 1
    assert events[-1][1]["complete"] is False


def test_ambiguous_background_is_not_a_clear_survivor():
    old, geometry, plan, _, _, _, query = fixture()

    def ambiguous(state):
        row = query(state)
        if state[0] > 0:
            row.update(decision="numerically_ambiguous", possible_inside=101)
        return row

    result = search(geometry, old, plan, ambiguous, lambda *_: None, time.monotonic())
    assert result["stop"] == "beam_empty" and result["selected"] is None
    assert result["counts"]["numerically_ambiguous"] > 0


def test_scalar_checker_has_no_search_or_vector_import():
    import ast

    path = ROOT / "experiments/iter158_constraint_aware_search/check.py"
    imports = [
        n.module for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.ImportFrom)
    ]
    assert not any(
        n and (n.endswith(".search") or n.endswith(".background") or n == "search") for n in imports
    )


def test_frozen_inventory_and_raw_commit_controls(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, stderr=subprocess.DEVNULL)

    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    (tmp_path / BASE).mkdir(parents=True)
    (tmp_path / BASE / "PLAN.json").write_text("{}\n")
    (tmp_path / "source.py").write_text("x = 1\n")
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "data.json").write_text("{}\n")
    git("add", ".")
    git("commit", "-qm", "Fixture")
    commit = git("rev-parse", "HEAD").decode().strip()
    plan = dict(source_files=["source.py"], max_output_bytes=100)
    source_check(tmp_path, plan, commit)
    raw_check(tmp_path, raw, commit, plan)
    (tmp_path / "source.py").write_text("x = 2\n")
    with pytest.raises(ValueError, match="source_changed"):
        source_check(tmp_path, plan, commit)
    with pytest.raises(subprocess.CalledProcessError):
        source_check(tmp_path, dict(source_files=["nonexistent.py"]), commit)
    (raw / "data.json").write_text('{"changed":true}\n')
    with pytest.raises(ValueError, match="raw_not_committed"):
        raw_check(tmp_path, raw, commit, plan)
    (raw / "extra.json").write_text("{}\n")
    with pytest.raises(ValueError, match="raw_inventory"):
        raw_check(tmp_path, raw, commit, plan)
