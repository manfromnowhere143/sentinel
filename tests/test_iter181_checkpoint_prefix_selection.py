"""Checkpoint selection, independent replay and adverse-result controls."""

import copy
import json
import math
from pathlib import Path

import pytest

from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter181_checkpoint_prefix_selection import (
    adapter,
    check,
    contract,
    selection,
    selection_check,
)
from experiments.iter181_checkpoint_prefix_selection.comparison import compare
from tests.test_iter169_full_horizon_control import case, OLD
from tests.test_iter175_connection_allocation import PLAN
from tests.test_iter175_connection_allocation import paired

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("experiments/iter181_checkpoint_prefix_selection")


def fixture(checkpoints=(), origin=0):
    c = case()
    c["geometry"]["comparators"] = {
        str(i): dict(hazard_time=f / 4, rc=0.0) for i, f in enumerate(checkpoints)
    }
    rows = [dict(state=[float(i), 0.0, 0.0, 1.0, 0.0], frame=origin + i) for i in range(5)]
    e = dict(
        trace=rows, valid_prefix=4, interrupted=None, world_complete=False, selected_prefix=1, id=1
    )
    connection = dict(before=[*rows[0]["state"], origin], target=[*rows[1]["state"], origin + 1])
    return c, e, connection


def select(c, e, connection):
    frames = selection.checkpoint_frames(c["geometry"], OLD)
    actual = selection.prefix_index(
        e["trace"],
        e["valid_prefix"],
        e["interrupted"],
        e["world_complete"],
        connection["target"],
        connection["before"][5],
        frames,
    )
    assert actual == selection_check.selection_index(e, connection, c, OLD)
    return actual


@pytest.mark.parametrize(
    "checkpoints,origin,expected",
    [
        ((), 0, 1),
        ((2,), 0, 2),
        ((2, 2), 0, 2),
        ((2, 4), 0, 4),
        ((2,), 2, 1),
        ((8,), 0, 1),
        ((0,), 0, 1),
    ],
)
def test_only_new_distinct_crossings_affect_selection(checkpoints, origin, expected):
    c, e, conn = fixture(checkpoints, origin)
    assert select(c, e, conn) == expected
    for frame in range(origin, origin + 5):
        assert selection.crossed(
            frame, origin, selection.checkpoint_frames(c["geometry"], OLD)
        ) == selection_check.count_checkpoints(frame, origin, c, OLD)


@pytest.mark.parametrize(
    "valid,interrupted,world,expected",
    [(1, None, False, 1), (0, None, False, 0), (4, "time_budget", False, 0), (4, None, True, 4)],
)
def test_invalid_suffix_interruption_and_completion_priority(valid, interrupted, world, expected):
    c, e, conn = fixture((3,))
    e.update(valid_prefix=valid, interrupted=interrupted, world_complete=world)
    assert select(c, e, conn) == expected


def test_equal_distance_keeps_earliest_prefix_and_heading_wrap():
    c, e, conn = fixture()
    conn["target"] = [2.5, 0.0, -math.pi + 1e-6, 1.0, 0.0, 2.5]
    for r in e["trace"]:
        r["state"][2] = math.pi - 1e-6
    assert select(c, e, conn) == 2


def test_checkpoint_ranking_across_evaluations_and_world_precedence():
    c, e, conn = fixture((3,))
    e["selected_prefix"] = 3
    e["id"] = 2
    closer = copy.deepcopy(e)
    closer["selected_prefix"] = 1
    closer["id"] = 1
    frames = selection.checkpoint_frames(c["geometry"], OLD)

    def key(x):
        return selection.evaluation_rank(x, conn["target"], 0, frames)

    def independent(x):
        return selection_check.selection_rank(x, conn, c, OLD)

    assert key(e) == independent(e) and key(closer) == independent(closer)
    assert min([closer, e], key=key) is e
    closer["world_complete"] = True
    assert min([closer, e], key=key) is closer


