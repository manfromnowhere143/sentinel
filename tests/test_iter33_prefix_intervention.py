from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter33_prefix_preserving_bridge_intervention"
BUILD = EXP / "build_prefix_manifests.py"
FEEDER = EXP / "feeder_intervention.py"
ANALYZE = EXP / "analyze_intervention.py"
PATCH = EXP / "server_patch_intervention.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def target_log_row(index: int, label_name: str = "eligible_lowdiv") -> dict:
    return {
        "scene": "scene-a",
        "split": "calibration",
        "sample_index": index,
        "timestamp_us": 1000 + index,
        "target_row": True,
        "label_name": label_name,
        "intervention_alpha": 0.5,
        "objs": [[100.0, 100.0]],
        "futs": [[[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]]],
        "original_traj": [[0.0, 0.0], [1.0, 0.0]],
        "intervened_traj": [[0.0, 0.0], [2.0, 0.0]],
        "original_cands": [
            [[0.0, 0.0], [0.0, 0.0]],
            [[0.0, 0.0], [1.0, 0.0]],
            [[0.0, 0.0], [0.0, 1.0]],
        ],
        "intervened_cands": [
            [[0.0, 0.0], [0.0, 0.0]],
            [[0.0, 0.0], [2.0, 0.0]],
            [[0.0, 0.0], [0.0, 2.0]],
        ],
    }


def test_iter33_prefix_manifest_counts_all_registered_splits():
    build = load_module("iter33_build_counts", BUILD)

    for split, expected in build.EXPECTED_SPLITS.items():
        source_rows = json.loads(expected["source_manifest"].read_text(encoding="utf-8"))
        manifest = build.make_prefix_manifest(source_rows)
        stats = build.prefix_stats(manifest)

        assert stats["scenes"] == expected["scenes"]
        assert stats["prefix_replay_rows"] == expected["prefix_replay_rows"]
        assert stats["target_rows"] == expected["target_rows"]
        assert stats["context_only_rows"] == expected["context_only_rows"]
        assert stats["target_label_counts"]["eligible_lowdiv"] == expected["eligible_lowdiv"]
        assert stats["target_label_counts"]["benign_control"] == expected["benign_control"]


def test_iter33_feeder_context_zeroes_prefix_alpha():
    feeder = load_module("iter33_feeder_context", FEEDER)

    prefix = feeder.row_context("scene-a", {"target_row": False}, 0, 1000, 0.75)
    target = feeder.row_context(
        "scene-a",
        {
            "target_row": True,
            "source_split": "heldout",
            "source_label": 1,
            "source_label_name": "eligible_lowdiv",
        },
        1,
        1001,
        0.75,
    )

    assert prefix["run_alpha"] == 0.75
    assert prefix["intervention_alpha"] == 0.0
    assert prefix["alpha"] == 0.0
    assert not prefix["target_row"]
    assert target["run_alpha"] == 0.75
    assert target["intervention_alpha"] == 0.75
    assert target["alpha"] == 0.75
    assert target["target_row"]


def test_iter33_analyzer_detects_context_contamination():
    analyze = load_module("iter33_analyze_contamination", ANALYZE)
    rows = [
        {
            "scene": "scene-a",
            "sample_index": 0,
            "timestamp_us": 1000,
            "target_row": False,
            "intervention_alpha": 0.25,
            "intervention_applied": True,
            "bridge_sha256_changed": True,
        }
    ]

    report = analyze.context_contamination_report(rows)

    assert not report["context_contamination_pass"]
    assert report["context_contamination_failure_count"] == 3


def test_iter33_metrics_are_target_only(tmp_path):
    analyze = load_module("iter33_analyze_target_only", ANALYZE)
    analyze.PREFIX_EXPECTED["calibration"] = {
        "non_reset_rows": 4,
        "target_rows": 2,
        "context_only_rows": 2,
    }
    path = tmp_path / "calibration.jsonl"
    rows = [
        {"scene": "scene-a", "sample_index": 0, "timestamp_us": 1000, "target_row": False},
        target_log_row(1, "eligible_lowdiv"),
        {"scene": "scene-a", "sample_index": 2, "timestamp_us": 1002, "target_row": False},
        target_log_row(3, "benign_control"),
    ]
    write_jsonl(path, rows)

    summaries, metrics = analyze.target_metrics_from_paths([path], "calibration")

    assert summaries[0]["row_count_pass"]
    assert summaries[0]["context_only_rows"] == 2
    assert len(metrics) == 2
    assert {row["label_name"] for row in metrics} == {"eligible_lowdiv", "benign_control"}


