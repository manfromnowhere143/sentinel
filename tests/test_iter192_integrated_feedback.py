"""Constructed native integration and adversarial evidence-envelope checks."""

import copy
import json
import os
from pathlib import Path
import time

import pytest
from experiments.iter191_stop_wait_release import fixtures
from experiments.iter192_integrated_feedback import check, common, contract, records, worker

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_contract():
    assert contract.check_contract(ROOT, json.loads((ROOT / common.BASE / "PLAN.json").read_text()))


@pytest.mark.parametrize(
    "key,value",
    [
        ("seeds", [1, 2, 3, 4]),
        ("cases", ["bend_left"]),
        ("arms", ["new_policy"]),
        ("retained_comparators", [189]),
        ("worker_supervisor_seconds", 181),
        ("search_producer_seconds", 901),
        ("parent_commit", "0" * 40),
        ("source_files", []),
    ],
)
def test_contract_changes_rejected(key, value):
    plan = json.loads((ROOT / common.BASE / "PLAN.json").read_text())
    plan[key] = value
    with pytest.raises(ValueError, match="plan_changed|source_inventory"):
        contract.check_contract(ROOT, plan)


def test_source_changed_rejected(tmp_path, monkeypatch):
    folder = tmp_path / common.BASE
    folder.mkdir(parents=True)
    (folder / "PLAN.json").write_bytes(b"original")
    monkeypatch.setattr(common, "git", lambda *args: b"original")
    assert common.source_check(tmp_path, {"source_files": []}, "a" * 40) is None
    (folder / "PLAN.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source_changed"):
        common.source_check(tmp_path, {"source_files": []}, "a" * 40)


def test_raw_changed_rejected(tmp_path, monkeypatch):
    folder = tmp_path / "raw"
    folder.mkdir()
    (folder / "file").write_bytes(b"changed")
    monkeypatch.setattr(
        records, "git", lambda root, cmd, *args: b"raw/file\n" if cmd == "ls-tree" else b"original"
    )
    with pytest.raises(ValueError, match="raw_not_committed"):
        records.committed(tmp_path, folder, "a" * 40, {"max_output_bytes": 1000})


def test_population_known_bads():
    plan = contract.fixed()
    population = [dict(case=c, seed=s) for c, s in zip(plan["cases"], plan["seeds"])]
    check.population(plan, population)
    for bad in (population[:-1], population[::-1], population + population[:1]):
        with pytest.raises(ValueError, match="execution_population|case_identity"):
            check.population(plan, bad)
    population[0]["seed"] += 1
    with pytest.raises(ValueError, match="case_identity"):
        check.population(plan, population)


def test_decision_reports_losses_and_censoring():
    rows = [dict(complete=True, stop="model_complete") for _ in range(4)]
    comparisons = {"189": dict(lost_cases=0), "183": dict(lost_cases=0)}
    assert check.classify(rows, comparisons) == "supported"
    rows[0].update(complete=False, stop="attempt_budget")
    assert check.classify(rows, comparisons) == "contradicted"
    rows[0]["stop"] = "time_budget"
    assert check.classify(rows, comparisons) == "inconclusive"
    rows[0].update(complete=True, stop="model_complete")
    comparisons["183"]["lost_cases"] = 1
    assert check.classify(rows, comparisons) == "contradicted"
    rows[0]["complete"] = 1
    with pytest.raises(ValueError, match="completion_type"):
        check.classify(rows, comparisons)


@pytest.fixture(scope="module", params=["untimed", "timed_curve"])
def acquired(request, tmp_path_factory):
    library = os.environ.get("SENTINEL_RRT186_LIBRARY")
    if not library:
        pytest.skip("qualified native library not supplied")
    case = fixtures.case(request.param)
    old = json.loads((ROOT / common.OLD).read_text())
    planner = json.loads((ROOT / common.PREVIOUS / "PLAN.json").read_text())
    planner.update(attempt_budget=512, per_run_seconds=10)
    folder = tmp_path_factory.mktemp("iter192")
    result = worker.collect(folder, case, old, planner, 20261028, Path(library))
    result.update(
        worker_seconds=result["collection_seconds"] + 0.01,
        worker_peak_rss_bytes=result["collection_peak_rss_bytes"],
    )
    common.write(folder / "result.json", result)
    return folder, case, old, planner, result


def test_exact_native_wrapper_and_scalar_replay(acquired):
    folder, case, old, planner, result = acquired
    actual = check.case_check(folder, case, old, planner, result, time.monotonic() + 60)
    assert actual["complete"] is (case["id"] != "constructed_untimed")
    assert actual["recorded_queries"] == actual["queries"]
    assert actual["scalar_classifications"] > 0


@pytest.mark.parametrize(
    "mutation", ["false_completion", "action", "missing_mask", "token", "query_count"]
)
def test_native_evidence_corruption_rejected(acquired, mutation, tmp_path):
    import shutil

    original, case, old, planner, result = acquired
    folder = tmp_path / "raw"
    shutil.copytree(original, folder)
    result = copy.deepcopy(result)
    if mutation == "false_completion":
        result["complete"] = not result["complete"]
        (folder / "result.json").write_bytes(common.encode(result))
    elif mutation == "action":
        trace = json.loads((folder / "trace.json").read_text())
        trace[1]["action"][0] += 0.1
        (folder / "trace.json").write_bytes(common.encode(trace))
    elif mutation == "missing_mask":
        next((folder / "masks").glob("*.bin")).unlink()
    elif mutation == "token":
        sequences = json.loads((folder / "sequences.json").read_text())
        next(iter(sequences.values()))["parent"] += 10
        (folder / "sequences.json").write_bytes(common.encode(sequences))
    else:
        result["recorded_queries"] += 1
        (folder / "result.json").write_bytes(common.encode(result))
    with pytest.raises((ValueError, FileNotFoundError)):
        check.case_check(folder, case, old, planner, result, time.monotonic() + 60)
