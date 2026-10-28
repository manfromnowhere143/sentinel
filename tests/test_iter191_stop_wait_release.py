"""Constructed positive controls, native dispatch and independent known-bads."""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import pytest
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter183_timing_eligibility.connection import task_for
from experiments.iter189_uniform_timing_eligibility.eligibility import Eligibility
from experiments.iter190_late_continuation_audit.masks import Queries, verify
from experiments.iter191_stop_wait_release import (
    callback_check,
    check,
    contract,
    fixtures,
    policy,
    policy_check,
    population_check,
    worker,
)
from experiments.iter191_stop_wait_release.common import BASE, OLD, PREVIOUS, encode

ROOT = Path(__file__).resolve().parents[1]
OLD_VALUE = json.loads((ROOT / OLD).read_text())
PLANNER = json.loads((ROOT / PREVIOUS / "PLAN.json").read_text())


def acquire(folder, case, record, enabled=True, query_hook=None):
    folder.mkdir()
    query = Queries(folder / "masks", query_for(case))
    actual = query if query_hook is None else query_hook(query)
    value, _ = worker.request(record, case, OLD_VALUE, PLANNER, actual, enabled)
    value = json.loads(encode(value))
    if query.calls:
        query.finish()
        masks = verify(folder, case, time.monotonic() + 30)
    else:
        masks = {}
    return value, masks


@pytest.fixture(scope="module")
def acquired(tmp_path_factory):
    values = {}
    for label in fixtures.LABELS:
        case = fixtures.case(label)
        record = fixtures.request(case)
        for enabled in (False, True):
            folder = tmp_path_factory.mktemp("i191") / "case"
            value, masks = acquire(folder, case, record, enabled)
            values[label, enabled] = folder, case, record, value, masks
    return values


@pytest.mark.parametrize("label", fixtures.LABELS)
@pytest.mark.parametrize("enabled", [False, True])
def test_full_callback_and_summary(acquired, label, enabled):
    _, case, record, value, masks = acquired[label, enabled]
    result = callback_check.check(value, record, case, OLD_VALUE, PLANNER, masks, enabled)
    seconds = value["before_payload_seconds"] + 0.01
    timing = dict(charged_seconds=seconds, original_plus_seconds=seconds, censored=False)
    entry = check.arm_entry(result, timing, value, record, case, OLD_VALUE, PLANNER, value["arm"])
    assert entry["attempts"] <= 128 and result["used"] == set(masks)
    assert result["feedback_requests"] == int(enabled and label != "untimed")
    assert entry["complete"] is (label != "untimed")


@pytest.mark.parametrize("speed", [-1e-13, 0, 0.125, 0.49, 0.5, 0.625, 2, 6, 6 + 1e-13])
def test_exact_stop_and_independent_action(speed):
    case = fixtures.case("timed_curve")
    geometry = case["geometry"]
    geometry["comparators"]["checkpoint"]["hazard_time"] = 4
    state = geometry["reset"][:]
    state[3] = speed
    feedback = policy.Feedback([*state, 0], geometry, OLD_VALUE)
    for frame in range(1, 17):
        action = feedback.action(None, frame, state)
        assert action == policy_check.action(state, frame, geometry, OLD_VALUE)
        assert abs(action[0]) <= 2 and action[1] == 0
        after = transition(state, action, OLD_VALUE)
        assert after[3] == pytest.approx(max(0, state[3] - 0.5), abs=1e-15)
        if state[3] == 0:
            assert after == state
        state = after
    assert state[3] == 0
    release = feedback.action(None, 17, state)
    assert release == pytest.approx(policy_check.action(state, 17, geometry, OLD_VALUE), abs=1e-12)
    assert release[0] > 0


@pytest.mark.parametrize(
    "frame,expected", [(0, False), (23, False), (24, True), (31, True), (32, False), (33, False)]
)
def test_schedule_activation(frame, expected):
    g = fixtures.case("timed_straight")["geometry"]
    g["comparators"] = {"early": dict(hazard_time=2, rc=0.1), "late": dict(hazard_time=8, rc=0.2)}
    before = [*g["reset"], frame]
    assert policy.active(g, before, OLD_VALUE, PLANNER) is expected
    assert policy_check.active(g, before, OLD_VALUE, PLANNER) is expected
    g["comparators"] = {}
    assert not policy.active(g, before, OLD_VALUE, PLANNER)


