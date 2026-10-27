"""Constructed certificate, counterexample, identity and immutable-record controls."""

import copy
from fractions import Fraction as F
import json
import math
from pathlib import Path
import subprocess

import pytest

from experiments.iter188_early_timing_feasibility import bound, check, contract, produce, runtime
from experiments.iter188_early_timing_feasibility.bound_check import verify
from experiments.iter188_early_timing_feasibility.common import BASE, OLD, encode, sha, source_check
from experiments.iter188_early_timing_feasibility.population_check import verify_population
from experiments.iter188_early_timing_feasibility.probes import actions, probe
from experiments.iter188_early_timing_feasibility.probes_check import grid, verify as countercheck

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def old():
    return json.loads((ROOT / OLD).read_text())


@pytest.fixture
def geometry():
    return {"route": [[0.0, float(i)] for i in range(20)], "comparators": {"fixed": {"hazard_time": 8.0}}}


def forced():
    return [16.49, 0.0, 0.0, 3.5, 0.0]


def test_forced_completion_is_necessary_at_early_frames(geometry, old):
    for frame in (0, 1, 12, 21, 23, 24, 30):
        record = bound.certificate(forced(), frame, geometry, old)
        assert record["status"] == "excluded"
        assert verify(record, forced(), frame, geometry, old)
        for action in actions(forced()):
            observation = probe(forced(), frame, action, geometry, old)
            assert not countercheck(observation, forced(), frame, action, geometry, record)


@pytest.mark.parametrize("state", [[16, 0, 0, 0, 0], [16.49, 0, math.pi, 3.5, 0], [16.49, 0, math.pi / 2, 3.5, 0.2], [16.5, 0, 0, 0, 0], [15.75000001, 0, 0, 3.5, 0]])
def test_wait_turn_reverse_tie_and_insufficient_margin_remain_unknown(state, geometry, old):
    record = bound.certificate(state, 21, geometry, old)
    assert record["status"] == "unknown"
    assert not verify(record, state, 21, geometry, old)


def test_duplicate_route_sites_cannot_create_strict_dominance(geometry, old):
    geometry["route"][17] = geometry["route"][16].copy()
    state = [16, 0, 0, 0, 0]
    row = bound.certificate(state, 21, geometry, old)
    assert row["status"] == "unknown" and not verify(row, state, 21, geometry, old)


@pytest.mark.parametrize("frame", [31, 32, 96])
def test_completion_at_or_after_checkpoint_is_not_excluded(frame, geometry, old):
    row = bound.certificate(forced(), frame, geometry, old)
    assert row["reason"] == "next_frame_not_early" and row["box"] is None
    assert not verify(row, forced(), frame, geometry, old)


@pytest.mark.parametrize("mutation", ["clock", "state_nan", "state_bool", "state_shape", "route_nan", "route_empty", "checkpoints_empty"])
def test_malformed_input_is_never_a_favorable_result(mutation, geometry, old):
    state, frame = forced(), 21
    if mutation == "clock":
        frame = -1
    elif mutation == "state_nan":
        state[0] = float("nan")
    elif mutation == "state_bool":
        state[0] = True
    elif mutation == "state_shape":
        state.pop()
    elif mutation == "route_nan":
        geometry["route"][0][0] = float("inf")
    elif mutation == "route_empty":
        geometry["route"] = []
    else:
        geometry["comparators"] = {}
    with pytest.raises(ValueError):
        bound.certificate(state, frame, geometry, old)


@pytest.mark.parametrize("change", ["position", "heading", "speed", "route", "dt", "checkpoint"])
def test_unsupported_numeric_contract_is_explicitly_unknown(change, geometry, old):
    state = forced()
    if change == "position":
        state[0] = 1001
    elif change == "heading":
        state[2] = 1001
    elif change == "speed":
        state[3] = 7
    elif change == "route":
        geometry["route"][0][0] = 1001
    elif change == "dt":
        old["dt"] = 0.5
    else:
        geometry["comparators"]["fixed"]["hazard_time"] = 9
    row = bound.certificate(state, 21, geometry, old)
    assert row["status"] == "unknown" and row["box"] is None
    assert not verify(row, state, 21, geometry, old)