def test_equal_checkpoint_and_distance_keep_evaluation_id_tie_order():
    c, e, conn = fixture((3,))
    e["selected_prefix"] = 3
    e["id"] = 2
    earlier = copy.deepcopy(e)
    earlier["id"] = 1
    assert selection.evaluation_rank(earlier, conn["target"], 0, [3]) < selection.evaluation_rank(
        e, conn["target"], 0, [3]
    )
    assert selection_check.selection_rank(earlier, conn, c, OLD) < selection_check.selection_rank(
        e, conn, c, OLD
    )


@pytest.mark.parametrize("time", [-0.25, 0.3, float("inf"), float("nan")])
def test_invalid_checkpoint_schedule_rejected_by_both_implementations(time):
    c, e, conn = fixture()
    c["geometry"]["comparators"] = {"bad": dict(hazard_time=time, rc=0.0)}
    with pytest.raises(ValueError, match="checkpoint_grid"):
        selection.checkpoint_frames(c["geometry"], OLD)
    with pytest.raises(ValueError, match="checkpoint_grid"):
        selection_check.count_checkpoints(4, 0, c, OLD)


@pytest.fixture
def toy_connection():
    c = case()
    c["geometry"]["comparators"] = {"checkpoint": dict(hazard_time=0.75, rc=0.0)}
    query = query_for(c)
    events = []
    edges = adapter.Edges(
        c["geometry"],
        OLD,
        PLAN,
        lambda s: summary(query(s)),
        lambda kind, row: events.append(dict(kind=kind, **row)),
    )
    edges.directed([*c["geometry"]["reset"], 0], [0.325, 0.0, 0.0, 1.3, 0.0, 4.0])
    row = events[-1]
    assert check.connection_check(row, events[:-1], c, OLD, PLAN, 18000) == (
        row["result"]["attempts"],
        row["result"]["queries"],
    )
    assert edges.attempts == row["result"]["attempts"] <= 128
    assert row["trace"][-1]["frame"] >= 3
    return c, row, events[:-1]


def test_real_connection_changes_selection_without_changing_accounting(toy_connection):
    c, row, events = toy_connection
    contrast = selection_check.change_summary(row, events)
    assert contrast["original_rule_frame"] < 3 <= contrast["candidate_frame"]
    assert row["result"]["optimizer"]["started"] is False
    assert row["result"]["stop"] in ("attempt_budget", "qualified_candidate")


@pytest.mark.parametrize(
    "field",
    [
        "selected_evaluation",
        "selected_prefix",
        "attempts",
        "queries",
        "target_complete",
        "world_complete",
    ],
)
def test_corrupt_connection_selection_or_accounting_rejected(toy_connection, field):
    c, row, events = toy_connection
    bad = copy.deepcopy(row)
    value = bad["result"][field]
    bad["result"][field] = not value if type(value) is bool else value + 1
    with pytest.raises(ValueError):
        check.connection_check(bad, events, c, OLD, PLAN, 18000)


@pytest.mark.parametrize("field", ["selected_prefix", "valid_prefix", "interrupted"])
def test_corrupt_evaluation_selection_domain_rejected(toy_connection, field):
    c, row, events = toy_connection
    bad = copy.deepcopy(events)
    e = next(r for r in bad if r["kind"] == "evaluation" and r["selected_prefix"] >= 3)
    e[field] = "time_budget" if field == "interrupted" else 0
    with pytest.raises(ValueError):
        check.connection_check(row, bad, c, OLD, PLAN, 18000)


def test_returned_trace_cannot_be_replaced_by_unselected_prefix(toy_connection):
    c, row, events = toy_connection
    bad = copy.deepcopy(row)
    bad["trace"] = bad["trace"][:2]
    with pytest.raises(ValueError, match="selected_trace"):
        check.connection_check(bad, events, c, OLD, PLAN, 18000)