@pytest.mark.parametrize("time_value", [-1, 0.1, float("nan"), float("inf")])
def test_invalid_schedule_rejected(time_value):
    g = fixtures.case("timed_straight")["geometry"]
    g["comparators"]["checkpoint"]["hazard_time"] = time_value
    for function in (policy.checkpoint, policy_check.final_frame):
        with pytest.raises((ValueError, OverflowError)):
            function(g, OLD_VALUE)


def test_feedback_cache_cannot_alias_physical_parameters(tmp_path):
    case = fixtures.case("timed_straight")
    case["geometry"]["reset"][0] = 1
    record = fixtures.request(case, target_frame=1)
    query = Queries(tmp_path / "masks", query_for(case))
    ev = policy.Evaluator(
        case["geometry"],
        record["before"],
        record["target"],
        task_for(record["before"], record["target"], PLANNER),
        OLD_VALUE,
        PLANNER,
        128,
        time.monotonic() + 30,
        query,
        lambda *_: None,
        Eligibility(case["geometry"], OLD_VALUE, time.monotonic()),
    )
    controls = ev.controls
    physical = ev.evaluate(np.asarray([1.0, 2.0]), "constructed")
    feedback = ev.evaluate_feedback()
    assert ev.controls is controls and ev.evaluations == ev.attempts == 2
    assert physical["id"] != feedback["id"] and ev.cache_hits == 0
    ev.evaluate_feedback()
    assert ev.evaluations == 2 and ev.cache_hits == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "action",
        "state",
        "clock",
        "bool_clock",
        "parent",
        "mask",
        "missing_work",
        "queries",
        "attempts",
        "program",
        "parameters",
        "cache",
        "token",
        "branches",
        "completion",
        "expired",
        "elapsed",
    ],
)
def test_callback_corruption_rejected(acquired, mutation):
    _, case, record, source, masks = acquired["timed_curve", True]
    value = copy.deepcopy(source)
    evaluation = next(e for e in value["events"] if e["kind"] == "evaluation")
    row = evaluation["trace"][1]
    request = value["events"][0]
    if mutation == "action":
        row["action"][0] += 0.1
    elif mutation == "state":
        row["state"][0] += 0.1
    elif mutation == "clock":
        row["frame"] += 1
    elif mutation == "bool_clock":
        row["frame"] = True
    elif mutation == "parent":
        row["parent"] += 1
    elif mutation == "mask":
        row["background"]["count"] += 1
    elif mutation == "missing_work":
        value["events"].remove(evaluation)
    elif mutation == "queries":
        value["queries"] -= 1
    elif mutation == "attempts":
        value["attempts"] -= 1
    elif mutation == "program":
        request["caller"] = "initial"
    elif mutation == "parameters":
        request["values"][1] = 3
    elif mutation == "cache":
        request["cached"] = True
    elif mutation == "token":
        value["events"][-1]["tokens"][0] += 1
    elif mutation == "branches":
        value["branches"] = []
    elif mutation == "completion":
        value["events"][-2]["result"]["world_complete"] = False
    elif mutation == "expired":
        value["events"][-1]["expired"] = True
    else:
        value["before_payload_seconds"] = -1
    with pytest.raises((ValueError, KeyError, IndexError)):
        callback_check.check(value, record, case, OLD_VALUE, PLANNER, masks, True)


@pytest.mark.parametrize("remaining", [0, 1, 7, 8, 9])
def test_horizon_reservation_and_exact_budget(tmp_path, remaining):
    case = fixtures.case("untimed")
    record = fixtures.request(case, consumed=18000 - remaining)
    if remaining == 0:
        with pytest.raises(ValueError, match="call_after_budget"):
            acquire(tmp_path / "case", case, record)
        return
    value, masks = acquire(tmp_path / "case", case, record)
    result = callback_check.check(value, record, case, OLD_VALUE, PLANNER, masks, True)
    assert result["attempts"] == (8 if remaining >= 8 else 0)
    assert not result["complete"]


