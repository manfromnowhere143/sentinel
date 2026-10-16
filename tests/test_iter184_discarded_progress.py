"""Constructed controls only; never acquire retained-root continuation outcomes."""

import copy
import ctypes
import json
import os
import struct
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from experiments.iter153_action_feasibility.check import motion
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter172_integrated_rrt.check import outcome
from experiments.iter184_discarded_progress import adapter, contract, retained, replay, records
from experiments.iter184_discarded_progress.produce import extract
from experiments.iter184_discarded_progress.worker import Queries
from experiments.iter184_discarded_progress.check import probe_check, budget_check
from experiments.iter184_discarded_progress.common import write, BASE, document, encode, sha
from tests.test_iter169_full_horizon_control import case as base_case, OLD

ROOT = Path(__file__).resolve().parents[1]
PARENT = json.loads((ROOT / retained.PREVIOUS / "PLAN.json").read_text())


def case():
    value = base_case()
    value["geometry"]["comparators"] = dict(final=dict(hazard_time=8.0, rc=0.1))
    return value


def fixture():
    c = case()
    q = Queries(query_for(c))
    state = c["geometry"]["reset"]
    trace = []
    for i in range(4):
        if i:
            state = motion(state, [0.0, 0.0])
        trace.append(
            dict(
                id=i,
                frame=i,
                parent=i - 1 if i else None,
                action=[0.0, 0.0] if i else None,
                state=state,
                background=q(state),
                route=outcome(state, c["geometry"]),
                reason="clear",
            )
        )
    first = dict(
        call=1,
        before=[*trace[0]["state"], 0],
        trace=copy.deepcopy(trace[:2]),
        result=dict(attempts=5, selected_evaluation=1, selected_prefix=1),
    )
    duplicate = dict(copy.deepcopy(first), call=2)
    start = dict(copy.deepcopy(trace[1]), parent=None, action=None)
    final = dict(
        call=3,
        before=[*trace[1]["state"], 1],
        trace=[start],
        result=dict(attempts=9, selected_evaluation=None, selected_prefix=0),
    )
    trial = dict(
        call=3, id=1, trace=[start] + copy.deepcopy(trace[2:]), eligibility=dict(eligible_prefix=2)
    )
    return c, q, [first, duplicate, final], trial


def test_numeric_path_and_complete_ambiguity_inventory():
    c, _, connections, trial = fixture()
    p = extract(connections, trial, 2)
    assert p["chain"] == [1] and p["ambiguous_joins"] == 1
    assert p["joins"][0]["choices"] == [1, 2]
    replay.binding(p, connections, [trial], c["geometry"]["reset"])


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("state", "path_source_binding"),
        ("chain", "join_selection"),
        ("choices", "join_inventory"),
        ("ambiguity", "join_ambiguity"),
        ("prefix", "eligible_prefix"),
        ("missing_join", "join_count"),
    ],
)
def test_changed_retained_paths_rejected(mutation, reason):
    c, _, connections, trial = fixture()
    p = extract(connections, trial, 2)
    if mutation == "state":
        p["trace"][-1]["state"][0] += 0.1
    elif mutation == "chain":
        p["chain"] = [2]
    elif mutation == "choices":
        p["joins"][0]["choices"] = [1]
    elif mutation == "ambiguity":
        p["ambiguous_joins"] = 0
    elif mutation == "prefix":
        p["prefix"] = 3
    else:
        p["joins"] = []
    with pytest.raises(ValueError, match=reason):
        replay.binding(p, connections, [trial], c["geometry"]["reset"])


def test_population_preserves_every_prefix_and_checks_separate_route_indices():
    c, _, connections, trial = fixture()
    high, population, maxima = retained.population(connections, [trial])
    assert high == 1 and len(population) == 2 and maxima[0]["prefix"] == 2
    assert replay.population_check(population, connections, [trial], c["geometry"]) == 1
    for bad in [population[:-1], population + population[-1:], list(reversed(population))]:
        with pytest.raises(ValueError, match="audited_population"):
            replay.population_check(bad, connections, [trial], c["geometry"])


def test_discovery_call_is_fully_charged():
    _, _, connections, _ = fixture()
    assert retained.remaining(connections, 3, 100) == 81
    assert retained.remaining(connections, 2, 100) == 90
    with pytest.raises(ValueError, match="remaining_work_domain"):
        retained.remaining(connections, 3, 19)


@pytest.mark.parametrize("budget,wall", [(0, 1), (18000, 1), (64.0, 1), (64, 0), (64, 120)])
def test_invalid_conditional_budgets_rejected(budget, wall):
    with pytest.raises(ValueError, match="conditional_"):
        retained.conditional_plan(PARENT, budget, wall)


