"""Timing eligibility, cache identity, interruption and loss controls."""

import itertools
import json
from pathlib import Path

import pytest

from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter183_timing_eligibility import (
    adapter,
    check,
    contract,
    selection,
    selection_check,
)
from experiments.iter183_timing_eligibility.eligibility import Eligibility
from experiments.iter183_timing_eligibility.eligibility_check import EligibilityReplay
from experiments.iter183_timing_eligibility.comparison import compare
from tests.test_iter169_full_horizon_control import case, OLD
from tests.test_iter175_connection_allocation import PLAN, paired

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("experiments/iter183_timing_eligibility")


def geometry():
    value = case()["geometry"]
    value.update(
        route=[[0.0, float(i)] for i in range(40)],
        obstacles=[],
        comparators=dict(first=dict(hazard_time=4.0, rc=0.3), final=dict(hazard_time=8.0, rc=0.8)),
    )
    return value


def producer(g=None, times=None):
    p = Eligibility(g or geometry(), OLD, 0)
    ticks = iter(times) if times is not None else itertools.count(0, 0.001)
    p.elapsed = lambda: next(ticks)
    return p


def scan(p, states=None, first=29, deadline=10):
    states = states or [[29.0, 0.0, 0.0, 2.0, 0.0]]
    rows = [dict(frame=first - 1)] + [dict(state=s, frame=first + i) for i, s in enumerate(states)]
    claim = p.scan(rows, len(states), None, deadline)
    return dict(
        trace=rows,
        valid_prefix=len(states),
        eligibility=claim,
        interrupted=None if claim["complete"] else "time_budget",
    )


def replay(p, row, checker=None, limit=10):
    checker = checker or EligibilityReplay(p.geometry, OLD, limit)
    checker.check(row)
    return checker


def test_cold_and_warm_certificates_replay():
    p = producer()
    first = scan(p)
    checker = replay(p, first)
    second = scan(p)
    replay(p, second, checker)
    assert first["eligibility"]["records"][0]["hit"] is False
    assert second["eligibility"]["records"][0]["hit"] is True
    assert checker.summary()["distinct_certificate_pairs"] == 1
    assert checker.summary()["cache_hits"] == 1


@pytest.mark.parametrize(
    "state,frame,expected",
    [([34.49, 0, 0, 2, 0], 29, True), ([0, 0, 0, 0, 0], 31, True), ([29, 0, 0, 2, 0], 29, False)],
)
def test_checked_constraints_are_not_finite_miss_labels(state, frame, expected):
    p = producer()
    row = scan(p, [state], frame)
    replay(p, row)
    assert row["eligibility"]["records"][0]["excluded"] is expected
    assert row["eligibility"]["eligible_prefix"] == (0 if expected else 1)


def test_exclusion_inherits_to_later_prefixes_without_new_bounds():
    p = producer()
    row = scan(p, [[34, 0, 0, 2, 0], [34.49, 0, 0, 2, 0], [29, 0, 0, 2, 0]], 28)
    checker = replay(p, row)
    assert row["eligibility"]["eligible_prefix"] == 1
    assert row["eligibility"]["records"][-1]["status"] == "inherited_exclusion"
    assert checker.summary()["progress_certificates"] == 2
    row.update(world_complete=False, id=1, selected_prefix=1)
    connection = dict(before=[0, 0, 0, 0, 0, 27], target=[29, 0, 0, 2, 0, 30])
    c = dict(geometry=p.geometry)
    assert (
        selection.prefix_index(row["trace"], 1, None, False, connection["target"], 27, [16, 32])
        == 1
    )
    assert selection_check.selection_index(row, connection, c, OLD) == 1


def test_checkpoint_counterwitness_invalidates_producer_and_checker():
    p = producer()
    with pytest.raises(ValueError, match="constraint_false_exclusion"):
        scan(p, [[34.49, 0, 0, 2, 0]] * 4, 29)
    p = producer()
    row = scan(p, [[34.49, 0, 0, 2, 0]], 29)
    row["trace"].append(dict(frame=32, state=[35, 0, 0, 2, 0]))
    row["valid_prefix"] = 2
    row["eligibility"]["records"].append(dict(row["eligibility"]["records"][0], prefix=2, frame=32))
    with pytest.raises(ValueError, match="constraint_false_exclusion"):
        replay(p, row)