def test_short_target_is_not_lengthened(tmp_path):
    case = fixtures.case("timed_straight")
    case["geometry"]["comparators"]["checkpoint"]["hazard_time"] = 2
    record = fixtures.request(case, target_frame=1)
    value, masks = acquire(tmp_path / "case", case, record)
    result = callback_check.check(value, record, case, OLD_VALUE, PLANNER, masks, True)
    assert result["connection"]["task"]["terminal_frame"] == 1
    first = next(e for e in value["events"] if e["kind"] == "evaluation")
    assert len(first["trace"]) == 2 and first["trace"][-1]["state"][3] == 0
    assert not first["world_complete"]


def test_deadline_before_callback(tmp_path):
    case = fixtures.case("timed_straight")
    with pytest.raises(ValueError, match="call_after_budget"):
        acquire(tmp_path / "case", case, fixtures.request(case, debit=121))


def test_deadline_during_query_censors_completion(tmp_path, monkeypatch):
    case = fixtures.case("timed_straight")
    record = fixtures.request(case)
    clock = time.monotonic
    offset = [0.0]

    def hook(query):
        def wrapped(state):
            value = query(state)
            offset[0] = 121.0
            return value

        return wrapped

    monkeypatch.setattr(time, "monotonic", lambda: clock() + offset[0])
    value, masks = acquire(tmp_path / "case", case, record, query_hook=hook)
    result = callback_check.check(value, record, case, OLD_VALUE, PLANNER, masks, True)
    assert result["expired"] and not result["complete"] and not value["branches"]


@pytest.mark.parametrize("mutation", ["debit", "undercharge", "negative", "nan", "false_censor"])
def test_timing_known_bads(acquired, mutation):
    _, _, record, value, _ = acquired["timed_straight", True]
    seconds = value["before_payload_seconds"] + 1
    timing = dict(charged_seconds=seconds, original_plus_seconds=seconds, censored=False)
    if mutation == "debit":
        timing["original_plus_seconds"] += 1
    elif mutation == "undercharge":
        timing["charged_seconds"] = 0
    elif mutation == "negative":
        timing["charged_seconds"] = -1
    elif mutation == "nan":
        timing["charged_seconds"] = float("nan")
    else:
        timing["censored"] = True
    with pytest.raises(ValueError):
        callback_check.timing_check(timing, value, record, PLANNER)


def test_serialization_expiry_censors_observed_completion(acquired):
    _, case, record, value, masks = acquired["timed_straight", True]
    result = callback_check.check(value, record, case, OLD_VALUE, PLANNER, masks, True)
    timing = dict(charged_seconds=120, original_plus_seconds=120, censored=True)
    entry = check.arm_entry(result, timing, value, record, case, OLD_VALUE, PLANNER, "candidate")
    assert entry["observed_complete"] and entry["censored"] and not entry["complete"]


@pytest.mark.parametrize("mutation", ["mask", "missing", "counts", "extra"])
def test_scalar_inventory_known_bads(acquired, tmp_path, mutation):
    folder, case, _, _, _ = acquired["timed_straight", True]
    target = tmp_path / "case"
    shutil.copytree(folder, target)
    rows = json.loads((target / "masks/states.json").read_text())
    path = target / "masks" / (rows[-1]["key"] + ".bin")
    if mutation == "mask":
        path.write_bytes(b"\xff")
    elif mutation == "missing":
        path.unlink()
    elif mutation == "extra":
        (target / "masks/extra.bin").write_bytes(b"0")
    else:
        rows[-1]["background"]["count"] += 1
        (target / "masks/states.json").write_bytes(encode(rows))
    with pytest.raises((ValueError, FileNotFoundError)):
        verify(target, case, time.monotonic() + 30)


@pytest.mark.parametrize("mutation", ["attempts", "call", "nodes", "trace", "target", "omit"])
def test_population_substitution_rejected(monkeypatch, mutation):
    original = population_check.read
    value = json.loads(original(ROOT, BASE / "POPULATION.json"))
    row = value["records"][-1]
    if mutation == "attempts":
        row["consumed_attempts"] += 1
    elif mutation == "call":
        row["call"] = 1
    elif mutation == "nodes":
        row["nodes"].pop(next(iter(row["nodes"])))
    elif mutation == "trace":
        row["trace"][1]["state"][0] += 0.1
    elif mutation == "target":
        row["target"][5] -= 1
    else:
        value["records"].pop()
    monkeypatch.setattr(
        population_check,
        "read",
        lambda root, name: (
            encode(value) if name == BASE / "POPULATION.json" else original(root, name)
        ),
    )
    with pytest.raises(ValueError):
        population_check.load(ROOT)