@pytest.mark.parametrize("mutation", ["box", "speed", "coefficient", "anchor", "gap", "margin", "status", "reason", "target", "frame", "extra_field", "numeric_bool", "noncanonical_fraction"])
def test_separate_checker_rejects_certificate_corruption(mutation, geometry, old):
    row = bound.certificate(forced(), 21, geometry, old)
    if mutation == "box":
        row["box"][0][0] = math.nextafter(row["box"][0][0], math.inf)
    elif mutation == "speed":
        row["speed_interval"][0] += 0.01
    elif mutation == "coefficient":
        row["coefficients"][0] = 0.9
    elif mutation == "anchor":
        row["anchor"] = 0
    elif mutation == "gap":
        row["minimum_squared_distance_gap"][0] = "999999999"
    elif mutation == "margin":
        row["comparison_margin"] = ["0", "1"]
    elif mutation == "status":
        row["status"] = "unknown"
    elif mutation == "reason":
        row["reason"] = "not_certified"
    elif mutation == "target":
        row["target_frame"] = 31
    elif mutation == "frame":
        row["frame"] = 22
    elif mutation == "extra_field":
        row["unbound"] = True
    elif mutation == "numeric_bool":
        row["coefficients"][0] = True
    else:
        row["comparison_margin"] = ["2", str(2**24)]
    with pytest.raises(ValueError):
        verify(row, forced(), 21, geometry, old)


def test_actual_counterexample_defeats_a_false_exclusion(geometry, old):
    state = [16.0, 0.0, 0.0, 0.0, 0.0]
    record = bound.certificate(state, 21, geometry, old)
    action = [0.0, 0.0]
    observed = probe(state, 21, action, geometry, old)
    assert countercheck(observed, state, 21, action, geometry, record)
    record["status"] = "excluded"
    with pytest.raises(ValueError, match="counterexample_defeats"):
        countercheck(observed, state, 21, action, geometry, record)


def test_joint_constraints_and_source_update_order(geometry, old):
    state = [0.0, 0.0, 0.0, 5.5, 0.4]
    row = bound.certificate(state, 10, geometry, old)
    observed = probe(state, 10, [1.0, 0.0], geometry, old)
    assert not observed["controls_valid"]
    assert observed["state"][1] == 0 and observed["state"][2] > 0
    assert not countercheck(observed, state, 10, [1.0, 0.0], geometry, row)


@pytest.mark.parametrize("state", [[-999.9, 999.9, -2.1, 6 + 1e-12, 0.0], [0, 0, 0, -1e-12, 0], [16, 0, 0, 0.125, -0.25], [16.49, 0, -0.5, 3.5, 0]])
def test_full_fixed_probe_grid_replays_and_encloses_valid_motion(state, geometry, old):
    assert actions(state) == grid(state)
    row = bound.certificate(state, 20, geometry, old)
    for action in actions(state):
        observed = probe(state, 20, action, geometry, old)
        countercheck(observed, state, 20, action, geometry, row)


@pytest.mark.parametrize("mutation", ["action", "state", "index", "control", "witness", "boolean"])
def test_scalar_countercheck_rejects_corruption(mutation, geometry, old):
    state, action = [16.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0]
    row = probe(state, 21, action, geometry, old)
    certificate = bound.certificate(state, 21, geometry, old)
    if mutation == "action":
        row["action"] = [1.0, 0.0]
    elif mutation == "state":
        row["state"][0] += 0.001
    elif mutation == "index":
        row["nearest"] += 1
    elif mutation == "control":
        row["controls_valid"] = False
    elif mutation == "witness":
        row["timing_counterexample"] = False
    else:
        row["controls_valid"] = 1
    with pytest.raises(ValueError):
        countercheck(row, state, 21, action, geometry, certificate)


def test_comparison_guard_exceeds_derived_operator_error():
    each_norm_squared_error = 2 * (4096 * F(1, 2**42) + F(1, 2**84) + F(1, 2**30)) + F(1, 2**29) + 8192 * F(1, 2**40) + F(1, 2**80)
    assert each_norm_squared_error < F(1, 2**25)
    assert 2 * each_norm_squared_error < F(1, 2**23)


def test_positive_retained_transition_is_not_excluded(geometry, old):
    state, action = forced(), [0.0, 0.0]
    observed = probe(state, 31, action, geometry, old)
    item = dict(id="constructed", state=state, frame=31, next=dict(action=action, state=observed["state"], frame=32, route={"nearest": observed["nearest"], "rc": observed["rc"]}))
    row = dict(id=item["id"], group="successful_transition_controls", certificate=bound.certificate(state, 31, geometry, old), probes=[observed])
    assert not check.check_record(item, row, row["group"], geometry, old)["excluded"]
    row["probes"] = []
    with pytest.raises(ValueError, match="probe_population"):
        check.check_record(item, row, row["group"], geometry, old)