@pytest.mark.parametrize(
    "first,state,status",
    [
        (23, [29, 0, 0, 2, 0], "outside_window"),
        (32, [29, 0, 0, 2, 0], "outside_window"),
        (29, [1001, 0, 0, 2, 0], "outside_domain"),
        (29, [29, 0, 1001, 2, 0], "outside_domain"),
    ],
)
def test_uncertified_states_stay_eligible(first, state, status):
    p = producer()
    row = scan(p, [state], first)
    replay(p, row)
    assert row["eligibility"]["eligible_prefix"] == 1
    assert row["eligibility"]["records"][0]["status"] == status


def test_unsupported_checkpoint_contract_is_explicit_unknown():
    g = geometry()
    g["comparators"]["final"]["hazard_time"] = 9
    p = producer(g)
    row = scan(p)
    replay(p, row)
    assert row["eligibility"]["eligible_prefix"] == 1
    assert row["eligibility"]["records"][0]["status"] == "outside_contract"


@pytest.mark.parametrize(
    "times,status",
    [
        ([10, 10], "deadline_before"),
        ([0, 10, 10], "partial_progress"),
        ([0, 1, 10, 10], "partial_progress"),
        ([0, 1, 2, 11, 11], "checked"),
        ([0, 1, 2, 3, 11], "checked"),
    ],
)
def test_every_eligibility_deadline_boundary_preserves_interruption(times, status):
    p = producer(times=times)
    row = scan(p)
    replay(p, row)
    assert row["interrupted"] == "time_budget"
    assert row["eligibility"]["eligible_prefix"] == 0
    assert row["eligibility"]["records"][0]["status"] == status


def test_motion_interruption_skips_certificate_work():
    p = producer(times=[10])
    rows = [dict(frame=28), dict(frame=29, state=[29, 0, 0, 2, 0])]
    row = dict(
        trace=rows,
        valid_prefix=1,
        interrupted="time_budget",
        eligibility=p.scan(rows, 1, "time_budget", 10),
    )
    replay(p, row)
    assert row["eligibility"]["records"] == [] and not p.cache


def test_cache_hit_does_not_escape_deadline():
    p = producer(times=[0, 1, 2, 3, 4, 9, 11, 11])
    first = scan(p)
    checker = replay(p, first)
    second = scan(p)
    replay(p, second, checker)
    assert second["eligibility"]["records"][0]["hit"]
    assert second["eligibility"]["eligible_prefix"] == 0


def test_scene_clock_and_dynamics_cache_identity():
    p = producer()
    first = scan(p)
    different_clock = scan(p, first=30)
    assert not different_clock["eligibility"]["records"][0]["hit"]
    g = geometry()
    g["route"] = [[y, -x] for y, x in g["route"]]
    other = producer(g)
    other.cache = p.cache.copy()  # Deliberate accidental shared-cache simulation.
    changed = scan(other)
    assert not changed["eligibility"]["records"][0]["hit"]
    assert changed["eligibility"]["records"][0]["key"] != first["eligibility"]["records"][0]["key"]
    with pytest.raises(ValueError, match="cache_identity"):
        EligibilityReplay(g, OLD, 10).check(first)
    altered = dict(OLD, progress_slack=0.04)
    assert Eligibility(g, altered, 0).namespace != other.namespace


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "outside_window"),
        ("key", "wrong"),
        ("hit", True),
        ("excluded", True),
        ("excluded", 1),
        ("prefix", 2),
        ("frame", 30),
        ("start", -1),
        ("end", -1),
        ("end", float("nan")),
        ("progress_end", 20),
        ("completion_start", 10),
        ("extra", False),
    ],
)
def test_certificate_record_corruption_rejected(field, value):
    p = producer()
    row = scan(p)
    row["eligibility"]["records"][0][field] = value
    with pytest.raises(ValueError):
        replay(p, row)


@pytest.mark.parametrize(
    "kind", ["progress", "completion", "complete", "eligible", "missing", "finish", "motion"]
)
def test_bound_and_aggregate_corruption_rejected(kind):
    p = producer()
    row = scan(p)
    claim = row["eligibility"]
    if kind == "progress":
        claim["records"][0]["progress"]["radius"] = ["0", "1"]
    if kind == "completion":
        claim["records"][0]["completion"]["anchor"] = 0
    if kind == "complete":
        claim["complete"] = False
    if kind == "eligible":
        claim["eligible_prefix"] = 0
    if kind == "missing":
        claim["records"] = []
    if kind == "finish":
        claim["finish"] = 0
    if kind == "motion":
        claim["motion_interrupted"] = True
    with pytest.raises(ValueError):
        replay(p, row)


