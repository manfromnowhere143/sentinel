from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter37_track_query_site_intervention"
BUILD = EXP / "build_track_direction.py"
FEEDER = EXP / "feeder_intervention.py"
ANALYZE = EXP / "analyze_intervention.py"
PATCH = EXP / "server_patch_intervention.py"


def load_module():
    return load_path("iter37_build_track_direction", BUILD)


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(split: str, label: int, values: list[float], index: int) -> dict:
    return {
        "split": split,
        "label": label,
        "scene": f"scene-{index:04d}",
        "sample_index": index,
        "timestamp_us": 1000 + index,
        "sdc_track_query": values,
    }


class DigestModule:
    @staticmethod
    def array_digest(*_arrays):
        return "digest"


def test_iter37_track_features_uses_track_query_only():
    module = load_module()
    payload = {"sdc_track_query": [1.0, 2.0], "sdc_traj_query_last": [99.0]}

    assert module.track_features(payload).tolist() == [1.0, 2.0]


def test_iter37_direction_is_fit_only_track_centroid_delta():
    module = load_module()
    rows = [
        row("fit", 1, [0.0, 0.0, 5.0], 1),
        row("fit", 1, [0.0, 2.0, 5.0], 2),
        row("fit", 0, [2.0, 4.0, 5.0], 3),
        row("fit", 0, [4.0, 6.0, 5.0], 4),
        row("heldout", 1, [100.0, 100.0, 100.0], 5),
    ]

    direction, arrays = module.derive_direction(DigestModule, rows)

    assert direction["feature_count"] == 3
    assert direction["target_site"] == "track_query"
    assert direction["fit_rows"] == 4
    assert direction["dropped_dimension_count"] == 1
    assert direction["constant_dimension_indices"] == [2]
    assert arrays["direction_raw"].tolist() == pytest.approx([3.0, 4.0, 0.0])
    assert direction["direction_raw"] == pytest.approx([3.0, 4.0, 0.0])


def test_iter37_direction_enforces_expected_feature_count_when_requested():
    module = load_module()
    rows = [
        row("fit", 1, [0.0, 0.0, 5.0], 1),
        row("fit", 0, [2.0, 4.0, 5.0], 2),
    ]

    with pytest.raises(ValueError, match="feature_count=3 != 256"):
        module.derive_direction(
            DigestModule,
            rows,
            expected_feature_count=module.EXPECTED_TRACK_FEATURE_COUNT,
        )


def test_iter37_feeder_context_zeroes_prefix_alpha():
    feeder = load_path("iter37_feeder_context", FEEDER)

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


def test_iter37_context_contamination_checks_track_and_wrong_site_hashes():
    analyze = load_path("iter37_analyze_context_contamination", ANALYZE)
    rows = [
        {
            "scene": "scene-a",
            "sample_index": 0,
            "timestamp_us": 1000,
            "target_row": False,
            "intervention_alpha": 0.25,
            "intervention_applied": True,
            "bridge_sha256_changed": True,
            "track_query_sha256_changed": True,
            "sdc_traj_query_last_sha256_changed": True,
        }
    ]

    report = analyze.context_contamination_report(rows)

    assert not report["context_contamination_pass"]
    assert report["context_contamination_failure_count"] == 5


def test_iter37_nonzero_site_report_requires_track_change_and_traj_unchanged():
    analyze = load_path("iter37_analyze_nonzero_track_query", ANALYZE)
    target_rows = []
    for repeat in range(2):
        for index in range(12):
            target_rows.append(
                {
                    "scene": f"scene-{index:04d}",
                    "sample_index": index,
                    "timestamp_us": 1000 + index,
                    "target_row": True,
                    "run_alpha": 0.5,
                    "intervention_alpha": 0.5,
                    "intervention_applied": True,
                    "target_site": "track_query",
                    "original_track_query_sha256": f"track-before-{index}",
                    "intervened_track_query_sha256": f"track-after-{repeat}-{index}",
                    "track_query_sha256_changed": True,
                    "original_sdc_traj_query_last_sha256": f"traj-{index}",
                    "intervened_sdc_traj_query_last_sha256": f"traj-{index}",
                    "sdc_traj_query_last_sha256_changed": False,
                    "original_bridge_sha256": f"bridge-before-{index}",
                    "intervened_bridge_sha256": f"bridge-after-{repeat}-{index}",
                    "bridge_sha256_changed": True,
                }
            )

    report = analyze.nonzero_track_query_report([{"target_rows_data": target_rows}])

    assert report["alpha0p50_track_query_site_pass"]
    assert report["alpha0p50_target_rows_checked"] == 24
    assert report["alpha0p50_unique_target_rows_checked"] == 12
    assert report["alpha0p50_changed_track_query_sha_rows"] == 24
    assert report["alpha0p50_unchanged_sdc_traj_query_last_sha_rows"] == 24