@pytest.mark.parametrize("mutation", ["omit", "duplicate", "node", "parent", "token", "frame", "control", "parent_commit"])
def test_independent_population_identity_rejects_corruption(mutation):
    population = json.loads((ROOT / BASE / "POPULATION.json").read_text())
    if mutation == "omit":
        population["endpoints"].pop()
    elif mutation == "duplicate":
        population["endpoints"].append(population["endpoints"][0])
    elif mutation in ("node", "parent", "token", "frame"):
        population["endpoints"][1][mutation] += 1
    elif mutation == "control":
        population["successful_transition_controls"].pop()
    else:
        population["parent_commit"] = "0" * 40
    with pytest.raises(ValueError):
        verify_population(ROOT, population)


def test_frozen_population_identity_without_new_bound_evaluation():
    population = json.loads((ROOT / BASE / "POPULATION.json").read_text())
    assert verify_population(ROOT, population) == dict(endpoints=255, successful_paths=9, successful_transition_controls=300)


@pytest.mark.parametrize("key", ["producer_seconds", "checker_seconds", "max_rss_bytes", "max_output_bytes", "cases", "source_files", "inputs", "cohort_commit"])
def test_plan_cannot_silently_change_population_budget_or_bindings(key):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    if key in ("cases", "source_files"):
        plan[key].pop()
    elif key == "inputs":
        plan[key].pop(next(iter(plan[key])))
    elif key == "cohort_commit":
        plan[key] = "0" * 40
    else:
        plan[key] += 1
    with pytest.raises(ValueError):
        contract.check_plan(ROOT, plan)


def test_parent_inputs_and_closed_plan_are_current():
    contract.check_plan(ROOT, json.loads((ROOT / BASE / "PLAN.json").read_text()))


def test_runtime_and_source_identity_gates(monkeypatch):
    with pytest.raises(ValueError, match="source_id"):
        source_check(ROOT, "bad", {})
    monkeypatch.setattr(runtime, "observe", lambda: {"wrong": True})
    with pytest.raises(ValueError, match="runtime_identity"):
        runtime.verify(ROOT)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}\n', b'{ "x": 1 }\n', b'{"x":NaN}\n', b'{"x":1}'])
def test_noncanonical_or_nonfinite_records_are_rejected(raw):
    with pytest.raises(ValueError):
        check.canonical_document(raw)