def test_population_complete_and_contract():
    population, cases = population_check.load(ROOT)
    assert len(population["records"]) == 44 and len(cases) == 4
    assert sum(r["kind"] == "original" for r in population["records"]) == 23
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    assert contract.check_contract(ROOT, plan)


@pytest.mark.parametrize(
    "field", ["arms", "native_attempts", "qualification_producer_seconds", "source_files"]
)
def test_contract_change_rejected(field):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    if isinstance(plan[field], list):
        plan[field].pop()
    else:
        plan[field] += 1
    with pytest.raises(ValueError):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (None, "supported"),
        ("baseline", "contradicted"),
        ("lost", "contradicted"),
        ("goal_only", "contradicted"),
        ("native", "contradicted"),
        ("censored", "inconclusive"),
    ],
)
def test_primary_criterion_cannot_be_rescued(mutation, expected):
    record = dict(
        kind="original",
        case="bend_left",
        baseline_reproduced=True,
        arms=[dict(complete=False, censored=False), dict(complete=True, censored=False)],
    )
    native = [dict(qualified=True, censored=False)]
    records = [record]
    if mutation == "baseline":
        record["baseline_reproduced"] = False
    elif mutation == "lost":
        loss = copy.deepcopy(record)
        loss["arms"][0]["complete"], loss["arms"][1]["complete"] = True, False
        records.append(loss)
    elif mutation == "goal_only":
        record["kind"] = "goal"
    elif mutation == "native":
        native[0]["qualified"] = False
    elif mutation == "censored":
        record["arms"][0]["censored"] = True
    assert check.classify(records, native)["status"] == expected


def test_baseline_reproduction_excludes_only_resource_observations(acquired):
    connection = acquired["timed_straight", False][3]["events"][-2]
    changed = copy.deepcopy(connection)
    changed["result"]["elapsed_seconds"] += 1
    changed["result"]["peak_rss_bytes"] += 1
    assert check.baseline_match(changed, connection)
    changed["result"]["attempts"] += 1
    assert not check.baseline_match(changed, connection)


@pytest.mark.parametrize("blocked", [False, True])
def test_rejected_feedback_still_accounts_every_attempt_and_query(tmp_path, blocked):
    case = fixtures.case("untimed")
    case["geometry"]["comparators"] = {"checkpoint": dict(hazard_time=0.25, rc=0)}
    case["geometry"]["reset"] = [0, 0, 0, 6, 0]
    if blocked:
        case["points"] = [[0, 0.5, 5]] * 101
    record = fixtures.request(case)
    value, masks = acquire(tmp_path / "case", case, record)
    result = callback_check.check(value, record, case, OLD_VALUE, PLANNER, masks, True)
    first = next(e for e in value["events"] if e["kind"] == "evaluation")
    assert first["trace"][1]["state"][3] == 5.5  # Braking cannot instantaneously stop.
    assert len(first["trace"]) == 9
    assert result["used"] == set(masks)
    if blocked:
        rejected = [i for i, row in enumerate(first["trace"]) if row["reason"] != "clear"]
        assert rejected and rejected[0] < 8
        assert any(row["background"] is not None for row in first["trace"][rejected[0] + 1 :])
        assert not first["world_complete"]