def test_conditional_plan_changes_only_remaining_caps():
    p = retained.conditional_plan(PARENT, 7385, 12.51213537500007)
    assert p["attempt_budget"] == 7385 and p["per_run_seconds"] == 120 - 12.51213537500007
    assert {k for k in p if p[k] != PARENT[k]} == {"attempt_budget", "per_run_seconds"}


def test_absolute_root_does_not_change_sampler_clock(monkeypatch):
    samples = []

    class Function:
        def __call__(
            self,
            seed,
            initial,
            low,
            high,
            target,
            directed,
            goal,
            stop,
            sample,
            output,
            capacity,
            length,
            error,
        ):
            assert initial[5] == 24 and low[5] == 0 and high[5] == 96
            for _ in range(100):
                row = (ctypes.c_double * 6)()
                sample(row)
                samples.append(row[5])
            length._obj.value = 0
            return 0

    monkeypatch.setattr(adapter.C, "CDLL", lambda _: SimpleNamespace(sentinel_rrt=Function()))
    c = case()
    q = Queries(query_for(c))
    r = adapter.search("fake", c["geometry"], OLD, PARENT, q, lambda *a: None, 10, start_frame=24)
    assert r["trace"][0]["frame"] == 24 and min(samples) < 24 and max(samples) > 24


@pytest.mark.parametrize("mutation", ["clock", "state", "mask", "parent"])
def test_scalar_path_does_not_reset_history(mutation):
    c, q, connections, trial = fixture()
    p = extract(connections, trial, 2)
    trace = p["trace"]
    keys = [sha(struct.pack(">5d", *r["state"])) for r in trace]
    assert replay.path_check(trace, keys, c, OLD, q.rows) == 0
    if mutation == "clock":
        trace[-1]["frame"] = 0
    elif mutation == "state":
        trace[0]["state"] = [100, 0, 0, 0, 0]
    elif mutation == "mask":
        keys[-1] = "0" * 64
    else:
        trace[-1]["parent"] = None
    with pytest.raises(ValueError):
        replay.path_check(trace, keys, c, OLD, q.rows)


def native_fixture():
    c, _, connections, trial = fixture()
    start = trial["trace"][0]
    edge = dict(connections[-1], trace=trial["trace"])
    last = edge["trace"][-1]
    native = dict(
        rows=[
            [*start["state"], start["frame"], 0, 0, 0],
            [*last["state"], last["frame"], 3, 0, 0.5],
        ],
        selected_connections=[3],
    )
    return c, edge, native


@pytest.mark.parametrize("mutation", [None, "root", "token", "duration", "endpoint", "selection"])
def test_native_absolute_sequence_contract(mutation):
    _, edge, native = native_fixture()
    root, frame = edge["trace"][0]["state"], edge["trace"][0]["frame"]
    if mutation == "root":
        native["rows"][0][5] = 0
    elif mutation == "token":
        native["rows"][1][6] = 4
    elif mutation == "duration":
        native["rows"][1][8] = 0.25
    elif mutation == "endpoint":
        native["rows"][1][0] += 1
    elif mutation == "selection":
        native["selected_connections"] = []
    if mutation is None:
        replay.native_binding(native, {3: edge}, edge["trace"], root, frame, OLD)
    else:
        with pytest.raises(ValueError, match="native_"):
            replay.native_binding(native, {3: edge}, edge["trace"], root, frame, OLD)


@pytest.mark.parametrize(
    "args,expected",
    [
        ((True, False, False, False), "verified_full_route_continuation"),
        ((False, False, False, False), "unresolved_bounded_miss"),
        ((False, True, False, False), "demonstrated_timing_constraint"),
        ((False, False, True, False), "demonstrated_timing_constraint"),
        ((False, False, False, True), "unobserved_continuation"),
    ],
)
def test_classification_keeps_unknowns(args, expected):
    assert replay.classify(*args) == expected


@pytest.mark.parametrize(
    "args",
    [
        (True, True, False, False),
        (True, False, True, False),
        (True, False, False, True),
        (0, False, False, False),
    ],
)
def test_witness_contradiction_rejected(args):
    with pytest.raises(ValueError):
        replay.classify(*args)


def test_early_root_has_explicit_unknown_certificate():
    c = case()
    last = dict(frame=14, state=c["geometry"]["reset"])
    cert = dict(status="outside_window", progress=None, completion=None)
    assert replay.certificates_check(cert, last, c, OLD) == (False, False)
    cert["status"] = "feasible"
    with pytest.raises(ValueError, match="unknown_certificate"):
        replay.certificates_check(cert, last, c, OLD)


