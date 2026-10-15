"""Constructed late-clock, continuous-bound and case-identity controls."""

import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import random
import time

import pytest

from experiments.iter153_action_feasibility.planner import transition
from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter179_frontier_continuation_audit.check import scalar_masks
from experiments.iter182_late_frontier_timing.bound import progress_bound
from experiments.iter182_late_frontier_timing.bound_check import check_bound
from experiments.iter182_late_frontier_timing.premature import completion_bound
from experiments.iter182_late_frontier_timing.premature_check import check_completion
from experiments.iter182_late_frontier_timing.check import classify, case_check
from experiments.iter182_late_frontier_timing.common import BASE, document, write
from experiments.iter182_late_frontier_timing.contract import FIXED, check_plan
from experiments.iter182_late_frontier_timing.probe import probe
from experiments.iter182_late_frontier_timing.produce import Masks
from experiments.iter182_late_frontier_timing.replay import probe_check, path_check
from experiments.iter182_late_frontier_timing.retained import load, state_key

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def old():
    return json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())


@pytest.fixture
def case():
    return dict(
        id="constructed",
        geometry=dict(
            reset=[0.0, 0.0, 0.0, 4.0, 0.0],
            route=[[0.0, float(i)] for i in range(70)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators=dict(
                first=dict(hazard_time=4.0, rc=0.2), final=dict(hazard_time=8.0, rc=0.5)
            ),
        ),
        points=[[100.0, 0.5, 100.0]],
        ground=[[[float(i == j) for j in range(4)] for i in range(4)]],
    )


def prefix(case, old, count):
    state, rows, query = case["geometry"]["reset"], [], query_for(case)
    for frame in range(count + 1):
        action = None if frame == 0 else [0.0, 0.0]
        if frame:
            state = transition(state, action, old)
        rows.append(
            dict(
                id=frame,
                parent=frame - 1 if frame else None,
                frame=frame,
                action=action,
                state=state,
                route=route_outcome(state, case["geometry"]["route"]),
                background=summary(query(state)),
                reason="clear",
            )
        )
    return rows


def bundle(case, old, count=24, **changes):
    retained = prefix(case, old, count)
    plan, query = dict(FIXED, **changes), query_for(case)
    result = probe(
        retained[-1]["state"],
        count,
        case["geometry"],
        old,
        plan,
        lambda s: summary(query(s)),
        time.monotonic() + 30,
    )
    suffix, attempts = result.pop("trace"), result.pop("attempt_records")
    combined = copy.deepcopy(retained + suffix[1:])
    for i, row in enumerate(combined):
        row.update(id=i, parent=i - 1 if i else None)
    masks = {
        state_key(r["state"]): dict(state=r["state"], background=r["background"])
        for r in retained + attempts
        if r["background"] is not None
    }
    record = dict(
        result=result,
        masks=[state_key(r["state"]) for r in combined],
        selected_attempt_ids=[r["id"] for r in suffix],
    )
    return record, attempts, combined, retained, plan, masks


@pytest.mark.parametrize("count", [24, 25, 26, 27, 31])
def test_extended_probe_and_full_path_replay(case, old, count):
    record, attempts, combined, retained, plan, masks = bundle(case, old, count)
    assert probe_check(record, attempts, combined, retained, case, old, plan, masks)
    assert len(combined) == 33
    assert record["result"]["attempts"] <= 18 * (1 + 16 * (31 - count))


@pytest.mark.parametrize("steps", [5, 6, 7, 8])
def test_progress_extension_has_independent_corner_proof(case, old, steps):
    state = [0.0, 0.0, 0.0, 0.0, 0.0]
    record = progress_bound(state, 32 - steps, case["geometry"], old, 32)
    assert check_bound(record, state, 32 - steps, case["geometry"], old, 32)


@pytest.mark.parametrize("function", [progress_bound, completion_bound])
def test_nine_steps_rejected(case, old, function):
    with pytest.raises(ValueError):
        function(case["geometry"]["reset"], 23, case["geometry"], old, 32)


@pytest.mark.parametrize(
    "field,value",
    [("radius", ["0", "1"]), ("anchor", -1), ("excluded", False), ("allowed_indices", [])],
)
def test_extended_progress_corruption(case, old, field, value):
    state = [0.0] * 5
    record = progress_bound(state, 24, case["geometry"], old, 32)
    record[field] = value
    with pytest.raises(ValueError):
        check_bound(record, state, 24, case["geometry"], old, 32)


def completion_fixture(case):
    g = copy.deepcopy(case["geometry"])
    g["route"] = [[0.0, float(i)] for i in range(40)]
    return g, [34.49, 0.0, 0.0, 6.0, 0.0]


def test_premature_continuous_exclusion(case, old):
    geometry, state = completion_fixture(case)
    record = completion_bound(state, 29, geometry, old, 32)
    assert check_completion(record, state, 29, geometry, old, 32)
    rng = random.Random(182)
    box = [[Fraction(int(a), int(b)) for a, b in axis] for axis in record["box"]]
    for _ in range(300):
        after = transition(
            state, [rng.uniform(-2, 0), rng.uniform(-math.pi / 12, math.pi / 12)], old
        )
        assert all(box[k][0] <= Fraction(after[k]) <= box[k][1] for k in (0, 1))
        assert route_outcome(after, geometry["route"])["rc"] >= 1


@pytest.mark.parametrize(
    "state",
    [
        [34.4, 0, 0, 0, 0],
        [34.5, 0, 0, 0, 0],
        [35, 0, -math.pi, 2, 0],
        [0, 0, 0, 4, 0],
        [34.5, 0, -math.pi / 2, 0, 0],
    ],
)
def test_waiting_boundary_and_negative_heading_do_not_false_exclude(case, old, state):
    geometry, _ = completion_fixture(case)
    record = completion_bound(state, 29, geometry, old, 32)
    assert not check_completion(record, state, 29, geometry, old, 32)


@pytest.mark.parametrize("velocity", [-1e-12, 0.0, 6.0, 6 + 1e-12])
def test_speed_tolerance_remains_inside_outward_box(case, old, velocity):
    geometry, state = completion_fixture(case)
    state[3] = velocity
    record = completion_bound(state, 29, geometry, old, 32)
    check_completion(record, state, 29, geometry, old, 32)
    box = [[Fraction(int(a), int(b)) for a, b in axis] for axis in record["box"]]
    for acceleration in (-2 - 1e-12, 0, 2 + 1e-12):
        after = transition(state, [acceleration, 0], old)
        if -1e-12 <= after[3] <= 6 + 1e-12:
            assert all(box[k][0] <= Fraction(after[k]) <= box[k][1] for k in (0, 1))


def test_exact_checkpoint_step_is_inapplicable(case, old):
    geometry, state = completion_fixture(case)
    record = completion_bound(state, 31, geometry, old, 32)
    assert record["applicable"] is False and record["box"] is None
    assert check_completion(record, state, 31, geometry, old, 32) is False
    record["excluded"] = True
    with pytest.raises(ValueError, match="inapplicable"):
        check_completion(record, state, 31, geometry, old, 32)


@pytest.mark.parametrize(
    "field,value",
    [
        ("anchor", 0),
        ("noncompleting_indices", []),
        ("velocity_interval", [["0", "1"], ["0", "1"]]),
        ("box", []),
        ("minimum_squared_distance_gap", ["1", "1"]),
        ("excluded", False),
        ("applicable", False),
        ("frame", 28),
        ("target_frame", 33),
        ("extra", 0),
    ],
)
def test_completion_corruption_rejected(case, old, field, value):
    geometry, state = completion_fixture(case)
    record = completion_bound(state, 29, geometry, old, 32)
    record[field] = value
    with pytest.raises(ValueError):
        check_completion(record, state, 29, geometry, old, 32)


@pytest.mark.parametrize(
    "mutation", ["nan", "position", "heading", "speed", "route", "dynamics", "target"]
)
def test_completion_outside_declared_model_rejected(case, old, mutation):
    geometry, state = completion_fixture(case)
    if mutation == "nan":
        state[0] = float("nan")
    if mutation == "position":
        state[0] = 1001
    if mutation == "heading":
        state[2] = 1001
    if mutation == "speed":
        state[3] = 6.001
    if mutation == "route":
        geometry["route"][0][0] = 1001
    if mutation == "dynamics":
        old["dt"] = 0.5
    if mutation == "target":
        geometry["comparators"]["final"]["hazard_time"] = 9
    with pytest.raises(ValueError):
        completion_bound(state, 29, geometry, old, 32)


@pytest.mark.parametrize(
    "flags,label",
    [
        ((True, False, False, False), "verified_continuation"),
        ((False, True, False, False), "progress_excluded"),
        ((False, False, True, False), "premature_completion_excluded"),
        ((False, True, True, True), "both_constraints_excluded"),
        ((False, False, False, False), "bounded_miss"),
        ((False, False, False, True), "unobserved_continuation"),
    ],
)
def test_scientific_distinctions(flags, label):
    assert classify(*flags) == label


@pytest.mark.parametrize(
    "flags",
    [
        (True, True, False, False),
        (True, False, True, False),
        (True, False, False, True),
        (1, False, False, False),
    ],
)
def test_witness_bound_or_censor_conflict_invalid(flags):
    with pytest.raises(ValueError):
        classify(*flags)


def test_same_state_different_scene_masks_cannot_be_shared(tmp_path, case):
    state = [0.0] * 5
    changed = copy.deepcopy(case)
    changed["points"] = [[0.0, 0.5, 0.0]] * 101
    counts = []
    for name, scene in (("first", case), ("second", changed)):
        folder = tmp_path / name
        folder.mkdir()
        query = query_for(scene)
        masks = Masks(folder / "masks", query)
        masks.add(state, summary(query(state)))
        masks.finish()
        verified = scalar_masks(folder, scene, time.monotonic() + 10)
        counts.append(verified[state_key(state)]["background"]["count"])
    assert counts == [0, 101]
    with pytest.raises(ValueError):
        scalar_masks(tmp_path / "first", changed, time.monotonic() + 10)


def test_entire_case_audit_replays_and_requires_unselected_masks(tmp_path, case, old):
    record, attempts, combined, retained, plan, _ = bundle(case, old, 24)
    connection = dict(call=1, before=[*retained[0]["state"], 0], result={}, trace=retained)
    path = dict(call=1, chain=[1], ambiguous_joins=0, representative=1, trace=retained)
    query = query_for(case)
    masks = Masks(tmp_path / "masks", query)
    path["masks"] = masks.path(retained)
    for row in attempts:
        if row["background"] is not None:
            masks.add(row["state"], row["background"])
    record["masks"] = masks.path(combined)
    record.update(
        call=1,
        bound=progress_bound(retained[-1]["state"], 24, case["geometry"], old, 32),
        completion_bound=completion_bound(retained[-1]["state"], 24, case["geometry"], old, 32),
    )
    masks.finish()
    write(tmp_path / "paths.json", [path])
    write(tmp_path / "retained_evaluations.json", [])
    write(tmp_path / "probes.json", [record])
    (tmp_path / "probe_001").mkdir()
    write(tmp_path / "probe_001/attempts.json", attempts)
    write(tmp_path / "probe_001/trace.json", combined)
    result = case_check(
        tmp_path, case, [connection], [connection], [], old, plan, {}, time.monotonic() + 30
    )
    assert result["records"][0]["checkpoint_continuation"]
    key = next(
        state_key(r["state"])
        for r in attempts
        if r["background"] is not None and state_key(r["state"]) not in record["masks"]
    )
    rows = document(tmp_path / "masks", "states.json")
    (tmp_path / "masks/states.json").unlink()  # Corruption of a constructed fixture only.
    write(tmp_path / "masks/states.json", [r for r in rows if r["key"] != key])
    (tmp_path / "masks" / (key + ".bin")).unlink()
    with pytest.raises(ValueError):
        case_check(
            tmp_path, case, [connection], [connection], [], old, plan, {}, time.monotonic() + 30
        )


def test_work_cap_stays_a_miss_and_34_record_path_rejected(case, old):
    record, attempts, combined, retained, plan, masks = bundle(case, old, per_root_attempts=1)
    assert not probe_check(record, attempts, combined, retained, case, old, plan, masks)
    assert record["result"]["stop"] == "attempt_budget"
    with pytest.raises(ValueError, match="path_length"):
        path_check([combined[0]] * 34, [record["masks"][0]] * 34, case, old, masks)


def test_fixed_population_and_no_pruning_contract():
    plan = document(ROOT, BASE / "PLAN.json")
    check_plan(plan)
    inputs = load(ROOT, plan)  # Inventory only; no retained-root bound or search.
    assert sum(len(selected) for _, _, selected, _ in inputs) == 7
    assert sum(len(trials) for _, _, _, trials in inputs) == 582
    plan["prune_using_bounds"] = True
    with pytest.raises(ValueError):
        check_plan(plan)
