"""Constructed audit controls; no retained-root bound or continuation acquisition."""

import copy
from fractions import Fraction
import hashlib
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
from experiments.iter179_frontier_continuation_audit.bound import progress_bound
from experiments.iter179_frontier_continuation_audit.bound_check import check_bound
from experiments.iter179_frontier_continuation_audit.check import classify, scalar_masks
from experiments.iter179_frontier_continuation_audit.common import encode, source_check, BASE
from experiments.iter179_frontier_continuation_audit.contract import FIXED, check_plan
from experiments.iter179_frontier_continuation_audit.probe import probe
from experiments.iter179_frontier_continuation_audit.produce import extract, Masks
from experiments.iter179_frontier_continuation_audit.replay import (
    path_binding,
    path_check,
    probe_check,
)
from experiments.iter179_frontier_continuation_audit.retained import state_key, load

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


def trace_for(case, old, count=12):
    query = query_for(case)
    state = case["geometry"]["reset"]
    rows = []
    for frame in range(count + 1):
        action = None if frame == 0 else [0.0, 0.0]
        if action:
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


def bundle(case, old, **overrides):
    plan = dict(FIXED, **overrides)
    retained = trace_for(case, old)
    query = query_for(case)
    raw = probe(
        retained[-1]["state"],
        12,
        case["geometry"],
        old,
        plan,
        lambda s: summary(query(s)),
        time.monotonic() + 30,
    )
    suffix = raw.pop("trace")
    attempts = raw.pop("attempt_records")
    combined = copy.deepcopy(retained + suffix[1:])
    for i, row in enumerate(combined):
        row.update(id=i, parent=i - 1 if i else None)
    masks = {
        state_key(r["state"]): dict(state=r["state"], background=r["background"]) for r in combined
    }
    record = dict(
        result=raw,
        masks=[state_key(r["state"]) for r in combined],
        selected_attempt_ids=[r["id"] for r in suffix],
    )
    return record, attempts, combined, retained, plan, masks


def test_constructed_checkpoint_witness_independently_replays(case, old):
    record, attempts, combined, retained, plan, masks = bundle(case, old)
    assert probe_check(record, attempts, combined, retained, case, old, plan, masks)
    assert combined[-1]["frame"] == 16 and len(combined) == 17
    assert record["result"]["attempts"] <= 1024


def test_partial_work_is_not_a_witness(case, old):
    args = bundle(case, old, per_root_attempts=1)
    record, attempts, combined, retained, plan, masks = args
    assert not probe_check(record, attempts, combined, retained, case, old, plan, masks)
    assert record["result"]["stop"] == "attempt_budget" and record["result"]["attempts"] == 1


def test_blocked_foreground_is_a_bounded_miss(case, old):
    case["geometry"]["obstacles"] = [[14.5, 0.0, 0.0, 2.0, 1.0, 2.0, 0.0]]
    record, attempts, combined, retained, plan, masks = bundle(case, old)
    assert not probe_check(record, attempts, combined, retained, case, old, plan, masks)
    assert record["result"]["stop"] == "beam_empty"
    assert all(r["reason"] in {"foreground", "foreground_sweep", "controls"} for r in attempts[1:])
    assert classify(False, False, False) == "bounded_miss"


def test_deadline_progress_exclusion_does_not_skip_probe(case, old):
    case["geometry"]["reset"][3] = 0.0
    case["geometry"]["comparators"]["first"]["rc"] = 0.9
    record, attempts, combined, retained, plan, masks = bundle(case, old)
    assert not probe_check(record, attempts, combined, retained, case, old, plan, masks)
    bound = progress_bound(retained[-1]["state"], 12, case["geometry"], old, 16)
    assert check_bound(bound, retained[-1]["state"], 12, case["geometry"], old, 16)
    assert record["result"]["attempts"] > 0 and not record["result"]["witness"]


@pytest.mark.parametrize("kind", ["beam", "proposal_count", "query_count", "root"])
def test_replay_rejects_additional_accounting_corruptions(case, old, kind):
    record, attempts, combined, retained, plan, masks = bundle(case, old)
    if kind == "beam":
        record["result"]["depths"][0]["beam"] = []
    if kind == "proposal_count":
        del attempts[1]
        record["result"]["attempts"] -= 1
    if kind == "query_count":
        record["result"]["queries"] += 1
    if kind == "root":
        attempts[0]["frame"] += 1
    with pytest.raises(ValueError):
        probe_check(record, attempts, combined, retained, case, old, plan, masks)


