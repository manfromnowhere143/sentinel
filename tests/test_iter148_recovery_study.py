from copy import deepcopy
import json
from pathlib import Path
import pytest
from experiments.iter148_recovery_study import admission as a
from experiments.iter148_recovery_study.compare import compare
from experiments.iter146_route_outcome_contract.compare import compare as old_compare
from experiments.iter147_full_horizon_execution.protocol import identity
from experiments.iter147_full_horizon_execution.coordinator import record

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def document():
    return a.study_plan(ROOT)


def receipt(document, pair, previous=None):
    return dict(
        status="supported",
        pair=pair,
        plan_sha256=identity(document),
        previous_receipt_sha256=previous,
        raw_commit="a" * 40,
        raw_inventory_sha256="b" * 64,
        scenario_comparison_status="supported",
    )


def parent(document, pair):
    return dict(
        status="completed",
        pair=pair,
        plan_sha256=identity(document),
        cases=[
            dict(slot=s, returncode=0, deadline_exceeded=False, cleanup=dict(status="absent"))
            for s in document["slots"][pair * 2 : pair * 2 + 2]
        ],
    )


def test_exact_preserved_population_and_basis(document):
    assert document == json.loads(
        (ROOT / "experiments/iter147_full_horizon_execution/STUDY_PLAN.json").read_text()
    )
    assert len(document["slots"]) == 112
    assert len(a.basis(ROOT)) == 64


@pytest.mark.parametrize(
    "field,value",
    [("seed", 145), ("reset_count", True), ("max_actions", 401.0), ("probe", "monitor_hold")],
)
def test_typed_population_mutation(document, field, value):
    v = deepcopy(document)
    v["slots"][0][field] = value
    with pytest.raises(ValueError, match="study_plan_changed"):
        a.validate_plan(ROOT, v)


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "failed"),
        ("pair", True),
        ("plan_sha256", "0" * 64),
        ("previous_receipt_sha256", "a" * 64),
        ("raw_commit", "z" * 40),
        ("raw_inventory_sha256", None),
    ],
)
def test_fabricated_or_unordered_history(document, field, value):
    r = receipt(document, 0)
    r[field] = value
    with pytest.raises(ValueError):
        a.history(document, [r], 1)


def test_complete_chain_and_no_skipped_scenario_comparison(document):
    rows = []
    for i in range(4):
        rows.append(receipt(document, i, identity(rows[-1]) if rows else None))
    assert a.history(document, rows, 4) == identity(rows[-1])
    with pytest.raises(ValueError, match="pair_order"):
        a.history(document, rows, 5)
    rows[-1].pop("scenario_comparison_status")
    with pytest.raises(ValueError, match="scenario_comparison_missing"):
        a.history(document, rows, 4)


@pytest.mark.parametrize(
    "change",
    ["status", "slot", "deadline", "cleanup", "returncode", "boolean_returncode", "missing_case"],
)
def test_parent_failures_rejected(tmp_path, document, change):
    p = parent(document, 0)
    if change == "status":
        p["status"] = "failed"
    elif change == "slot":
        p["cases"][0]["slot"] = document["slots"][2]
    elif change == "deadline":
        p["cases"][0]["deadline_exceeded"] = True
    elif change == "cleanup":
        p["cases"][0]["cleanup"] = {"status": "unobserved"}
    elif change == "returncode":
        p["cases"][0]["returncode"] = 124
    elif change == "boolean_returncode":
        p["cases"][0]["returncode"] = False
    else:
        p["cases"].pop()
    record(tmp_path / "pair_000_result.json", p)
    with pytest.raises(ValueError):
        a.completed_pair(tmp_path, document, 0)


def test_exclusive_initialization_and_bound_history(tmp_path, document):
    q = a.basis(ROOT)
    assert a.claim(ROOT, tmp_path, document, 0, [], q, 0) == document["slots"][:2]
    with pytest.raises(ValueError, match="initialized_history"):
        a.claim(ROOT, tmp_path, document, 0, [], q, 0)
    with pytest.raises(FileNotFoundError):
        a.claim(ROOT, tmp_path, document, 1, [receipt(document, 0)], q, 0)
    record(tmp_path / "pair_000_result.json", parent(document, 0))
    a.claim(ROOT, tmp_path, document, 1, [receipt(document, 0)], q, 0)
    with pytest.raises(ValueError, match="execution_block"):
        a.claim(ROOT, tmp_path, document, 2, [], q, 1)
    with pytest.raises(ValueError, match="qualification_binding"):
        a.claim(ROOT, tmp_path, document, 2, [], "0" * 64, 0)


def test_changed_started_record(tmp_path, document):
    q = a.basis(ROOT)
    a.claim(ROOT, tmp_path, document, 0, [], q, 0)
    p = tmp_path / "pair_000_started.json"
    r = json.loads(p.read_text())
    r["block"] = 1
    p.write_text(json.dumps(r))
    record(tmp_path / "pair_000_result.json", parent(document, 0))
    with pytest.raises(ValueError, match="started_receipt_changed"):
        a.claim(ROOT, tmp_path, document, 1, [receipt(document, 0)], q, 0)


