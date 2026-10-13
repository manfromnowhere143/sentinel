"""Source wrapper admission, population identity and adverse-run accounting."""

import copy
import json
from pathlib import Path
import subprocess

import numpy as np
import pytest

from experiments.iter162_source_grouping_qualification import check as checker
from experiments.iter162_source_grouping_qualification import run as producer
from experiments.iter162_source_grouping_qualification.audit import audit_run
from experiments.iter162_source_grouping_qualification.common import BASE, encode, sha, source_check

ROOT = Path(__file__).resolve().parents[1]
OLD = json.loads((ROOT / "experiments/iter153_action_feasibility/PLAN.json").read_text())


def controls():
    geometry = dict(
        reset=[0.0, 0.0, 0.0, 2.0, 0.0],
        route=[[0.0, i / 10] for i in range(21)],
        ego_dimensions=[1.6, 3.0, 1.5],
        obstacles=[],
        comparators={str(i): dict(hazard_time=i / 4, rc=0.0) for i in (1, 2)},
    )
    points = np.array([[100.0, 0.5, 100.0]], dtype="<f4")
    arrays = dict(
        population_xyz=points.copy(),
        selected_xyz=points.copy(),
        population_features=np.array([[0.0, 0.0, 1.0]], dtype="<f4"),
        population_opacity=np.array([1.0], dtype="<f4"),
        selection=np.array([1], dtype="u1"),
        ground_poses=np.eye(4, dtype="<f4")[None, :, :],
    )
    plan = dict(
        arms=["quantized", "exact"],
        beam_width=24,
        attempt_budget=2500,
        max_actions=12,
        per_run_seconds=30,
        producer_seconds=120,
        checker_seconds=120,
        max_rss_bytes=1024**3,
        minimum_free_bytes=0,
        max_output_bytes=16 * 1024**2,
        finalization_reserve_bytes=1024**2,
        selected_points=1,
        population_sha256=sha(points.tobytes()),
        source_files=[],
        inputs={},
    )
    return geometry, arrays, plan


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root).decode().strip()


def commit(root):
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Daniel Wahnich",
        "-c",
        "user.email=cogitoergosum143@gmail.com",
        "commit",
        "-qm",
        "qualification fixture",
    )
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def acquired(tmp_path, monkeypatch, request):
    geometry, arrays, plan = controls()
    plan.update(getattr(request, "param", {}))
    root = tmp_path
    (root / BASE).mkdir(parents=True)
    (root / BASE / "PLAN.json").write_bytes(encode(plan))
    git(root, "init", "-q")
    source = commit(root)
    for module in (producer, checker):
        monkeypatch.setattr(module, "inputs", lambda *_: (geometry, OLD, arrays.copy()))
    raw = root / BASE / "raw"
    producer.run(root, raw, source)
    return root, raw, source, plan, arrays


def test_two_arms_full_acquisition_and_independent_admission(acquired):
    root, raw, source, _, _ = acquired
    with pytest.raises(ValueError, match="raw_inventory"):
        checker.check(root, raw, source)
    result = checker.check(root, raw, commit(root))
    assert result["status"] == "supported"
    assert result["complete_runs"] == result["candidate_completions"] + 1 == 2
    assert result["progress_checks"] == 4 and result["invalid_runs"] == 0
    assert result["selected_points"] == 1
    assert [r["aggregation"] for r in result["records"]] == ["quantized", "exact"]
    with pytest.raises(FileExistsError):
        producer.run(root, raw, git(root, "rev-parse", "HEAD"))


@pytest.mark.parametrize(
    "field,reason",
    [
        ("selection", "selected_population"),
        ("selected_xyz", "selected_population"),
        ("population_xyz", "selected_population"),
        ("population_features", "selected_population"),
        ("population_opacity", "selected_population"),
    ],
)
def test_changed_population_rejected(field, reason):
    _, arrays, plan = controls()
    execution = dict(selected_points=1, population_sha256=plan["population_sha256"])
    assert len(checker.verify_population(arrays, plan, execution)) == 1
    arrays[field].flat[0 if field != "population_features" else 2] = 0
    with pytest.raises(ValueError, match=reason):
        checker.verify_population(arrays, plan, execution)