@pytest.mark.parametrize(
    "mutation", [None, "attempts", "unused", "premature_time", "elapsed", "status"]
)
def test_outer_budget_and_censoring(mutation):
    p = dict(attempt_budget=64, per_run_seconds=10)
    r = dict(
        attempts=60, unused_attempt_budget=4, complete=False, native_status=0, stop="attempt_budget"
    )
    edges = {1: dict(stop="attempt_reservation")}
    elapsed = 1
    if mutation == "attempts":
        r["attempts"] = 65
    elif mutation == "unused":
        r["unused_attempt_budget"] = 0
    elif mutation == "premature_time":
        r["stop"] = "time_budget"
    elif mutation == "elapsed":
        elapsed = 16
    elif mutation == "status":
        r["native_status"] = 2
    if mutation is None:
        budget_check(r, p, edges, 60, elapsed)
    else:
        with pytest.raises(ValueError):
            budget_check(r, p, edges, 60, elapsed)


def test_contract_and_exact_sampler_edit(monkeypatch):
    p = document(ROOT, BASE / "PLAN.json")
    contract.check_plan(ROOT, p)
    p["remaining_attempts"][0] += 1
    with pytest.raises(ValueError, match="fixed_contract"):
        contract.check_plan(ROOT, p)
    p = document(ROOT, BASE / "PLAN.json")
    original = contract.read
    monkeypatch.setattr(
        contract,
        "read",
        lambda root, name: (
            original(root, name).replace(
                b'rng.uniform(0, plan["max_actions"])',
                b'rng.uniform(start_frame, plan["max_actions"])',
            )
            if name == BASE / "adapter.py"
            else original(root, name)
        ),
    )
    with pytest.raises(ValueError, match="conditional_adapter"):
        contract.check_plan(ROOT, p)


def test_duplicate_initialization_rejected(tmp_path, monkeypatch):
    output = tmp_path / BASE / "proof/audit_raw"
    output.mkdir(parents=True)
    monkeypatch.setattr(records, "document", lambda *a: dict(minimum_free_bytes=0))
    monkeypatch.setattr(records, "source_check", lambda *a: None)
    monkeypatch.setattr(records, "git", lambda *a: b"")
    with pytest.raises(FileExistsError):
        records.initialize(tmp_path, output, "0" * 40, "audit")


@pytest.mark.skipif(
    not os.environ.get("SENTINEL_RRT172_LIBRARY"), reason="selected native library unavailable"
)
def test_nonzero_root_native_smoke_and_all_query_admission(tmp_path):
    c = case()
    q = Queries(query_for(c))
    trace = []
    state = c["geometry"]["reset"]
    for i in range(15):
        if i:
            state = motion(state, [0.0, 0.0])
        trace.append(
            dict(
                id=i,
                frame=i,
                parent=i - 1 if i else None,
                action=[0.0, 0.0] if i else None,
                state=state,
                background=q(state),
                route=outcome(state, c["geometry"]),
                reason="clear",
            )
        )
    q.calls = 0
    g = copy.deepcopy(c["geometry"])
    g["reset"] = state
    settings = retained.conditional_plan(PARENT, 64, 110)
    events = []
    result = adapter.search(
        os.environ["SENTINEL_RRT172_LIBRARY"],
        g,
        OLD,
        settings,
        q,
        lambda kind, row: events.append(dict(kind=kind, **row)),
        901,
        start_frame=14,
    )
    suffix = result.pop("trace")
    combined = trace + suffix[1:]
    result.update(
        query_calls=q.calls,
        distinct_scalar_candidates=len(q.rows),
        charged_wall_seconds=result["elapsed_seconds"] + 110,
    )
    q.finish(tmp_path / "masks")
    write(tmp_path / "result.json", result)
    write(tmp_path / "suffix.json", suffix)
    write(tmp_path / "trace.json", combined)
    (tmp_path / "events.jsonl").write_bytes(b"".join(encode(r) for r in events))
    path = dict(
        call=1,
        evaluation=1,
        prefix=14,
        trace=trace,
        certificates=dict(status="outside_window", progress=None, completion=None),
    )
    admitted = probe_check(tmp_path, path, result, c, OLD, settings, time.monotonic() + 60)
    assert admitted["attempts"] <= 64 and admitted["verified_states"] >= 15
    returned = {sha(struct.pack(">5d", *r["state"])) for r in combined}
    unselected = next(k for k in q.rows if k not in returned)
    mask_file = tmp_path / "masks" / (unselected + ".bin")
    saved = mask_file.read_bytes()
    mask_file.write_bytes(bytes([saved[0] ^ 1]) + saved[1:])
    with pytest.raises(ValueError, match="scalar_mask"):
        probe_check(tmp_path, path, result, c, OLD, settings, time.monotonic() + 60)
    mask_file.write_bytes(saved)
    inventory = [r for r in q.rows.values() if r["key"] != unselected]
    (tmp_path / "masks/states.json").write_bytes(encode(inventory))
    mask_file.unlink()
    with pytest.raises(ValueError, match="all_query_scalar_binding"):
        probe_check(tmp_path, path, result, c, OLD, settings, time.monotonic() + 60)