def test_complete_checker_orchestration_on_constructed_population(tmp_path, monkeypatch):
    """Exercise all 44 record summaries without evaluating a retained scientific input."""
    from experiments.iter153_action_feasibility.geometry import route_outcome

    root = tmp_path
    raw = root / BASE / "proof/qualification_raw"
    raw.mkdir(parents=True)
    plan = dict(**contract.fixed(), source_files=[])
    for name, value in (
        (BASE / "PLAN.json", plan),
        (OLD, OLD_VALUE),
        (PREVIOUS / "PLAN.json", PLANNER),
    ):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encode(value))
    records, cases, queries = [], {}, {}
    for name in PLANNER["cases"]:
        case = fixtures.case("timed_straight")
        case["id"] = name
        cases[name] = case
        (raw / name).mkdir()
        queries[name] = Queries(raw / name / "masks", query_for(case))
    offline = {name: 0 for name in cases}
    for i in range(44):
        name = PLANNER["cases"][i % 4]
        case, query = cases[name], queries[name]
        record = fixtures.request(case)
        state = case["geometry"]["reset"]
        prefix = dict(
            id=0,
            parent=None,
            frame=0,
            action=None,
            state=state,
            route=route_outcome(state, case["geometry"]["route"]),
            reason="clear",
            background=query(state),
        )
        offline[name] += 1
        record.update(
            id=f"constructed_{i}",
            kind="original" if i < 23 else "goal",
            members=[i],
            trace=[prefix],
            original_connection=None,
        )
        records.append(record)
        target = raw / name / f"request_{i:03d}"
        target.mkdir()
        for enabled in (False, True):
            value, _ = worker.request(record, case, OLD_VALUE, PLANNER, query, enabled)
            arm = value["arm"]
            (target / (arm + ".json")).write_bytes(encode(value))
            seconds = value["before_payload_seconds"] + 0.01
            timing = dict(charged_seconds=seconds, original_plus_seconds=seconds, censored=False)
            (target / (arm + "-timing.json")).write_bytes(encode(timing))
            if not enabled and i < 23:
                record["original_connection"] = json.loads(encode(value["events"][-2]))
    summaries = []
    for name, query in queries.items():
        query.finish()
        summary = dict(
            case=name,
            offline_queries=offline[name],
            total_queries=query.calls,
            distinct_states=len(query.rows),
        )
        (raw / name / "summary.json").write_bytes(encode(summary))
        summaries.append(summary)
    execution = dict(
        source_commit="0" * 40,
        native_workers=6,
        children_reaped=True,
        new_integrated_runs=0,
        cases=summaries,
        schedule=[
            dict(index=i, input_id=r["id"], arm=a)
            for i, r in enumerate(records)
            for a in (plan["arms"] if i % 2 == 0 else reversed(plan["arms"]))
        ],
    )
    monkeypatch.setattr(check, "load", lambda _: (dict(records=records), cases))
    monkeypatch.setattr(check, "check_contract", lambda *_: True)
    monkeypatch.setattr(check, "verify", lambda *_: True)
    monkeypatch.setattr(check, "committed", lambda *_: execution)
    # Actual native producer and admission are independently tested below.
    monkeypatch.setattr(
        check,
        "native_admit",
        lambda folder, label, enabled, root, deadline: dict(
            fixture=label,
            arm="candidate" if enabled else "baseline",
            complete=True,
            censored=False,
            feedback_requests=int(enabled and label != "untimed"),
            attempts=0,
            queries=0,
            scalar_states=0,
            scalar_classifications=0,
            native_nodes=0,
            semantic={},
        ),
    )
    result = check.check(root, "1" * 40)
    assert result["status"] == "contradicted"  # These controls already complete in the baseline.
    assert result["paired_requests"] == len(result["records"]) == 44
    assert result["baseline_reproduced"] and result["original_completion_losses"] == 0
    assert result["original_baseline_completions"] == result["original_candidate_completions"] == 23
    assert result["goal_baseline_completions"] == result["goal_candidate_completions"] == 21
    assert result["retained_attempts"] == 132 and result["retained_queries"] == 220


@pytest.mark.parametrize("label", fixtures.LABELS)
def test_actual_native_dispatch_in_fresh_processes(tmp_path, label):
    library = os.environ.get("SENTINEL_RRT186_LIBRARY")
    if not library:
        pytest.skip("frozen local native library is not available on this host")
    admitted = []
    for enabled in (False, True):
        output = tmp_path / ("candidate" if enabled else "baseline")
        command = [
            sys.executable,
            "-m",
            "experiments.iter191_stop_wait_release.worker",
            "--output",
            str(output),
            "--library",
            library,
            "--fixture",
            label,
        ]
        if enabled:
            command.append("--candidate")
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=15)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        admitted.append(check.native_admit(output, label, enabled, ROOT, time.monotonic() + 60))
    if label == "untimed":
        assert admitted[0]["semantic"] == admitted[1]["semantic"]
        assert admitted[1]["feedback_requests"] == 0
    else:
        assert admitted[1]["complete"] and admitted[1]["feedback_requests"] > 0