def test_deadline_preserves_censoring(case, old):
    query = query_for(case)
    result = probe(
        [12.0, 0.0, 0.0, 4.0, 0.0],
        12,
        case["geometry"],
        old,
        FIXED,
        lambda s: summary(query(s)),
        time.monotonic() - 1,
    )
    assert result["stop"] == "time_budget" and result["attempts"] == 0
    assert classify(False, False, True) == "unobserved_continuation"


def test_stepwise_proposals_can_switch_steering(case, old):
    g = copy.deepcopy(case["geometry"])
    g["comparators"]["first"]["hazard_time"] = 3.5

    def query(s):
        clear = s[0] == 12 or (
            abs(s[3] - 2) < 1e-12
            and (
                (s[0] < 12.7 and abs(s[4] + math.pi / 48) < 1e-12)
                or (s[0] >= 12.7 and abs(s[4]) < 1e-12)
            )
        )
        n = 0 if clear else 101
        return dict(
            count=n,
            certain_inside=n,
            possible_inside=n,
            decision="clear" if clear else "collision",
            mask_sha256="oracle_fixture",
        )

    result = probe(
        [12.0, 0.0, 0.0, 2.0, 0.0],
        12,
        g,
        old,
        dict(FIXED, target_frame=14),
        query,
        time.monotonic() + 30,
    )
    assert result["witness"]
    assert [r["action"][1] for r in result["trace"][1:]] == [-math.pi / 12, math.pi / 12]


@pytest.mark.parametrize(
    "corruption",
    [
        "count",
        "clock",
        "parent",
        "action",
        "reason",
        "background",
        "guide",
        "effort",
        "depth",
        "selected",
        "trace",
        "mask",
        "stop",
    ],
)
def test_probe_corruptions_fail(case, old, corruption):
    record, attempts, combined, retained, plan, masks = bundle(case, old)
    if corruption == "count":
        record["result"]["attempts"] += 1
    if corruption == "clock":
        attempts[1]["frame"] += 1
    if corruption == "parent":
        attempts[1]["parent"] = 1
    if corruption == "action":
        attempts[1]["action"][0] += 0.1
    if corruption == "reason":
        attempts[1]["reason"] = "clear" if attempts[1]["reason"] != "clear" else "collision"
    if corruption == "background":
        attempts[0]["background"] = None
    if corruption == "guide":
        attempts[1]["guide_distance"] += 1
    if corruption == "effort":
        attempts[1]["effort"] += 1
    if corruption == "depth":
        record["result"]["depths"][0]["survivors"] += 1
    if corruption == "selected":
        record["selected_attempt_ids"] = [0]
    if corruption == "trace":
        combined[-1]["state"][0] += 0.1
    if corruption == "mask":
        record["masks"][-1] = "0" * 64
    if corruption == "stop":
        record["result"]["stop"] = "beam_empty"
    with pytest.raises(ValueError):
        probe_check(record, attempts, combined, retained, case, old, plan, masks)


def chain_fixture(case, old):
    rows = trace_for(case, old)

    def edge(call, a, b):
        trace = copy.deepcopy(rows[a : b + 1])
        trace[0].update(action=None, parent=None)
        return dict(call=call, before=[*rows[a]["state"], a], result={}, trace=trace)

    return [edge(1, 0, 4), edge(2, 0, 4), edge(3, 4, 8), edge(4, 8, 12)]


def test_earliest_numeric_join_retains_ambiguity(case, old):
    connections = chain_fixture(case, old)
    record = extract(connections, 4)
    assert record["chain"] == [1, 3, 4] and record["ambiguous_joins"] == 1
    path_binding(record, connections, case["geometry"]["reset"])


