"""Separate grouping from width, preserve the baseline, and reject false reflections."""

import copy
import json
import math
from pathlib import Path
import time

import pytest

from experiments.iter158_constraint_aware_search.check import verify_path
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for, witness
from experiments.iter159_route_search_qualification.search import search as previous_search
from experiments.iter161_grouping_width_ablation.check import audit_beam, audit_run, key
from experiments.iter161_grouping_width_ablation.common import encode
from experiments.iter161_grouping_width_ablation.fixtures import reflect
from experiments.iter161_grouping_width_ablation.reflection import check_cases, check_pair
from experiments.iter161_grouping_width_ablation.search import choose, grouping_key, search

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/iter161_grouping_width_ablation"
OLD = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())


def row(identity, x=0.5, effort=0):
    return dict(
        id=identity,
        frame=1,
        parent=0,
        state=[x, 0.0, 0.0, 2.0, 0.0],
        guide_distance=1.0,
        route=dict(nearest=0, distance=0.0, rc=0.1),
        effort=effort,
    )


def test_grouping_and_width_are_different_stages():
    rows = [row(1), row(2, 0.6), row(3, 2.1)]
    beam, stages = choose(rows, 1, "quantized")
    assert [r["id"] for r in beam] == [1]
    assert stages == dict(cell_representatives=[1, 3], grouping_removed=1, width_removed=1)
    exact, stages = choose(rows, 1, "exact")
    assert len(exact) == 1 and stages["grouping_removed"] == 0 and stages["width_removed"] == 2
    for aggregation in ("quantized", "exact"):
        for width in (1, 2, 24, 48):
            beam, stages = choose(rows, width, aggregation)
            assert audit_beam(rows, width, aggregation) == dict(
                stages, beam=[r["id"] for r in beam]
            )
            assert len(beam) + stages["grouping_removed"] + stages["width_removed"] == len(rows)


def test_exact_duplicates_choose_lower_effort_then_generation_order():
    rows = [row(4, effort=2), row(3, effort=1), row(2, effort=1)]
    beam, stages = choose(rows, 24, "exact")
    assert [r["id"] for r in beam] == [2] and stages["grouping_removed"] == 2


def test_exact_key_preserves_signed_zero_and_absolute_frame():
    a, b = row(1), row(2)
    b["state"][1] = -0.0
    assert grouping_key(a, "exact") != grouping_key(b, "exact")
    assert key(a, "exact") != key(b, "exact")
    b = copy.deepcopy(a)
    b["frame"] = 2
    assert grouping_key(a, "exact") != grouping_key(b, "exact")
    assert key(a, "exact") != key(b, "exact")


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, True])
def test_nonfinite_and_boolean_states_rejected(bad):
    a = row(1)
    a["state"][0] = bad
    for function in (grouping_key, key):
        with pytest.raises(ValueError, match="key_state"):
            function(a, "exact")


