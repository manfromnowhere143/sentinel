"""Actual native wiring, corruptions and unchanged scientific budgets."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from experiments.iter189_uniform_timing_eligibility import adapter, check, contract, fixtures
from experiments.iter189_uniform_timing_eligibility.common import BASE
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter183_timing_eligibility.adapter import Edges

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / BASE / "PLAN.json").read_text())
OLD = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())


@pytest.fixture(scope="module")
def library():
    value = os.environ.get("SENTINEL_RRT186_LIBRARY")
    if not value:
        pytest.skip("Iter186 qualified native build unavailable")
    return Path(value)


@pytest.fixture(scope="module")
def acquired(tmp_path_factory, library):
    folder = tmp_path_factory.mktemp("i189-wiring") / "constructed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "experiments.iter189_uniform_timing_eligibility.fixtures",
            "--root",
            str(ROOT),
            "--output",
            str(folder),
            "--library",
            str(library),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=30,
    )
    return folder


def load(folder):
    def read(name):
        return json.loads((folder / name).read_text())

    return dict(
        events=[json.loads(r) for r in (folder / "events.jsonl").read_text().splitlines()],
        sequences=read("sequences.json"),
        result=read("result.json"),
        trace=read("selected/trace.json"),
        **read("inputs.json"),
    )


def replay(value):
    return check.wiring(**value, deadline=time.monotonic() + 30)


def test_full_native_worker_and_registered_scalar_replay(acquired):
    value = load(acquired)
    result = check.case_check(
        acquired, value["case"], OLD, value["plan"], value["result"], time.monotonic() + 30
    )
    assert result["registered_extra"] == 3 and result["selected_extra"] == 2
    assert result["attempts"] == 510 and result["distinct_registered_states"] == 27


@pytest.mark.parametrize(
    "mutation",
    [
        "parent",
        "target",
        "token",
        "duration",
        "control",
        "selection",
        "drop_extra",
        "drop_event",
        "attempts",
        "queries",
        "late_complete",
        "clock",
        "extra_count",
        "sequence_omission",
        "reuse_node",
    ],
)
def test_independent_wiring_rejects_corruption(acquired, mutation):
    v = copy.deepcopy(load(acquired))
    e, sequences, r = v["events"], v["sequences"], v["result"]
    reg = next(x["event"] for x in e if x["kind"] == "native_event" and x["event"]["kind"] == 2)
    choice = next(x for x in e if x["kind"] == "branch_choice" and x["extra"])
    conn = next(x for x in e if x["kind"] == "connection")
    sequence = next(iter(sequences.values()))
    if mutation == "parent":
        reg["parent"] += 1
    elif mutation == "target":
        conn["target"][0] += 1
    elif mutation == "token":
        reg["token"] += 100
    elif mutation == "duration":
        reg["steps"] += 1
    elif mutation == "control":
        sequence["trace"][1]["action"][0] += 0.1
    elif mutation == "selection":
        choice["extra"]["evaluation"] += 1
    elif mutation == "drop_extra":
        choice["extra"] = None
    elif mutation == "drop_event":
        e.remove(next(x for x in e if x["kind"] == "native_event" and x["event"] is reg))
    elif mutation == "attempts":
        r["attempts"] -= 1
    elif mutation == "queries":
        r["queries"] -= 1
    elif mutation == "late_complete":
        r["complete"] = True
        r["elapsed_seconds"] = 11
    elif mutation == "clock":
        e[0]["elapsed"] = -1
    elif mutation == "extra_count":
        r["registered_extra"] += 1
    elif mutation == "sequence_omission":
        sequences.pop(next(iter(sequences)))
    else:
        reg["node"] = 1
    with pytest.raises(ValueError):
        replay(v)


@pytest.mark.parametrize("mutation", ["mask", "missing_mask", "false_count"])
def test_registered_scalar_replay_rejects_corruption(acquired, tmp_path, mutation):
    import shutil

    folder = tmp_path / "raw"
    shutil.copytree(acquired, folder)
    states = json.loads((folder / "masks/states.json").read_text())
    path = folder / "masks" / (states[-1]["key"] + ".bin")
    if mutation == "missing_mask":
        path.unlink()
    elif mutation == "mask":
        path.write_bytes(b"\x01")
    else:
        states[-1]["background"]["count"] = 1
        from experiments.iter189_uniform_timing_eligibility.common import encode

        (folder / "masks/states.json").write_bytes(encode(states))
    v = load(folder)
    with pytest.raises((ValueError, FileNotFoundError)):
        check.case_check(folder, v["case"], OLD, v["plan"], v["result"], time.monotonic() + 30)


def test_primary_and_motion_work_unchanged_and_selection_issues_no_query():
    c, logs, counts = fixtures.case(), [[], []], [0, 0]
    q = query_for(c)

    def query(which, state):
        counts[which] += 1
        return summary(q(state))

    old = Edges(
        c["geometry"],
        OLD,
        PLAN,
        lambda s: query(0, s),
        lambda kind, row: logs[0].append(dict(kind=kind, **row)),
    )
    new = adapter.RetainingEdges(
        c["geometry"],
        OLD,
        PLAN,
        lambda s: query(1, s),
        lambda kind, row: logs[1].append(dict(kind=kind, **row)),
    )
    start, target = [*c["geometry"]["reset"], 0], [0.325, 0.0, 0.0, 1.3, 0.0, 4.0]
    new.event(dict(kind=0, node=1, parent=0, token=0, steps=0, state=start, target=None))
    primary = old.directed(start, target)
    rows = new.branches(1, start, target)
    assert len(rows) == 2
    assert new.accepted[1]["trace"] == primary["trace"]
    assert counts[0] == counts[1] and old.attempts == new.attempts == 128
    assert rows[0]["token"] == 1 and rows[1]["token"] == 2
    with pytest.raises(ValueError, match="callback_parent"):
        new.branches(999, start, target)


@pytest.mark.parametrize("boundary", ["choice", "primary", "extra"])
def test_integrated_deadline_drops_solution(library, monkeypatch, boundary):
    original = adapter.RetainingEdges.__init__

    def initialized(self, geometry, old, plan, query, emit):
        def timed_emit(kind, row):
            event_kind = row.get("event", {}).get("kind")
            if (
                (boundary == "choice" and kind == "branch_choice")
                or (boundary == "primary" and event_kind == 1)
                or (boundary == "extra" and event_kind == 2)
            ):
                self.started = time.monotonic() - plan["per_run_seconds"]
            emit(kind, row)

        original(self, geometry, old, plan, query, timed_emit)

    monkeypatch.setattr(adapter.RetainingEdges, "__init__", initialized)
    c = fixtures.case()
    q = query_for(c)
    result = adapter.search(
        library,
        c["geometry"],
        OLD,
        dict(PLAN, attempt_budget=512),
        lambda s: summary(q(s)),
        lambda *args: None,
        20261027,
    )
    assert not result["complete"] and result["native_stop_code"] == 2
    assert len(result["trace"]) == 1 and result["selected_tokens"] == []


@pytest.mark.parametrize(
    "key",
    [
        "cases",
        "seeds",
        "attempt_budget",
        "per_run_seconds",
        "connection_attempt_budget",
        "connection_horizon",
        "max_actions",
    ],
)
def test_frozen_population_and_budgets_cannot_change(key):
    plan = copy.deepcopy(PLAN)
    plan[key] = list(reversed(plan[key])) if isinstance(plan[key], list) else plan[key] + 1
    with pytest.raises(ValueError, match="changed_contract:" + key):
        contract.check_contract(ROOT, plan)


def test_all_parent_and_runtime_bindings_are_current():
    assert contract.check_contract(ROOT, PLAN)


def test_missing_source_binding_rejected():
    plan = copy.deepcopy(PLAN)
    plan["source_files"].pop()
    with pytest.raises(ValueError, match="source_inventory"):
        contract.check_contract(ROOT, plan)


def test_wrong_native_binary_rejected(tmp_path):
    from experiments.iter189_uniform_timing_eligibility.runtime import verify

    library = tmp_path / "wrong.dylib"
    library.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="bridge_identity"):
        verify(ROOT, library, tmp_path)


@pytest.mark.parametrize("mutation", ["source", "status", "commit"])
def test_qualification_admission_binding_rejects_corruption(monkeypatch, mutation):
    from experiments.iter189_uniform_timing_eligibility import qualify
    from experiments.iter189_uniform_timing_eligibility.common import encode

    source, commit = "a" * 40, "b" * 40
    value = dict(status="supported", source_commit=source, raw_commit="c" * 40)
    if mutation == "source":
        value["source_commit"] = "d" * 40
    elif mutation == "status":
        value["status"] = "invalid"
    data = encode(value)
    monkeypatch.setattr(qualify, "read", lambda *args: data)
    monkeypatch.setattr(qualify, "git", lambda *args: b"wrong" if mutation == "commit" else data)
    with pytest.raises(ValueError, match="qualification_"):
        qualify.admitted(ROOT, source, commit)


@pytest.fixture(scope="module")
def timed_acquired(tmp_path_factory, library):
    folder = tmp_path_factory.mktemp("i189-timed") / "constructed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "experiments.iter189_uniform_timing_eligibility.fixtures",
            "--root",
            str(ROOT),
            "--output",
            str(folder),
            "--library",
            str(library),
            "--timed",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=30,
    )
    return folder


def test_timed_native_registration_exercises_early_exclusions(timed_acquired):
    v = load(timed_acquired)
    result = check.case_check(
        timed_acquired, v["case"], OLD, v["plan"], v["result"], time.monotonic() + 30
    )
    assert result["eligibility"]["uniform"]["early_first_excluded_prefixes"] > 0
    assert result["registered_primary"] > 0 and result["registered_extra"] > 0


@pytest.mark.parametrize(
    "mutation", ["certificate", "prefix", "omit", "cache", "clock", "status", "finish"]
)
def test_native_timing_replay_rejects_bypass(timed_acquired, mutation):
    v = copy.deepcopy(load(timed_acquired))
    row = next(
        e
        for e in v["events"]
        if e["kind"] == "evaluation"
        and any(r["excluded"] is True and r["certificate"] for r in e["eligibility"]["records"])
    )
    claim = row["eligibility"]
    record = next(r for r in claim["records"] if r["excluded"] is True and r["certificate"])
    if mutation == "certificate":
        record["certificate"]["status"] = "unknown"
        record["excluded"] = False
    elif mutation == "prefix":
        claim["eligible_prefix"] = claim["legacy"]["eligible_prefix"]
    elif mutation == "omit":
        claim["records"] = []
    elif mutation == "cache":
        record["hit"] = True
        record["certificate"] = None
    elif mutation == "clock":
        record["start"] = -1
    elif mutation == "status":
        record["status"] = "after_checkpoint"
    else:
        claim["finish"] = 0
    with pytest.raises(ValueError):
        replay(v)


def retained_trap():
    population = json.loads(
        (ROOT / "experiments/iter188_early_timing_feasibility/POPULATION.json").read_text()
    )
    trap = next(x for x in population["endpoints"] if x["id"] == "bend_left:18")
    cases = json.loads(
        (ROOT / "experiments/iter161_grouping_width_ablation/CASES.json").read_text()
    )
    geometry = next(c["geometry"] for c in cases if c["id"] == trap["case"])
    return trap, geometry


def scan_row(engine, trace, deadline):
    claim = engine.scan(trace, len(trace) - 1, None, deadline)
    return dict(
        trace=trace,
        valid_prefix=len(trace) - 1,
        eligibility=claim,
        interrupted=None if claim["complete"] else "time_budget",
    )


def test_uniform_truncation_inheritance_cache_and_empty_survivors():
    from experiments.iter189_uniform_timing_eligibility.eligibility import Eligibility
    from experiments.iter189_uniform_timing_eligibility.eligibility_check import EligibilityReplay

    trap, geometry = retained_trap()
    trace = [dict(state=trap["state"], frame=f) for f in (18, 19, 20)]
    start = time.monotonic()
    producer, checker = Eligibility(geometry, OLD, start), EligibilityReplay(geometry, OLD, 120)
    first = scan_row(producer, trace, start + 120)
    checker.check(first)
    assert first["eligibility"]["eligible_prefix"] == 0
    assert first["eligibility"]["records"][1]["status"] == "inherited_exclusion"
    second = scan_row(producer, trace, start + 120)
    checker.check(second)
    assert second["eligibility"]["records"][0]["hit"] is True
    assert checker.summary()["uniform"]["cache_hits"] == 1
    assert checker.summary()["uniform"]["early_first_excluded_prefixes"] == 2


@pytest.mark.parametrize("stage", ["before", "during", "finalization"])
def test_uniform_expiry_never_returns_eligible_prefix(monkeypatch, stage):
    from experiments.iter189_uniform_timing_eligibility.eligibility import Eligibility
    from experiments.iter189_uniform_timing_eligibility.eligibility_check import EligibilityReplay

    trap, geometry = retained_trap()
    trace = [dict(state=trap["state"], frame=f) for f in (18, 19)]
    producer = Eligibility(geometry, OLD, 0)
    monkeypatch.setattr(producer.legacy, "elapsed", lambda: 0.0)
    clocks = {"before": [10.0, 10.0], "during": [0.0, 10.0, 10.0], "finalization": [0.0, 0.0, 10.0]}
    clock = iter(clocks[stage])
    monkeypatch.setattr(producer, "elapsed", lambda: next(clock))
    row = scan_row(producer, trace, 10)
    EligibilityReplay(geometry, OLD, 10).check(row)
    assert row["eligibility"]["eligible_prefix"] == 0 and row["interrupted"] == "time_budget"


@pytest.mark.parametrize(
    "change", ["unsupported", "outside", "next_checkpoint", "after_checkpoint", "empty"]
)
def test_uncertified_states_are_not_pruned(change):
    from experiments.iter189_uniform_timing_eligibility.eligibility import Eligibility
    from experiments.iter189_uniform_timing_eligibility.eligibility_check import EligibilityReplay

    trap, geometry = retained_trap()
    geometry, old, state, frame = (
        copy.deepcopy(geometry),
        copy.deepcopy(OLD),
        list(trap["state"]),
        19,
    )
    if change == "unsupported":
        old["acceleration_bound"] = 3
    elif change == "outside":
        state[0] = 1001
    elif change == "next_checkpoint":
        frame = 31
        state = [0.0, 0.0, 0.0, 0.0, 0.0]
        geometry["comparators"] = {"final": {"hazard_time": 8, "rc": 0.0}}
    elif change == "after_checkpoint":
        frame = 32
    else:
        geometry["comparators"] = {}
    trace = [dict(state=state, frame=f) for f in (frame - 1, frame)]
    start = time.monotonic()
    row = scan_row(Eligibility(geometry, old, start), trace, start + 120)
    EligibilityReplay(geometry, old, 120).check(row)
    assert row["eligibility"]["eligible_prefix"] == 1


@pytest.mark.parametrize("mutation", ["nan", "boolean_frame", "negative_frame", "nan_route"])
def test_malformed_early_state_is_invalid(mutation):
    from experiments.iter189_uniform_timing_eligibility.eligibility import Eligibility

    trap, geometry = retained_trap()
    geometry, row = copy.deepcopy(geometry), dict(state=list(trap["state"]), frame=19)
    if mutation == "nan":
        row["state"][0] = float("nan")
    elif mutation == "boolean_frame":
        row["frame"] = True
    elif mutation == "negative_frame":
        row["frame"] = -1
    else:
        geometry["route"][0][0] = float("nan")
    start = time.monotonic()
    with pytest.raises(ValueError):
        Eligibility(geometry, OLD, start).inspect(row, 1, False, start + 120)


def test_all_retained_paths_and_two_traps(tmp_path):
    from experiments.iter189_uniform_timing_eligibility.retained import produce
    from experiments.iter189_uniform_timing_eligibility.retained_check import (
        check as retained_check,
    )

    path = tmp_path / "retained.json"
    produce(ROOT, path)
    result = retained_check(ROOT, path, time.monotonic() + 120)
    assert result["excluded_paths"] == ["bend_left:18", "bend_left:50"]
    assert result["successful_paths"] == 9 and result["successful_transitions"] == 300
    records = json.loads(path.read_text())
    records.pop()
    path.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="retained_population"):
        retained_check(ROOT, path, time.monotonic() + 120)


@pytest.mark.parametrize("change", ["case", "budget", "dynamics"])
def test_qualification_fixture_substitution_rejected(tmp_path, change):
    from experiments.iter189_uniform_timing_eligibility.qualify import checked_inputs

    values = fixtures.inputs(ROOT, True)
    if change == "case":
        values["case"]["geometry"]["reset"][0] += 1
    elif change == "budget":
        values["plan"]["attempt_budget"] += 1
    else:
        values["old"]["dt"] *= 2
    (tmp_path / "inputs.json").write_text(json.dumps(values))
    with pytest.raises(ValueError, match="qualification_inputs"):
        checked_inputs(ROOT, tmp_path, True)


def test_composed_checker_rejects_cache_identity_change():
    from experiments.iter189_uniform_timing_eligibility.eligibility import Eligibility
    from experiments.iter189_uniform_timing_eligibility.eligibility_check import EligibilityReplay

    trap, geometry = retained_trap()
    trace = [dict(state=trap["state"], frame=f) for f in (18, 19)]
    start = time.monotonic()
    row = scan_row(Eligibility(geometry, OLD, start), trace, start + 120)
    row["eligibility"]["records"][0]["key"] += "wrong"
    with pytest.raises(ValueError, match="uniform_cache_identity"):
        EligibilityReplay(geometry, OLD, 120).check(row)


def test_parent_bytes_cannot_change(monkeypatch):
    original = contract.read
    name = "experiments/iter188_early_timing_feasibility/bound.py"
    monkeypatch.setattr(
        contract, "read", lambda root, path: b"wrong" if str(path) == name else original(root, path)
    )
    with pytest.raises(ValueError, match="parent_changed"):
        contract.check_contract(ROOT, PLAN)