def test_iter33_alpha_zero_reference_report_checks_targets_only():
    analyze = load_module("iter33_analyze_reference_filter", ANALYZE)
    reference = [
        {
            "scene": "scene-a",
            "sample_index": 1,
            "timestamp_us": 1001,
            "traj": [[0.0, 0.0]],
            "cands": [[[0.0, 0.0]], [[1.0, 0.0]], [[0.0, 1.0]]],
        }
    ]
    canary = [
        {
            "scene": "scene-a",
            "sample_index": 0,
            "timestamp_us": 1000,
            "target_row": False,
            "intervention_alpha": 0.0,
        },
        {
            "scene": "scene-a",
            "sample_index": 1,
            "timestamp_us": 1001,
            "target_row": True,
            "intervention_alpha": 0.0,
            "intervention_applied": False,
            "original_traj": reference[0]["traj"],
            "intervened_traj": reference[0]["traj"],
            "original_cands": reference[0]["cands"],
            "intervened_cands": reference[0]["cands"],
        },
    ]

    report = analyze.alpha_zero_reference_report(canary, reference)

    assert report["alpha_zero_reference_pass"]
    assert report["alpha_zero_rows"] == 1


def test_iter33_baseline_projection_normalizes_noop_metadata():
    analyze = load_module("iter33_analyze_projection", ANALYZE)
    row = {
        "scene": "scene-a",
        "sample_index": 1,
        "timestamp_us": 1001,
        "target_row": True,
        "split": "calibration",
        "source_label": 1,
        "source_label_name": "eligible_lowdiv",
        "intervention_alpha": 0.0,
        "intervention_applied": False,
        "intervention_direction_json": "/model/iter33_direction.json",
        "iter33_patch_mode": "prefix_preserving_bridge_intervention",
        "bridge_sha256": "abc",
        "traj": [[0.0, 0.0]],
        "cands": [[[0.0, 0.0]]],
        "objs": [],
        "scores": [],
        "futs": [],
        "sdc_traj_query_last": [1.0],
        "sdc_traj_query_last_shape": [1],
        "sdc_traj_query_last_dtype": "torch.float32",
        "sdc_track_query": [2.0],
        "sdc_track_query_shape": [1],
        "sdc_track_query_dtype": "torch.float32",
        "runner_timestamp": 1,
        "command": 2,
    }

    projected = analyze.iter32_model_projection(row)

    assert projected["intervention_direction_json"] == ""
    assert projected["iter32_patch_mode"] == "prefix_replay_noop"
    assert "iter33_patch_mode" not in projected


def test_iter33_patch_source_forces_context_alpha_zero():
    source = PATCH.read_text(encoding="utf-8")

    assert 'SENTINEL_E33_PREFIX_INTERVENTION' in source
    assert "_e33_alpha = _e33_run_alpha if _e33_target_row else 0.0" in source
    assert "server_patch_sha256" in source
    assert "uniad_source_commit" in source
    assert "if _e33_target_row and abs(_e33_alpha) > 0.0:" in source
    assert '"original_traj" not in _e33_stash' in source
    assert '"bridge_sha256_changed"' in source
    assert '@app.post("/sentinel_e33_context")' in source


def test_iter33_run_scripts_pass_patch_provenance():
    for script_name in (
        "canary_intervention_run.sh",
        "calibration_grid_run.sh",
        "heldout_selected_alpha_run.sh",
    ):
        source = (EXP / script_name).read_text(encoding="utf-8")

        assert "PATCH_SHA256=$(sha256sum \"$PATCH\" | awk '{print $1}')" in source
        assert "UNIAD_COMMIT=$(git -C \"$UNIAD\" rev-parse HEAD)" in source
        assert "missing patch hash or UniAD commit" in source
        assert '-e SENTINEL_E33_PATCH_SHA256="$PATCH_SHA256"' in source
        assert '-e SENTINEL_E33_UNIAD_COMMIT="$UNIAD_COMMIT"' in source