def test_false_early_scan_termination_rejected():
    p = producer()
    row = scan(p, [[29, 0, 0, 2, 0], [29.5, 0, 0, 2, 0]])
    row["eligibility"].update(
        records=row["eligibility"]["records"][:1], complete=False, finish=10, eligible_prefix=0
    )
    row["interrupted"] = "time_budget"
    with pytest.raises(ValueError, match="early_stop"):
        replay(p, row)


def late_case():
    c = case()
    c["geometry"] = geometry()
    c["geometry"]["reset"] = [33.99, 0.0, 0.0, 2.0, 0.0]
    return c


def edge(c, before, target):
    events = []
    query = query_for(c)
    e = adapter.Edges(
        c["geometry"],
        OLD,
        PLAN,
        lambda s: summary(query(s)),
        lambda kind, row: events.append(dict(kind=kind, **row)),
    )
    e.directed(before, target)
    record = events[-1]
    checker = EligibilityReplay(c["geometry"], OLD, PLAN["per_run_seconds"])
    check.connection_check(record, events[:-1], c, OLD, PLAN, 18000, checker)
    return e, record, events, checker


def test_physically_reached_but_ineligible_target_does_not_stop_proposals():
    c = late_case()
    e, record, events, checker = edge(c, [*c["geometry"]["reset"], 28], [34.49, 0, 0, 2, 0, 29])
    evaluations = [r for r in events if r["kind"] == "evaluation"]
    assert evaluations[0]["target_complete"] and evaluations[0]["selected_prefix"] == 0
    assert record["result"]["stop"] == "attempt_budget"
    assert len(evaluations) > 1 and e.attempts == 128
    assert len(record["trace"]) == 1 and checker.summary()["first_excluded_prefixes"] > 0


def test_completion_cannot_bypass_expired_eligibility():
    c = late_case()
    c["geometry"]["reset"] = [34.49, 0.0, 0.0, 2.0, 0.0]
    query = query_for(c)
    events = []
    e = adapter.Edges(
        c["geometry"],
        OLD,
        PLAN,
        lambda s: summary(query(s)),
        lambda kind, row: events.append(dict(kind=kind, **row)),
    )
    e.eligibility.elapsed = lambda: 121.0  # Constructed clock fault after physical motion.
    e.directed([*c["geometry"]["reset"], 31], [35, 0, 0, 2, 0, 32])
    evaluation = next(r for r in events if r["kind"] == "evaluation")
    assert evaluation["world_complete"] and evaluation["selected_prefix"] == 0
    assert events[-1]["result"]["stop"] == "time_budget" and len(events[-1]["trace"]) == 1
    check.connection_check(
        events[-1], events[:-1], c, OLD, PLAN, 18000, EligibilityReplay(c["geometry"], OLD, 120)
    )


def test_original_selection_outside_window_is_preserved():
    c = case()
    c["geometry"]["comparators"] = {"checkpoint": dict(hazard_time=0.75, rc=0.0)}
    _, record, _, checker = edge(c, [*c["geometry"]["reset"], 0], [0.325, 0, 0, 1.3, 0, 4])
    assert record["trace"][-1]["frame"] >= 3
    assert checker.summary()["distinct_certificate_pairs"] == 0


@pytest.mark.parametrize(
    "field", ["attempt_budget", "per_run_seconds", "connection_attempt_budget", "max_actions"]
)
def test_frozen_budget_cannot_change(field):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    plan[field] += 1
    with pytest.raises(ValueError, match="changed_contract"):
        contract.check_contract(ROOT, plan)


def test_exact_source_integration_contract():
    contract.check_contract(ROOT, json.loads((ROOT / BASE / "PLAN.json").read_text()))


@pytest.mark.parametrize("iteration", [178, 181])
def test_both_comparators_preserve_losses(iteration):
    new, retained = paired()
    retained["iteration"] = iteration
    new[2]["complete"] = False
    new[0]["complete"] = True
    result = compare(new, retained, iteration)
    assert result["reference_iteration"] == iteration
    assert result["gained_cases"] == 1 and result["lost_cases"] == 1
