"""Constructed controls and corruptions; no retained request audit or search."""

import copy
import json
from pathlib import Path
import time

import pytest

from experiments.iter159_route_search_qualification.run import query_for, retain_trace, witness
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter169_full_horizon_control.check import variables
from experiments.iter176_connector_guidance_audit import check, produce, retained
from experiments.iter176_connector_guidance_audit.common import document
from tests.test_iter169_full_horizon_control import case, OLD

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("experiments/iter176_connector_guidance_audit")


def problem(duplicate=False):
    reset = [0., 0., 0., 1., 0.]
    task = dict(target=[10., 1., .2, 1. if duplicate else 2., 0. if duplicate else .1],
                terminal_frame=8, wait_until=0, stop_from=None,
                tolerance=[.02, .02, .002, .01, .002])
    return reset, task


def audit_pair(duplicate=False):
    reset, task = problem(duplicate)
    mirror, mirror_task = produce.reflected(reset, task)
    a = produce.nominal(reset, task, 128)
    b = produce.nominal(mirror, mirror_task, 128)
    pa, _ = check.check_nominal(a, reset, task, 128, 4096)
    pb, _ = check.check_nominal(b, mirror, mirror_task, 128, 4096)
    return check.coverage(pa, pb, variables(task))


def test_complete_steering_pairs_preserve_nominal_reflection_coverage():
    result = audit_pair()
    assert result["reflection_closed"]
    assert result["original_programs"] == result["mirrored_programs"] == 16


def test_initial_duplicate_exposes_unpaired_next_program_without_more_work():
    result = audit_pair(True)
    assert not result["reflection_closed"]
    assert result["original_programs"] == result["mirrored_programs"] == 16
    assert result["missing_reflected"] == result["extra_mirrored"] == 1


def test_signed_zero_cache_cost_is_distinct_from_numeric_program_coverage():
    reset, task = problem(True)
    task["target"][4] = -0.0
    task["terminal_frame"] = 2
    actual = produce.nominal(reset, task, 4)
    programs, duplicates = check.check_nominal(actual, reset, task, 4, 4096)
    assert actual["nominal_transitions"] == 4 and actual["unique_evaluations"] == 2
    assert len(programs) == 1 and duplicates == 1


def test_reflection_changes_lateral_pose_and_rate_but_not_speed_or_clock():
    reset, task = problem()
    reset[1:3] = [.3, .4]
    reset[4] = .2
    mirrored, mirror_task = produce.reflected(reset, task)
    assert mirrored == [0., -.3, -.4, 1., -.2]
    assert mirror_task["target"] == [10., -1., -.2, 2., -.1]
    assert mirror_task["terminal_frame"] == task["terminal_frame"]
    programs = {(1., -.5)}
    assert check.coverage(programs, {(1., .5)}, [(1, 0), (1, 1)])["reflection_closed"]
    assert not check.coverage(programs, {(-1., -.5)}, [(1, 0), (1, 1)])["reflection_closed"]


def test_pose_changes_do_not_change_this_baselines_proposal_family():
    reset, task = problem()
    changed = copy.deepcopy(task)
    changed["target"][:3] = [-7., 8., -2.]
    assert produce.nominal(reset, task, 128) == produce.nominal(reset, changed, 128)


