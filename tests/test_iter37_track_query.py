from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "experiments/iter37_track_query_site_intervention/build_track_direction.py"


def load_module():
    spec = importlib.util.spec_from_file_location("iter37_build_track_direction", BUILD)
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