@pytest.mark.parametrize("kind", ["ancestry", "ambiguity", "trace", "missing"])
def test_path_binding_known_bads(case, old, kind):
    connections = chain_fixture(case, old)
    record = extract(connections, 4)
    if kind == "ancestry":
        record["chain"][0] = 2
    if kind == "ambiguity":
        record["ambiguous_joins"] = 0
    if kind == "trace":
        record["trace"][1]["state"][0] += 0.1
    if kind == "missing":
        connections = connections[2:]
    with pytest.raises((ValueError, KeyError)):
        path_binding(record, connections, case["geometry"]["reset"])


def test_missing_ancestor_extraction_fails(case, old):
    with pytest.raises(ValueError, match="ancestor_missing"):
        extract(chain_fixture(case, old)[2:], 4)


def test_scalar_masks_and_selected_path(case, old, tmp_path):
    rows = trace_for(case, old)
    material = Masks(tmp_path / "masks", query_for(case))
    keys = material.path(rows)
    material.finish()
    checked = scalar_masks(tmp_path, case, time.monotonic() + 30)
    assert path_check(rows, keys, case, old, checked) == 13


@pytest.mark.parametrize("kind", ["mask", "counts", "inventory", "duplicate", "state"])
def test_scalar_mask_corruptions(case, old, tmp_path, kind):
    material = Masks(tmp_path / "masks", query_for(case))
    material.path(trace_for(case, old, 1))
    material.finish()
    file = tmp_path / "masks/states.json"
    rows = json.loads(file.read_text())
    if kind == "mask":
        (tmp_path / "masks" / (rows[0]["key"] + ".bin")).write_bytes(b"\xff")
    if kind == "counts":
        rows[0]["background"]["count"] = 1
    if kind == "inventory":
        (tmp_path / "masks/extra.bin").write_bytes(b"x")
    if kind == "duplicate":
        rows.append(rows[0])
    if kind == "state":
        rows[0]["state"][0] += 1
    file.write_bytes(encode(rows))
    with pytest.raises(ValueError):
        scalar_masks(tmp_path, case, time.monotonic() + 30)


def test_mask_producer_refuses_changed_retained_label(case, tmp_path):
    material = Masks(tmp_path / "masks", query_for(case))
    with pytest.raises(ValueError, match="vector_materialization"):
        material.add(case["geometry"]["reset"], dict(count=123))


def test_bound_excludes_impossible_progress_and_keeps_witness(case, old):
    g = copy.deepcopy(case["geometry"])
    g["comparators"]["first"]["rc"] = 0.9
    state = [0.0, 0.0, 0.0, 0.0, 0.0]
    record = progress_bound(state, 15, g, old, 16)
    assert check_bound(record, state, 15, g, old, 16)
    state = [32.0, 0.0, 0.0, 4.0, 0.0]
    record = progress_bound(state, 15, g, old, 16)
    assert not check_bound(record, state, 15, g, old, 16)


@pytest.mark.parametrize(
    "field,value",
    [
        ("excluded", False),
        ("anchor", 39),
        ("allowed_indices", [0]),
        ("radius", ["0", "1"]),
        ("minimum_squared_distance_gap", ["0", "1"]),
        ("frame", 14),
        ("extra", 1),
    ],
)
def test_bound_forgery_fails(case, old, field, value):
    g = copy.deepcopy(case["geometry"])
    g["comparators"]["first"]["rc"] = 0.9
    state = [0.0, 0.0, 0.0, 0.0, 0.0]
    record = progress_bound(state, 15, g, old, 16)
    record[field] = value
    with pytest.raises(ValueError):
        check_bound(record, state, 15, g, old, 16)


@pytest.mark.parametrize("kind", ["clock", "speed", "domain", "checkpoint", "dynamics"])
def test_bound_outside_scope_fails(case, old, kind):
    state = [0.0, 0.0, 0.0, 0.0, 0.0]
    frame = 15
    g = copy.deepcopy(case["geometry"])
    if kind == "clock":
        frame = 11
    if kind == "speed":
        state[3] = 6.001
    if kind == "domain":
        state[0] = 1001
    if kind == "checkpoint":
        g["comparators"]["first"]["hazard_time"] = 5.0
    if kind == "dynamics":
        old["dt"] = 0.5
    with pytest.raises(ValueError):
        progress_bound(state, frame, g, old, 16)