def test_missing_changed_qualification_inputs(tmp_path):
    d = tmp_path / a.BASE
    d.mkdir(parents=True)
    p = tmp_path / "input"
    p.write_text("source")
    import hashlib

    record(
        d / "INPUTS.json",
        dict(files={"input": dict(bytes=6, sha256=hashlib.sha256(b"source").hexdigest())}),
    )
    digest = a.verify_inputs(tmp_path)
    record(
        d / "QUALIFICATION.json",
        dict(
            status="supported",
            inputs_sha256=digest,
            iter147_pairs=4,
            iter147_steps=912,
            iter146_pairs=4,
            iter146_steps=192,
            raw_before_replay=1,
        ),
    )
    with pytest.raises(ValueError, match="qualification_receipt"):
        a.basis(tmp_path)
    p.write_text("change")
    with pytest.raises(ValueError, match="qualified_input_changed"):
        a.verify_inputs(tmp_path)
    p.unlink()
    with pytest.raises(FileNotFoundError):
        a.verify_inputs(tmp_path)


@pytest.mark.parametrize("seconds", [2600, 0, -1, True, float("nan"), float("inf")])
def test_insufficient_time(seconds):
    with pytest.raises(ValueError):
        a.remaining_budget(seconds)


def test_finite_reserves():
    assert a.remaining_budget(2600.01) and a.local_capacity(17 * a.GIB)
    with pytest.raises(ValueError):
        a.local_capacity(17 * a.GIB - 1)
    with pytest.raises(ValueError):
        a.local_capacity(True)


def report(arm):
    o = dict(
        completion_qualified=False,
        collision_observed=False,
        off_route_observed=False,
        censored=True,
        first_failure_time=None,
    )
    rows = [
        dict(
            time=(i + 1) / 4,
            state=[0] * 5,
            action=[0, 0],
            nominal_action=[0, 0],
            rc=0.0,
            nominal="same",
            delivered="same",
            rgb="same",
            actors={},
            collision=False,
            off_route=False,
        )
        for i in range(10)
    ]
    return dict(
        status="supported",
        arm=arm,
        outcome=o,
        scientific=rows,
        route=[[0, 0], [1, 0]],
        reset_state=[0] * 5,
    )


@pytest.mark.parametrize(
    "field,value", [("rgb", "different"), ("time", 0.5), ("nominal_action", [0.5, 0]), ("rc", 0.1)]
)
def test_retained_preexisting_prefix_gaps(field, value):
    n, m, p = (report(arm) for arm in ("nominal", "monitor", "brake_t2_5"))
    p["scientific"][0][field] = value
    args = ([n, deepcopy(n)], [m, deepcopy(m)], [p, deepcopy(p)])
    assert old_compare(*args)["status"] == "supported"
    with pytest.raises(ValueError):
        compare(*args)


def test_unknown_witness_preserved():
    args = tuple([report(arm), report(arm)] for arm in ("nominal", "monitor", "brake_t2_5"))
    r = compare(*args)
    assert r["prefix_steps_verified"] == 10 and r["intersection_witness"] is None


def test_uncommitted_receipt_rejected(tmp_path):
    import subprocess

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    p = tmp_path / "receipt"
    p.write_text("retained")
    subprocess.run(["git", "add", "receipt"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Daniel Wahnich",
            "-c",
            "user.email=cogitoergosum143@gmail.com",
            "commit",
            "-m",
            "Receipt fixture",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    assert a.committed_file(tmp_path, commit, p) == b"retained"
    p.write_text("changed")
    with pytest.raises(ValueError, match="receipt_not_committed"):
        a.committed_file(tmp_path, commit, p)


def test_aggregate_keeps_unknown_false_missing_distinct(document):
    from experiments.iter148_recovery_study.aggregate import predicates, summarize

    assert predicates([True, False, None], 14) == dict(true=1, false=1, unknown=1, missing=11)
    with pytest.raises(ValueError, match="predicate_type"):
        predicates([0], 14)
    with pytest.raises(ValueError, match="comparison_count"):
        predicates([False, None], 1)
    empty = summarize(document, [])
    assert empty["status"] == "inconclusive"
    assert empty["slots_without_supported_admission"] == 112
    assert empty["per_pulse"]["brake_t0"]["nominal"]["witness"] == dict(
        true=0, false=0, unknown=0, missing=14
    )
    rows = []
    for i in range(56):
        row = receipt(document, i, identity(rows[-1]) if rows else None)
        row["steps"] = 2
        if i % 4 == 3:
            comparator = dict(opportunity=True, progress_at_hazard_satisfied=None, witness=False)
            answer = dict(
                nominal=comparator,
                monitor=comparator,
                intersection_witness=False,
                action_contrast=True,
                harm_vs_successful_nominal=None,
            )
            row["comparisons"] = dict(brake_t0=answer, brake_t2_5=answer)
        rows.append(row)
    assert summarize(document, rows[:4])["per_pulse"]["brake_t0"]["intersection_witness"] == dict(
        true=0, false=1, unknown=0, missing=13
    )
    full = summarize(document, rows)
    assert full["status"] == "supported" and full["compared_scenarios"] == 14
    assert full["slots_without_supported_admission"] == 0
    assert full["per_pulse"]["brake_t0"]["harm_vs_successful_nominal"]["unknown"] == 14