@pytest.mark.parametrize("field,value", [("selected_points", 2), ("population_sha256", "0" * 64)])
def test_false_population_identity_rejected(field, value):
    _, arrays, plan = controls()
    execution = dict(selected_points=1, population_sha256=plan["population_sha256"])
    execution[field] = value
    with pytest.raises(ValueError, match="population_identity"):
        checker.verify_population(arrays, plan, execution)


def test_complete_requires_all_checkpoints_partial_does_not():
    checker.completion_check(dict(progress_checks=1), False, 2)
    checker.completion_check(dict(progress_checks=2), True, 2)
    with pytest.raises(ValueError, match="missing_completion_checkpoint"):
        checker.completion_check(dict(progress_checks=1), True, 2)


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("extra_file", "raw_file_set"),
        ("missing_arm", "result.json"),
        ("arm", "arm_identity"),
        ("width", "arm_identity"),
        ("time", "run_time"),
        ("materialization", "materialization_count"),
        ("scope", "execution_scope"),
        ("source", "initialization_identity"),
        ("producer_time", "producer_time"),
        ("producer_memory", "producer_memory"),
        ("records", "record_binding"),
        ("mask", "scalar_mask"),
        ("output", "output_budget"),
        ("changed_source", "source_changed"),
    ],
)
def test_raw_corruption_rejected(acquired, mutation, reason):
    root, raw, source, plan, _ = acquired

    def alter(name, fn):
        path = raw / name
        data = json.loads(path.read_bytes())
        fn(data)
        path.write_bytes(encode(data))

    if mutation == "extra_file":
        (raw / "extra").write_text("unregistered")
    elif mutation == "missing_arm":
        (raw / "exact/result.json").unlink()
    elif mutation in {"arm", "width", "time", "materialization"}:
        field, value = dict(
            arm=("aggregation", "quantized"),
            width=("width", True),
            time=("elapsed_seconds", 36),
            materialization=("materialization_queries", 0),
        )[mutation]
        alter("exact/result.json", lambda d: d.update({field: value}))
    elif mutation == "scope":
        alter("execution.json", lambda d: d.update(provider_spend=1))
    elif mutation == "source":
        alter("initialized.json", lambda d: d.update(source_commit="0" * 40))
    elif mutation == "producer_time":
        alter("execution.json", lambda d: d.update(elapsed_seconds=121))
    elif mutation == "producer_memory":
        alter("execution.json", lambda d: d.update(peak_rss_bytes=1024**3 + 1))
    elif mutation == "records":
        alter("execution.json", lambda d: d["records"].pop())
    elif mutation == "mask":
        (raw / "exact/selected/mask_000.bin").write_bytes(b"\x01")
    elif mutation == "output":
        plan["max_output_bytes"] = 1
        (root / BASE / "PLAN.json").write_bytes(encode(plan))
    elif mutation == "changed_source":
        plan["attempt_budget"] += 1
        (root / BASE / "PLAN.json").write_bytes(encode(plan))
    with pytest.raises((ValueError, FileNotFoundError), match=reason):
        checker.check(root, raw, commit(root))
    assert source != git(root, "rev-parse", "HEAD")


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("initial", "initial_rejected"),
        ("complete", "complete_type"),
        ("horizon", "depth_budget"),
        ("scope", "attempt_depth_scope"),
        ("beam", "beam_replay"),
        ("grouping", "grouping_replay"),
        ("partition", "retention_partition"),
        ("false_budget", "budget_partial_depth"),
        ("false_horizon", "false_horizon"),
    ],
)
def test_mechanical_audit_known_bads(acquired, mutation, reason):
    _, raw, _, plan, _ = acquired
    folder = raw / "exact"
    attempts = [json.loads(line) for line in (folder / "attempts.jsonl").read_bytes().splitlines()]
    depths = [json.loads(line) for line in (folder / "depths.jsonl").read_bytes().splitlines()]
    result = json.loads((folder / "result.json").read_bytes())
    if mutation == "initial":
        attempts[0]["reason"] = "collision"
    elif mutation == "complete":
        depths[0]["complete"] = 1
    elif mutation == "horizon":
        plan["max_actions"] = 1
    elif mutation == "scope":
        depths.pop()
    elif mutation == "beam":
        depths[0]["beam"] = []
    elif mutation == "grouping":
        depths[0]["cell_representatives"] = []
    elif mutation == "partition":
        depths[0]["width_removed"] += 1
    else:
        result["stop"] = "attempt_budget" if mutation == "false_budget" else "horizon"
        result["selected"] = None
        trace_path = folder / "selected/trace.json"
        trace_path.write_bytes(encode([attempts[0]]))
    (folder / "attempts.jsonl").write_bytes(b"".join(encode(r) for r in attempts))
    (folder / "depths.jsonl").write_bytes(b"".join(encode(r) for r in depths))
    with pytest.raises(ValueError, match=reason):
        audit_run(folder, result, plan)