@pytest.mark.parametrize("horizon", range(1, 9))
def test_all_retained_horizons_admit_parameter_and_reservation_replay(horizon):
    reset, task = problem()
    task["terminal_frame"] = horizon
    row = produce.nominal(reset, task, 128)
    check.check_nominal(row, reset, task, 128, 4096)
    assert row["nominal_transitions"] == (128 // horizon)*horizon
    assert row["unique_evaluations"] == 128 // horizon
    if horizon <= 2:
        assert any(r["index"] >= 82 and r["evaluation"] is not None for r in row["requests"])


@pytest.mark.parametrize("mutation", ["missing", "extra", "count", "values", "cache", "zero_sign"])
def test_nominal_replay_rejects_missing_uncharged_or_changed_programs(mutation):
    reset, task = problem()
    row = produce.nominal(reset, task, 128)
    if mutation == "missing":
        row["requests"].pop()
    if mutation == "extra":
        row["requests"].append(copy.deepcopy(row["requests"][-1]))
    if mutation == "count":
        row["nominal_transitions"] -= 8
    if mutation == "values":
        row["requests"][0]["values"][0] += .1
    if mutation == "cache":
        row["requests"][0]["cached"] = True
    if mutation == "zero_sign":
        row["requests"][1]["values"][1] = -0.0
    with pytest.raises(ValueError):
        check.check_nominal(row, reset, task, 128, 4096)


@pytest.mark.parametrize("limit,deadline,reason", [(1, None, "proposal_limit"),
                                                  (4096, 0, "producer_deadline")])
def test_nominal_supervision_limits_fail_instead_of_becoming_empty_success(limit, deadline, reason):
    reset, task = problem()
    with pytest.raises(ValueError, match=reason):
        produce.nominal(reset, task, 128, limit, deadline)


def path_fixture():
    c = case()
    c["geometry"]["comparators"] = {"early": dict(hazard_time=.25, rc=0.),
                                       "late": dict(hazard_time=1., rc=0.)}
    c["witness_actions"] = [[0., 0.]]*4
    trace = witness(c, OLD, query_for(c))
    first = dict(call=1, before=[*trace[0]["state"], 0], result={}, trace=trace[:3])
    duplicate = dict(first, call=2)
    root = copy.deepcopy(trace[2])
    root.update(parent=None, action=None)
    trial = dict(trace=[root, *trace[3:]], interrupted=None, valid_prefix=2, selected_prefix=1)
    target = dict(call=3, before=[*root["state"], 2], result={}, trace=[root, trace[3]])
    return c, [first, duplicate, target], trial


def test_retained_path_uses_earliest_ancestor_and_scalar_checks_full_partial_path(tmp_path):
    c, connections, trial = path_fixture()
    trace, provenance = produce.extract_path(connections, trial, 3, c["geometry"]["reset"])
    assert provenance == dict(ancestor_calls=[1], ambiguous_joins=1)
    record = dict(call=3, **provenance)
    check.check_binding(trace, record, connections, trial, c["geometry"]["reset"])
    retain_trace(tmp_path / "path", trace, query_for(c))
    metrics = verify_path(trace, c["geometry"], OLD, c["points"], c["ground"],
                          lambda f: (tmp_path / "path" / f"mask_{f:03}.bin").read_bytes(),
                          False, time.monotonic()+10)
    assert metrics["verified_states"] == 5 and metrics["progress_checks"] == 2
    with pytest.raises(ValueError, match="scalar_mask"):
        verify_path(trace, c["geometry"], OLD, c["points"], c["ground"],
                    lambda f: b"wrong", False, time.monotonic()+10)


@pytest.mark.parametrize("mutation", ["ancestor", "missing", "state", "clock", "ambiguity"])
def test_retained_path_corruptions_rejected(mutation):
    c, connections, trial = path_fixture()
    trace, provenance = produce.extract_path(connections, trial, 3, c["geometry"]["reset"])
    record = dict(call=3, **provenance)
    if mutation == "ancestor":
        record["ancestor_calls"] = [2]
    if mutation == "missing":
        record["ancestor_calls"] = []
    if mutation == "state":
        trace[-1]["state"][0] += .1
    if mutation == "clock":
        trace[-1]["frame"] -= 1
    if mutation == "ambiguity":
        record["ambiguous_joins"] = 0
    with pytest.raises(ValueError):
        check.check_binding(trace, record, connections, trial, c["geometry"]["reset"])


@pytest.mark.parametrize("mutation,reason", [("reference", "reference_identity"),
                                             ("population", "case_population"),
                                             ("inventory", "input_inventory"),
                                             ("hash", "input_hash")])
def test_retained_input_contract_rejects_scope_or_identity_changes(mutation, reason):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    if mutation == "reference":
        plan["parent_commit"] = "0"*40
    if mutation == "population":
        plan["cases"].reverse()
    if mutation == "inventory":
        plan["input_files"].pop(next(iter(plan["input_files"])))
    if mutation == "hash":
        plan["input_files"][retained.PREVIOUS + "PLAN.json"] = "0"*64
    with pytest.raises(ValueError, match=reason):
        retained.verify_inputs(ROOT, plan)


@pytest.mark.parametrize("raw,reason", [(b'{"x":1,"x":2}\n', "duplicate_key"),
                                        (b'{ "x":1}\n', "canonical_document"),
                                        (b'{"x":NaN}\n', "nonfinite")])
def test_noncanonical_or_ambiguous_new_raw_rejected(tmp_path, raw, reason):
    (tmp_path / "good.json").write_bytes(b'{"x":1}\n')
    assert document(tmp_path, "good.json") == {"x": 1}
    (tmp_path / "bad.json").write_bytes(raw)
    with pytest.raises(ValueError, match=reason):
        document(tmp_path, "bad.json")


def test_boolean_count_cannot_become_one_evaluation():
    reset, task = problem()
    row = produce.nominal(reset, task, 8)
    row["unique_evaluations"] = True
    with pytest.raises(ValueError, match="count_type"):
        check.check_nominal(row, reset, task, 8, 4096)