@pytest.fixture
def raw_repository(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], stderr=subprocess.DEVNULL)
    git("init")
    git("config", "user.name", "Sentinel fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("commit", "--allow-empty", "-m", "Constructed source")
    source = git("rev-parse", "HEAD").decode().strip()
    plan = dict(max_output_bytes=100000, producer_seconds=300, max_rss_bytes=1024**3)
    folder = tmp_path / BASE / "proof/raw"
    folder.mkdir(parents=True)
    execution = dict(status="completed", source_commit=source, plan_sha256=sha(encode(plan)), records=0,
                     scalar_probes=0, elapsed_seconds=0.1, peak_rss_bytes=1000, new_driving_episodes=0,
                     new_integrated_runs=0, background_queries=0, provider_spend=0)
    (folder / "initialized.json").write_bytes(encode(dict(source_commit=source, plan_sha256=sha(encode(plan)))))
    (folder / "execution.json").write_bytes(encode(execution))
    (folder / "records.jsonl").write_bytes(b"")
    monkeypatch.setattr(check, "source_check", lambda *args: None)
    return tmp_path, folder, plan, execution, git


@pytest.mark.parametrize("mutation", [None, "extra", "uncommitted", "deadline", "scope", "source", "count_bool"])
def test_raw_before_replay_inventory_and_envelope(raw_repository, mutation):
    root, folder, plan, execution, git = raw_repository
    if mutation == "deadline":
        execution["elapsed_seconds"] = 301
    elif mutation == "scope":
        execution["background_queries"] = 1
    elif mutation == "source":
        execution["plan_sha256"] = "0" * 64
    elif mutation == "count_bool":
        execution["records"] = False
    (folder / "execution.json").write_bytes(encode(execution))
    if mutation == "extra":
        (folder / "unexpected.json").write_bytes(b"{}\n")
    git("add", ".")
    git("commit", "-m", "Constructed raw")
    commit = git("rev-parse", "HEAD").decode().strip()
    if mutation == "uncommitted":
        (folder / "records.jsonl").write_bytes(b"{}\n")
    if mutation is None:
        assert check.committed(root, commit, plan) == execution
    else:
        with pytest.raises(ValueError):
            check.committed(root, commit, plan)


def test_checker_has_no_producer_predicate_imports():
    import ast
    for name in ("bound_check.py", "probes_check.py", "population_check.py", "check.py"):
        tree = ast.parse((ROOT / BASE / name).read_text())
        modules = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not {"bound", "probes", "population", "produce"}.intersection(modules)


def test_countercheck_record_identity_and_unknown_corruption(geometry, old):
    state = forced()
    item = dict(id="constructed", state=state, frame=31)
    record = dict(id="wrong", group="endpoints", certificate=bound.certificate(state, 31, geometry, old), probes=[])
    with pytest.raises(ValueError, match="record_identity"):
        check.check_record(item, record, "endpoints", geometry, old)
    unknown = copy.deepcopy(record["certificate"])
    unknown["status"] = "excluded"
    with pytest.raises(ValueError, match="unknown_contract"):
        verify(unknown, state, 31, geometry, old)


def test_outside_coefficient_contract_rejected(monkeypatch, geometry, old):
    monkeypatch.setattr(bound.math, "cos", lambda h: 2.0)
    with pytest.raises(ValueError, match="coefficient_domain"):
        bound.certificate(forced(), 21, geometry, old)


@pytest.mark.parametrize("mutation", [None, "clock", "memory", "size"])
def test_constructed_acquisition_is_exclusive_and_retains_failure(tmp_path, monkeypatch, geometry, old, mutation):
    plan = dict(producer_seconds=300, minimum_free_bytes=0, max_rss_bytes=1024**3, max_output_bytes=64 * 1024**2)
    population = dict(endpoints=[dict(id="constructed", case="toy", state=forced(), frame=21)], successful_transition_controls=[])
    documents = {str(BASE / "PLAN.json"): plan, str(BASE / "POPULATION.json"): population,
                 produce.GEOMETRY: [dict(id="toy", geometry=geometry)], OLD: old}
    monkeypatch.setattr(produce, "read", lambda root, name: encode(documents[str(name)]))
    monkeypatch.setattr(produce, "source_check", lambda *args: None)
    monkeypatch.setattr(produce, "check_plan", lambda *args: None)
    monkeypatch.setattr(produce, "verify", lambda *args: None)
    if mutation == "clock":
        clock = iter([0, 301, 302])
        monkeypatch.setattr(produce.time, "monotonic", lambda: next(clock))
    elif mutation == "memory":
        monkeypatch.setattr(produce, "rss", lambda: 1024**3 + 1)
    elif mutation == "size":
        plan["max_output_bytes"] = 100001
    if mutation is None:
        produce.acquire(tmp_path, "constructed")
        folder = tmp_path / BASE / "proof/raw"
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        with pytest.raises(FileExistsError):
            produce.acquire(tmp_path, "constructed")
        assert before == {p.name: p.read_bytes() for p in folder.iterdir()}
    else:
        with pytest.raises(ValueError):
            produce.acquire(tmp_path, "constructed")
        failure = json.loads((tmp_path / BASE / "proof/raw/failure.json").read_text())
        assert failure["status"] == "invalid"


def test_completed_endpoint_gets_a_zero_length_retained_suffix():
    item = dict(id="toy:31", case="toy", frame=31, state=[0.0] * 5,
                next=dict(frame=32, state=[1.0] * 5, route={"rc": 1.0}))
    witnesses = check.retained_witnesses([item])
    endpoint = dict(case="toy", frame=32, state=[1.0] * 5)
    assert witnesses[check.state_key(endpoint)] == ["toy:31:complete"]
    endpoint["state"][0] = math.nextafter(1.0, math.inf)
    assert check.state_key(endpoint) not in witnesses
    item["next"]["frame"] = 31
    with pytest.raises(ValueError, match="completed_suffix_clock"):
        check.retained_witnesses([item])


def test_parent_input_digest_corruption_is_rejected():
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    plan["inputs"][next(iter(plan["inputs"]))] = "0" * 64
    with pytest.raises(ValueError, match="parent_input"):
        contract.check_plan(ROOT, plan)


def test_frozen_source_byte_change_is_rejected(monkeypatch):
    from experiments.iter188_early_timing_feasibility import common
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    # Exercise a real existing committed PLAN while this new source is still unfrozen.
    monkeypatch.setattr(common, "BASE", Path(common.HISTORY[187]))
    monkeypatch.setattr(common, "read", lambda *args: b"mutated\n")
    with pytest.raises(ValueError, match="source_changed"):
        source_check(ROOT, source, {"source_files": [], "inputs": {}})