@pytest.mark.parametrize("constraint", ["progress", "foreground"])
def test_real_rejection_still_limits_checkpoint_eligible_prefix(constraint):
    c = case()
    c["geometry"]["comparators"] = {
        "checkpoint": dict(hazard_time=0.75, rc=0.99 if constraint == "progress" else 0.0)
    }
    if constraint == "foreground":
        c["geometry"]["obstacles"] = [[3.0, 0.0, 0.0, 0.5, 0.5, 1.0, 0.0]]
    query = query_for(c)
    events = []
    edges = adapter.Edges(
        c["geometry"],
        OLD,
        PLAN,
        lambda s: summary(query(s)),
        lambda kind, row: events.append(dict(kind=kind, **row)),
    )
    edges.directed([*c["geometry"]["reset"], 0], [0.325, 0.0, 0.0, 1.3, 0.0, 4.0])
    row = events[-1]
    check.connection_check(row, events[:-1], c, OLD, PLAN, 18000)
    rejected = [
        r
        for e in events[:-1]
        if e["kind"] == "evaluation"
        for r in e["trace"]
        if r["reason"].startswith(constraint)
    ]
    assert rejected and all(r["background"] is None for r in rejected)
    if constraint == "progress":
        assert row["trace"][-1]["frame"] < 3
    for e in events[:-1]:
        if e["kind"] == "evaluation":
            assert all(r["reason"] == "clear" for r in e["trace"][: e["selected_prefix"] + 1])


def test_checkpoint_crossing_does_not_introduce_an_early_stop(toy_connection):
    _, row, events = toy_connection
    assert row["result"]["stop"] == "attempt_budget"
    assert row["result"]["attempts"] == 128
    assert any(e["kind"] == "evaluation" and e["selected_prefix"] >= 3 for e in events)


def test_target_complete_stop_and_return_flag_remain_consistent():
    c = case()
    c["geometry"]["comparators"] = {"checkpoint": dict(hazard_time=0.5, rc=0.0)}
    query = query_for(c)
    events = []
    edges = adapter.Edges(
        c["geometry"],
        OLD,
        PLAN,
        lambda s: summary(query(s)),
        lambda kind, row: events.append(dict(kind=kind, **row)),
    )
    edges.directed([*c["geometry"]["reset"], 0], [1.3, 0.0, 0.0, 1.3, 0.0, 4.0])
    row = events[-1]
    check.connection_check(row, events[:-1], c, OLD, PLAN, 18000)
    assert row["result"]["stop"] == "qualified_candidate"
    assert row["result"]["target_complete"] is True
    assert row["trace"][-1]["frame"] == 4


def test_original_call67_selects_admitted_checkpoint_program_without_propagation():
    original = (
        ROOT
        / "experiments/iter178_root_domain_consistency/proof/search_raw/bend_right/events.jsonl"
    )
    events = [json.loads(line) for line in original.read_text().splitlines()]
    conn = next(e for e in events if e["kind"] == "connection" and e["call"] == 67)
    c = next(
        c
        for c in json.loads(
            (ROOT / "experiments/iter161_grouping_width_ablation/CASES.json").read_text()
        )
        if c["id"] == "bend_right"
    )
    evaluated = []
    for row in events:
        if row["kind"] == "evaluation" and row["call"] == 67:
            row = copy.deepcopy(row)
            row["selected_prefix"] = select(c, row, conn)
            if row["selected_prefix"]:
                evaluated.append(row)
    frames = selection.checkpoint_frames(c["geometry"], OLD)
    best = min(
        evaluated,
        key=lambda r: selection.evaluation_rank(r, conn["target"], conn["before"][5], frames),
    )
    assert best["id"] == 28 and best["selected_prefix"] == 4
    assert min(evaluated, key=lambda r: selection_check.selection_rank(r, conn, c, OLD))["id"] == 28
    admitted = json.loads(
        (
            ROOT / "experiments/iter180_equal_work_continuation/proof/study_raw/run_03/trace.json"
        ).read_text()
    )
    for row in best["trace"][1:]:
        assert all(
            row[k] == admitted[row["frame"]][k]
            for k in ("state", "frame", "action", "route", "background", "reason")
        )
    assert conn["result"]["selected_evaluation"] == 6 and conn["trace"][-1]["frame"] == 13


