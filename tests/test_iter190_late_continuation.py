"""Constructed programs, independent scalar admission and frozen-work known-bads."""

import copy
import json
from pathlib import Path
import time

import pytest
from experiments.iter190_late_continuation_audit import (
    fixtures,
    probe,
    probe_check,
    population_check,
    contract,
)
from experiments.iter190_late_continuation_audit.common import BASE, OLD, encode
from experiments.iter190_late_continuation_audit.masks import verify
from experiments.iter190_late_continuation_audit.check import path_check, timing_check

ROOT = Path(__file__).resolve().parents[1]
OLD_VALUE = json.loads((ROOT / OLD).read_text())
PLAN = json.loads((ROOT / BASE / "PLAN.json").read_text())


@pytest.fixture(scope="module")
def acquired(tmp_path_factory):
    values = {}
    for blocked in (False, True):
        for method in PLAN["arms"]:
            folder = tmp_path_factory.mktemp("i190") / "case"
            case, prefix, value = fixtures.produce(folder, OLD_VALUE, method, blocked)
            masks = verify(folder, case, time.monotonic() + 60)
            values[(method, blocked)] = (folder, case, prefix, value, masks)
    return values


@pytest.mark.parametrize("method", ["stop_wait_route", "beam_then_route"])
@pytest.mark.parametrize("blocked", [False, True])
def test_full_constructed_arms(acquired, method, blocked):
    folder, case, prefix, value, masks = acquired[(method, blocked)]
    checked = probe_check.check(value, prefix, case, OLD_VALUE, 2048, masks)
    assert checked["checkpoint"]
    assert checked["complete"] is (not blocked)
    used = path_check(prefix, case, OLD_VALUE, masks) | checked["used"]
    assert used == set(masks)
    if checked["complete"]:
        path_check(
            prefix + [value["rows"][i] for i in value["complete_ids"][1:]], case, OLD_VALUE, masks
        )


@pytest.mark.parametrize("method", ["stop_wait_route", "beam_then_route"])
@pytest.mark.parametrize(
    "mutation",
    [
        "motion",
        "action",
        "parent",
        "clock",
        "bool_clock",
        "mask",
        "witness",
        "missing_work",
        "budget",
        "query_count",
        "program",
        "stop",
    ],
)
def test_replay_rejects_corruption(acquired, method, mutation):
    _, case, prefix, source, masks = acquired[(method, False)]
    v = copy.deepcopy(source)
    if mutation == "motion":
        v["rows"][1]["state"][0] += 0.1
    elif mutation == "action":
        v["rows"][1]["action"][0] += 0.1
    elif mutation == "parent":
        v["rows"][1]["parent"] = 1
    elif mutation == "clock":
        v["rows"][1]["frame"] += 1
    elif mutation == "bool_clock":
        v["rows"][1]["frame"] = True
    elif mutation == "mask":
        v["rows"][0]["background"]["count"] += 1
    elif mutation == "witness":
        v["complete_ids"] = [0]
    elif mutation == "missing_work":
        v["rows"].pop()
    elif mutation == "budget":
        v["attempts"] -= 1
    elif mutation == "query_count":
        v["queries"] -= 1
    elif mutation == "program":
        if v["programs"]:
            v["programs"][0]["speed"] = 3.0
        else:
            v["beam"]["selected"] = 0
    else:
        v["stop"] = "complete" if v["stop"] != "complete" else "programs_exhausted"
    with pytest.raises((ValueError, IndexError, KeyError)):
        probe_check.check(v, prefix, case, OLD_VALUE, 2048, masks)


@pytest.mark.parametrize("method", ["stop_wait_route", "beam_then_route"])
def test_zero_transition_budget(tmp_path, method):
    folder = tmp_path / "zero"
    case, prefix, value = fixtures.produce(folder, OLD_VALUE, method, False, cap=0)
    masks = verify(folder, case, time.monotonic() + 30)
    assert not probe_check.check(value, prefix, case, OLD_VALUE, 0, masks)["complete"]
    assert value["attempts"] == 0 and value["stop"] == "attempt_budget"


@pytest.mark.parametrize("method", ["stop_wait_route", "beam_then_route"])
def test_expired_deadline_retains_no_new_transition(acquired, method):
    _, case, prefix, _, masks = acquired[(method, False)]

    def query(state):
        return masks[next(k for k, r in masks.items() if r["state"] == state)]["background"]

    value = probe.run(
        method,
        prefix[-1]["state"],
        26,
        case["geometry"],
        OLD_VALUE,
        2048,
        query,
        time.monotonic() - 1,
        1073741824,
    )
    assert value["attempts"] == 0 and value["stop"] == "time_budget"
    assert not probe_check.check(value, prefix, case, OLD_VALUE, 2048, masks)["complete"]


@pytest.mark.parametrize("mutation", ["mask", "missing_mask", "counts", "extra_mask"])
def test_scalar_gate_rejects_corruption(acquired, tmp_path, mutation):
    import shutil

    folder, case, _, _, _ = acquired[("stop_wait_route", False)]
    target = tmp_path / "copy"
    shutil.copytree(folder, target)
    rows = json.loads((target / "masks/states.json").read_text())
    path = target / "masks" / (rows[-1]["key"] + ".bin")
    if mutation == "mask":
        path.write_bytes(b"\xff")
    elif mutation == "missing_mask":
        path.unlink()
    elif mutation == "extra_mask":
        (target / "masks/extra.bin").write_bytes(b"0")
    else:
        rows[-1]["background"]["count"] += 1
        (target / "masks/states.json").write_bytes(encode(rows))
    with pytest.raises((ValueError, FileNotFoundError)):
        verify(target, case, time.monotonic() + 30)


