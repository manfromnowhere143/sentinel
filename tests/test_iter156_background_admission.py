"""A real disposable Git graph exercises producer-to-independent-checker admission."""

import hashlib
import json
import subprocess

import numpy as np
import pytest

from experiments.iter156_background_calibration.execute import collect
from experiments.iter156_background_calibration.check import check
from experiments.iter155_background_witness.storage import put_array


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit(root):
    git(root, "add", ".")
    git(root, "commit", "-qm", "Synthetic qualification fixture")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path
    git(root, "init", "-q")
    git(root, "config", "user.name", "Synthetic fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    base = root / "experiments/iter155_background_witness/proof/raw"
    base.mkdir(parents=True)
    p = np.tile(np.array([[0, 0.5, 0]], dtype="<f4"), (101, 1))
    feat = np.zeros((101, 3), dtype="<f4")
    feat[:, 2] = 1
    arrays = {}
    for name, a in [
        ("selected_xyz", p),
        ("population_xyz", p),
        ("population_features", feat),
        ("population_opacity", np.ones(101, dtype="<f4")),
        ("selection", np.ones(101, dtype="u1")),
        ("ground_poses", np.eye(4, dtype="<f8")[None]),
    ]:
        put_array(base, name, a, arrays)
    write(base / "witness.json", {"arrays": arrays})
    event = {
        "event": "step",
        "frame": 1,
        "time": 0.25,
        "after": [0, 0, 0, 0, 0],
        "info": {"ego_box": [0, 0, 0, 1.6, 3.0, 1.5, 0], "collision": True},
        "collision_records": [{"kind": "background", "time": 0.25, "result": True}],
    }
    trace = root / "trace.jsonl"
    trace.write_text(json.dumps(event) + "\n")
    inputs = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in base.iterdir()}
    inputs["trace.jsonl"] = sha(trace.read_bytes())
    plan = {
        "inputs": inputs,
        "source_files": [],
        "selected_points": 101,
        "traces": [{"path": "trace.jsonl", "steps": 1}],
        "step_bindings": 1,
        "unique_states": 1,
        "producer_seconds": 10,
        "checker_seconds": 10,
        "minimum_free_bytes": 0,
        "max_rss_bytes": 1024**3,
        "max_output_bytes": 8 * 1024**2,
        "label_counts": {
            "direct_background": 1,
            "negative_composite_implication": 0,
            "unattributed_collision": 0,
        },
    }
    planpath = root / "plan.json"
    write(planpath, plan)
    source = commit(root)
    raw = root / "raw"
    collect(root, planpath, raw, source)
    raw_commit = commit(root)
    return root, planpath, raw, source, raw_commit


def test_complete_roundtrip(fixture):
    root, plan, raw, _, raw_commit = fixture
    r = check(root, plan, raw, raw_commit)
    assert r["status"] == "supported"
    assert r["states"][0]["count"] == 101
    assert r["label_counts"]["direct_background"] == 1
    assert r["physical_occupancy"] is None


@pytest.mark.parametrize(
    "fault",
    [
        "count",
        "mask",
        "state",
        "index",
        "ground",
        "box",
        "native",
        "missing_state",
        "rows",
        "unknown_to_clear",
        "threshold",
        "ambiguity",
        "timing",
        "source",
        "plan",
        "mask_padding",
        "extra",
        "missing_file",
        "uncommitted",
    ],
)
def test_forged_prediction_is_rejected(fixture, fault):
    root, plan, raw, _, raw_commit = fixture
    path = raw / "predictions.json"
    data = json.loads(path.read_text())
    row = data["states"][0]
    if fault == "count":
        row["count"] = 100
    elif fault == "mask":
        b = bytearray((raw / row["mask"]["path"]).read_bytes())
        b[0] ^= 1
        (raw / row["mask"]["path"]).write_bytes(b)
        row["mask"]["sha256"] = sha(b)
    elif fault == "mask_padding":
        b = bytearray((raw / row["mask"]["path"]).read_bytes())
        b[-1] |= 128
        (raw / row["mask"]["path"]).write_bytes(b)
        row["mask"]["sha256"] = sha(b)
    elif fault == "state":
        row["state"][0] = 1
    elif fault == "index":
        row["index"] = 1
    elif fault == "ground":
        row["height"] = 1
    elif fault == "box":
        row["box"][0][0] += 0.1
    elif fault == "native":
        data["rows"][0]["native_background"] = False
    elif fault == "missing_state":
        data["states"] = []
    elif fault == "rows":
        data["rows"] = []
    elif fault == "unknown_to_clear":
        data["rows"][0]["native_background"] = None
    elif fault == "threshold":
        row["predicate_collision"] = False
    elif fault == "ambiguity":
        row["possible_inside"] = 100
    elif fault == "timing":
        row["query_seconds"] = -1
    elif fault == "source":
        data["source_commit"] = "not-a-commit"
    elif fault == "plan":
        data["plan_sha256"] = "0" * 64
    elif fault == "extra":
        (raw / "extra.txt").write_text("unregistered")
    elif fault == "missing_file":
        (raw / row["mask"]["path"]).unlink()
    elif fault == "uncommitted":
        row["count"] = 100
    write(path, data)
    if fault != "uncommitted":
        raw_commit = commit(root)
    with pytest.raises((ValueError, OSError, subprocess.CalledProcessError)):
        check(root, plan, raw, raw_commit)


