from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter25_staged_data_inventory/inventory_roots.py"


def load_inventory_module():
    spec = importlib.util.spec_from_file_location("iter25_inventory_roots", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_split_records_uses_frozen_50_25_remainder_rule():
    module = load_inventory_module()
    records = [{"available_keyframes": 1, "name": f"scene-{idx:04d}"} for idx in range(5)]

    splits = module.split_records(records)

    assert [record["name"] for record in splits["fit"]] == ["scene-0000", "scene-0001"]
    assert [record["name"] for record in splits["calibration"]] == ["scene-0002"]
    assert [record["name"] for record in splits["heldout"]] == ["scene-0003", "scene-0004"]


def test_choose_selected_root_prefers_more_keyframes_then_path():
    module = load_inventory_module()
    reports = [
        {
            "availability_gate": {"pass": True},
            "counts": {"total_keyframe_count": 1200},
            "root": "/b",
        },
        {
            "availability_gate": {"pass": True},
            "counts": {"total_keyframe_count": 1400},
            "root": "/c",
        },
        {
            "availability_gate": {"pass": True},
            "counts": {"total_keyframe_count": 1400},
            "root": "/a",
        },
    ]
    manifests = {"/a": {}, "/b": {}, "/c": {}}

    assert module.choose_selected_root(reports, manifests) == "/a"


def test_token_field_guard_rejects_committed_identifier_keys():
    module = load_inventory_module()

    with pytest.raises(SystemExit, match="nuScenes token fields"):
        module.assert_no_nuscenes_identifier_fields({"sample_token": "secret-like-id"})

    module.assert_no_nuscenes_identifier_fields(
        {
            "scene": "scene-0001",
            "frames": [{"sample_index": 0, "timestamp_us": 123, "path": "samples/CAM/foo.jpg"}],
        }
    )