def test_partial_budget_and_time_rules(tmp_path):
    from experiments.iter158_constraint_aware_search.search import summary
    from experiments.iter159_route_search_qualification.run import query_for, retain_trace
    from experiments.iter161_grouping_width_ablation.search import search

    geometry, arrays, plan = controls()
    plan["attempt_budget"] = 1
    query = query_for(
        dict(geometry=geometry, points=arrays["selected_xyz"], ground=arrays["ground_poses"])
    )
    events = dict(attempt=[], depth=[])
    result = search(
        geometry, OLD, plan, lambda s: summary(query(s)), lambda k, r: events[k].append(r), "exact"
    )
    trace = result.pop("trace")
    result.update(aggregation="exact", width=24)
    retain_trace(tmp_path / "selected", trace, query)
    for kind, filename in [("attempt", "attempts"), ("depth", "depths")]:
        (tmp_path / (filename + ".jsonl")).write_bytes(b"".join(encode(r) for r in events[kind]))
    _, retention = audit_run(tmp_path, result, plan)
    assert result["stop"] == "attempt_budget" and retention["retained"] == 0
    mutated = copy.deepcopy(result)
    mutated["stop"] = "time_budget"
    with pytest.raises(ValueError, match="false_time_budget"):
        audit_run(tmp_path, mutated, plan)
    mutated["elapsed_seconds"] = plan["per_run_seconds"]
    audit_run(tmp_path, mutated, plan)
    events["depth"][0]["grouping_removed"] = 0
    (tmp_path / "depths.jsonl").write_bytes(encode(events["depth"][0]))
    with pytest.raises(ValueError, match="partial_fields"):
        audit_run(tmp_path, result, plan)


def test_source_encoding_rejected(tmp_path):
    with pytest.raises(ValueError, match="source_encoding"):
        source_check(tmp_path, {}, "typo")


@pytest.mark.parametrize("acquired", [{"attempt_budget": 1}], indirect=True)
def test_admitted_misses_are_contradicted_not_invalid(acquired):
    root, raw, _, _, _ = acquired
    result = checker.check(root, raw, commit(root))
    assert result["status"] == "contradicted"
    assert result["complete_runs"] == result["candidate_completions"] == result["invalid_runs"] == 0
    assert result["incomplete_runs"] == 2 and result["verified_states"] == 2
    assert result["progress_checks"] == 0


def test_initialized_failure_retains_invalid_record(acquired, monkeypatch):
    root, raw, source, _, _ = acquired

    def fail(*args):
        raise ValueError("known_bad_input")

    monkeypatch.setattr(producer, "inputs", fail)
    failed = raw.parent / "failed"
    with pytest.raises(ValueError, match="known_bad_input"):
        producer.run(root, failed, source)
    result = json.loads((failed / "failure.json").read_bytes())
    assert result["status"] == "invalid" and result["completed_records"] == 0
    assert (failed / "initialized.json").is_file()
    assert not (failed / "execution.json").exists()