def controls():
    case = dict(
        id="toy_left",
        geometry=dict(
            reset=[0.0, 0.0, 0.0, 2.0, 0.0],
            route=[[0.0, i / 10] for i in range(21)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators={},
        ),
        points=[[100.0, 0.5, 100.0]],
        ground=[
            [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        ],
        witness_actions=[[0.0, 0.0]] * 10,
    )
    plan = dict(
        beam_width=24,
        attempt_budget=2500,
        max_actions=12,
        per_run_seconds=30,
        max_rss_bytes=1024**3,
    )
    return case, plan


def acquire(tmp_path, aggregation="quantized", width=24, budget=2500):
    case, plan = controls()
    plan.update(beam_width=width, attempt_budget=budget)
    query = query_for(case)
    events = dict(attempt=[], depth=[])
    result = search(
        case["geometry"],
        OLD,
        plan,
        lambda s: summary(query(s)),
        lambda k, r: events[k].append(r),
        aggregation,
    )
    trace = result.pop("trace")
    result.update(aggregation=aggregation, width=width)
    folder = tmp_path / "run"
    folder.mkdir()
    (folder / "selected").mkdir()
    (folder / "selected/trace.json").write_bytes(encode(trace))
    for event, name in [("attempt", "attempts"), ("depth", "depths")]:
        (folder / (name + ".jsonl")).write_bytes(b"".join(encode(r) for r in events[event]))
    return case, plan, result, trace, events, folder, witness(case, OLD, query)


@pytest.mark.parametrize(
    "aggregation,width", [("quantized", 24), ("quantized", 48), ("exact", 24), ("exact", 48)]
)
def test_four_arms_complete_and_replay(aggregation, width, tmp_path):
    case, plan, result, trace, _, folder, reference = acquire(tmp_path, aggregation, width)
    assert result["stop"] == "model_complete"
    audit_run(folder, result, reference, plan)
    verify_path(
        trace,
        case["geometry"],
        OLD,
        case["points"],
        case["ground"],
        lambda _: b"\x00",
        True,
        time.monotonic() + 10,
    )


def test_quantized_width24_is_unchanged_search(tmp_path):
    case, plan, result, _, events, _, _ = acquire(tmp_path)
    query = query_for(case)
    prior = dict(attempt=[], depth=[])
    old = previous_search(
        case["geometry"],
        OLD,
        plan,
        lambda s: summary(query(s)),
        lambda k, r: prior[k].append(r),
        "route",
        "speed_groups",
    )
    assert old["stop"] == result["stop"] and old["attempts"] == result["attempts"]
    assert encode(prior["attempt"]) == encode(events["attempt"])
    for a, b in zip(prior["depth"], events["depth"]):
        assert all(b[k] == v for k, v in a.items())


def test_budget_does_not_admit_partial_depth(tmp_path):
    _, plan, result, _, events, folder, reference = acquire(tmp_path, budget=1)
    assert result["stop"] == "attempt_budget" and result["attempts"] == 1
    assert events["depth"][-1]["complete"] is False
    _, _, retention = audit_run(folder, result, reference, plan)
    assert retention["retained"] == 0


@pytest.mark.parametrize(
    "field,reason",
    [
        ("beam", "beam_replay"),
        ("cell_representatives", "grouping_replay"),
        ("grouping_removed", "retention_partition"),
        ("width_removed", "retention_partition"),
    ],
)
def test_forged_selection_stage_rejected(field, reason, tmp_path):
    _, plan, result, _, events, folder, reference = acquire(tmp_path)
    events["depth"][0][field] = [999] if field in ("beam", "cell_representatives") else 999
    (folder / "depths.jsonl").write_bytes(b"".join(encode(r) for r in events["depth"]))
    with pytest.raises(ValueError, match=reason):
        audit_run(folder, result, reference, plan)


def test_complete_reflections_and_round_trip():
    cases = json.loads((BASE / "CASES.json").read_text())
    prior = json.loads(
        (ROOT / "experiments/iter159_route_search_qualification/CASES.json").read_text()
    )
    check_cases(cases, prior)
    for i in (0, 2):
        assert encode(reflect(reflect(cases[i]))) == encode(cases[i])
        with pytest.raises(ValueError, match="reflection"):
            check_pair(cases[i], prior[i + 1])


@pytest.mark.parametrize(
    "field,reason",
    [
        ("reset", "reflection_reset"),
        ("route", "reflection_route"),
        ("obstacles", "reflection_foreground"),
        ("points", "reflection_points"),
        ("ground", "reflection_ground"),
        ("witness_actions", "reflection_commands"),
        ("comparators", "reflection_fixed_fields"),
    ],
)
def test_incomplete_reflection_rejected(field, reason):
    left = json.loads((BASE / "CASES.json").read_text())[0]
    right = reflect(left)
    if field in ("reset", "route", "obstacles", "comparators"):
        if field == "comparators":
            right["geometry"][field]["checkpoint_16"]["rc"] += 0.1
        elif field == "reset":
            right["geometry"][field][1] += 1
        else:
            right["geometry"][field][0][0] += 1
    elif field == "ground":
        right[field][0][0][3] += 1
    else:
        right[field][0][0] += 1
    with pytest.raises(ValueError, match=reason):
        check_pair(left, right)


def test_nontrivial_pose_reflection_and_clock_preservation():
    case, _ = controls()
    case["geometry"]["reset"] = [1.0, 2.0, 0.3, 4.0, 0.1]
    case["geometry"]["obstacles"] = [[2.0, 3.0, 0.5, 1.0, 2.0, 1.5, 0.4]]
    case["ground"] = [
        [[0.0, 0.0, 1.0, 3.0], [0.0, 1.0, 0.0, 4.0], [-1.0, 0.0, 0.0, 5.0], [0.0, 0.0, 0.0, 1.0]]
    ]
    case["geometry"]["comparators"] = {"timed": dict(hazard_time=4.0, rc=0.5)}
    mirrored = reflect(case)
    check_pair(case, mirrored)
    assert (
        mirrored["ground"][0][0][3] == -3.0
        and mirrored["geometry"]["comparators"] == case["geometry"]["comparators"]
    )
    assert encode(reflect(mirrored)) == encode(case)