def test_iter37_nonzero_site_report_rejects_wrong_site_mutation():
    analyze = load_path("iter37_analyze_wrong_site", ANALYZE)
    row = {
        "scene": "scene-a",
        "sample_index": 1,
        "timestamp_us": 1001,
        "target_row": True,
        "run_alpha": 0.5,
        "intervention_alpha": 0.5,
        "intervention_applied": True,
        "target_site": "track_query",
        "original_track_query_sha256": "track-before",
        "intervened_track_query_sha256": "track-after",
        "track_query_sha256_changed": True,
        "original_sdc_traj_query_last_sha256": "traj-before",
        "intervened_sdc_traj_query_last_sha256": "traj-after",
        "sdc_traj_query_last_sha256_changed": True,
        "original_bridge_sha256": "bridge-before",
        "intervened_bridge_sha256": "bridge-after",
        "bridge_sha256_changed": True,
    }

    report = analyze.nonzero_track_query_report([{"target_rows_data": [row]}])

    assert not report["alpha0p50_track_query_site_pass"]
    assert any("sdc_traj_query_last_sha" in failure for failure in report["alpha0p50_track_query_site_failures"])


def test_iter37_baseline_projection_normalizes_track_query_metadata():
    analyze = load_path("iter37_analyze_projection", ANALYZE)
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
        "intervention_direction_json": "/model/track_query_direction_iter37.json",
        "iter37_patch_mode": "prefix_preserving_track_query_intervention",
        "target_site": "track_query",
        "track_query_sha256_changed": False,
        "sdc_traj_query_last_sha256_changed": False,
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
    assert "iter37_patch_mode" not in projected
    assert "track_query_sha256_changed" not in projected


def test_iter37_patch_source_mutates_only_track_query_site():
    source = PATCH.read_text(encoding="utf-8")

    assert 'SENTINEL_E37_PREFIX_INTERVENTION' in source
    assert "_e37_alpha = _e37_run_alpha if _e37_target_row else 0.0" in source
    assert 'if len(_e37_direction_values) != 256:' in source
    assert 'outs_motion["sdc_track_query"] = _e37_trk + _e37_alpha * _e37_dir_trk' in source
    assert 'outs_motion["sdc_traj_query"][-1] =' not in source
    assert '"original_track_query_sha256"' in source
    assert '"sdc_traj_query_last_sha256_changed"' in source
    assert "server_patch_sha256" in source
    assert "uniad_source_commit" in source
    assert '@app.post("/sentinel_e37_context")' in source


def test_iter37_run_scripts_pass_patch_provenance_and_track_direction():
    for script_name in (
        "canary_intervention_run.sh",
        "calibration_grid_run.sh",
        "heldout_selected_alpha_run.sh",
    ):
        source = (EXP / script_name).read_text(encoding="utf-8")

        assert "PATCH_SHA256=$(sha256sum \"$PATCH\" | awk '{print $1}')" in source
        assert "UNIAD_COMMIT=$(git -C \"$UNIAD\" rev-parse HEAD)" in source
        assert "missing patch hash or UniAD commit" in source
        assert '-e SENTINEL_E37_PATCH_SHA256="$PATCH_SHA256"' in source
        assert '-e SENTINEL_E37_UNIAD_COMMIT="$UNIAD_COMMIT"' in source
        assert "track_query_direction_iter37.json" in source