@pytest.mark.parametrize("fault", ["input", "source_tree", "plan_tree"])
def test_input_or_frozen_source_drift_rejected(fixture, fault):
    root, plan, raw, _, raw_commit = fixture
    if fault == "input":
        (root / "trace.jsonl").write_text("{}\n")
    elif fault == "source_tree":
        data = json.loads(plan.read_text())
        data["source_files"] = ["not-frozen.py"]
        (root / "not-frozen.py").write_text("changed")
        write(plan, data)
    else:
        data = json.loads(plan.read_text())
        data["producer_seconds"] = 20
        write(plan, data)
    with pytest.raises((ValueError, OSError, subprocess.CalledProcessError)):
        check(root, plan, raw, raw_commit)


@pytest.mark.parametrize("kind", ["direct_disagreement", "negative_composite", "unknown_collision"])
def test_unknown_is_distinct_from_negative_and_mismatch(fixture, kind):
    root, plan, _, _, _ = fixture
    trace = root / "trace.jsonl"
    row = json.loads(trace.read_text())
    counts = {
        "direct_background": 0,
        "negative_composite_implication": 0,
        "unattributed_collision": 0,
    }
    if kind == "direct_disagreement":
        row["collision_records"][0]["result"] = False
        counts["direct_background"] = 1
    else:
        del row["collision_records"]
        row["info"]["collision"] = kind == "unknown_collision"
        counts[
            "negative_composite_implication"
            if kind == "negative_composite"
            else "unattributed_collision"
        ] = 1
    trace.write_text(json.dumps(row) + "\n")
    p = json.loads(plan.read_text())
    p["inputs"]["trace.jsonl"] = sha(trace.read_bytes())
    p["label_counts"] = counts
    write(plan, p)
    source = commit(root)
    raw = root / "second_raw"
    collect(root, plan, raw, source)
    admitted = check(root, plan, raw, commit(root))
    assert admitted["label_counts"] == counts
    assert admitted["status"] == ("supported" if kind == "unknown_collision" else "contradicted")
    assert len(admitted["native_boolean_disagreements"]) == (
        0 if kind == "unknown_collision" else 1
    )


@pytest.mark.parametrize(
    "fault", ["storage", "memory", "output", "deadline", "wrong_source", "dirty"]
)
def test_producer_resource_and_source_gates(fixture, fault):
    root, plan, _, source, _ = fixture
    p = json.loads(plan.read_text())
    changes = {
        "storage": ("minimum_free_bytes", 2**63),
        "memory": ("max_rss_bytes", 0),
        "output": ("max_output_bytes", 1),
        "deadline": ("producer_seconds", 0),
    }
    if fault in changes:
        k, v = changes[fault]
        p[k] = v
        write(plan, p)
        source = commit(root)
    elif fault == "wrong_source":
        source = "0" * 40
    else:
        source = git(root, "rev-parse", "HEAD")
        (root / "trace.jsonl").write_text("changed")
    with pytest.raises((ValueError, TimeoutError, subprocess.CalledProcessError)):
        collect(root, plan, root / "bad_run", source)