@pytest.mark.parametrize(
    "mutation", ["remaining", "identity", "trace", "duplicate", "calls", "omit"]
)
def test_population_and_original_work_reject_substitution(monkeypatch, mutation):
    original = population_check.read
    value = json.loads(original(ROOT, BASE / "POPULATION.json"))
    row = value["records"][0]
    if mutation == "remaining":
        row["remaining_attempts"] += 1
    elif mutation == "identity":
        row["node"] += 1
    elif mutation == "trace":
        row["trace"][2]["state"][0] += 0.1
    elif mutation == "duplicate":
        row["representative"] = "wrong"
    elif mutation == "calls":
        row["outgoing_calls"] = []
    else:
        value["records"].pop()
    monkeypatch.setattr(
        population_check,
        "read",
        lambda root, name: (
            encode(value) if str(name) == str(BASE / "POPULATION.json") else original(root, name)
        ),
    )
    with pytest.raises(ValueError, match="population_complete_identity"):
        population_check.load(ROOT)


def test_all_native_population_and_remaining_budgets():
    population, _ = population_check.load(ROOT)
    assert len(population["records"]) == 22
    assert len({r["representative"] for r in population["records"]}) == 21
    assert sum(len(r["outgoing_evaluations"]) for r in population["records"]) == 691
    assert all(
        r["consumed_attempts"] + r["remaining_attempts"] == 18000 for r in population["records"]
    )
    assert all(
        r["charged_original_wall"] + r["remaining_seconds"] == 120 for r in population["records"]
    )


@pytest.mark.parametrize("mutation", ["budget", "time", "query", "uncensored", "early_timeout"])
def test_clock_and_budget_known_bads(mutation):
    value = dict(method="stop_wait_route", queries=1, stop="complete")
    timing = dict(
        method="stop_wait_route",
        attempt_cap=50,
        wall_cap=20,
        common_seconds=0.1,
        charged_seconds=1.0,
        queries=1,
        censored=False,
    )
    if mutation == "budget":
        timing["attempt_cap"] += 1
    elif mutation == "time":
        timing["charged_seconds"] = -1.0
    elif mutation == "query":
        timing["queries"] = 2
    elif mutation == "uncensored":
        timing["charged_seconds"] = 20.0
    else:
        value["stop"] = "time_budget"
        timing["censored"] = True
    with pytest.raises(ValueError):
        timing_check(timing, value, 50, 20, 0.1)


def test_payload_expiry_censors_an_observed_witness():
    value = dict(method="stop_wait_route", queries=1, stop="complete")
    timing = dict(
        method="stop_wait_route",
        attempt_cap=50,
        wall_cap=20,
        common_seconds=0.1,
        charged_seconds=20.0,
        queries=1,
        censored=True,
    )
    assert timing_check(timing, value, 50, 20, 0.1) is False


@pytest.mark.parametrize(
    "key",
    [
        "per_arm_attempts",
        "per_arm_seconds",
        "audit_producer_seconds",
        "audit_checker_seconds",
        "arms",
    ],
)
def test_frozen_schedule_and_resource_contract(key):
    plan = copy.deepcopy(PLAN)
    plan[key] = list(reversed(plan[key])) if isinstance(plan[key], list) else plan[key] + 1
    with pytest.raises(ValueError, match="plan_changed"):
        contract.check_contract(ROOT, plan)


def test_source_inventory_and_runtime_bindings():
    assert contract.check_contract(ROOT, PLAN)
    from experiments.iter190_late_continuation_audit.runtime import verify as runtime

    from experiments.iter171_centered_shooting.runtime import identity
    from experiments.iter188_early_timing_feasibility.runtime import observe

    expected = json.loads((ROOT / BASE / "RUNTIME.json").read_text())
    if expected == dict(numeric=observe(), science=identity()):
        runtime(ROOT)
    else:
        with pytest.raises(ValueError, match="runtime_identity"):
            runtime(ROOT)


def test_source_omission_rejected():
    plan = copy.deepcopy(PLAN)
    plan["source_files"].pop()
    with pytest.raises(ValueError, match="source_inventory"):
        contract.check_contract(ROOT, plan)


def test_matching_prefix_is_not_full_continuation():
    suffix = [dict(state=[i], frame=i, action=[0, 0], reason="clear") for i in range(4)]
    assert population_check.match(suffix, suffix[:2]) == 1
    wrong = copy.deepcopy(suffix)
    wrong[2]["state"] = [999]
    assert population_check.match(suffix, wrong) == 1


def test_unexpanded_node_is_descriptive_not_feasibility():
    record = dict(node=7, frame=26, outgoing_calls=[])
    value = population_check.expansion(
        record,
        [dict(state=[0], frame=26), dict(state=[1], frame=27, action=[0, 0], reason="clear")],
        dict(outgoing={}, ancestry={}, paths={}),
    )
    assert value["requested"] is False and value["full_continuation_generated"] is False