def test_bound_never_excludes_constructed_motion_witnesses(case, old):
    rng = random.Random(179)
    for _ in range(128):
        start = [rng.uniform(0, 30), rng.uniform(-2, 2), rng.uniform(-1, 1), rng.uniform(0, 6), 0.0]
        frame = rng.randrange(12, 16)
        state = list(start)
        g = copy.deepcopy(case["geometry"])
        g["comparators"]["first"]["rc"] = rng.uniform(0.1, 0.9)
        record = progress_bound(start, frame, g, old, 16)
        assert check_bound(record, start, frame, g, old, 16) == record["excluded"]
        for _ in range(16 - frame):
            a = rng.uniform(max(-2, -4 * state[3]), min(2, 4 * (6 - state[3])))
            state = transition(state, [a, rng.uniform(-math.pi / 12, math.pi / 12)], old)
        radius = Fraction(*map(int, record["radius"]))
        assert max(abs(Fraction(state[k]) - Fraction(start[k])) for k in (0, 1)) <= radius
        rc = route_outcome(state, g["route"])["rc"]
        assert not (record["excluded"] and rc >= g["comparators"]["first"]["rc"] - 0.05)


@pytest.mark.parametrize(
    "witness,excluded,censored,label",
    [
        (True, False, False, "verified_continuation"),
        (False, True, False, "progress_excluded"),
        (False, False, False, "bounded_miss"),
        (False, False, True, "unobserved_continuation"),
        (False, True, True, "progress_excluded"),
    ],
)
def test_outcome_categories_stay_distinct(witness, excluded, censored, label):
    assert classify(witness, excluded, censored) == label


def test_false_exclusion_is_invalid():
    with pytest.raises(ValueError, match="bound_false_exclusion"):
        classify(True, True, False)
    with pytest.raises(ValueError, match="classification_type"):
        classify(None, False, False)


@pytest.mark.parametrize(
    "field",
    [
        "minimum_frame",
        "target_frame",
        "per_root_attempts",
        "maximum_total_attempts",
        "aggregate_search_seconds",
        "beam_width",
        "parent_commit",
    ],
)
def test_frozen_contract_cannot_expand(field):
    plan = dict(FIXED, status="preregistered")
    check_plan(plan)
    plan[field] = "bad" if isinstance(plan[field], str) else plan[field] + 1
    with pytest.raises(ValueError, match="audit_contract"):
        check_plan(plan)


def test_source_binding_catches_changed_bytes(tmp_path, monkeypatch):
    from experiments.iter179_frontier_continuation_audit import common

    folder = tmp_path / BASE
    folder.mkdir(parents=True)
    (folder / "PLAN.json").write_bytes(b"{}\n")
    monkeypatch.setattr(common, "git", lambda *args: b"bad\n")
    with pytest.raises(ValueError, match="source_changed"):
        source_check(tmp_path, {"source_files": []}, "a" * 40)
    with pytest.raises(ValueError, match="source_encoding"):
        source_check(tmp_path, {"source_files": []}, "BAD")


def test_retained_population_identity_and_known_bad(monkeypatch):
    from experiments.iter179_frontier_continuation_audit import retained

    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    _, _, selected, trials = load(ROOT, plan)
    assert len(selected) == 19 and len(trials) == 2609
    corrupt = copy.deepcopy(plan)
    corrupt["input_files"][retained.EVENTS] = "0" * 64
    with pytest.raises(ValueError, match="input_hash"):
        load(ROOT, corrupt)
    corrupt = copy.deepcopy(plan)
    corrupt["parent_commit"] = "0" * 40
    with pytest.raises(ValueError, match="reference_identity"):
        load(ROOT, corrupt)
    corrupt = copy.deepcopy(plan)
    corrupt["input_files"].pop(retained.EVENTS)
    with pytest.raises(ValueError, match="input_inventory"):
        load(ROOT, corrupt)


def test_materialization_state_key_preserves_signed_zero():
    assert state_key([0.0, 0.0, 0.0, 0.0, 0.0]) != state_key([0.0, -0.0, 0.0, 0.0, 0.0])
    assert hashlib.sha256(b"x").hexdigest() != state_key([0.0, 0.0, 0.0, 0.0, 0.0])
