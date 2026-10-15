"""Constructed paired-search controls; no retained-root continuation acquisition."""

import copy
import json
import math
from pathlib import Path
import time

import pytest

from experiments.iter153_action_feasibility.planner import transition
from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter179_frontier_continuation_audit.probe import probe
from experiments.iter179_frontier_continuation_audit.replay import probe_check
from experiments.iter179_frontier_continuation_audit.produce import Masks
from experiments.iter179_frontier_continuation_audit.check import scalar_masks
from experiments.iter180_equal_work_continuation.contract import FIXED, check_plan, schedule
from experiments.iter180_equal_work_continuation.target import target_for
from experiments.iter180_equal_work_continuation.target_check import check_target
from experiments.iter180_equal_work_continuation.program import run_program
from experiments.iter180_equal_work_continuation.program_check import program_check
from experiments.iter180_equal_work_continuation.comparison import compare

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def old():
    return json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())


@pytest.fixture
def case():
    return dict(
        geometry=dict(
            reset=[0.0, 0.0, 0.0, 4.0, 0.0],
            route=[[0.0, float(i)] for i in range(40)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators=dict(
                first=dict(hazard_time=4.0, rc=0.35), final=dict(hazard_time=8.0, rc=0.8)
            ),
        ),
        points=[[100.0, 0.5, 100.0]],
        ground=[[[float(i == j) for j in range(4)] for i in range(4)]],
    )


def prefix(case, old, frame=12):
    query = query_for(case)
    state = case["geometry"]["reset"]
    trace = []
    for i in range(frame + 1):
        action = [0.0, 0.0] if i else None
        if action is not None:
            state = transition(state, action, old)
        trace.append(
            dict(
                id=i,
                parent=i - 1 if i else None,
                frame=i,
                action=action,
                state=state,
                route=route_outcome(state, case["geometry"]["route"]),
                reason="clear",
                background=summary(query(state)),
            )
        )
    return trace


def bundle(case, old, tmp_path, arm="program", expired=False, **overrides):
    plan = dict(FIXED, **overrides)
    retained = prefix(case, old)
    root = retained[-1]
    vector = query_for(case)

    def query(s):
        return summary(vector(s))

    started = time.monotonic()
    target = target_for(root["state"], root["frame"], case["geometry"], plan["target_frame"])
    deadline = started - 1 if expired else started + 30
    if arm == "program":
        out = run_program(
            root["state"], root["frame"], case["geometry"], old, plan, query, target, deadline
        )
        result, events, suffix = out["result"], out["events"], out["trace"]
        extras = {}
    else:
        result = probe(root["state"], root["frame"], case["geometry"], old, plan, query, deadline)
        suffix, events = result.pop("trace"), result.pop("attempt_records")
        extras = dict(selected_attempt_ids=[r["id"] for r in suffix])
    elapsed = time.monotonic() - started
    combined = copy.deepcopy(retained + suffix[1:])
    for i, r in enumerate(combined):
        r.update(id=i, parent=i - 1 if i else None)
    m = Masks(tmp_path / "masks", vector)
    keys = m.path(combined)
    rows = (
        [r for e in events if e["kind"] == "evaluation" for r in e["trace"]]
        if arm == "program"
        else events
    )
    for r in rows:
        if r["background"] is not None:
            m.add(r["state"], r["background"])
    m.finish()
    masks = scalar_masks(tmp_path, case, time.monotonic() + 30)
    record = dict(target=target, result=result, masks=keys, search_seconds=elapsed, **extras)
    return record, events, combined, retained, plan, masks


@pytest.mark.parametrize("arm", ["program", "beam"])
def test_clear_four_step_task_fits_equal_budget(case, old, tmp_path, arm):
    record, events, trace, retained, plan, masks = bundle(case, old, tmp_path, arm)
    checker = program_check if arm == "program" else probe_check
    assert checker(record, events, trace, retained, case, old, plan, masks)
    assert record["result"]["attempts"] <= (128 if arm == "program" else 126)
    assert trace[-1]["frame"] == 16


@pytest.mark.parametrize("arm", ["program", "beam"])
def test_expired_deadline_is_censored_not_zero_evidence(case, old, tmp_path, arm):
    record, events, trace, retained, plan, masks = bundle(case, old, tmp_path, arm, expired=True)
    checker = program_check if arm == "program" else probe_check
    assert not checker(record, events, trace, retained, case, old, plan, masks)
    assert record["result"]["attempts"] == 0 and record["result"]["stop"] == "time_budget"


def test_program_reserves_full_rollout_before_any_motion(case, old, tmp_path):
    args = bundle(case, old, tmp_path, per_root_attempts=3)
    record, events, trace, retained, plan, masks = args
    assert not program_check(record, events, trace, retained, case, old, plan, masks)
    assert record["result"]["attempts"] == 0 and record["result"]["stop"] == "attempt_budget"


def test_retained_generator_has_varying_phases_and_cache(case, old, tmp_path):
    # Impossible deadline ensures enumeration continues through phase changes.
    case["geometry"]["comparators"]["first"]["rc"] = 0.99
    record, events, trace, retained, plan, masks = bundle(case, old, tmp_path)
    assert not program_check(record, events, trace, retained, case, old, plan, masks)
    assert record["result"]["attempts"] == 128
    assert record["result"]["cache_hits"] > 0
    trials = [e for e in events if e["kind"] == "evaluation"]
    assert any(len({tuple(r["action"]) for r in e["trace"][1:]}) > 1 for e in trials)


def test_program_charges_invalid_suffixes_and_verifies_their_masks(case, old, tmp_path):
    case["geometry"]["obstacles"] = [[14.5, 0.0, 0.0, 2.0, 1.0, 2.0, 0.0]]
    record, events, trace, retained, plan, masks = bundle(case, old, tmp_path)
    assert not program_check(record, events, trace, retained, case, old, plan, masks)
    trials = [e for e in events if e["kind"] == "evaluation"]
    assert any(e["valid_prefix"] < len(e["trace"]) - 2 for e in trials)
    assert record["result"]["attempts"] == sum(len(e["trace"]) - 1 for e in trials)


@pytest.mark.parametrize(
    "corruption",
    [
        "counts",
        "queries",
        "attempts",
        "request",
        "value",
        "cache",
        "action",
        "clock",
        "parent",
        "reason",
        "mask",
        "selection",
        "stop",
        "trace",
        "target",
        "elapsed",
        "hidden_witness",
    ],
)
def test_program_corruptions_fail(case, old, tmp_path, corruption):
    record, events, trace, retained, plan, masks = bundle(case, old, tmp_path)
    trial = next(e for e in events if e["kind"] == "evaluation")
    if corruption == "counts":
        record["result"]["counts"]["clear"] += 1
    if corruption == "queries":
        record["result"]["queries"] += 1
    if corruption == "attempts":
        record["result"]["attempts"] += 1
    if corruption == "request":
        events[0]["id"] = 2
    if corruption == "value":
        events[0]["values"][0] += 0.1
    if corruption == "cache":
        events[0]["cached"] = True
    if corruption == "action":
        trial["trace"][1]["action"][0] += 0.1
    if corruption == "clock":
        trial["trace"][1]["frame"] += 1
    if corruption == "parent":
        trial["trace"][1]["parent"] = 0
    if corruption == "reason":
        trial["trace"][1]["reason"] = "collision"
    if corruption == "mask":
        masks.pop(record["masks"][-1])
    if corruption == "selection":
        record["result"]["selected_prefix"] -= 1
    if corruption == "stop":
        record["result"]["generator_stop"] = "time_budget"
    if corruption == "trace":
        trace[-1]["state"][0] += 0.1
    if corruption == "target":
        record["target"]["state"][0] += 0.1
    if corruption == "elapsed":
        record["search_seconds"] = -1
    if corruption == "hidden_witness":
        record["result"]["witness"] = False
    with pytest.raises(ValueError):
        program_check(record, events, trace, retained, case, old, plan, masks)


@pytest.mark.parametrize(
    "field",
    [
        "per_root_attempts",
        "maximum_total_attempts",
        "beam_width",
        "target_frame",
        "per_run_seconds",
        "max_proposals",
        "parent_commit",
        "arms",
    ],
)
def test_fixed_envelope_cannot_drift(field):
    p = dict(FIXED, status="preregistered")
    check_plan(p)
    p[field] = "corrupt"
    with pytest.raises(ValueError):
        check_plan(p)


def test_width_is_derived_from_maximum_work():
    assert all(18 * (1 + 2 * (n - 1)) <= 128 for n in range(1, 5))
    assert 18 * (1 + 3 * (4 - 1)) > 128


def test_alternating_schedule_preserves_all_roots_and_duplicates():
    paths = [dict(call=i, representative=i) for i in range(16)] + [dict(call=16, representative=1)]
    jobs = schedule(paths)
    assert len(jobs) == 32
    assert [a for _, a in jobs[:4]] == ["program", "beam", "beam", "program"]
    assert sum(jobs[i][1] == "program" for i in range(0, 32, 2)) == 8


@pytest.mark.parametrize("frame", [12, 13, 14, 15])
def test_target_uses_nominal_speed_arc_not_a_witness(case, frame):
    state = [12.0, 0.0, 0.0, 4.0, 0.0]
    target = target_for(state, frame, case["geometry"])
    task = check_target(target, state, frame, case["geometry"], 16)
    assert target["index"] == 12 + (16 - frame) and task["terminal_frame"] == 16 - frame
    assert task["target"][3:] == [4.0, 0.0]


@pytest.mark.parametrize(
    "kind", ["index", "nearest", "station", "heading", "frame", "speed", "schema"]
)
def test_target_corruptions_fail(case, kind):
    state = [12.0, 0.0, 0.0, 4.0, 0.0]
    target = target_for(state, 12, case["geometry"])
    if kind in ("index", "nearest", "station", "frame"):
        target[kind] += 1
    if kind == "heading":
        target["state"][2] += 0.1
    if kind == "speed":
        target["state"][3] += 0.1
    if kind == "schema":
        target["extra"] = 0
    with pytest.raises(ValueError):
        check_target(target, state, 12, case["geometry"], 16)


def paired_fixture(program=False, beam=False, censored=False):
    return [
        dict(
            call=i,
            arm=a,
            witness=program if a == "program" else (False if censored and i == 0 else beam),
            censored=censored and i == 0 and a == "beam",
        )
        for i in range(16)
        for a in ("program", "beam")
    ]


@pytest.mark.parametrize(
    "program,beam,status",
    [
        (False, False, "null"),
        (True, True, "null"),
        (False, True, "supported"),
        (True, False, "contradicted"),
    ],
)
def test_paired_claim_counts_losses(program, beam, status):
    d = compare(paired_fixture(program, beam))
    assert d["status"] == status
    assert (
        sum(d[k] for k in ["gains", "losses", "both_witness", "both_miss", "censored_pairs"]) == 16
    )


def test_censoring_does_not_become_a_loss_or_a_miss():
    d = compare(paired_fixture(False, False, True))
    assert d["status"] == "inconclusive" and d["censored_pairs"] == 1 and d["both_miss"] == 15


def test_narrow_beam_can_lose_a_scalar_verified_program_witness(case, old, tmp_path):
    # Dense route rewards early acceleration; the late wall requires retaining coasting.
    # Offset points avoid placing them exactly on binary32 box side faces.
    case["geometry"]["route"] = [[0.0, i / 10] for i in range(400)]
    case["points"] = [[-5.0 + (i + 0.037) / 100, 0.5, 17.6] for i in range(1001)]
    outcomes = {}
    for arm in ("program", "beam"):
        folder = tmp_path / arm
        folder.mkdir()
        record, events, trace, retained, plan, masks = bundle(case, old, folder, arm)
        checker = program_check if arm == "program" else probe_check
        outcomes[arm] = checker(record, events, trace, retained, case, old, plan, masks)
    assert outcomes == {"program": True, "beam": False}


def test_target_rotates_and_translates_with_route(case):
    state = [12.0, 0.0, 0.0, 4.0, 0.0]
    expected = target_for(state, 12, case["geometry"])
    angle = 0.7

    def point(x, y):
        return [
            3 + x * math.cos(angle) - y * math.sin(angle),
            -2 + x * math.sin(angle) + y * math.cos(angle),
        ]

    g = copy.deepcopy(case["geometry"])
    g["route"] = [list(reversed(point(p[1], p[0]))) for p in g["route"]]
    transformed = [*point(state[0], state[1]), angle, state[3], state[4]]
    actual = target_for(transformed, 12, g)
    check_target(actual, transformed, 12, g, 16)
    assert actual["state"][:2] == pytest.approx(point(*expected["state"][:2]))
    assert math.remainder(
        actual["state"][2] - expected["state"][2] - angle, 2 * math.pi
    ) == pytest.approx(0)


@pytest.mark.parametrize("kind", ["missing", "duplicate", "type"])
def test_incomplete_or_invalid_pair_population_rejected(kind):
    rows = paired_fixture()
    if kind == "missing":
        rows.pop()
    if kind == "duplicate":
        rows[0]["arm"] = "beam"
    if kind == "type":
        rows[0]["witness"] = 0
    with pytest.raises(ValueError):
        compare(rows)


def test_known_loss_falsifies_retention_even_with_other_censoring():
    rows = paired_fixture(True, True, True)
    rows[3]["witness"] = False
    d = compare(rows)
    assert d["status"] == "contradicted" and d["losses"] == 1 and d["censored_pairs"] == 1


@pytest.mark.parametrize("kind", ["hash", "inventory", "parent"])
def test_retained_input_corruptions_fail_before_search(kind):
    from experiments.iter180_equal_work_continuation.retained import load

    p = json.loads((ROOT / "experiments/iter180_equal_work_continuation/PLAN.json").read_text())
    if kind == "hash":
        p["input_files"][next(iter(p["input_files"]))] = "0" * 64
    if kind == "inventory":
        p["input_files"]["unexpected"] = "0" * 64
    if kind == "parent":
        p["parent_commit"] = "0" * 40
    with pytest.raises(ValueError):
        load(ROOT, p)


@pytest.mark.parametrize("frame", [11, 16, 12.0, True])
def test_target_rejects_out_of_scope_clock(case, frame):
    with pytest.raises(ValueError):
        target_for([12.0, 0.0, 0.0, 4.0, 0.0], frame, case["geometry"])


def test_target_rejects_degenerate_route_segment(case):
    case["geometry"]["route"][2] = case["geometry"]["route"][1]
    with pytest.raises(ValueError):
        target_for([12.0, 0.0, 0.0, 4.0, 0.0], 12, case["geometry"])


def test_known_rational_progress_exclusions_do_not_select_population():
    # The schedule depends on duplicate identity alone, never a diagnostic label.
    paths = [
        dict(
            call=i,
            representative=i,
            classification="progress_excluded" if i % 2 else "verified_continuation",
        )
        for i in range(16)
    ]
    assert {p["call"] for p, _ in schedule(paths)} == set(range(16))


def test_witness_cannot_also_be_time_censored():
    rows = paired_fixture()
    rows[0].update(witness=True, censored=True)
    with pytest.raises(ValueError, match="witness_censor_conflict"):
        compare(rows)