@pytest.mark.parametrize(
    "key",
    [
        "attempt_budget",
        "per_run_seconds",
        "connection_attempt_budget",
        "connection_horizon",
        "max_actions",
        "max_proposals",
        "cases",
        "seeds",
        "target_tolerance",
    ],
)
def test_ranking_trial_cannot_change_registered_search_contract(key):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    contract.check_contract(ROOT, plan)
    plan[key] = list(reversed(plan[key])) if isinstance(plan[key], list) else plan[key] + 1
    with pytest.raises(ValueError, match="changed_contract:" + key):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize(
    "name,reason",
    [
        ("connection.py", "evaluator_substitution"),
        ("replay.py", "replay_substitution"),
        ("adapter.py", "adapter_substitution"),
        ("controls.py", "unchanged:controls.py"),
        ("RUNTIME.json", "unchanged:RUNTIME.json"),
    ],
)
def test_unregistered_source_changes_rejected(monkeypatch, name, reason):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    original = contract.read
    monkeypatch.setattr(
        contract,
        "read",
        lambda root, path: original(root, path) + (b" " if Path(path) == BASE / name else b""),
    )
    with pytest.raises(ValueError, match=reason):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("field", "plan_fields"),
        ("parent", "parent_identity"),
        ("iteration", "study_identity"),
        ("reference", "reference_changed:"),
    ],
)
def test_identity_known_bads(monkeypatch, mutation, reason):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    original = contract.read
    if mutation == "field":
        plan["extra"] = 0
    if mutation == "parent":
        plan["parent_commit"] = "0" * 40
    if mutation == "iteration":
        plan["iteration"] = 180
    if mutation == "reference":
        monkeypatch.setattr(
            contract,
            "read",
            lambda root, path: (
                original(root, path)
                + (b" " if str(path) == contract.PREVIOUS + "proof/admission.json" else b"")
            ),
        )
    with pytest.raises(ValueError, match=reason):
        contract.check_contract(ROOT, plan)


def test_unknown_or_wrong_baseline_cannot_become_a_three_case_comparator(monkeypatch):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    original_read, original_git = contract.read, contract.git
    name = contract.PREVIOUS + "proof/admission.json"
    bad = json.loads(original_read(ROOT, name))
    bad["complete_cases"] = None
    data = json.dumps(bad).encode()
    monkeypatch.setattr(
        contract,
        "read",
        lambda root, path: data if str(path) == name else original_read(root, path),
    )
    monkeypatch.setattr(
        contract,
        "git",
        lambda root, *args: (
            data if args == ("show", contract.PARENT + ":" + name) else original_git(root, *args)
        ),
    )
    with pytest.raises(ValueError, match="reference_status"):
        contract.check_contract(ROOT, plan)


def test_source_substitution_anchor_must_be_unique():
    with pytest.raises(ValueError, match="substitution_anchor"):
        contract.replace_once(b"xx", b"x", b"y")


def test_case_gain_does_not_erase_lost_success():
    rows, old = paired()
    old["iteration"] = 178
    rows[2]["complete"] = False
    rows[0]["complete"] = True
    result = compare(rows, old)
    assert result["gained_cases"] == result["lost_cases"] == 1


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("missing", "comparison_population"),
        ("order", "comparison_pair"),
        ("unknown", "comparison_outcome"),
        ("open", "reference_status"),
    ],
)
def test_unobserved_or_unpaired_outcomes_remain_invalid(mutation, reason):
    rows, old = paired()
    old["iteration"] = 178
    if mutation == "missing":
        rows.pop()
    if mutation == "order":
        rows.reverse()
    if mutation == "unknown":
        rows[0]["complete"] = None
    if mutation == "open":
        old["phase"] = "running"
    with pytest.raises(ValueError, match=reason):
        compare(rows, old)
