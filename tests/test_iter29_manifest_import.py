import importlib.util
import json


def load_module():
    path = "experiments/iter29_trainval_risk_support_atlas/import_iter28_manifest.py"
    spec = importlib.util.spec_from_file_location("iter29_import", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_iter29_source_manifest_matches_frozen_counts():
    mod = load_module()
    assert mod.sha256_file(mod.ITER28_MANIFEST) == mod.read_expected_sha(mod.ITER28_SHA)
    manifest = json.loads(mod.ITER28_MANIFEST.read_text())
    scene_counts, keyframe_counts = mod.split_counts(manifest)
    assert manifest["root"] == mod.EXPECTED_ROOT
    assert manifest["root_id"] == mod.EXPECTED_ROOT
    assert scene_counts == mod.EXPECTED_SPLIT_SCENES
    assert keyframe_counts == mod.EXPECTED_SPLIT_KEYFRAMES
    assert sum(keyframe_counts.values()) == mod.EXPECTED_TOTAL_KEYFRAMES
    assert manifest["counts"]["known_data_contamination_count"] == 0
    assert manifest["counts"]["mixed_root_keyframe_count"] == 0
    assert mod.count_identifier_fields(manifest) == 0


def test_iter29_token_guard_detects_identifier_fields():
    mod = load_module()
    assert mod.count_identifier_fields({"sample_token": "abc"}) == 1
    assert mod.count_identifier_fields({"frames": [{"sample_index": 0}]}) == 0
