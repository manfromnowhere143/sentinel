from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter32_prefix_replay_baseline_recovery"
BUILD = EXP / "build_prefix_manifest.py"
ANALYZE = EXP / "analyze_prefix_replay.py"
ITER31_CANARY = (
    ROOT
    / "experiments/iter31_full_trainval_bridge_intervention/proof-direction/replay_manifest_canary.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def target_row(index: int) -> dict:
    return {
        "scene": "scene-a",
        "sample_index": index,
        "timestamp_us": 1000 + index,
        "split": "calibration",
        "label": index % 2,
        "label_name": "eligible_lowdiv" if index % 2 else "benign_control",
    }


def model_row(index: int, target: bool) -> dict:
    return {
        "scene": "scene-a",
        "sample_index": index,
        "timestamp_us": 1000 + index,
        "target_row": target,
        "command": 2,
        "runner_timestamp": 1 + index,
        "traj": [[float(index), 0.0]],
        "cands": [[[float(index), 0.0]], [[float(index), 1.0]], [[float(index), 2.0]]],
        "objs": [[float(index), 3.0]],
        "futs": [[[[float(index), 4.0]]]],
        "sdc_traj_query_last": [float(index), 5.0],
        "sdc_track_query": [float(index), 6.0],
    }


def gt_row(index: int, target: bool) -> dict:
    return {
        "scene": "scene-a",
        "sample_index": index,
        "timestamp_us": 1000 + index,
        "target_row": target,
        "command": 2,
        "speed": float(index),
        "yaw_rate": float(index) / 10,
        "accel": float(index) / 100,
        "gt_future": [[float(index), 7.0]],
    }


def test_iter32_prefix_manifest_counts_registered_canary():
    build = load_module("iter32_build_prefix_counts", BUILD)
    rows = json.loads(ITER31_CANARY.read_text(encoding="utf-8"))

    manifest = build.make_prefix_manifest(rows)

    assert len(manifest) == 44
    assert sum(1 for row in manifest if row["target_row"]) == 12
    assert sum(1 for row in manifest if not row["target_row"]) == 32


def test_iter32_prefix_manifest_fills_scene_prefixes():
    build = load_module("iter32_build_prefix_synthetic", BUILD)
    rows = [
        {
            "scene": "scene-a",
            "sample_index": 1,
            "timestamp_us": 101,
            "split": "calibration",
            "label": 0,
            "label_name": "benign_control",
        },
        {
            "scene": "scene-a",
            "sample_index": 3,
            "timestamp_us": 103,
            "split": "calibration",
            "label": 1,
            "label_name": "eligible_lowdiv",
        },
    ]

    manifest = build.make_prefix_manifest(rows)

    assert [row["sample_index"] for row in manifest] == [0, 1, 2, 3]
    assert [row["target_row"] for row in manifest] == [False, True, False, True]


def test_iter32_analyzer_reads_split_gzip_and_passes_matching_rows(tmp_path):
    analyze = load_module("iter32_analyze_pass", ANALYZE)
    target_manifest = tmp_path / "targets.json"
    target_rows = [target_row(index) for index in range(12)]
    target_manifest.write_text(json.dumps(target_rows), encoding="utf-8")
    model_rows = [model_row(index, index < 12) for index in range(44)]
    gt_rows = [gt_row(index, index < 12) for index in range(44)]
    log_a = tmp_path / "model_a.jsonl"
    log_b = tmp_path / "model_b.jsonl"
    gt_a = tmp_path / "gt_a.jsonl"
    gt_b = tmp_path / "gt_b.jsonl"
    for path, rows in ((log_a, model_rows), (log_b, model_rows), (gt_a, gt_rows), (gt_b, gt_rows)):
        write_jsonl(path, rows)
    extract_payload = "".join(json.dumps(model_row(index, True), sort_keys=True) + "\n" for index in range(12))
    compressed = gzip.compress(extract_payload.encode("utf-8"))
    part_a = tmp_path / "extract.jsonl.gz.part-0000"
    part_b = tmp_path / "extract.jsonl.gz.part-0001"
    midpoint = len(compressed) // 2
    part_a.write_bytes(compressed[:midpoint])
    part_b.write_bytes(compressed[midpoint:])
    iter29_gt = tmp_path / "iter29_gt.jsonl.gz"
    with gzip.open(iter29_gt, "wt", encoding="utf-8") as f:
        for index in range(12):
            f.write(json.dumps(gt_row(index, True), sort_keys=True) + "\n")

    report = analyze.analyze(
        [log_a, log_b],
        [gt_a, gt_b],
        target_manifest,
        [part_a, part_b],
        iter29_gt,
    )

    assert report["s1_prefix_replay_pass"]
    assert report["max_model_abs_delta_vs_iter29"] == 0.0
    assert report["max_gt_abs_delta_vs_iter29"] == 0.0


def test_iter32_analyzer_fails_model_drift(tmp_path):
    analyze = load_module("iter32_analyze_fail", ANALYZE)
    target_manifest = tmp_path / "targets.json"
    target_rows = [target_row(index) for index in range(12)]
    target_manifest.write_text(json.dumps(target_rows), encoding="utf-8")
    model_rows = [model_row(index, index < 12) for index in range(44)]
    drift_rows = [dict(row) for row in model_rows]
    drift_rows[0] = {**drift_rows[0], "traj": [[999.0, 0.0]]}
    gt_rows = [gt_row(index, index < 12) for index in range(44)]
    paths = {}
    for name, rows in (
        ("log_a", drift_rows),
        ("log_b", model_rows),
        ("gt_a", gt_rows),
        ("gt_b", gt_rows),
        ("extract", [model_row(index, True) for index in range(12)]),
        ("iter29_gt", [gt_row(index, True) for index in range(12)]),
    ):
        paths[name] = tmp_path / f"{name}.jsonl"
        write_jsonl(paths[name], rows)

    report = analyze.analyze(
        [paths["log_a"], paths["log_b"]],
        [paths["gt_a"], paths["gt_b"]],
        target_manifest,
        [paths["extract"]],
        paths["iter29_gt"],
    )

    assert not report["s1_prefix_replay_pass"]
    assert any("traj_max_abs" in failure for failure in report["failures"])
